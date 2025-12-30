"""CLI entry point for spindle."""

import sys

import click

from spindle import __version__
from spindle.config import load_scripts
from spindle.install import install_component
from spindle.runner import run_script

# Shortcut script names that can be run directly
SHORTCUT_SCRIPTS = ["start", "dev", "launch", "build", "test", "deploy"]


class SpindleCLI(click.MultiCommand):
    """Custom MultiCommand that handles dynamic shortcut commands."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        # Return static commands
        return ["install", "run"] + SHORTCUT_SCRIPTS

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Built-in commands
        if cmd_name == "install":
            return install_cmd
        if cmd_name == "run":
            return run_cmd

        # Shortcut commands
        if cmd_name in SHORTCUT_SCRIPTS:
            return _make_shortcut_command(cmd_name)

        return None


def _make_shortcut_command(script_name: str) -> click.Command:
    """Create a click command for a shortcut script."""

    @click.command(name=script_name, help=f"Run the '{script_name}' script if configured")
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    @click.pass_context
    def shortcut_cmd(ctx: click.Context, args: tuple[str, ...]) -> None:
        _run_shortcut(script_name, list(args))

    return shortcut_cmd


def _run_shortcut(script_name: str, args: list[str]) -> None:
    """Run a shortcut script."""
    result = load_scripts()
    if result is None:
        click.echo(
            "No scripts configuration found. Create spindle.yaml, spindle.json, "
            "or [tool.spindle.scripts] in pyproject.toml."
        )
        sys.exit(1)

    scripts, source = result
    if script_name not in scripts:
        available = ", ".join(sorted(scripts.keys()))
        click.echo(
            f"No '{script_name}' script found in {source}. "
            f"Use 'spindle run <name>' for other scripts. Available: {available}"
        )
        sys.exit(1)

    exit_code = run_script(scripts[script_name], args)
    sys.exit(exit_code)


@click.command()
@click.argument("component_identifier")
def install_cmd(component_identifier: str) -> None:
    """Install a component from a Git repository.
    
    COMPONENT_IDENTIFIER: The component to install (e.g., GitHubUser/repo/component)
    """
    success = install_component(component_identifier)
    if not success:
        sys.exit(1)


@click.command(name="run")
@click.argument("name")
@click.argument("script_args", nargs=-1, type=click.UNPROCESSED)
def run_cmd(name: str, script_args: tuple[str, ...]) -> None:
    """Run a configured script from spindle.yaml/json/pyproject.toml.
    
    NAME: The script name to run (as defined in your config)
    """
    result = load_scripts()
    if result is None:
        click.echo(
            "No scripts configuration found. Create spindle.yaml, spindle.json, "
            "or [tool.spindle.scripts] in pyproject.toml."
        )
        sys.exit(1)

    scripts, source = result
    if name not in scripts:
        available = ", ".join(sorted(scripts.keys()))
        click.echo(f"Script '{name}' not found in {source}. Available: {available}")
        sys.exit(1)

    exit_code = run_script(scripts[name], list(script_args))
    sys.exit(exit_code)


@click.command(cls=SpindleCLI)
@click.version_option(version=__version__, prog_name="spindle")
def main() -> None:
    """A tool to install components from Git repositories and run project scripts."""
    pass


if __name__ == "__main__":
    main()
