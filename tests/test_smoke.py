from typer.testing import CliRunner

from norfolk_path.cli import app


def test_cli_is_alive():
    result = CliRunner().invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "is alive" in result.stdout
