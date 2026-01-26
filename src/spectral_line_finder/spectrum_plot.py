from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Footer
from textual_plot import PlotWidget

from spectral_line_finder.data import SpectralLines


class SpectrumPlot(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(
        self,
        spectral_lines: SpectralLines,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.spectral_lines = spectral_lines

    def compose(self) -> ComposeResult:
        yield PlotWidget()
        yield Footer()

    def on_mount(self) -> None:
        plot = self.query_one(PlotWidget)
        plot.margin_left = 1
        for wavelength, color in self.spectral_lines:
            plot.add_v_line(x=wavelength, line_style=color)
        plot.set_xlimits(350.0, 750.0)
        plot.set_yticks([])
        plot.set_xlabel("Wavelength (nm)")

    @on(PlotWidget.ScaleChanged)
    def restrict_zoom(self, event: PlotWidget.ScaleChanged) -> None:
        x_min = max(350.0, event.x_min)
        x_max = min(750.0, event.x_max)
        if x_min != event.x_min or x_max != event.x_max:
            self.query_one(PlotWidget).set_xlimits(x_min, x_max)
