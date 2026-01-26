import re

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.validation import Integer, Number, ValidationResult, Validator
from textual.widgets import Button, Checkbox, Footer, Input, Label

from spectral_line_finder.data import (
    DataFilters,
    ElementFilter,
    MinMaxNanFilter,
)

re_element = re.compile(r"^[A-Z][a-z]?(?:,\s*[A-Z][a-z]?)*$")


class ElementsValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        if re_element.fullmatch(value):
            return self.success()
        else:
            return self.failure("Malformed element list")


class FilterDataDialog(ModalScreen):
    BINDINGS = [
        ("escape", "discard_choices", "Close and Discard Choices"),
        ("ctrl+y", "confirm_choices", "Confirm and Close"),
    ]

    AUTO_FOCUS = "#elements"

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
            with HorizontalGroup():
                yield Label("Elements:")
                yield Input(
                    placeholder="H, He, Li",
                    value=", ".join(self.filters.elements.elements),
                    validators=[ElementsValidator()],
                    id="elements",
                )
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
                    filter = getattr(self.filters, name)
                    if hasattr(filter, "show_nan"):
                        yield Checkbox(
                            label="Show empty",
                            value=filter.show_nan,
                            id=f"{name}_show_nan",
                        )
            yield Button("Confirm and Close", variant="primary")

    @on(Button.Pressed)
    def action_confirm_choices(self) -> None:
        for input in self.query(Input):
            if not input.is_valid:
                self.notify("Please fix invalid input.", severity="error")
                return

        elements: ElementFilter = self.filters.elements
        elements.elements = [
            stripped
            for e in self.query_one("#elements", Input).value.split(",")
            if (stripped := e.strip())
        ]
        for name in ["sp_num", "obs_wl", "intens", "Ei", "Ek"]:
            filter: MinMaxNanFilter = getattr(self.filters, name)
            min_value = self.query_one(f"#{name}_min", Input).value
            filter.min = float(min_value) if min_value else None
            max_value = self.query_one(f"#{name}_max", Input).value
            filter.max = float(max_value) if max_value else None
            try:
                show_nan = self.query_one(f"#{name}_show_nan", Checkbox).value
                filter.show_nan = show_nan
            except NoMatches:
                pass
        self.dismiss(True)

    def action_discard_choices(self) -> None:
        self.dismiss(False)
