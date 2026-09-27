from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ruamel.yaml import YAML

MANAGER = Path(__file__).resolve().parents[1] / "skill-manager.py"


class SkillManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.upstream = self.root / "upstream"
        self.catalog = self.root / "catalog"
        self.upstream.mkdir()
        (self.catalog / "skills").mkdir(parents=True)

        self.git("init", "--initial-branch=main", str(self.upstream))
        skill = self.upstream / "skill"
        (skill / "bin").mkdir(parents=True)
        (skill / "README.md").write_text("# Example\n", encoding="utf-8")
        script = skill / "bin" / "run.sh"
        script.write_text("#!/bin/sh\necho first\n", encoding="utf-8")
        script.chmod(0o755)
        self.commit_upstream("Initial skill")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(
        self, *arguments: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )

    def commit_upstream(self, message: str) -> None:
        self.git("add", ".", cwd=self.upstream)
        self.git(
            "-c",
            "user.name=Skill Manager Tests",
            "-c",
            "user.email=tests@example.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
            cwd=self.upstream,
        )

    def write_config(self, skills: str) -> None:
        repository = json.dumps(str(self.upstream))
        (self.catalog / "sources.yaml").write_text(
            f"schema_version: 1\n\nskills:\n{skills.format(repository=repository)}",
            encoding="utf-8",
        )

    def manager(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(MANAGER),
                "--config",
                str(self.catalog / "sources.yaml"),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def load_config(self) -> dict:
        yaml = YAML(typ="safe")
        return yaml.load(self.catalog.joinpath("sources.yaml").read_text())

    def test_sync_update_check_and_remove(self) -> None:
        self.write_config(
            "  external:\n"
            "    repository: {repository}\n"
            "    path: skill\n"
            "    ref: refs/heads/main\n"
        )

        self.assertEqual(self.manager("validate").returncode, 0)
        unresolved_update = self.manager("update")
        self.assertEqual(unresolved_update.returncode, 2)
        self.assertIn("requires commit and sha256", unresolved_update.stderr)
        initial_check = self.manager("check")
        self.assertEqual(initial_check.returncode, 1)
        self.assertIn("unresolved", initial_check.stderr)

        synchronized = self.manager("sync")
        self.assertEqual(synchronized.returncode, 0, synchronized.stderr)
        config = self.load_config()
        entry = config["skills"]["external"]
        self.assertRegex(entry["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")

        destination = self.catalog / "skills" / "external"
        self.assertEqual(
            destination.joinpath("bin/run.sh").read_text(),
            "#!/bin/sh\necho first\n",
        )
        self.assertTrue(os.access(destination / "bin" / "run.sh", os.X_OK))
        self.assertTrue(destination.joinpath(".agent-skills-managed").is_file())
        self.assertEqual(self.manager("check").returncode, 0)

        current = self.manager("update")
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertIn("Already current: 1 skill(s)", current.stdout)

        destination.joinpath("bin/run.sh").write_text("locally modified\n")
        self.assertEqual(self.manager("check").returncode, 1)
        resynchronized = self.manager("sync")
        self.assertEqual(resynchronized.returncode, 0, resynchronized.stderr)
        self.assertEqual(
            destination.joinpath("bin/run.sh").read_text(),
            "#!/bin/sh\necho first\n",
        )

        old_commit = entry["commit"]
        self.upstream.joinpath("skill/bin/run.sh").write_text(
            "#!/bin/sh\necho second\n", encoding="utf-8"
        )
        self.commit_upstream("Update skill")

        pinned = self.manager("sync")
        self.assertEqual(pinned.returncode, 0, pinned.stderr)
        self.assertEqual(
            destination.joinpath("bin/run.sh").read_text(),
            "#!/bin/sh\necho first\n",
        )
        self.assertEqual(self.load_config()["skills"]["external"]["commit"], old_commit)

        updated = self.manager("update")
        self.assertEqual(updated.returncode, 0, updated.stderr)
        self.assertNotEqual(
            self.load_config()["skills"]["external"]["commit"], old_commit
        )
        self.assertIn("echo second", destination.joinpath("bin/run.sh").read_text())

        removed = self.manager("remove", "external")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(destination.exists())
        self.assertEqual(self.load_config()["skills"], {})

    def test_collision_and_prune_protect_unmanaged_directories(self) -> None:
        self.write_config(
            "  external:\n"
            "    repository: {repository}\n"
            "    path: skill\n"
            "    ref: refs/heads/main\n"
            "    commit: null\n"
            "    sha256: null\n"
        )
        personal = self.catalog / "skills" / "personal"
        personal.mkdir()
        personal.joinpath("notes.txt").write_text("keep me\n", encoding="utf-8")

        self.assertEqual(self.manager("sync").returncode, 0)
        config = self.load_config()
        config["skills"] = {}
        yaml = YAML()
        with self.catalog.joinpath("sources.yaml").open("w", encoding="utf-8") as file:
            yaml.dump(config, file)

        pruned = self.manager("sync", "--prune")
        self.assertEqual(pruned.returncode, 0, pruned.stderr)
        self.assertFalse(self.catalog.joinpath("skills/external").exists())
        self.assertEqual(personal.joinpath("notes.txt").read_text(), "keep me\n")

        self.write_config(
            "  personal:\n"
            "    repository: {repository}\n"
            "    path: skill\n"
            "    ref: refs/heads/main\n"
        )
        collision = self.manager("sync")
        self.assertEqual(collision.returncode, 2)
        self.assertIn("destination is unmanaged", collision.stderr)
        self.assertEqual(personal.joinpath("notes.txt").read_text(), "keep me\n")

    def test_every_command_rejects_an_invalid_configuration(self) -> None:
        self.write_config(
            "  invalid.name:\n"
            "    repository: {repository}\n"
            "    path: skill\n"
            "    ref: refs/heads/main\n"
        )
        invalid_name = self.manager("validate")
        self.assertEqual(invalid_name.returncode, 2)
        self.assertIn("invalid skill name", invalid_name.stderr)

        self.catalog.joinpath("sources.yaml").write_text(
            "schema_version: [\n", encoding="utf-8"
        )

        commands = (("validate",), ("check",), ("sync",), ("update",), ("remove", "x"))
        for command in commands:
            with self.subTest(command=command[0]):
                result = self.manager(*command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("cannot load", result.stderr)

    def test_rejects_a_symlinked_skills_root(self) -> None:
        self.write_config("  {{}}\n")
        self.catalog.joinpath("skills").rmdir()
        outside = self.root / "outside"
        outside.mkdir()
        self.catalog.joinpath("skills").symlink_to(outside, target_is_directory=True)

        result = self.manager("check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("skills directory is a symlink", result.stderr)


if __name__ == "__main__":
    unittest.main()
