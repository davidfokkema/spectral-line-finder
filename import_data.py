from pathlib import Path

import pandas as pd

DATAFILE = "lines-na.tsv"

rows_to_skip = [
    idx
    for idx, row in enumerate(Path(DATAFILE).read_text().splitlines())
    if row.startswith("element")
][1:]

extract_columns = ["intens", "Ei(eV)", "Ek(eV)"]

df = (
    pd.read_csv(DATAFILE, delimiter="\t", usecols=range(20), skiprows=rows_to_skip)
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

print(df.dtypes)
print(df.columns)
