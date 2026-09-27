#!/usr/bin/env python3
"""Synchronize vendored skill directories from Git repositories."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError
except ModuleNotFoundError:
    raise SystemExit(
        "Install dependencies with: python3 -m pip install -r requirements.txt"
    )


SCHEMA_VERSION = 1
MARKER_NAME = ".agent-skills-managed"
NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]+\Z")
COMMIT_PATTERN = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
ENTRY_FIELDS = {"repository", "path", "ref", "commit", "sha256"}
USER_FIELDS = ("repository", "path", "ref")


class ManagerError(Exception):
    """A user-actionable manager failure."""


@dataclass
class SkillSpec:
    name: str
    repository: str
    path: str
    ref: str
    commit: str | None
    sha256: str | None


@dataclass(frozen=True)
class StagedSkill:
    name: str
    directory: Path
    commit: str
    sha256: str


@dataclass
class Catalog:
    path: Path
    document: dict[str, Any]
    skills: dict[str, SkillSpec]
    yaml: Any

    @property
    def root(self) -> Path:
        return self.path.parent

    @property
    def skills_dir(self) -> Path:
        return self.root / "skills"

    def record_snapshot(self, staged: StagedSkill) -> bool:
        """Record generated fields and report whether the catalog changed."""

        entry = self.document["skills"][staged.name]
        changed = (
            entry.get("commit") != staged.commit or entry.get("sha256") != staged.sha256
        )
        entry["commit"] = staged.commit
        entry["sha256"] = staged.sha256

        skill = self.skills[staged.name]
        skill.commit = staged.commit
        skill.sha256 = staged.sha256
        return changed

    def remove(self, name: str) -> None:
        del self.document["skills"][name]
        del self.skills[name]

    def save(self) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                self.yaml.dump(self.document, stream)
            temporary.chmod(self.path.stat().st_mode & 0o777)
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)


# CLI


def build_parser() -> argparse.ArgumentParser:
    default_config = Path(__file__).resolve().parent.parent / "sources.yaml"

    parser = argparse.ArgumentParser(description="Sync external skills to project")
    parser.add_argument("--config", type=Path, default=default_config)
    commands = parser.add_subparsers(dest="command", required=True)

    # No additional checks — the script will validate the YAML each time it is run
    commands.add_parser("validate", help="validate sources file")

    check = commands.add_parser("check", help="check local managed skills")
    check.add_argument("skills", nargs="*")

    sync = commands.add_parser("sync", help="materialize recorded commits")
    sync.add_argument("skills", nargs="*")
    sync.add_argument("--prune", action="store_true")

    update = commands.add_parser("update", help="update skills from their refs")
    update.add_argument("skills", nargs="*")

    remove = commands.add_parser("remove", help="remove a managed skill")
    remove.add_argument("skill")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = build_parser().parse_args(argv)
        catalog = load_catalog(arguments.config.resolve())

        if arguments.command == "validate":
            return command_validate(catalog)
        elif arguments.command == "check":
            return command_check(catalog, arguments.skills)
        elif arguments.command == "sync":
            return command_sync(catalog, arguments.skills, arguments.prune)
        elif arguments.command == "update":
            return command_update(catalog, arguments.skills)
        elif arguments.command == "remove":
            return command_remove(catalog, arguments.skill)
        raise AssertionError(f"unknown command: {arguments.command}")
    except ManagerError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, tarfile.TarError, YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


# Commands


def command_validate(catalog: Catalog) -> int:
    print(f"Valid: {catalog.path} ({len(catalog.skills)} external skill(s))")
    return 0


def command_check(catalog: Catalog, names: Sequence[str]) -> int:
    validate_skills_root(catalog)
    skills = select_skills(catalog, names)
    failures = []

    for skill in skills:
        destination = catalog.skills_dir / skill.name
        if skill.commit is None or skill.sha256 is None:
            failures.append(f"{skill.name}: unresolved; run sync")
        elif destination.is_symlink() or not destination.is_dir():
            failures.append(f"{skill.name}: directory is missing or invalid")
        elif read_owner(destination) != skill.name:
            failures.append(f"{skill.name}: ownership marker is missing or invalid")
        elif hash_directory(destination) != skill.sha256:
            failures.append(f"{skill.name}: content hash does not match")

    if not names:
        failures.extend(
            f"{directory.name}: orphaned managed directory"
            for directory in find_orphaned_directories(catalog)
        )

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"Checked {len(skills)} external skill(s): workspace is current")
    return 0


def command_sync(catalog: Catalog, names: Sequence[str], prune: bool) -> int:
    validate_skills_root(catalog)
    skills = select_skills(catalog, names)
    for skill in skills:
        require_managed_destination(catalog, skill)

    orphans = find_orphaned_directories(catalog) if prune else []
    with staging_workspace(catalog) as workspace:
        staged = []

        for skill in skills:
            repository = initialize_repository(workspace, skill, catalog.root)
            if skill.commit is None:
                commit = resolve_ref_commit(repository, skill, catalog.root)
            else:
                commit = fetch_recorded_commit(repository, skill, catalog.root)

            staged.append(
                stage_skill(
                    catalog,
                    skill,
                    repository,
                    commit,
                    workspace,
                    expected_sha256=skill.sha256,
                )
            )

        catalog_changed = False
        for snapshot in staged:
            catalog_changed |= catalog.record_snapshot(snapshot)

        install_staged_skills(catalog, staged)
        remove_directories(orphans)
        if catalog_changed:
            catalog.save()

    print(f"Synchronized {len(staged)} external skill(s)")
    if orphans:
        print(f"Pruned {len(orphans)} orphaned managed skill(s)")
    return 0


def command_update(catalog: Catalog, names: Sequence[str]) -> int:
    validate_skills_root(catalog)
    skills = select_skills(catalog, names)
    unresolved = [
        skill.name for skill in skills if skill.commit is None or skill.sha256 is None
    ]
    if unresolved:
        raise ManagerError(
            "update requires commit and sha256; run sync first for: "
            + ", ".join(unresolved)
        )

    for skill in skills:
        require_managed_destination(catalog, skill)

    with staging_workspace(catalog) as workspace:
        staged = []

        for skill in skills:
            repository = initialize_repository(workspace, skill, catalog.root)
            latest_commit = resolve_ref_commit(repository, skill, catalog.root)
            if latest_commit == skill.commit:
                continue

            staged.append(
                stage_skill(
                    catalog,
                    skill,
                    repository,
                    latest_commit,
                    workspace,
                )
            )

        for snapshot in staged:
            catalog.record_snapshot(snapshot)

        install_staged_skills(catalog, staged)
        if staged:
            catalog.save()

    print(f"Updated {len(staged)} external skill(s)")
    current = len(skills) - len(staged)
    if current:
        print(f"Already current: {current} skill(s)")
    return 0


def command_remove(catalog: Catalog, name: str) -> int:
    validate_skills_root(catalog)
    skill = select_skills(catalog, [name])[0]
    destination = catalog.skills_dir / skill.name
    require_managed_destination(catalog, skill)

    catalog.remove(skill.name)
    remove_directories([destination])
    catalog.save()

    print(f"Removed external skill {skill.name!r}")
    return 0


# Configuration


def load_catalog(path: Path) -> Catalog:
    yaml = YAML(typ="rt")
    yaml.allow_duplicate_keys = False
    yaml.preserve_quotes = True

    try:
        with path.open(encoding="utf-8") as stream:
            document = yaml.load(stream)
    except (OSError, YAMLError) as error:
        raise ManagerError(f"cannot load {path}: {error}") from error

    if not isinstance(document, dict):
        raise ManagerError("configuration must be a YAML mapping")
    elif document.get("schema_version") != SCHEMA_VERSION:
        raise ManagerError(f"schema_version must be {SCHEMA_VERSION}")
    elif not isinstance(document.get("skills"), dict):
        raise ManagerError("skills must be a YAML mapping")

    skills = {}
    normalized_names = set()
    for name, entry in document["skills"].items():
        skill = parse_skill(name, entry)
        normalized_name = skill.name.casefold()
        if normalized_name in normalized_names:
            raise ManagerError(f"skill name {skill.name!r} collides with another entry")
        normalized_names.add(normalized_name)
        skills[skill.name] = skill

    return Catalog(path, document, skills, yaml)


def parse_skill(name: Any, entry: Any) -> SkillSpec:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise ManagerError(f"invalid skill name {name!r}")
    if not isinstance(entry, dict):
        raise ManagerError(f"skill {name!r} must be a YAML mapping")

    unknown_fields = set(entry) - ENTRY_FIELDS
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ManagerError(f"skill {name!r} has unknown field(s): {fields}")

    for field in USER_FIELDS:
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            raise ManagerError(f"skill {name!r} requires a non-empty {field}")

    source_path = PurePosixPath(entry["path"])
    if source_path.is_absolute() or ".." in source_path.parts:
        raise ManagerError(f"skill {name!r} has an invalid repository path")

    commit = entry.get("commit")
    if commit is not None:
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise ManagerError(f"skill {name!r} has an invalid commit")
        commit = commit.lower()

    sha256 = entry.get("sha256")
    if sha256 is not None:
        if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256):
            raise ManagerError(f"skill {name!r} has an invalid sha256")
        sha256 = sha256.lower()

    return SkillSpec(
        name=name,
        repository=entry["repository"],
        path=entry["path"],
        ref=entry["ref"],
        commit=commit,
        sha256=sha256,
    )


def select_skills(catalog: Catalog, names: Sequence[str]) -> list[SkillSpec]:
    if not names:
        return list(catalog.skills.values())

    unknown = [name for name in names if name not in catalog.skills]
    if unknown:
        raise ManagerError(f"unknown skill(s): {', '.join(unknown)}")
    return [catalog.skills[name] for name in names]


# Workspace state


def validate_skills_root(catalog: Catalog) -> None:
    if catalog.skills_dir.is_symlink():
        raise ManagerError(f"skills directory is a symlink: {catalog.skills_dir}")
    if catalog.skills_dir.exists() and not catalog.skills_dir.is_dir():
        raise ManagerError(f"skills path is not a directory: {catalog.skills_dir}")


def read_owner(directory: Path) -> str | None:
    marker = directory / MARKER_NAME
    if marker.is_symlink():
        raise ManagerError(f"invalid ownership marker: {marker}")
    if not marker.exists():
        return None

    owner = marker.read_text(encoding="utf-8").strip()
    if not NAME_PATTERN.fullmatch(owner):
        raise ManagerError(f"invalid ownership marker: {marker}")
    return owner


def write_owner(directory: Path, name: str) -> None:
    marker = directory / MARKER_NAME
    if marker.exists() or marker.is_symlink():
        raise ManagerError(
            f"upstream skill {name!r} contains reserved file {MARKER_NAME}"
        )
    marker.write_text(f"{name}\n", encoding="utf-8")


def require_managed_destination(catalog: Catalog, skill: SkillSpec) -> None:
    destination = catalog.skills_dir / skill.name
    if destination.is_symlink():
        raise ManagerError(f"skill {skill.name!r} destination is a symlink")
    if not destination.exists():
        return
    if not destination.is_dir():
        raise ManagerError(f"skill {skill.name!r} destination is not a directory")

    owner = read_owner(destination)
    if owner is None:
        raise ManagerError(f"skill {skill.name!r} destination is unmanaged")
    if owner != skill.name:
        raise ManagerError(f"skill {skill.name!r} destination is owned by {owner!r}")


def find_orphaned_directories(catalog: Catalog) -> list[Path]:
    if not catalog.skills_dir.exists():
        return []

    orphans = []
    for directory in sorted(catalog.skills_dir.iterdir()):
        if directory.is_symlink() or not directory.is_dir():
            continue
        owner = read_owner(directory)
        if owner is None:
            continue
        if owner != directory.name:
            raise ManagerError(f"{directory} claims to belong to {owner!r}")
        if owner not in catalog.skills:
            orphans.append(directory)
    return orphans


def hash_directory(directory: Path) -> str:
    """Hash paths, file contents, symlinks, and executable bits."""

    digest = hashlib.sha256()

    def add(value: bytes) -> None:
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)

    paths = sorted(directory.rglob("*"), key=lambda path: path.relative_to(directory))
    for path in paths:
        relative = path.relative_to(directory)
        if relative == Path(MARKER_NAME):
            continue

        add(relative.as_posix().encode())
        if path.is_symlink():
            add(b"link")
            add(os.fsencode(os.readlink(path)))
        elif path.is_dir():
            add(b"directory")
        elif path.is_file():
            add(b"file")
            metadata = path.stat()
            add(b"executable" if metadata.st_mode & 0o111 else b"regular")
            add(metadata.st_size.to_bytes(8, "big"))
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
        else:
            raise ManagerError(f"unsupported file in skill: {path}")

    return digest.hexdigest()


# Staging and installation


def staging_workspace(catalog: Catalog) -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix=".skill-manager-", dir=catalog.root)


def initialize_repository(workspace: str, skill: SkillSpec, cwd: Path) -> Path:
    repository = Path(workspace) / "repositories" / skill.name
    repository.parent.mkdir(parents=True, exist_ok=True)
    run_git(["init", "--bare", "--quiet", str(repository)], cwd=cwd)
    return repository


def stage_skill(
    catalog: Catalog,
    skill: SkillSpec,
    repository: Path,
    commit: str,
    workspace: str,
    *,
    expected_sha256: str | None = None,
) -> StagedSkill:
    directory = Path(workspace) / "staged" / skill.name
    directory.parent.mkdir(parents=True, exist_ok=True)
    export_skill_tree(repository, skill, commit, directory, catalog.root)
    sha256 = hash_directory(directory)

    if expected_sha256 is not None and sha256 != expected_sha256:
        raise ManagerError(f"skill {skill.name!r} does not match its sha256")

    write_owner(directory, skill.name)
    return StagedSkill(skill.name, directory, commit, sha256)


def install_staged_skills(catalog: Catalog, staged: Sequence[StagedSkill]) -> None:
    if staged:
        catalog.skills_dir.mkdir(parents=True, exist_ok=True)
    for snapshot in staged:
        destination = catalog.skills_dir / snapshot.name
        replace_managed_directory(snapshot.directory, destination)


def replace_managed_directory(source: Path, destination: Path) -> None:
    """Replace one directory, restoring the previous version if the swap fails."""

    backup = source.parent / f".{destination.name}-backup"
    had_destination = destination.exists()
    if had_destination:
        os.replace(destination, backup)

    try:
        os.replace(source, destination)
    except Exception:
        if had_destination:
            os.replace(backup, destination)
        raise

    if had_destination:
        shutil.rmtree(backup)


def remove_directories(directories: Sequence[Path]) -> None:
    for directory in directories:
        if directory.exists():
            shutil.rmtree(directory)


# Git snapshots


def run_git(arguments: Sequence[str], *, cwd: Path) -> str:
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ManagerError("git is not installed") from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "git command failed"
        raise ManagerError(message) from error
    return result.stdout.strip()


def resolve_ref_commit(repository: Path, skill: SkillSpec, cwd: Path) -> str:
    run_git(
        [
            f"--git-dir={repository}",
            "fetch",
            "--quiet",
            "--no-tags",
            skill.repository,
            skill.ref,
        ],
        cwd=cwd,
    )
    return run_git(
        [f"--git-dir={repository}", "rev-parse", "FETCH_HEAD^{commit}"], cwd=cwd
    ).lower()


def fetch_recorded_commit(repository: Path, skill: SkillSpec, cwd: Path) -> str:
    assert skill.commit is not None
    try:
        run_git(
            [
                f"--git-dir={repository}",
                "fetch",
                "--quiet",
                "--depth=1",
                "--no-tags",
                skill.repository,
                skill.commit,
            ],
            cwd=cwd,
        )
    except ManagerError:
        run_git(
            [
                f"--git-dir={repository}",
                "fetch",
                "--quiet",
                "--no-tags",
                skill.repository,
                skill.ref,
            ],
            cwd=cwd,
        )

    return run_git(
        [
            f"--git-dir={repository}",
            "rev-parse",
            "--verify",
            f"{skill.commit}^{{commit}}",
        ],
        cwd=cwd,
    ).lower()


def export_skill_tree(
    repository: Path,
    skill: SkillSpec,
    commit: str,
    destination: Path,
    cwd: Path,
) -> None:
    tree = commit if skill.path == "." else f"{commit}:{skill.path}"
    archive = destination.parent / f".{skill.name}.tar"
    destination.mkdir(parents=True)

    try:
        run_git(
            [
                f"--git-dir={repository}",
                "archive",
                "--format=tar",
                f"--output={archive}",
                tree,
            ],
            cwd=cwd,
        )
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, filter="data")
    finally:
        archive.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
