# Agent Skills

<div align="center">

[![Dependencies Status](https://img.shields.io/badge/Dependencies-Up%20to%20Date-brightgreen?style=for-the-badge&logo=dependabot)][dependabot-pulls]
[![Semantic Versioning](https://img.shields.io/badge/versioning-semantic-lightgrey?style=for-the-badge&logo=semver)][github-releases]
[![Pre-Commit Enabled](https://img.shields.io/badge/Pre--Commit-Enabled-blue?style=for-the-badge&logo=pre-commit)][precommit-config]
[![License](https://img.shields.io/badge/License-GNU%20GPL-green?style=for-the-badge&logo=lumen)][project-license]

Just a bunch of generic stuff to get my agents working!

</div>


## Initial Setup

To get a working copy of `agent-skills` on your end, simply clone the repository

```sh
git clone git@github.com:notsatan-labs/agent-skills.git
```
</details>
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
pre-commit run --all-files
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
