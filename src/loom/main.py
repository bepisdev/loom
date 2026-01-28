"""Main module for loom application."""

import click

from blueprint_parser.parser import BlueprintParser


@click.group()
@click.version_option(version="0.1.0", prog_name="loom")
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
            for idx, task in enumerate(execution_plan['tasks'], 1):
                click.echo(f"\n  Task {idx}: {task['source_file']}")
                if task['condition']:
                    click.echo(f"    Condition: {task['condition']}")
                click.echo(f"    Steps: {len(task['steps'])}")
                for step_idx, step in enumerate(task['steps'], 1):
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
        
        for idx, task in enumerate(execution_plan['tasks'], 1):
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
def init() -> None:
    """
    Initialize a new loom project in the current directory.

    Creates the necessary directory structure for blueprints and tasks.
    """
    from pathlib import Path

    project_root = Path.cwd()
    tasks_dir = project_root / "tasks"
    blueprints_dir = project_root / "blueprints"
    
    try:
        # Create directories
        tasks_dir.mkdir(exist_ok=True)
        blueprints_dir.mkdir(exist_ok=True)
        
        # Create a sample blueprint
        sample_blueprint = blueprints_dir / "example.yaml"
        if not sample_blueprint.exists():
            sample_blueprint.write_text("""name: Example Blueprint
target: localhost
user: root
vars:
  port: 8080
  app_name: myapp

run:
  - file: example_task.yaml
""")
        
        # Create a sample task
        sample_task = tasks_dir / "example_task.yaml"
        if not sample_task.exists():
            sample_task.write_text("""steps:
  - name: Example step
    uses: shell
    ensure: present
    with:
      cmd: echo "Hello from {{ vars.app_name }}"
""")
        
        click.echo("[✓] Loom project initialized successfully!")
        click.echo(f"    Created: {tasks_dir}")
        click.echo(f"    Created: {blueprints_dir}")
        click.echo(f"    Sample blueprint: {sample_blueprint}")
        click.echo(f"    Sample task: {sample_task}")
        click.echo("\nNext steps:")
        click.echo("  1. Edit the blueprint in blueprints/example.yaml")
        click.echo("  2. Run: loom validate blueprints/example.yaml")
        click.echo("  3. Run: loom run blueprints/example.yaml --dry-run")
        
    except Exception as e:
        click.echo(f"[✗] Error initializing project: {e}", err=True)
        raise click.Abort() from e


def main() -> None:
    """Entry point for the loom application."""
    cli(obj={})
