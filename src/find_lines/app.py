from pathlib import Path
from typing import Annotated, Any

import typer
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header

from find_lines import data
from find_lines.select_columns import SelectColumnsDialog

app = typer.Typer()


class FindLinesApp(App[None]):
    BINDINGS = [("c", "select_columns", "Select Columns")]
    _selected_columns = [
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
        self.spectrum = data.NistSpectralLines()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    def on_mount(self):
        self.spectrum.read_data_file(self.db_path)
        self.fill_table()

    def fill_table(self):
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        table.add_columns(*self._selected_columns)
        table.add_rows(self.spectrum.get_display_rows(self._selected_columns))
        self.notify(f"Showing {table.row_count} spectral lines.")

    def action_select_columns(self) -> None:
        self.select_columns()

    @work
    async def select_columns(self) -> None:
        self._selected_columns = await self.push_screen_wait(
            SelectColumnsDialog(self._selected_columns)
        )
        self.fill_table()


@app.command()
def main(path: Annotated[Path, typer.Argument(exists=True)]):
    FindLinesApp(path).run()


if __name__ == "__main__":
    app()
