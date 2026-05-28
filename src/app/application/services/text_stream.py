"""Progressive text reveal for message edits."""


def build_stream_steps(text: str) -> list[str]:
    """Build edit targets, skipping steps that only add whitespace.

    Example: ``دوستت دارم`` → ``د``, ``دو``, ``دوس``, ...
    Whitespace is kept in the buffer but does not trigger its own edit step.
    """
    if not text:
        return []

    accumulated = ""
    steps: list[str] = []
    for char in text:
        accumulated += char
        if char.isspace():
            continue
        steps.append(accumulated)

    if (
        accumulated
        and (not steps or steps[-1] != accumulated)
        and any(not char.isspace() for char in accumulated)
    ):
        steps.append(accumulated)

    return steps
