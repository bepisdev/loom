"""Tests for the main module."""

from click.testing import CliRunner

from loom.main import cli


def test_cli_help() -> None:
    """Test that CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Loom - A configuration management and provisioning tool" in result.output


def test_cli_version() -> None:
    """Test that CLI version command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_init_command() -> None:
    """Test that init command creates project structure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Loom project initialized successfully" in result.output
        # Verify project directory, main.yaml and tasks directory are created
        from pathlib import Path
        assert Path("my_project").exists()
        assert Path("my_project/main.yaml").exists()
        assert Path("my_project/tasks").exists()
        assert Path("my_project/tasks").is_dir()


def test_init_command_with_name() -> None:
    """Test that init command accepts a custom project name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "Web Server"])
        assert result.exit_code == 0
        assert "Loom project initialized successfully" in result.output
        # Verify project directory and main.yaml contains the custom name
        from pathlib import Path
        assert Path("web_server").exists()
        assert Path("web_server/main.yaml").exists()
        content = Path("web_server/main.yaml").read_text()
        assert "name: Web Server" in content


def test_validate_command_missing_file() -> None:
    """Test that validate command fails gracefully with missing file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "nonexistent.yaml"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_run_command_missing_file() -> None:
    """Test that run command fails gracefully with missing file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "nonexistent.yaml"])
    assert result.exit_code == 1
    assert "Error" in result.output

