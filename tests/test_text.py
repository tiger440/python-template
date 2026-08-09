"""Tests for the placeholder text helpers."""

import pytest

from trust_template.text import EmptyTextError, normalize_whitespace


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hello world", "hello world"),
        ("  hello world  ", "hello world"),
        ("hello    world", "hello world"),
        ("hello\nworld", "hello world"),
        ("hello\t\r\nworld", "hello world"),
        ("a\n\n\nb\tc  d", "a b c d"),
    ],
)
def test_normalize_whitespace_collapses_separators(raw: str, expected: str) -> None:
    assert normalize_whitespace(raw) == expected


def test_normalize_whitespace_is_idempotent() -> None:
    once = normalize_whitespace("  many   spaces\there ")
    assert normalize_whitespace(once) == once


@pytest.mark.parametrize("raw", ["", "   ", "\n\t\r"])
def test_normalize_whitespace_rejects_blank_input(raw: str) -> None:
    with pytest.raises(EmptyTextError):
        normalize_whitespace(raw)


def test_empty_text_error_is_a_value_error() -> None:
    assert issubclass(EmptyTextError, ValueError)
