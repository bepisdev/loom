# Loom

A configuration management and provisioning tool.

## Project Structure

Each Loom project follows a simple structure:

```
my-project/
├── main.yaml          # Main blueprint file
└── tasks/             # Task definitions
    ├── setup.yaml
    └── deploy.yaml
```

## Quick Start

### Initialize a New Project

```bash
# Create a new project directory with default name
loom init

# Create a project directory named "webserver"
loom init webserver

# Create a project with a multi-word name (creates "web_server" directory)
loom init "Web Server"

# Create a project in a specific parent directory
loom init "Database Setup" --directory /projects
# Creates: /projects/database_setup/main.yaml
```

This will create a directory structure like:
```
webserver/
├── main.yaml
└── tasks/
    └── webserver_task.yaml
```

### Validate a Blueprint

```bash
# Validate main.yaml in current directory
loom validate

# Validate a specific blueprint file
loom validate path/to/blueprint.yaml
```

### Run a Blueprint

```bash
# Dry run (validate without executing)
loom run --dry-run

# Run with verbose output
loom run --verbose

# Run a specific blueprint
loom run path/to/blueprint.yaml
```

## Blueprint Format

The `main.yaml` blueprint file defines your configuration:

```yaml
name: My Project
target: webserver01
user: admin
vars:
  port: 8080
  app_name: myapp

run:
  - file: setup_task.yaml
  - file: deploy_task.yaml
    when: ansible_os_family == 'Debian'
```

## Task Format

Task files in the `tasks/` directory define the steps:

```yaml
steps:
  - name: Install nginx
    uses: apt
    ensure: present
    with:
      name: nginx
      state: present

  - name: Configure port
    uses: template
    with:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
      port: "{{ vars.port }}"
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run loom
uv run loom --help
```
