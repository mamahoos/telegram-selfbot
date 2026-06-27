"""Discussion assistance — three-layer LLM reply pipeline."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from app.application.services.discuss_output_sanitizer import sanitize_discuss_output
from app.application.services.discuss_profile_loader import (
    DiscussResources,
    load_discuss_resources,
    load_voice_samples,
    voice_line_ids_for_scenario,
)
from app.infrastructure.llm.openai_chat_client import ChatMessage, OpenAiChatClient

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], Awaitable[None]]
TELEGRAM_MAX_CHARS = 4096


@dataclass(frozen=True, slots=True)
class DiscussProfile:
    """User worldview and tone profile (loaded from profile file)."""

    loaded: bool
    summary: str


@dataclass(frozen=True, slots=True)
class DiscussAnalysis:
    """Layer 1 structured understanding of the opponent message."""

    topic: str
    opponent_claims: tuple[str, ...]
    argument_type: str
    scenario: str
    scenario_confidence: str
    secondary_scenario: str | None
    response_strategy: str


class DiscussService:
    """Prepares discussion replies via analyze → worldview draft → tone polish."""

    def __init__(
        self,
        profile_path: Path,
        *,
        cognitive_path: Path,
        voice_path: Path,
        llm: OpenAiChatClient | None = None,
    ) -> None:
        self._profile_path = profile_path
        self._cognitive_path = cognitive_path
        self._voice_path = voice_path
        self._llm = llm
        self._resources: DiscussResources | None = None

    async def load_profile(self) -> DiscussProfile:
        resources = await self._get_resources()
        if not resources.worldview_profile:
            return DiscussProfile(
                loaded=False,
                summary=(
                    f"پروفایل دیدگاه‌ها هنوز تنظیم نشده. فایل `{self._profile_path}` را بسازید."
                ),
            )
        preview = resources.worldview_profile[:200].replace("\n", " ")
        if len(resources.worldview_profile) > 200:
            preview += "…"
        return DiscussProfile(loaded=True, summary=preview)

    @property
    def llm_enabled(self) -> bool:
        return self._llm is not None and self._llm.enabled

    @property
    def llm_model_name(self) -> str:
        if self._llm is None:
            return "off"
        return self._llm.model

    async def answer(
        self,
        opponent_message: str,
        *,
        extra_prompt: str = "",
        progress: ProgressCallback | None = None,
    ) -> str:
        profile = await self.load_profile()
        if not profile.loaded:
            return f"⚠️ **Discuss — پروفایل تنظیم نشده**\n\n{profile.summary}"

        if self._llm is None or not self._llm.enabled:
            return "⚠️ **LLM تنظیم نشده**\n\nمتغیر `LLM_API_KEY` را در `.env` بگذار."

        opponent = opponent_message.strip()
        if not opponent:
            return "⚠️ پیام طرف خالی است."

        if progress is not None:
            await progress("⏳ **لایه ۱** — تحلیل استدلال…")
        analysis = await self._layer1_analyze(opponent)

        if progress is not None:
            await progress("⏳ **لایه ۲** — پاسخ بر اساس پروفایل ذهنی…")
        draft = await self._layer2_draft(opponent, analysis, extra_prompt)

        if progress is not None:
            await progress("⏳ **لایه ۳** — ویرایش لحن…")
        polished = await self._layer3_tone(opponent, analysis, draft)

        if progress is not None:
            await progress("⏳ **پاک‌سازی** — حذف نشانه‌های مدل…")
        final = sanitize_discuss_output(polished)

        return _truncate_telegram(final)

    async def draft_reply(self, prompt: str, *, reply_to: str | None = None) -> str:
        opponent = (reply_to or prompt).strip()
        extra = "" if reply_to is None else prompt.strip()
        return await self.answer(opponent, extra_prompt=extra)

    async def _get_resources(self) -> DiscussResources:
        if self._resources is None:
            self._resources = await load_discuss_resources(
                profile_path=self._profile_path,
                cognitive_path=self._cognitive_path,
            )
        return self._resources

    async def _layer1_analyze(self, opponent_message: str) -> DiscussAnalysis:
        resources = await self._get_resources()
        system = (
            "You analyze Telegram debate messages for a Persian political/economic self-bot.\n"
            "Return ONLY valid JSON (no markdown) with keys:\n"
            "topic, opponent_claims (array of strings), argument_type, scenario (A-G), "
            "scenario_confidence (high|medium|low), secondary_scenario (A-G or null), "
            "response_strategy (one paragraph in Persian).\n"
            "Use scenario G when uncertain and pick the closest A-F in response_strategy.\n\n"
            f"{resources.scenario_guide}"
        )
        user = f"پیام طرف:\n{opponent_message}"
        raw = await self._llm_complete(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=900,
        )
        return _parse_analysis(raw)

    async def _layer2_draft(
        self,
        opponent_message: str,
        analysis: DiscussAnalysis,
        extra_prompt: str,
    ) -> str:
        resources = await self._get_resources()
        analysis_blob = _analysis_for_prompt(analysis)
        system = (
            "You write a substantive Persian reply for a Telegram private debate.\n"
            "Match the owner's worldview and reasoning — NOT their casual tone yet.\n"
            "Rules:\n"
            "- Use ideal vs present reality when relevant.\n"
            "- Result-oriented pragmatism; anti-dogmatic.\n"
            "- No IQ scores; no verbatim quotes from corpus.\n"
            "- Output ONLY the reply text — no headings, no meta.\n\n"
            f"### Cognitive profile\n{resources.cognitive_profile}\n\n"
            f"### Worldview profile\n{resources.worldview_profile}"
        )
        user_parts = [
            f"### Analysis (layer 1)\n{analysis_blob}",
            f"### Opponent message\n{opponent_message}",
        ]
        if extra_prompt.strip():
            user_parts.append(f"### Owner note\n{extra_prompt.strip()}")
        user_parts.append("Write the reply body in Persian.")
        return await self._llm_complete(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            temperature=0.55,
            max_tokens=1800,
        )

    async def _layer3_tone(
        self,
        opponent_message: str,
        analysis: DiscussAnalysis,
        draft: str,
    ) -> str:
        resources = await self._get_resources()
        line_ids = voice_line_ids_for_scenario(
            analysis.scenario,
            secondary=analysis.secondary_scenario,
        )
        voice_samples = await load_voice_samples(self._voice_path, line_ids)
        system = (
            "You are a tone editor for a Persian Telegram debater.\n"
            "Rewrite the draft to match the owner's voice — structure, rhythm, directness.\n"
            "Rules:\n"
            "- Keep the same arguments and conclusions.\n"
            "- Telegram-style Persian; short paragraphs; punchy where scenario D.\n"
            "- Do NOT copy corpus lines verbatim — only mimic patterns.\n"
            "- Output ONLY the final message — no meta.\n\n"
            f"### Tone profile\n{resources.tone_profile}\n\n"
            f"### Voice samples (patterns only)\n{voice_samples or '(none)'}"
        )
        user = (
            f"Scenario: {analysis.scenario} ({analysis.scenario_confidence})\n"
            f"Strategy: {analysis.response_strategy}\n\n"
            f"Opponent:\n{opponent_message}\n\n"
            f"Draft to polish:\n{draft}"
        )
        return await self._llm_complete(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.65,
            max_tokens=1800,
        )

    async def _llm_complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if self._llm is None:
            msg = "LLM client is not configured"
            raise RuntimeError(msg)
        try:
            return await self._llm.complete(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception:
            logger.exception("LLM request failed")
            raise


def _parse_analysis(raw: str) -> DiscussAnalysis:
    cleaned = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return DiscussAnalysis(
            topic="نامشخص",
            opponent_claims=(),
            argument_type="نامشخص",
            scenario="G",
            scenario_confidence="low",
            secondary_scenario=None,
            response_strategy=raw[:400],
        )

    claims_raw = data.get("opponent_claims", [])
    claims: list[str] = []
    if isinstance(claims_raw, list):
        claims = [str(item) for item in claims_raw if str(item).strip()]

    scenario = str(data.get("scenario", "G")).upper()[:1]
    if scenario not in {"A", "B", "C", "D", "E", "F", "G"}:
        scenario = "G"

    secondary_raw = data.get("secondary_scenario")
    secondary: str | None = None
    if isinstance(secondary_raw, str) and secondary_raw.strip():
        sec = secondary_raw.upper()[:1]
        if sec in {"A", "B", "C", "D", "E", "F"}:
            secondary = sec

    return DiscussAnalysis(
        topic=str(data.get("topic", "نامشخص")),
        opponent_claims=tuple(claims),
        argument_type=str(data.get("argument_type", "نامشخص")),
        scenario=scenario,
        scenario_confidence=str(data.get("scenario_confidence", "low")),
        secondary_scenario=secondary,
        response_strategy=str(data.get("response_strategy", "")),
    )


def _analysis_for_prompt(analysis: DiscussAnalysis) -> str:
    claims = "\n".join(f"- {claim}" for claim in analysis.opponent_claims) or "- (none)"
    secondary = analysis.secondary_scenario or "none"
    return (
        f"topic: {analysis.topic}\n"
        f"argument_type: {analysis.argument_type}\n"
        f"scenario: {analysis.scenario} ({analysis.scenario_confidence})\n"
        f"secondary_scenario: {secondary}\n"
        f"opponent_claims:\n{claims}\n"
        f"response_strategy: {analysis.response_strategy}"
    )


def _truncate_telegram(text: str) -> str:
    trimmed = text.strip()
    if len(trimmed) <= TELEGRAM_MAX_CHARS:
        return trimmed
    return trimmed[: TELEGRAM_MAX_CHARS - 1] + "…"
