"""Text stream step builder tests."""

from app.application.services.text_stream import build_stream_steps


def test_build_stream_steps_persian_with_space() -> None:
    steps = build_stream_steps("دوستت دارم")
    assert steps == [
        "د",
        "دو",
        "دوس",
        "دوست",
        "دوستت",
        "دوستت د",
        "دوستت دا",
        "دوستت دار",
        "دوستت دارم",
    ]
    assert "دوستت " not in steps


def test_build_stream_steps_persian_without_space() -> None:
    steps = build_stream_steps("دوستتدارم")
    assert steps[-1] == "دوستتدارم"
    assert len(steps) == len("دوستتدارم")


def test_build_stream_steps_skips_whitespace_only_steps() -> None:
    steps = build_stream_steps("hi there")
    assert steps == ["h", "hi", "hi t", "hi th", "hi the", "hi ther", "hi there"]
    assert "hi " not in steps


def test_build_stream_steps_empty() -> None:
    assert build_stream_steps("") == []
    assert build_stream_steps("   ") == []
