import importlib.resources
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


# Load CIE 1931 2° Standard Observer data globally
with importlib.resources.path("find_lines", "CIE_xyz_1931_2deg.csv") as data_path:
    cie_data = pd.read_csv(data_path, header=None, names=["wavelength", "X", "Y", "Z"])


def wavelength_to_xyz(wavelength: float) -> tuple[float, float, float]:
    """Convert wavelength to CIE XYZ values using linear interpolation.

    Args:
        wavelength: Wavelength in nanometers

    Returns:
        The (X, Y, Z) values as a tuple.
    """
    x = np.interp(wavelength, cie_data["wavelength"], cie_data["X"])
    y = np.interp(wavelength, cie_data["wavelength"], cie_data["Y"])
    z = np.interp(wavelength, cie_data["wavelength"], cie_data["Z"])

    return x, y, z


if __name__ == "__main__":
    wl = 550  # Green light
    x, y, z = wavelength_to_xyz(wl)
    print(f"Wavelength: {wl}nm -> X: {x:.4f}, Y: {y:.4f}, Z: {z:.4f}")

    # Test with multiple wavelengths
    test_wavelengths = [380, 450, 550, 600, 700]
    for wl in test_wavelengths:
        x, y, z = wavelength_to_xyz(wl)
        print(f"{wl}nm: ({x:.4f}, {y:.4f}, {z:.4f})")
