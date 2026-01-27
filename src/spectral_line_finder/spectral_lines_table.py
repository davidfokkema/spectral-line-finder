from rich.text import Text
from textual import work
from textual.widgets import DataTable

from spectral_line_finder import data
from spectral_line_finder.filter_data import FilterDataDialog
from spectral_line_finder.select_columns import SelectColumnsDialog
from spectral_line_finder.spectrum_plot import SpectrumPlot
from spectral_line_finder.wavelength_dialog import WavelengthDialog


class SpectralLinesTable(DataTable):
    BINDINGS = [
        ("c", "select_columns", "Select Columns"),
        ("f", "filter_data", "Filter data"),
        ("v", "visualize_spectrum", "Visualize"),
        ("j", "jump", "Jump"),
    ]

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

    filters = data.DataFilters()

    def on_mount(self):
        self.spectrum = data.NistSpectralLines()

    @work
    async def fill_table(self):
        self.loading = True
        self.clear(columns=True)
        self.cursor_type = "row"
        self.add_columns("Color", *self._selected_columns)

        worker = self.get_display_rows(
            display_columns=self._selected_columns, filters=self.filters
        )
        await worker.wait()
        self.add_rows(worker.result)
        self.notify(f"Showing {self.row_count} spectral lines.")
        self.loading = False

    @work(thread=True)
    def get_display_rows(
        self, display_columns, filters
    ) -> list[tuple[Text | str, ...]]:
        try:
            return list(self.spectrum.get_display_rows(display_columns, filters))
        except data.NistDataError as e:
            self.notify(str(e), severity="error")
            return []

    def action_select_columns(self) -> None:
        self.select_columns()

    @work
    async def select_columns(self) -> None:
        selection = await self.app.push_screen_wait(
            SelectColumnsDialog(self._selected_columns)
        )
        if selection is not None:
            self._selected_columns = selection
            self.fill_table()

    def action_filter_data(self) -> None:
        def callback(is_confirmed: bool | None) -> None:
            if is_confirmed:
                if self.filters.elements.elements:
                    self.fill_table()

        self.app.push_screen(FilterDataDialog(self.filters), callback=callback)

    def action_visualize_spectrum(self) -> None:
        try:
            spectral_lines = self.spectrum.get_spectral_lines(filters=self.filters)
            self.app.push_screen(SpectrumPlot(spectral_lines))
        except data.NistDataError as e:
            self.notify(str(e), severity="error")

    def action_jump(self) -> None:
        def callback(value: int | None) -> None:
            if value is not None:
                if (
                    wavelengths := self.spectrum.get_wavelengths(self.filters)
                ) is not None:
                    index = int(wavelengths.searchsorted(value))
                    self.move_cursor(row=index)

        self.app.push_screen(WavelengthDialog(), callback=callback)
