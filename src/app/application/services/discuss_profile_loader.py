"""Load worldview, tone, and voice corpus slices for DiscussService."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import aiofiles

SCENARIO_LINE_IDS: dict[str, tuple[str, ...]] = {
    "A": ("L029", "L034", "L057", "L058", "L059"),
    "B": ("L015", "L020", "L043"),
    "C": ("L024", "L027", "L031", "L033"),
    "D": ("L002", "L004", "L018", "L054", "L055"),
    "E": ("L032", "L035", "L041", "L042"),
    "F": ("L021", "L022", "L023", "L024", "L025"),
    "G": ("L018", "L029", "L004"),
}

SCENARIO_GUIDE = """\
| سناریو | موقعیت |
|--------|--------|
| A | utopia / دولت بی‌عمل / تعرفه / اقتصاد |
| B | تاریخ / اصل+اما / مثال موازی |
| C | اتهام چپ / رفع مانع ≠ مداخله |
| D | ضربه‌ای / سؤال / فشار |
| E | موافقت کوتاه |
| F | حقوق فردی / زن / پزشکی |
| G | Fallback — سناریو نامشخص؛ نزدیک‌ترین A–F را حدس بزن |
"""


@dataclass(frozen=True, slots=True)
class DiscussResources:
    cognitive_profile: str
    worldview_profile: str
    tone_profile: str
    scenario_guide: str


async def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    async with aiofiles.open(path, encoding="utf-8") as handle:
        return (await handle.read()).strip()


def extract_worldview(profile_md: str) -> str:
    """Sections 1-5, 7, 9 — political/economic views without tone corpus."""
    if not profile_md:
        return ""
    parts: list[str] = []
    identity = _section(profile_md, "## هویت سیاسی")
    if identity:
        parts.append(identity)
    for marker in (
        "## ۱. ",
        "## ۲. ",
        "## ۳. ",
        "## ۴. ",
        "## ۵. ",
        "## ۷. ",
        "## ۹. ",
    ):
        chunk = _section(profile_md, marker)
        if chunk:
            parts.append(chunk)
    return "\n\n---\n\n".join(parts)


def extract_tone(profile_md: str) -> str:
    """Section 6 — tone, scenarios, fallback."""
    if not profile_md:
        return ""
    return _section(profile_md, "## ۶. ")


def _section(content: str, header_prefix: str) -> str:
    pattern = re.compile(
        rf"(?ms)^({re.escape(header_prefix)}.*?)(?=^## |\Z)",
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


async def load_discuss_resources(
    *,
    profile_path: Path,
    cognitive_path: Path,
) -> DiscussResources:
    profile_md = await read_text(profile_path)
    cognitive = await read_text(cognitive_path)
    if not cognitive:
        cognitive = _section(profile_md, "## ۰. ")
    return DiscussResources(
        cognitive_profile=cognitive,
        worldview_profile=extract_worldview(profile_md),
        tone_profile=extract_tone(profile_md),
        scenario_guide=SCENARIO_GUIDE,
    )


async def load_voice_samples(voice_path: Path, line_ids: tuple[str, ...]) -> str:
    raw = await read_text(voice_path)
    if not raw:
        return ""
    index: dict[str, str] = {}
    for line in raw.splitlines():
        if "|" not in line or line.startswith("#"):
            continue
        line_id, _, text = line.partition("|")
        index[line_id.strip()] = text.strip()
    samples: list[str] = []
    for lid in line_ids:
        sample_text = index.get(lid)
        if sample_text:
            samples.append(f"{lid}|{sample_text}")
    return "\n".join(samples)


def voice_line_ids_for_scenario(scenario: str, *, secondary: str | None = None) -> tuple[str, ...]:
    primary = scenario.upper()
    if primary not in SCENARIO_LINE_IDS:
        primary = "G"
    ids = list(SCENARIO_LINE_IDS[primary])
    if secondary and secondary.upper() in SCENARIO_LINE_IDS and secondary.upper() != primary:
        for line_id in SCENARIO_LINE_IDS[secondary.upper()]:
            if line_id not in ids:
                ids.append(line_id)
    return tuple(ids)
