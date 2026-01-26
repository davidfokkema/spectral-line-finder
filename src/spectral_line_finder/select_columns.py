from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, SelectionList

from spectral_line_finder.data import NistSpectralLines


class SelectColumnsDialog(ModalScreen):
    BINDINGS = [("escape", "discard_choices", "Close and Discard Choices")]

    def __init__(
        self,
        initial_selected: list[str],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.initial_selected = initial_selected

    def compose(self) -> ComposeResult:
        yield Footer()
        with Vertical():
            yield SelectionList[str](
                *(
                    (col, col, col in self.initial_selected)
                    for col in NistSpectralLines.all_columns
                )
            )
            yield Button("Confirm Choices", variant="primary")

    def on_button_pressed(self) -> None:
        self.dismiss(
            [
                col
                for col in NistSpectralLines.all_columns
                if col in self.query_one(SelectionList).selected
            ]
        )

    def action_discard_choices(self) -> None:
        self.dismiss(None)
