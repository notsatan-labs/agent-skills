# Skill Manager

`skill-manager.py` keeps external agent skills inside this repository without
requiring each upstream project to become a Git submodule. A skill may live at
the root of another repository or several directories deep; the manager fetches
the configured revision and vendors that complete directory into `skills/`.

Vendoring makes the resulting collection self-contained and reviewable. Agents
use the checked-in files rather than contacting upstream repositories at run
time, while `sources.yaml` records where those files came from. Each managed
skill is pinned to its exact commit and hash, so an ordinary sync operation
is reproducible locally.

The manager copies the entire Git-tracked skill directory, not only its Markdown
instructions. Nested scripts, templates, assets, symlinks, and executable bits
are included. It also places an ownership marker in managed directories. This
allows updates and pruning to distinguish external skills from personal,
unlisted directories and prevents accidental overwrites.

## Setup

Install the YAML dependency:

```sh
python3 -m pip install -r requirements.txt
```

External skills are declared in the repository's `sources.yaml`:

```yaml
schema_version: 1

skills:
  example-skill:
    repository: https://github.com/example/skills.git
    path: skills/example-skill
    ref: refs/heads/main
    commit: null
    sha256: null
```

The mapping key becomes the local directory name. The example above is
installed at `skills/example-skill`.

| Field | Required | Managed by | Description |
| --- | --- | --- | --- |
| `ref` | Yes | User | Branch, tag, or other Git ref followed by `update`. |
| `path` | Yes | User | Directory containing the skill inside the repository; use `.` for its root. |
| `repository` | Yes | User | Git repository URL or local path. HTTPS and SSH remotes are supported. |
| `commit` | No | Script | Exact commit currently vendored. May initially be omitted or `null`. |
| `sha256` | No | Script | Hash of the vendored directory. May initially be omitted or `null`. |

Skill names may contain only letters, numbers, underscores, and hyphens.
Directories absent from `sources.yaml` are considered personal and are never
modified or pruned.

## Command Line

General form:

```sh
python3 scripts/skill-manager.py [--config CONFIG] COMMAND [ARGUMENTS]
```

Global options must appear before the subcommand:

| Option | Value | Description |
| --- | --- | --- |
| `--config` | `CONFIG` | Use a different sources file. Defaults to `sources.yaml` in the repository root; its parent determines the managed `skills/` directory. |
| `-h`, `--help` | None | Show help for the manager or the selected subcommand. |

### Subcommands

| Subcommand | Arguments and flags | Expects | Result |
| --- | --- | --- | --- |
| `validate` | None | A readable `sources.yaml` using the supported schema and field formats. | Validates the entire manifest without inspecting skill directories or contacting remotes. |
| `check` | `[SKILL ...]` | Selected skills to have generated fields and valid local managed directories. With no names, checks every configured skill and reports orphans. | Verifies ownership markers and content hashes without contacting remotes. |
| `sync` | `[SKILL ...]` | Configured source entries. New entries may omit `commit` and `sha256`; existing entries use their recorded commit. With no names, synchronizes all entries. | Downloads and installs the recorded snapshots, restores local drift, and fills missing generated fields. |
| `sync` | `--prune` | Any orphaned directory to contain a valid ownership marker. May be combined with selected skill names. | Also removes managed directories no longer present in `sources.yaml`; unmarked directories are untouched. |
| `update` | `[SKILL ...]` | Every selected skill to already have `commit` and `sha256`. Run `sync` first for new entries. | Resolves each configured `ref`, skips unchanged commits, and installs and records changed snapshots. |
| `remove` | `SKILL` | One configured skill name. Any existing destination must have the matching ownership marker. | Removes the manifest entry and its managed directory. |

Examples:

```sh
# Validate the complete manifest.
python3 scripts/skill-manager.py validate

# Initialize or reproduce every configured skill.
python3 scripts/skill-manager.py sync

# Synchronize one skill and remove orphaned managed directories.
python3 scripts/skill-manager.py sync example-skill --prune

# Check local state without accessing the network.
python3 scripts/skill-manager.py check

# Look for upstream changes to selected skills.
python3 scripts/skill-manager.py update example-skill

# Remove one external skill from the catalog and disk.
python3 scripts/skill-manager.py remove example-skill
```

Every command validates the complete manifest before doing any work.

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | The command completed successfully. |
| `1` | `check` found local drift or unresolved state. |
| `2` | The configuration was invalid or an operational error occurred. |
