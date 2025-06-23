from pathlib import Path
from typing import Annotated, Any

import typer
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from find_lines.spectral_lines_table import SpectralLinesTable

app = typer.Typer()


class FindLinesApp(App[None]):
    CSS_PATH = "app.tcss"

    def __init__(self, path: Path, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self.db_path = path

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield SpectralLinesTable()

    def on_mount(self) -> None:
        self.query_one(SpectralLinesTable).add_data_from_file(self.db_path)


@app.command()
def main(path: Annotated[Path, typer.Argument(exists=True)]):
    FindLinesApp(path).run()


if __name__ == "__main__":
    app()
