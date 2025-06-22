from pathlib import Path
from typing import Annotated, Any, Generator

import pandas as pd
import typer
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

from find_lines import data

app = typer.Typer()


class FindLinesApp(App[None]):
    _selected_columns = all_columns = [
        "element",
        "sp_num",
        "obs_wl(nm)",
        "ritz_wl_vac(nm)",
        "intens",
        "Ei(eV)",
        "Ek(eV)",
        "conf_i",
        "conf_k",
    ]

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
        table.add_columns(*self._selected_columns)
        table.add_rows(data.get_display_rows(self._data, self._selected_columns))
        self.notify(f"Added {len(self._data)} rows.")


@app.command()
def main(path: Annotated[Path, typer.Argument(exists=True)]):
    FindLinesApp(path).run()


if __name__ == "__main__":
    app()
