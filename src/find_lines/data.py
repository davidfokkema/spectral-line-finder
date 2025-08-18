import pathlib
from dataclasses import dataclass
from typing import Generator

import pandas as pd


@dataclass
class MinMaxNanFilter:
    min: float | None = None
    max: float | None = None
    show_nan: bool = True


@dataclass
class IntegerMinMaxNanFilter:
    min: int | None = None
    max: int | None = None
    show_nan: bool = True

    def __setattr__(self, name, value):
        if name in ("min", "max") and value is not None:
            value = int(value)
        super().__setattr__(name, value)


@dataclass
class DataFilters:
    sp_num = IntegerMinMaxNanFilter()
    obs_wl = MinMaxNanFilter()
    intens = MinMaxNanFilter()
    Ei = MinMaxNanFilter()
    Ek = MinMaxNanFilter()


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
        self, columns: list[str]
    ) -> Generator[tuple[str, ...], None, None]:
        for _, row in self._df[columns].iterrows():
            yield tuple("" if pd.isna(x) else str(x) for x in row)
