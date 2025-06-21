from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header


class FindLinesApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()


def main():
    FindLinesApp().run()


if __name__ == "__main__":
    main()
