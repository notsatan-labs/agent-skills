# Agent Skills

<div align="center">

[![Dependencies Status](https://img.shields.io/badge/Dependencies-Up%20to%20Date-brightgreen?style=for-the-badge&logo=dependabot)][dependabot-pulls]
[![Semantic Versioning](https://img.shields.io/badge/versioning-semantic-lightgrey?style=for-the-badge&logo=semver)][github-releases]
[![Pre-Commit Enabled](https://img.shields.io/badge/Pre--Commit-Enabled-blue?style=for-the-badge&logo=pre-commit)][precommit-config]
[![License](https://img.shields.io/badge/License-GNU%20GPL-green?style=for-the-badge&logo=lumen)][project-license]

Just a bunch of generic stuff to get my agents working!

</div>


## Initial Setup

Install Git, Make, and curl on macOS or Linux, then clone the repository
and set up the development environment:

```sh
git clone git@github.com:notsatan-labs/agent-skills.git
cd agent-skills
make local-setup
```

This installs uv if needed, syncs the dependencies pinned in `uv.lock` into
`~/.virtualenvs/agent-skills`, and installs the standard pre-commit and pre-push
hooks. All dependencies belong to one project environment. For dependency setup
without Git hooks, use `make install`.

Each machine uses its own home directory, so macOS and a Linux sandbox can share
a checkout while keeping their Python environments separate. Make sets
`UV_PROJECT_ENVIRONMENT` and prepends the environment and uv installation
directories to PATH for each command. Setup does not edit shell startup files.
uv uses the Python version pinned in `.python-version`, downloading it if needed.

Use `make` or `make help` to list available commands:

```sh
make checkstyle  # Run pre-commit checks on all tracked files
make stylize    # Format tracked Python files and run the checks
make test       # Run the skill manager tests
make lock-check # Check that the lockfile matches pyproject.toml
make versions   # Show uv, Python, and dependency versions
```

Override the Python executable, or the environment directory, when needed:

```sh
make local-setup PYTHON_EXEC=python3.14

make local-setup VENV="$HOME/.virtualenvs/agent-skills-custom"
```

Continue to use the same `VENV` and `PYTHON_EXEC` overrides, when set, for
subsequent Make commands.

Dependencies are declared in `pyproject.toml`. To add one, use
`make add-dep pkg="package"`. After editing the dependency list manually, run
`make lock`. Use `make uv-update` to upgrade the lockfile within the declared
version constraints. Both commands refresh `requirements.txt`.

`requirements.txt` is a generated, pinned export of the complete environment for
tools that need that format. Regenerate it with `make freeze`; edit
`pyproject.toml` rather than the export. Pre-commit checks lockfile consistency
and regenerates the export when dependency files change. Make commands use
`--locked`, so a stale lockfile causes a failure instead of silently changing it.
<br>


### Pre-Commit Hooks

This project uses [pre-commit][pre-commit] hooks to automatically enforce code style and quality checks before each commit

The hooks, defined in [`.pre-commit-config.yaml`][precommit-config], perform several checks, including:
 - Checks for merge conflicts, and possible leaks of private keys
 - File formatters - whitespace trimming, end-of-file fixers
 - Checks for executable scripts
 - JSON formatters
 - Code Formatters
 - Linters

For a watered-down explanation, [pre-commit][pre-commit] hooks are an abstraction over
[git-hooks][githooks], allowing you to define a series of commands (or checks), that
would be automatically run every time you use the `git commit` command.

The pre-commit hooks used are located within the
[`.pre-commit-config.yml`][precommit-config] file. These hooks are configured to run;

### Using `pre-commit`

While pre-commit hooks run automatically on every commit, you can also trigger them
manually to check all files in the repository:

```sh
make checkstyle
```

## Releases

You can check out a list of previous releases on the [Github Releases][github-releases]
page.

### Semantic versioning with Release Drafter

<details>
    <summary>
        What is Semantic Versioning?
    </summary><br>

Semantic versioning is a versioning scheme aimed at making software management easier.
Following semantic versioning, version identifiers are divided into three parts;

```sh
    <major>.<minor>.<patch>
```

> MAJOR version when you make incompatible API changes [breaking changes]<br>
> MINOR version when you add functionality in a backwards compatible manner [more features]<br>
> PATCH version when you make backwards compatible bug fixes [bug fixes and stuff]<br>

For a more detailed description, head over to [semver.org][semver-link]

</details>

[Release Drafter][release-drafter] automatically updates the release version as pull
requests are merged.

Labels allowed;

 - `major`: Affects the `<major>` version number for semantic versioning
 - `minor`, `patch`: Affects the `<patch>` version number for semantic versioning

Whenever a pull request with one of these labels is merged to the `master` branch,
the corresponding version number will be bumped by one digit!

### List of Labels

Pull requests once merged, will be classified into categories by
[release-drafter][release-drafter] based on pull request labels

This is managed by the [`release-drafter.yml`][release-drafter-config] config file.

|                        **Label**                        |      **Title in Releases**      |
|:-------------------------------------------------------:|:-------------------------------:|
| `security`                                              |         :lock: Security         |
| `enhancement`, `feature`,  `update`                     |         :rocket: Updates        |
| `bug`, `bugfix`, `fix`                                  |         :bug: Bug Fixes         |
| `documentation`, `docs`                                 |       :memo: Documentation      |
| `wip`, `in-progress`, `incomplete`, `partial`, `hotfix` | :construction: Work in Progress |
| `dependencies`, `dependency`                            |      :package: Dependencies     |
| `refactoring`, `refactor`, `tests`, `testing`           |  :test_tube: Tests and Refactor |
| `build`, `ci`, `pipeline`                               |   :robot: CI/CD and Pipelines   |

The labels `bug`, `enhancement`, and `documentation` are automatically created by Github
for repositories. [Dependabot][dependabot-link] will implicitly create the
`dependencies` label with the first pull request raised by it.

The remaining labels can be created as needed!
<br>


[project-license]: ./LICENSE
[github-actions]: ../../actions
[github-releases]: ../../releases
[precommit-config]: ./.pre-commit-config.yaml
[dependabot-pulls]: ../../pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot

[semver-link]: https://semver.org
[pre-commit]: https://pre-commit.com
[dependabot-link]: https://dependabot.com
[python-black]: https://github.com/psf/black
[githooks]: https://git-scm.com/docs/githooks
[release-drafter-config]: ./.github/release-drafter.yml
[release-drafter]: https://github.com/marketplace/actions/release-drafter
