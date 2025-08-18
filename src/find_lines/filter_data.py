from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.screen import ModalScreen
from textual.validation import Integer, Number
from textual.widgets import Button, Checkbox, Footer, Input, Label

from find_lines.data import DataFilters, MinMaxNanFilter


class FilterDataDialog(ModalScreen):
    BINDINGS = [("escape", "discard_choices", "Close and Discard Choices")]

    def __init__(
        self,
        initial_filters: DataFilters,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.filters = initial_filters

    def compose(self) -> ComposeResult:
        yield Footer()
        with VerticalScroll():
            for label, name, Validator in [
                ("Ionization Stage", "sp_num", Integer),
                ("Observed Wavelength", "obs_wl", Number),
                ("Intensity", "intens", Number),
                ("Initial Energy", "Ei", Number),
                ("Final Energy", "Ek", Number),
            ]:
                with HorizontalGroup():
                    filter = getattr(self.filters, name)
                    yield Label(f"{label}: ")
                    yield Input(
                        placeholder="Min",
                        value=str(filter.min) if filter.min is not None else "",
                        validators=[Validator()],
                        valid_empty=True,
                        id=f"{name}_min",
                    )
                    yield Input(
                        placeholder="Max",
                        value=str(filter.max) if filter.max is not None else "",
                        validators=[Validator()],
                        valid_empty=True,
                        id=f"{name}_max",
                    )
                    yield Checkbox(
                        label="Show empty", value=filter.show_nan, id=f"{name}_show_nan"
                    )
            yield Button("Confirm Choices", variant="primary")

    def on_button_pressed(self) -> None:
        for name in ["sp_num", "obs_wl", "intens", "Ei", "Ek"]:
            filter: MinMaxNanFilter = getattr(self.filters, name)
            min_value = self.query_one(f"#{name}_min", Input).value
            max_value = self.query_one(f"#{name}_max", Input).value
            show_nan = self.query_one(f"#{name}_show_nan", Checkbox).value
            filter.min = float(min_value) if min_value else None
            filter.max = float(max_value) if max_value else None
            filter.show_nan = show_nan
        self.dismiss(True)

    def action_discard_choices(self) -> None:
        self.dismiss(False)
