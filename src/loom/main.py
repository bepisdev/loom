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
@click.argument("blueprint", type=click.Path(exists=True), required=False, default="main.yaml")
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Path to the project root directory containing main.yaml and tasks.",
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

    BLUEPRINT: Path to the blueprint YAML file to execute (default: main.yaml).
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
@click.argument("blueprint", type=click.Path(exists=True), required=False, default="main.yaml")
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Path to the project root directory containing main.yaml and tasks.",
)
def validate(blueprint: str, project_root: str) -> None:
    """
    Validate a blueprint file without executing it.

    BLUEPRINT: Path to the blueprint YAML file to validate (default: main.yaml).
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
@click.argument("name", required=False, default="my_project")
@click.option(
    "--directory",
    "-d",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="Parent directory where the project directory should be created.",
)
def init(name: str, directory: str) -> None:
    """
    Initialize a new loom project.

    Creates a project directory with main.yaml blueprint and tasks directory.

    NAME: Name for the project directory and blueprint (default: my_project).
    """
    from pathlib import Path

    # Sanitize the name for use as directory name
    safe_name = name.lower().replace(" ", "_")
    
    # Create project directory inside the parent directory
    parent_dir = Path(directory).resolve()
    project_root = parent_dir / safe_name
    tasks_dir = project_root / "tasks"

    # Display name for the blueprint (use original name with proper formatting)
    if name == "my_project":
        display_name = "My Project"
    else:
        display_name = name
    
    task_filename = f"{safe_name}_task.yaml"

    try:
        # Create project root and tasks directory
        if project_root.exists():
            click.echo(f"[!] Warning: Directory already exists at {project_root}")
            if not click.confirm("    Continue and potentially overwrite files?"):
                click.echo("[*] Initialization cancelled")
                return
        
        project_root.mkdir(parents=True, exist_ok=True)
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Create the main blueprint
        blueprint_path = project_root / "main.yaml"
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
        task_path.write_text("""steps:
  - name: Example step for {{ vars.app_name }}
    uses: shell
    ensure: present
    with:
      cmd: echo "Hello from {{ vars.app_name }}"
""")

        click.echo("[✓] Loom project initialized successfully!")
        click.echo(f"    Project directory: {project_root}")
        click.echo(f"    Blueprint: {blueprint_path}")
        click.echo(f"    Tasks directory: {tasks_dir}")
        click.echo(f"    Example task: {task_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. cd {safe_name}")
        click.echo("  2. Edit the blueprint in main.yaml")
        click.echo("  3. Run: loom validate")
        click.echo("  4. Run: loom run --dry-run")

    except Exception as e:
        click.echo(f"[✗] Error initializing project: {e}", err=True)
        raise click.Abort() from e


def main() -> None:
    """Entry point for the loom application."""
    cli(obj={})
