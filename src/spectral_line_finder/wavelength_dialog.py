from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.validation import Number
from textual.widgets import Footer, Input


class WavelengthDialog(ModalScreen):
    BINDINGS = [("escape", "discard_choices", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Footer()
        with Vertical() as container:
            container.border_title = "Jump to wavelength"
            yield Input(
                placeholder="Value",
                validate_on=["submitted"],
                validators=[Number(minimum=0.0)],
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        assert event.validation_result is not None
        if event.validation_result.is_valid:
            self.dismiss(float(event.value))
        else:
            self.notify("Value must be a floating point number.", severity="error")

    def action_discard_choices(self) -> None:
        self.dismiss(None)
