"""Tests for DiscussService."""

from pathlib import Path

import pytest

from app.application.services.discuss_profile_loader import (
    extract_tone,
    extract_worldview,
    load_voice_samples,
    voice_line_ids_for_scenario,
)
from app.application.services.discuss_service import DiscussService, _parse_analysis
from app.infrastructure.llm.openai_chat_client import (
    ChatMessage,
    OpenAiChatClient,
    OpenAiChatConfig,
)


class FakeLlmClient:
    """Returns canned responses per call order."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls: list[list[ChatMessage]] = []

    @property
    def enabled(self) -> bool:
        return True

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        _ = temperature, max_tokens
        self.calls.append(messages)
        if not self._responses:
            msg = "No fake responses left"
            raise RuntimeError(msg)
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_load_profile_missing_file(tmp_path: Path) -> None:
    service = DiscussService(
        tmp_path / "missing.md",
        cognitive_path=tmp_path / "cognitive.md",
        voice_path=tmp_path / "voice.txt",
    )
    profile = await service.load_profile()
    assert profile.loaded is False
    assert "تنظیم نشده" in profile.summary


@pytest.mark.asyncio
async def test_answer_without_llm(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.md"
    profile_path.write_text("## ۱. فلسفه\nبازار آزاد.", encoding="utf-8")
    service = DiscussService(
        profile_path,
        cognitive_path=tmp_path / "cognitive.md",
        voice_path=tmp_path / "voice.txt",
        llm=None,
    )
    result = await service.answer("تورم بالاست")
    assert "LLM تنظیم نشده" in result


@pytest.mark.asyncio
async def test_three_layer_pipeline(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.md"
    profile_path.write_text(
        "## هویت سیاسی-اقتصادی\nراست لیبرال.\n\n## ۱. فلسفه\nبازار آزاد.\n\n## ۶. لحن\nمستقیم.",
        encoding="utf-8",
    )
    cognitive_path = tmp_path / "cognitive.md"
    cognitive_path.write_text("2e — سریع.", encoding="utf-8")
    voice_path = tmp_path / "voice.txt"
    voice_path.write_text("L029|نمونه لحن", encoding="utf-8")

    analysis_json = (
        '{"topic":"تورم","opponent_claims":["دولت مقصر است"],'
        '"argument_type":"اقتصاد","scenario":"A","scenario_confidence":"high",'
        '"secondary_scenario":null,"response_strategy":"ایده‌آل vs وضع موجود"}'
    )
    fake = FakeLlmClient(
        [
            analysis_json,
            "پیش‌نویس: بازار آزاد بهتر از مداخله است.",
            "نهایی: ببین حرفت روی کاغذ درسته ولی وضع موجود فرق داره.",
        ],
    )
    service = DiscussService(
        profile_path,
        cognitive_path=cognitive_path,
        voice_path=voice_path,
        llm=fake,  # type: ignore[arg-type]
    )
    result = await service.answer("دولت باید قیمت‌ها را کنترل کند")
    assert "وضع موجود" in result
    assert len(fake.calls) == 3
    assert "Layer 1" not in result


def test_parse_analysis_fallback_on_invalid_json() -> None:
    analysis = _parse_analysis("not json")
    assert analysis.scenario == "G"
    assert analysis.scenario_confidence == "low"


def test_extract_worldview_and_tone() -> None:
    content = "## ۱. فلسفه\nیک.\n\n## ۶. لحن\nدو.\n\n## ۷. چک\nسه."
    assert "یک." in extract_worldview(content)
    assert "دو." in extract_tone(content)
    assert "سه." not in extract_tone(content)


@pytest.mark.asyncio
async def test_load_voice_samples(tmp_path: Path) -> None:
    voice_path = tmp_path / "voice.txt"
    voice_path.write_text("L001|alpha\nL002|beta", encoding="utf-8")
    samples = await load_voice_samples(voice_path, ("L002", "L999"))
    assert "L002|beta" in samples
    assert "L999" not in samples


def test_voice_line_ids_for_scenario() -> None:
    ids = voice_line_ids_for_scenario("G", secondary="D")
    assert "L029" in ids
    assert "L002" in ids


def test_openai_client_disabled_without_key() -> None:
    client = OpenAiChatClient(
        OpenAiChatConfig(
            base_url="http://127.0.0.1:3001/v1",
            api_key="",
            model="auto",
            timeout_seconds=30.0,
        ),
    )
    assert client.enabled is False
