from typing import Any

from pydantic import BaseModel, Field


class StepModel(BaseModel):
    """
    Represents a single atomic unit of work within a task routine.

    A Step defines a specific action to be taken on the target system,
    mapping directly to an internal module (provider) and its arguments.

    Attributes:
        name (str): A human-readable description of the step, used for logging
            and output display.
        uses (str): The identifier of the internal module/provider to execute
            (e.g., 'apt', 'service', 'file', 'template').
        ensure (str): The desired state of the resource. Defaults to "present".
            Common values include "present", "absent", "latest", "directory".
        with_args (Dict[str, Any]): A dictionary of arguments specific to the
            module defined in `uses`.

            Note: In the YAML file, this field is keyed as `with`. Pydantic
            automatically maps the reserved Python keyword `with` to `with_args`.
    """

    name: str
    uses: str
    ensure: str = "present"  # Default value
    with_args: dict[str, Any] = Field(default_factory=dict, alias="with")


class RoutineModel(BaseModel):
    """
    Represents the structure of a Task file (a 'Routine').

    A Routine is a container for a sequential list of Steps. It does not
    contain global metadata or variables; it strictly defines *how* to
    perform a specific configuration task.

    Attributes:
        steps (List[StepModel]): The ordered list of steps to execute.
    """

    steps: list[StepModel]


class TaskRefModel(BaseModel):
    """
    Represents a reference to a Task file within the Blueprint's execution list.

    This model links the Blueprint to a specific Routine file in the `tasks/`
    directory and optionally attaches conditions for its execution.

    Attributes:
        file (str): The filename of the task routine to execute. The parser
            assumes this file is located relative to the `tasks/` directory.
        when (Optional[str]): A conditional expression string. If provided,
            the task file is only parsed and executed if this expression
            evaluates to True. Defaults to None (always run).
    """

    file: str
    when: str | None = None


class BlueprintModel(BaseModel):
    """
    Represents the root entrypoint configuration (the 'Blueprint').

    The Blueprint acts as the orchestrator. It defines the target environment,
    global variables (context), and the sequence of task files to execute.
    It serves as the 'Source of Truth' for all variables used by downstream tasks.

    Attributes:
        name (str): The display name of the entire provisioning play.
        target (str): The identifier for the host or group of hosts where
            this blueprint applies (e.g., 'web-nodes', 'prod-db').
        user (str): The default system user to use for SSH connections
            (e.g., 'root', 'ubuntu').
        vars (Dict[str, Any]): A global dictionary of variables available to
            all steps in all tasks. These are injected into steps via Jinja2
            templating (e.g., `{{ vars.key }}`). Defaults to an empty dict.
        run (List[TaskRefModel]): An ordered list of task files to execute.
    """

    name: str
    target: str
    user: str
    vars: dict[str, Any] = Field(default_factory=dict)
    run: list[TaskRefModel]
