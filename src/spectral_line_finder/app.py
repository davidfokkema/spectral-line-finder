import typer
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from spectral_line_finder.spectral_lines_table import SpectralLinesTable

app = typer.Typer()


class FindLinesApp(App[None]):
    CSS_PATH = "app.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield SpectralLinesTable()

    def on_mount(self) -> None:
        self.query_one(SpectralLinesTable).action_filter_data()


@app.command()
def main():
    FindLinesApp().run()


if __name__ == "__main__":
    app()
