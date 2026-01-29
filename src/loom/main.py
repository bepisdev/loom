"""Main module for loom application."""

import click
from blueprint_parser.parser import BlueprintParser

from . import __version__

@click.group()
@click.version_option(version=__version__, prog_name="loom")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Loom - A configuration management and provisioning tool.

    Loom reads blueprint files and executes tasks to configure target systems.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.argument("blueprint", type=click.Path(exists=True))
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Path to the project root directory containing blueprints and tasks.",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Parse and validate the blueprint without executing tasks.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
def run(blueprint: str, project_root: str, dry_run: bool, verbose: bool) -> None:
    """
    Parse and execute a blueprint file.

    BLUEPRINT: Path to the blueprint YAML file to execute.
    """
    try:
        parser = BlueprintParser(project_root)

        if verbose:
            click.echo(f"[*] Loading blueprint: {blueprint}")

        execution_plan = parser.parse_blueprint(blueprint)

        if verbose or dry_run:
            click.echo(f"\n[✓] Blueprint parsed successfully: {execution_plan['meta']['name']}")
            click.echo(f"    Target: {execution_plan['meta']['target']}")
            click.echo(f"    User: {execution_plan['meta']['user']}")
            click.echo(f"    Tasks: {len(execution_plan['tasks'])}")

        if dry_run:
            click.echo("\n[*] Dry run mode - no tasks will be executed")
            for idx, task in enumerate(execution_plan["tasks"], 1):
                click.echo(f"\n  Task {idx}: {task['source_file']}")
                if task["condition"]:
                    click.echo(f"    Condition: {task['condition']}")
                click.echo(f"    Steps: {len(task['steps'])}")
                for step_idx, step in enumerate(task["steps"], 1):
                    click.echo(f"      {step_idx}. {step['name']} (uses: {step['uses']})")
        else:
            click.echo("\n[*] Execution not yet implemented")
            click.echo("    Use --dry-run to validate the blueprint")

    except FileNotFoundError as e:
        click.echo(f"[✗] Error: {e}", err=True)
        raise click.Abort() from e
    except ValueError as e:
        click.echo(f"[✗] Validation Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"[✗] Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.argument("blueprint", type=click.Path(exists=True))
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Path to the project root directory containing blueprints and tasks.",
)
def validate(blueprint: str, project_root: str) -> None:
    """
    Validate a blueprint file without executing it.

    BLUEPRINT: Path to the blueprint YAML file to validate.
    """
    try:
        parser = BlueprintParser(project_root)
        execution_plan = parser.parse_blueprint(blueprint)

        click.echo(f"[✓] Blueprint is valid: {execution_plan['meta']['name']}")
        click.echo(f"    Target: {execution_plan['meta']['target']}")
        click.echo(f"    User: {execution_plan['meta']['user']}")
        click.echo(f"    Tasks: {len(execution_plan['tasks'])} task(s) found")

        for idx, task in enumerate(execution_plan["tasks"], 1):
            click.echo(f"      {idx}. {task['source_file']} ({len(task['steps'])} step(s))")

    except FileNotFoundError as e:
        click.echo(f"[✗] Error: {e}", err=True)
        raise click.Abort() from e
    except ValueError as e:
        click.echo(f"[✗] Validation Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"[✗] Unexpected error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.argument("name", required=False, default="example")
@click.option(
    "--directory",
    "-d",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="Directory where the project should be initialized.",
)
def init(name: str, directory: str) -> None:
    """
    Initialize a new loom project.

    Creates the necessary directory structure for blueprints and tasks,
    and generates a starter blueprint with the specified name.

    NAME: Name for the blueprint (default: example). This will be used
    for the blueprint filename and internal name.
    """
    from pathlib import Path

    project_root = Path(directory).resolve()
    tasks_dir = project_root / "tasks"
    blueprints_dir = project_root / "blueprints"

    # Sanitize the name for use as filename
    safe_name = name.lower().replace(" ", "_")
    blueprint_filename = f"{safe_name}.yaml"
    task_filename = f"{safe_name}_task.yaml"

    # Create a display name (capitalize words)
    display_name = " ".join(word.capitalize() for word in name.replace("_", " ").split())

    try:
        # Create directories
        tasks_dir.mkdir(parents=True, exist_ok=True)
        blueprints_dir.mkdir(parents=True, exist_ok=True)

        # Create the blueprint
        blueprint_path = blueprints_dir / blueprint_filename
        if blueprint_path.exists():
            click.echo(f"[!] Warning: Blueprint already exists at {blueprint_path}")
            if not click.confirm("    Overwrite?"):
                click.echo("[*] Initialization cancelled")
                return

        blueprint_path.write_text(f"""name: {display_name}
target: localhost
user: root
vars:
  port: 8080
  app_name: {safe_name}

run:
  - file: {task_filename}
""")

        # Create the task
        task_path = tasks_dir / task_filename
        if task_path.exists():
            click.echo(f"[!] Warning: Task file already exists at {task_path}")
            if not click.confirm("    Overwrite?"):
                click.echo("[*] Task file not created")
            else:
                task_path.write_text("""steps:
  - name: Example step for {{ vars.app_name }}
    uses: shell
    ensure: present
    with:
      cmd: echo "Hello from {{ vars.app_name }}"
""")
        else:
            task_path.write_text("""steps:
  - name: Example step for {{ vars.app_name }}
    uses: shell
    ensure: present
    with:
      cmd: echo "Hello from {{ vars.app_name }}"
""")

        click.echo("[✓] Loom project initialized successfully!")
        click.echo(f"    Project root: {project_root}")
        click.echo(f"    Tasks directory: {tasks_dir}")
        click.echo(f"    Blueprints directory: {blueprints_dir}")
        click.echo(f"    Blueprint: {blueprint_path}")
        click.echo(f"    Task: {task_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Edit the blueprint in blueprints/{blueprint_filename}")
        click.echo(f"  2. Run: loom validate blueprints/{blueprint_filename}")
        click.echo(f"  3. Run: loom run blueprints/{blueprint_filename} --dry-run")

    except Exception as e:
        click.echo(f"[✗] Error initializing project: {e}", err=True)
        raise click.Abort() from e


def main() -> None:
    """Entry point for the loom application."""
    cli(obj={})
