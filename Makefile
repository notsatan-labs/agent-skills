# Makefile - use `make` or `make help` to get a list of commands.
#
# Note - Comments inside this makefile should be made using a single hashtag `#`, lines
# with double hash-tags are help messages that will be printed by the `help` command

# Default Python version or executable to use
PYTHON_EXEC ?= $(shell cat .python-version)

# Virtual environment directory and uv commands with a local PATH
VENV ?= $(HOME)/.virtualenvs/agent-skills
UV := PATH="$(VENV)/bin:$$HOME/.local/bin:$$PATH" UV_PROJECT_ENVIRONMENT="$(VENV)" UV_PYTHON="$(PYTHON_EXEC)" uv
UV_RUN := $(UV) run --locked

# Tracked Python files used by the formatters
PYTHON_FILES := $(shell git ls-files -- '*.py')

# Firing a blank `make` command defaults to `help` command
.DEFAULT_GOAL := help


.PHONY: help
## `help`: Show available commands
help: Makefile
	@awk 'BEGIN { print "Commands available in agent-skills:\n" } \
		/^## :$$/ { print ""; next } \
		/^## / { \
			split($$0, parts, "## "); \
			split(parts[2], help, ": "); \
			printf "  %-15s %s\n", help[1], help[2] \
		}' $<


.PHONY: local-setup
## `local-setup`: Install dependencies and Git hooks
local-setup: install
	$(UV_RUN) pre-commit install --hook-type pre-commit --hook-type pre-push


.PHONY: uv-install
## `uv-install`: Install uv without changing shell startup files
uv-install:
	@if ! PATH="$$HOME/.local/bin:$$PATH" command -v uv >/dev/null 2>&1; then \
		installer=$$(mktemp) || exit $$?; \
		trap 'rm -f "$$installer"' 0; \
		curl -LsSf https://astral.sh/uv/0.13.7/install.sh -o "$$installer" || exit $$?; \
		UV_NO_MODIFY_PATH=1 sh "$$installer"; \
	fi


.PHONY: uv-update
## `uv-update`: Upgrade locked dependencies within their declared constraints
uv-update:
	$(UV) lock --upgrade
	$(MAKE) freeze


## :


.PHONY: checkstyle
## `checkstyle`: Run pre-commit checks on all tracked files
checkstyle:
	$(UV_RUN) pre-commit run --all-files


.PHONY: stylize
## `stylize`: Format tracked Python files and run pre-commit checks
stylize:
	$(UV_RUN) isort --profile black $(PYTHON_FILES)
	$(UV_RUN) black $(PYTHON_FILES)
	$(UV_RUN) pre-commit run --all-files


.PHONY: test
## `test`: Run the skill manager test suite
test:
	$(UV_RUN) python -m unittest discover -s scripts/tests -v


.PHONY: lock-check
## `lock-check`: Check that uv.lock matches pyproject.toml
lock-check:
	$(UV) lock --check


.PHONY: versions
## `versions`: Show uv, Python, and installed dependency versions
versions:
	$(UV) --version
	$(UV_RUN) python --version
	$(UV) pip list --python "$(VENV)/bin/python"


## :


.PHONY: install
## `install`: Install all locked project dependencies
install: uv-install
	$(UV) sync --locked --no-install-project


.PHONY: freeze
## `freeze`: Export locked dependencies to requirements.txt
freeze:
	$(UV) export --locked --no-emit-project --format requirements.txt --output-file requirements.txt > /dev/null


.PHONY: lock
## `lock`: Resolve dependencies and refresh the requirements export
lock:
	$(UV) lock
	$(MAKE) freeze


## :


.PHONY: add-dep
## `add-dep`: Add a project dependency (pkg="package")
add-dep:
	@test -n "$(pkg)" || { echo 'Usage: make add-dep pkg="package"'; exit 1; }
	$(UV) add "$(pkg)"
	$(MAKE) freeze
