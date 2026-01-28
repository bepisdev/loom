"""Tests for the blueprint_parser module."""

import tempfile
from pathlib import Path

import pytest
import yaml
from src.blueprint_parser.parser import BlueprintParser


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        tasks_dir = project_root / "tasks"
        tasks_dir.mkdir()
        yield project_root


@pytest.fixture
def sample_task_file(temp_project_dir):
    """Create a sample task file."""
    task_content = """
steps:
  - name: Install nginx
    uses: apt
    ensure: present
    with:
      name: nginx
      state: present
      
  - name: Start nginx service
    uses: systemd
    ensure: present
    with:
      name: nginx
      state: started
      enabled: true
"""
    task_path = temp_project_dir / "tasks" / "install_nginx.yaml"
    task_path.write_text(task_content)
    return "install_nginx.yaml"


@pytest.fixture
def sample_task_with_vars(temp_project_dir):
    """Create a task file with Jinja2 variables."""
    task_content = """
steps:
  - name: Configure web server
    uses: template
    ensure: present
    with:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
      port: {{ vars.port }}
      
  - name: Start on port {{ vars.port }}
    uses: systemd
    ensure: present
    with:
      name: nginx
      state: started
"""
    task_path = temp_project_dir / "tasks" / "configure_nginx.yaml"
    task_path.write_text(task_content)
    return "configure_nginx.yaml"


@pytest.fixture
def sample_blueprint(temp_project_dir, sample_task_file):
    """Create a sample blueprint file."""
    blueprint_content = {
        "name": "Web Server Setup",
        "target": "webserver01",
        "user": "admin",
        "run": [
            {"file": sample_task_file}
        ]
    }
    blueprint_path = temp_project_dir / "blueprint.yaml"
    with open(blueprint_path, "w") as f:
        yaml.dump(blueprint_content, f)
    return "blueprint.yaml"


