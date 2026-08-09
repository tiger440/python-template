"""Rename the template's placeholder package to a real project name.

Usage::

    uv run python scripts/rename_package.py groundcite

Renames ``src/trust_template`` to ``src/<new_package>`` and rewrites every
occurrence of the placeholder name (module form and distribution form) in the
tracked text files of the repository.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OLD_PACKAGE = "trust_template"
OLD_DISTRIBUTION = "trust-template"

ROOT = Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = frozenset({".py", ".toml", ".md", ".yml", ".yaml", ".cfg", ".txt", ".json"})
SKIP_DIRS = frozenset({".git", ".venv", ".ruff_cache", ".pytest_cache", "site", "dist", "build"})
SKIP_FILES = frozenset({"uv.lock"})

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*([-_][a-z0-9]+)*$")


class RenameError(RuntimeError):
    """Raised when the rename cannot be performed safely."""


def to_package_name(name: str) -> str:
    """Return the importable module form of ``name`` (underscores)."""
    return name.replace("-", "_")


def to_distribution_name(name: str) -> str:
    """Return the PyPI distribution form of ``name`` (hyphens)."""
    return name.replace("_", "-")


def validate(name: str) -> None:
    """Reject names that are not valid lowercase Python/PyPI identifiers.

    Raises:
        RenameError: If the name is malformed or is the placeholder itself.
    """
    if not NAME_PATTERN.match(name):
        raise RenameError(f"invalid project name {name!r}: use lowercase letters, digits, - or _")
    if to_package_name(name) == OLD_PACKAGE:
        raise RenameError("the new name is the placeholder name; nothing to do")


def iter_text_files() -> list[Path]:
    """Return every rewritable text file of the repository."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name in SKIP_FILES or path.suffix not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return files


def rewrite(files: list[Path], package: str, distribution: str) -> int:
    """Replace placeholder names in ``files``; return the number of files changed."""
    changed = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        updated = original.replace(OLD_PACKAGE, package).replace(OLD_DISTRIBUTION, distribution)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def move_package(package: str) -> None:
    """Move ``src/trust_template`` to ``src/<package>``.

    Raises:
        RenameError: If the source is missing or the destination already exists.
    """
    source = ROOT / "src" / OLD_PACKAGE
    destination = ROOT / "src" / package
    if not source.is_dir():
        raise RenameError(f"{source} does not exist: the package was probably already renamed")
    if destination.exists():
        raise RenameError(f"{destination} already exists")
    source.rename(destination)


def main(argv: list[str]) -> int:
    """Entry point. Returns a process exit code."""
    if len(argv) != 2:
        print("usage: rename_package.py <new_project_name>", file=sys.stderr)
        return 2

    name = argv[1].strip()
    try:
        validate(name)
        package = to_package_name(name)
        distribution = to_distribution_name(name)
        move_package(package)
        changed = rewrite(iter_text_files(), package, distribution)
    except RenameError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"renamed {OLD_PACKAGE} -> {package} ({changed} files updated)")
    print("next: uv sync --all-extras && make check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
