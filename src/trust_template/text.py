"""Small text helpers used as the template's placeholder module."""


class EmptyTextError(ValueError):
    """Raised when a text operation receives no usable content."""


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace in ``text`` into single spaces.

    Leading and trailing whitespace is stripped. Newlines, tabs and repeated
    spaces are all treated as a single separator.

    Args:
        text: The string to normalize.

    Returns:
        The normalized string.

    Raises:
        EmptyTextError: If ``text`` contains no non-whitespace character.

    Examples:
        >>> normalize_whitespace("  hello\\n\\tworld  ")
        'hello world'
    """
    normalized = " ".join(text.split())
    if not normalized:
        raise EmptyTextError("text contains no non-whitespace character")
    return normalized
