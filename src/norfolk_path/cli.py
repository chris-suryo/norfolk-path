"""norfolk-path — CLI entry point."""

from __future__ import annotations

import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def _root() -> None:
    """norfolk-path."""


@app.command()
def hello() -> None:
    """Replace me with the first real command."""
    typer.echo("norfolk-path is alive")


def main() -> None:
    app()
