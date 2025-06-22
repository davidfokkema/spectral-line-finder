import pathlib
from typing import Generator

import pandas as pd

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


def read_data_file(path: pathlib.Path) -> pd.DataFrame:
    rows_to_skip = [
        idx
        for idx, row in enumerate(path.read_text().splitlines())
        if row.startswith("element")
    ][1:]

    extract_columns = ["intens", "Ei(eV)", "Ek(eV)"]

    return (
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
    df: pd.DataFrame, columns: list[str]
) -> Generator[tuple[str, ...], None, None]:
    for _, row in df[columns].iterrows():
        yield tuple("" if pd.isna(x) else str(x) for x in row)