class TestBlueprintParser:
    """Test suite for BlueprintParser class."""

    def test_parser_initialization(self, temp_project_dir):
        """Test parser initializes correctly."""
        parser = BlueprintParser(str(temp_project_dir))
        
        assert parser.root == temp_project_dir
        assert parser.tasks_dir == temp_project_dir / "tasks"
        assert parser.jinja_env is not None

    def test_parse_simple_blueprint(self, temp_project_dir, sample_blueprint):
        """Test parsing a simple blueprint without variables."""
        parser = BlueprintParser(str(temp_project_dir))
        result = parser.parse_blueprint(sample_blueprint)
        
        assert result["meta"]["name"] == "Web Server Setup"
        assert result["meta"]["target"] == "webserver01"
        assert result["meta"]["user"] == "admin"
        assert len(result["tasks"]) == 1
        assert len(result["tasks"][0]["steps"]) == 2

    def test_parse_blueprint_with_variables(self, temp_project_dir, sample_task_with_vars):
        """Test parsing blueprint with Jinja2 variable substitution."""
        blueprint_content = {
            "name": "Nginx Config",
            "target": "webserver01",
            "user": "admin",
            "vars": {
                "port": 8080
            },
            "run": [
                {"file": sample_task_with_vars}
            ]
        }
        blueprint_path = temp_project_dir / "blueprint_vars.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        result = parser.parse_blueprint("blueprint_vars.yaml")
        
        assert len(result["tasks"]) == 1
        # Check that variables were rendered
        steps = result["tasks"][0]["steps"]
        assert steps[0]["with"]["port"] == 8080
        assert "8080" in steps[1]["name"]

    def test_parse_blueprint_with_when_condition(self, temp_project_dir, sample_task_file):
        """Test parsing blueprint with conditional execution."""
        blueprint_content = {
            "name": "Conditional Setup",
            "target": "webserver01",
            "user": "admin",
            "run": [
                {"file": sample_task_file, "when": "ansible_os_family == 'Debian'"}
            ]
        }
        blueprint_path = temp_project_dir / "conditional.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        result = parser.parse_blueprint("conditional.yaml")
        
        assert result["tasks"][0]["condition"] == "ansible_os_family == 'Debian'"

    def test_blueprint_not_found(self, temp_project_dir):
        """Test error handling when blueprint file doesn't exist."""
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(FileNotFoundError, match="Blueprint not found"):
            parser.parse_blueprint("nonexistent.yaml")

    def test_task_file_not_found(self, temp_project_dir):
        """Test error handling when task file doesn't exist."""
        blueprint_content = {
            "name": "Missing Task",
            "target": "webserver01",
            "user": "admin",
            "run": [
                {"file": "nonexistent_task.yaml"}
            ]
        }
        blueprint_path = temp_project_dir / "blueprint.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(FileNotFoundError, match="Task file missing"):
            parser.parse_blueprint("blueprint.yaml")

    def test_invalid_yaml_syntax(self, temp_project_dir):
        """Test error handling for invalid YAML syntax."""
        blueprint_path = temp_project_dir / "invalid.yaml"
        blueprint_path.write_text("name: Test\ninvalid: yaml: syntax:")
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(ValueError, match="YAML Syntax Error"):
            parser.parse_blueprint("invalid.yaml")

    def test_empty_blueprint_file(self, temp_project_dir):
        """Test error handling for empty blueprint file."""
        blueprint_path = temp_project_dir / "empty.yaml"
        blueprint_path.write_text("")
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(ValueError, match="empty"):
            parser.parse_blueprint("empty.yaml")

    def test_invalid_blueprint_schema(self, temp_project_dir):
        """Test error handling for blueprint that doesn't match schema."""
        blueprint_content = {
            "invalid_field": "value"
            # Missing required fields: name, target, user, run
        }
        blueprint_path = temp_project_dir / "invalid_schema.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(ValueError, match="Blueprint Grammar Error"):
            parser.parse_blueprint("invalid_schema.yaml")

    def test_missing_jinja_variable(self, temp_project_dir):
        """Test error handling when Jinja2 variable is missing."""
        task_content = """
stepuses: shell
    withUse missing var
    action: shell
    params:
      cmd: echo {{ vars.missing_var }}
"""
        task_path = temp_project_dir / "tasks" / "missing_var.yaml"
        task_path.write_text(task_content)
        
        blueprint_content = {
            "name": "Missing Var Test",
            "target": "webserver01",
            "user": "admin",
            "vars": {},  # No variables provided
            "run": [
                {"file": "missing_var.yaml"}
            ]
        }
        blueprint_path = temp_project_dir / "blueprint.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(ValueError, match="Variable Error"):
            parser.parse_blueprint("blueprint.yaml")

    def test_multiple_tasks(self, temp_project_dir, sample_task_file, sample_task_with_vars):
        """Test parsing blueprint with multiple tasks."""
        blueprint_content = {
            "name": "Multi Task Blueprint",
            "target": "webserver01",
            "user": "admin",
            "vars": {"port": 9000},
            "run": [
                {"file": sample_task_file},
                {"file": sample_task_with_vars}
            ]
        }
        blueprint_path = temp_project_dir / "multi_task.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        result = parser.parse_blueprint("multi_task.yaml")
        
        assert len(result["tasks"]) == 2
        assert result["tasks"][0]["source_file"] == sample_task_file
        assert result["tasks"][1]["source_file"] == sample_task_with_vars

    def test_invalid_task_schema(self, temp_project_dir):
        """Test error handling for task file with invalid schema."""
        task_content = """
invalid_field: value
"""
        task_path = temp_project_dir / "tasks" / "invalid_task.yaml"
        task_path.write_text(task_content)
        
        blueprint_content = {
            "name": "Invalid Task Test",
            "target": "webserver01",
            "user": "admin",
            "run": [
                {"file": "invalid_task.yaml"}
            ]
        }
        blueprint_path = temp_project_dir / "blueprint.yaml"
        with open(blueprint_path, "w") as f:
            yaml.dump(blueprint_content, f)
        
        parser = BlueprintParser(str(temp_project_dir))
        
        with pytest.raises(ValueError, match="Task Grammar Error"):
            parser.parse_blueprint("blueprint.yaml")
