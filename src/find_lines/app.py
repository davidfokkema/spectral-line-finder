from pathlib import Path
from typing import Annotated, Any

import pandas as pd
import typer
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

from find_lines import data

app = typer.Typer()


class FindLinesApp(App[None]):
    _selected_columns = {
        "element": True,
        "sp_num": True,
        "obs_wl(nm)": True,
        "unc_obs_wl": False,
        "ritz_wl_vac(nm)": True,
        "unc_ritz_wl": False,
        "intens": True,
        "Aki(s^-1)": False,
        "Acc": False,
        "Ei(eV)": True,
        "Ek(eV)": True,
        "conf_i": True,
        "term_i": False,
        "J_i": False,
        "conf_k": True,
        "term_k": False,
        "J_k": False,
        "Type": False,
        "tp_ref": False,
        "line_ref": False,
    }

    def __init__(self, path: Path, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self.db_path = path

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    def on_mount(self):
        self._data = data.read_data_file(self.db_path)
        self.fill_table()

    def fill_table(self):
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        columns = [k for k, v in self._selected_columns.items() if v is True]
        table.add_columns(*columns)
        table.add_rows(
            (
                ("" if pd.isna(x) else x for x in r)
                for _, r in self._data[columns].iterrows()
            )
        )
        self.notify(f"Added {len(self._data)} rows.")


@app.command()
def main(path: Annotated[Path, typer.Argument(exists=True)]):
    FindLinesApp(path).run()


if __name__ == "__main__":
    app()
