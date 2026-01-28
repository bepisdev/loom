from pathlib import Path
from typing import Any, Dict

import yaml
from jinja2 import Environment, StrictUndefined, TemplateError
from pydantic import ValidationError

from .schema import BlueprintModel, RoutineModel


class BlueprintParser:
    """Parser for blueprint YAML files with Jinja2 variable templating support."""

    def __init__(self, project_root: str):
        """
        Initialize the parser with a project root directory.

        Args:
            project_root: Path to the project root containing blueprints and tasks
        """
        self.root = Path(project_root)
        self.tasks_dir = self.root / "tasks"

        # Configure Jinja2 environment
        # StrictUndefined ensures we crash if a variable is missing (Safety Feature)
        self.jinja_env = Environment(undefined=StrictUndefined)

    def parse_blueprint(self, filename: str) -> Dict[str, Any]:
        """
        Main entry point. Loads the blueprint, validates it, and
        recursively loads/hydrates all task files.

        Args:
            filename: Name of the blueprint file to parse

        Returns:
            Dictionary containing the execution plan with meta information and tasks

        Raises:
            FileNotFoundError: If blueprint file is not found
            ValueError: If blueprint validation fails or has grammar errors
        """
        blueprint_path = self.root / filename

        # 1. Load the raw Blueprint YAML
        try:
            with open(blueprint_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Blueprint not found at {blueprint_path}")  # noqa: B904
        except yaml.YAMLError as e:
            raise ValueError(f"YAML Syntax Error in {filename}: {e}")  # noqa: B904

        if raw_data is None:
            raise ValueError(f"Blueprint file {filename} is empty")

        # 2. Validate Blueprint against Schema
        try:
            blueprint = BlueprintModel(**raw_data)
        except ValidationError as e:
            raise ValueError(f"Blueprint Grammar Error:\n{e}")  # noqa: B904

        # 3. Create the Execution Plan
        # We transform the Pydantic model into a clean dictionary for the executor
        execution_plan = {
            "meta": {
                "name": blueprint.name,
                "target": blueprint.target,
                "user": blueprint.user,
            },
            "tasks": [],
        }

        # 4. Process the Run List
        print(f"[*] Parsing Blueprint: {blueprint.name}")

        for task_ref in blueprint.run:
            # We pass the global vars down to the routine loader
            routine = self._load_and_render_routine(task_ref.file, blueprint.vars or {})

            execution_plan["tasks"].append(
                {
                    "source_file": task_ref.file,
                    "condition": task_ref.when,
                    "steps": [step.model_dump(by_alias=True) for step in routine.steps],
                }
            )

        return execution_plan

    def _load_and_render_routine(self, filename: str, context: dict[str, Any]) -> RoutineModel:
        """
        Loads a task file, renders variables using Jinja2, and then parses it.

        Args:
            filename: Name of the task file to load
            context: Dictionary of variables to use for Jinja2 rendering

        Returns:
            Validated RoutineModel instance

        Raises:
            FileNotFoundError: If task file is not found
            ValueError: If rendering or validation fails
        """
        task_path = self.tasks_dir / filename

        if not task_path.exists():
            raise FileNotFoundError(f"Task file missing: {task_path}")

        # A. Read Raw Content
        with open(task_path, encoding="utf-8") as f:
            raw_content = f.read()

        # B. Render Variables (The "Hydration" Step)
        # We wrap vars in a namespace so the user types {{ vars.port }}
        render_context = {"vars": context}

        try:
            template = self.jinja_env.from_string(raw_content)
            rendered_yaml = template.render(**render_context)
        except TemplateError as e:
            raise ValueError(f"Variable Error in {filename}: {e}")  # noqa: B904

        # C. Parse the Rendered YAML
        try:
            data = yaml.safe_load(rendered_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML Syntax Error in {filename} after rendering: {e}")  # noqa: B904

        if data is None:
            raise ValueError(f"Task file {filename} is empty after rendering")

        # D. Validate against Routine Schema
        try:
            return RoutineModel(**data)
        except ValidationError as e:
            raise ValueError(f"Task Grammar Error in {filename}:\n{e}")  # noqa: B904
