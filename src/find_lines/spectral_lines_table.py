from pathlib import Path

from textual import work
from textual.widgets import DataTable

from find_lines import data
from find_lines.select_columns import SelectColumnsDialog


class SpectralLinesTable(DataTable):
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

    def on_mount(self):
        self.spectrum = data.NistSpectralLines()

    def add_data_from_file(self, path: Path) -> None:
        self.spectrum.read_data_file(path)
        self.fill_table()

    def fill_table(self):
        self.clear(columns=True)
        self.cursor_type = "row"
        self.add_columns(*self._selected_columns)
        self.add_rows(self.spectrum.get_display_rows(self._selected_columns))
        self.notify(f"Showing {self.row_count} spectral lines.")

    def action_select_columns(self) -> None:
        self.select_columns()

    @work
    async def select_columns(self) -> None:
        self._selected_columns = await self.app.push_screen_wait(
            SelectColumnsDialog(self._selected_columns)
        )
        self.fill_table()
