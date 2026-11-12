# Makefile - use `make` or `make help` to get a list of commands.
#
# Note - Comments inside this makefile should be made using a single hashtag `#`, lines
# with double hash-tags are help messages that will be printed by the `help` command

# Default python executable to use
PYTHON_EXEC ?= python3

# Virtual environment directory and its Python executable
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python

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
	"$(VENV_PYTHON)" -m pre_commit install --hook-type pre-commit --hook-type pre-push


## :


.PHONY: checkstyle
## `checkstyle`: Run pre-commit checks on all tracked files
checkstyle: install
	"$(VENV_PYTHON)" -m pre_commit run --all-files


.PHONY: stylize
## `stylize`: Format tracked Python files and run pre-commit checks
stylize: install
	"$(VENV_PYTHON)" -m isort --profile black $(PYTHON_FILES)
	"$(VENV_PYTHON)" -m black $(PYTHON_FILES)
	"$(VENV_PYTHON)" -m pre_commit run --all-files


.PHONY: test
## `test`: Run the skill manager test suite
test: install
	"$(VENV_PYTHON)" -m unittest discover -s scripts/tests -v


## :


.PHONY: install
## `install`: Install dependencies in the virtual environment
install: $(VENV)/.requirements-installed


$(VENV_PYTHON):
	$(PYTHON_EXEC) -m venv "$(VENV)"


$(VENV)/.requirements-installed: requirements.txt $(VENV_PYTHON)
	"$(VENV_PYTHON)" -m pip install -r requirements.txt
	@touch "$@"
