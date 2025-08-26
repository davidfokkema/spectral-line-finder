import pathlib
from dataclasses import dataclass, field, fields
from typing import Any, Generator

import numpy as np
import pandas as pd
from rich.text import Text


@dataclass
class MinMaxFilter:
    col_name: str
    min: float | None = None
    max: float | None = None


@dataclass
class MinMaxNanFilter:
    col_name: str
    min: float | None = None
    max: float | None = None
    show_nan: bool = True


@dataclass
class IntegerMinMaxFilter:
    col_name: str
    min: int | None = None
    max: int | None = None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("min", "max") and value is not None:
            value = int(value)
        super().__setattr__(name, value)


@dataclass
class DataFilters:
    sp_num: IntegerMinMaxFilter = field(
        default_factory=lambda: IntegerMinMaxFilter(col_name="sp_num")
    )
    obs_wl: MinMaxNanFilter = field(
        default_factory=lambda: MinMaxNanFilter(col_name="obs_wl(nm)")
    )
    intens: MinMaxNanFilter = field(
        default_factory=lambda: MinMaxNanFilter(col_name="intens")
    )
    Ei: MinMaxFilter = field(default_factory=lambda: MinMaxFilter(col_name="Ei(eV)"))
    Ek: MinMaxFilter = field(default_factory=lambda: MinMaxFilter(col_name="Ek(eV)"))


class NistSpectralLines:
    all_columns = [
        "element",
        "sp_num",
        "obs_wl(nm)",
        "unc_obs_wl",
        "ritz_wl_vac(nm)",
        "unc_ritz_wl",
        "intens",
        "Aki(s^-1)",
        "Acc",
        "Ei(eV)",
        "Ek(eV)",
        "conf_i",
        "term_i",
        "J_i",
        "conf_k",
        "term_k",
        "J_k",
        "Type",
        "tp_ref",
        "line_ref",
    ]

    def read_data_file(self, path: pathlib.Path) -> None:
        rows_to_skip = [
            idx
            for idx, row in enumerate(path.read_text().splitlines())
            if row.startswith("element")
        ][1:]

        extract_columns = ["intens", "Ei(eV)", "Ek(eV)"]

        self._df = (
            pd.read_csv(path, delimiter="\t", usecols=range(20), skiprows=rows_to_skip)
            .rename(columns={"obs_wl_vac(nm)": "obs_wl(nm)"})
            .rename(columns={col: col + "_" for col in extract_columns})
            .assign(
                **{
                    col: lambda x, col=col: x[col + "_"]
                    .astype(str)
                    .str.extract(r"(\d+\.?\d*)", expand=False)
                    .pipe(pd.to_numeric)
                    for col in extract_columns
                }
            )
        )

    def get_display_rows(
        self, columns: list[str], filters: DataFilters
    ) -> Generator[tuple[Text | str, ...], None, None]:
        df = self._df
        mask = pd.Series(True, index=df.index)
        for field_ in fields(filters):
            filter = getattr(filters, field_.name)
            if filter.min is not None:
                mask &= df[filter.col_name] >= filter.min
            if filter.max is not None:
                mask &= df[filter.col_name] <= filter.max
            if hasattr(filter, "show_nan") and not filter.show_nan:
                mask &= df[filter.col_name].notna()
        filtered_df = df[mask][columns]
        for idx, row in filtered_df.iterrows():
            r, g, b = wavelength_to_rgb(
                row["ritz_wl_vac(nm)"]
                if np.isnan(row["obs_wl(nm)"])
                else row["obs_wl(nm)"]
            )
            yield (Text("█████", style=f"rgb({r},{g},{b})"),) + tuple(
                "" if pd.isna(x) else str(x) for x in row
            )


def wavelength_to_rgb(wavelength: float) -> tuple:
    """Convert a given wavelength of light to approximate RGB values.

    The algorithm for converting wavelength to RGB values is based on the work by Dan Bruton.
    Reference: http://www.physics.sfasu.edu/astro/color/spectra.html

    Args:
    wavelength: A float representing the wavelength of light.

    Returns:
    A tuple containing the RGB values as integers.
    """

    if 380 <= wavelength < 440:
        red = -(wavelength - 440) / (440 - 380)
        green = 0.0
        blue = 1.0
    elif 440 <= wavelength < 490:
        red = 0.0
        green = (wavelength - 440) / (490 - 440)
        blue = 1.0
    elif 490 <= wavelength < 510:
        red = 0.0
        green = 1.0
        blue = -(wavelength - 510) / (510 - 490)
    elif 510 <= wavelength < 580:
        red = (wavelength - 510) / (580 - 510)
        green = 1.0
        blue = 0.0
    elif 580 <= wavelength < 645:
        red = 1.0
        green = -(wavelength - 645) / (645 - 580)
        blue = 0.0
    else:
        red = 1.0
        green = 0.0
        blue = 0.0

    # Adjust the intensity for each color
    if 380 <= wavelength < 420:
        factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
    elif 420 <= wavelength < 645:
        factor = 1.0
    elif 645 <= wavelength < 780:
        factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 645)
    else:
        factor = 0.0

    # Convert to 8-bit RGB values
    red = int(max(0, min(255, (red * factor * 255))))
    green = int(max(0, min(255, (green * factor * 255))))
    blue = int(max(0, min(255, (blue * factor * 255))))

    return red, green, blue
