"""Tests for the package rename helper."""

import pytest
from rename_package import (
    RenameError,
    iter_text_files,
    to_distribution_name,
    to_package_name,
    validate,
)


@pytest.mark.parametrize(
    ("raw", "package", "distribution"),
    [
        ("groundcite", "groundcite", "groundcite"),
        ("sign-off", "sign_off", "sign-off"),
        ("sign_off", "sign_off", "sign-off"),
    ],
)
def test_name_forms(raw: str, package: str, distribution: str) -> None:
    assert to_package_name(raw) == package
    assert to_distribution_name(raw) == distribution


@pytest.mark.parametrize("raw", ["Groundcite", "1groundcite", "ground cite", "ground.cite", ""])
def test_validate_rejects_malformed_names(raw: str) -> None:
    with pytest.raises(RenameError):
        validate(raw)


def test_validate_rejects_the_placeholder_itself() -> None:
    with pytest.raises(RenameError):
        validate("trust-template")


def test_iter_text_files_covers_extensionless_files() -> None:
    names = {path.name for path in iter_text_files()}
    assert {"Dockerfile", "Makefile", "pyproject.toml"} <= names


def test_iter_text_files_skips_the_lockfile_and_virtualenv() -> None:
    paths = iter_text_files()
    assert all(path.name != "uv.lock" for path in paths)
    assert all(".venv" not in path.parts for path in paths)
