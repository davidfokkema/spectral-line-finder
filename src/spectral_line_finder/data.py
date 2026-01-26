import importlib.resources
import io
from dataclasses import dataclass, field, fields
from typing import Any, Generator, TypeAlias

import httpx
import numpy as np
import pandas as pd
from rich.text import Text

from spectral_line_finder.cache import cache

SpectralLines: TypeAlias = list[tuple[float, str]]


@dataclass
class ElementFilter:
    elements: list[str]


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
    elements: ElementFilter = field(default_factory=lambda: ElementFilter([]))
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

    @cache.memoize()
    def load_data_from_nist(self, element: str) -> pd.DataFrame:
        url = f"https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra={element}&output_type=0&low_w=&upp_w=&unit=1&de=0&plot_out=0&I_scale_type=1&format=3&line_out=0&remove_js=on&en_unit=1&output=0&bibrefs=1&page_size=15&show_obs_wl=1&show_calc_wl=1&unc_out=1&order_out=0&max_low_enrg=&show_av=2&max_upp_enrg=&tsb_value=0&min_str=&A_out=0&intens_out=on&max_str=&allowed_out=1&forbid_out=1&min_accur=&min_intens=&conf_out=on&term_out=on&enrg_out=on&J_out=on&submit=Retrieve+Data"

        data = httpx.get(url).text

        # Find header rows, interspersed in the data
        rows_to_skip = [
            idx
            for idx, row in enumerate(data.splitlines())
            if row.startswith("element")
        ][1:]

        extract_columns = ["intens", "Ei(eV)", "Ek(eV)", "ritz_wl_vac(nm)"]

        df = (
            pd.read_csv(
                io.StringIO(data),
                delimiter="\t",
                usecols=range(20),
                skiprows=rows_to_skip,
            )
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
        wavelength = df["ritz_wl_vac(nm)"].fillna(df["obs_wl(nm)"])
        df["wavelength"] = wavelength
        rgb_colors = wavelength.apply(wavelength_to_rgb)
        df[["r", "g", "b"]] = pd.DataFrame(rgb_colors.to_list(), index=df.index)
        return df

    def get_display_rows(
        self, display_columns: list[str], filters: DataFilters
    ) -> Generator[tuple[Text | str, ...], None, None]:
        df = self._get_filtered_dataframe(filters)

        columns_to_fetch = display_columns + ["r", "g", "b"]
        filtered_df = df[columns_to_fetch]
        for _, row in filtered_df.iterrows():
            r, g, b = row["r"], row["g"], row["b"]
            color_swatch = Text("█████", style=f"rgb({r},{g},{b})")
            display_values = tuple(
                "" if pd.isna(row[c]) else str(row[c]) for c in display_columns
            )
            yield (color_swatch,) + display_values

    def _get_filtered_dataframe(self, filters: DataFilters) -> pd.DataFrame:
        # Read all elements
        dfs = [
            self.load_data_from_nist(element) for element in filters.elements.elements
        ]
        # Stack them into a single dataframe
        df = pd.concat(dfs, ignore_index=True).sort_values(by="wavelength")

        mask = pd.Series(True, index=df.index)
        for field_ in (f for f in fields(filters)):
            filter = getattr(filters, field_.name)
            if isinstance(filter, (MinMaxFilter, MinMaxNanFilter, IntegerMinMaxFilter)):
                if filter.min is not None:
                    mask &= df[filter.col_name] >= filter.min
                if filter.max is not None:
                    mask &= df[filter.col_name] <= filter.max
            if isinstance(filter, MinMaxNanFilter):
                if not filter.show_nan:
                    mask &= df[filter.col_name].notna()
        return df.loc[mask]

    def get_spectral_lines(self, filters: DataFilters) -> SpectralLines:
        df = self._get_filtered_dataframe(filters)
        return [
            (row["wavelength"], f"#{row['r']:02x}{row['g']:02x}{row['b']:02x}")
            for _, row in df.iterrows()
        ]


# Load CIE 1931 2° Standard Observer data globally
with importlib.resources.path(
    "spectral_line_finder", "CIE_xyz_1931_2deg.csv"
) as data_path:
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


def xyz_to_srgb(x, y, z):
    """Convert CIE XYZ to sRGB values.

    Args:
        x, y, z (float): CIE XYZ values

    Returns:
        tuple: (R, G, B) values in range [0, 1]
    """
    # XYZ to linear RGB transformation matrix (sRGB/Rec.709)
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b = 0.0557 * x - 0.2040 * y + 1.0570 * z

    # sRGB gamma correction
    def gamma_correct(val):
        if val > 0.0031308:
            return 1.055 * (val ** (1 / 2.4)) - 0.055
        else:
            return 12.92 * val

    r = gamma_correct(r)
    g = gamma_correct(g)
    b = gamma_correct(b)

    return np.clip([r, g, b], 0, 1)


def wavelength_to_rgb(wavelength: float) -> tuple[int, int, int]:
    """Convert wavelength to sRGB values.

    Args:
        wavelength: Wavelength in nanometers

    Returns:
        The (R, G, B) values as a tuple in range [0, 255].
    """
    x, y, z = wavelength_to_xyz(wavelength)
    r, g, b = xyz_to_srgb(x, y, z)
    return int(r * 255), int(g * 255), int(b * 255)
