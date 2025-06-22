from pathlib import Path
from typing import Annotated, Any

import pandas as pd
import typer
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

app = typer.Typer()


class FindLinesApp(App[None]):
    def __init__(self, path: Path, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self.db_path = path

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    def on_mount(self):
        df = self.read_data_file()
        table = self.query_one(DataTable)
        columns = [
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
        table.add_columns(*columns)
        table.add_rows(
            (("" if pd.isna(x) else x for x in r) for _, r in df[columns].iterrows())
        )
        self.notify(f"Added {len(df)} rows.")

    def read_data_file(self):
        rows_to_skip = [
            idx
            for idx, row in enumerate(self.db_path.read_text().splitlines())
            if row.startswith("element")
        ][1:]

        extract_columns = ["intens", "Ei(eV)", "Ek(eV)"]

        return (
            pd.read_csv(
                self.db_path, delimiter="\t", usecols=range(20), skiprows=rows_to_skip
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


@app.command()
def main(path: Annotated[Path, typer.Argument(exists=True)]):
    FindLinesApp(path).run()


if __name__ == "__main__":
    app()
