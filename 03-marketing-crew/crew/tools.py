# crew/tools.py
from __future__ import annotations

from crewai.tools import tool

_BRAND_GUIDE = {
    "voice": (
        "Energetic, peer-to-peer, never corporate. "
        "Write like a student texting a friend a "
        "good deal, not like a press release."
    ),
    "banned": (
        "Never claim 'fastest in the country', "
        "'cheaper than cooking', or any superlative "
        "not listed in the brief's key_facts."
    ),
    "cta": (
        "Every piece ends with one clear action: "
        "download the app or use the launch code."
    ),
}

_KEYWORD_STATS = {
    "food delivery": (8100, "high"),
    "campus food delivery": (320, "low"),
    "student discount app": (590, "medium"),
    "late night food near campus": (410, "low"),
    "cheap delivery college": (260, "low"),
}


@tool("Keyword Research")
def keyword_research(topic: str) -> str:
    """Estimated monthly search volume and ranking
    difficulty for a marketing topic. A stub over a
    static table - swap for Ahrefs/Semrush later."""
    words = topic.lower().split()
    hits = [
        f"{kw}: ~{vol}/mo, {diff} difficulty"
        for kw, (vol, diff) in _KEYWORD_STATS.items()
        if any(w in kw for w in words)
    ]
    if not hits:
        hits = [
            f"{kw}: ~{vol}/mo, {diff} difficulty"
            for kw, (vol, diff)
            in list(_KEYWORD_STATS.items())[:3]
        ]
    return "\n".join(hits)


@tool("Brand Guide Lookup")
def brand_guide_lookup(section: str) -> str:
    """Retrieve one section of the brand guide:
    voice, banned, or cta. Call this before writing
    or editing any customer-facing copy."""
    key = section.strip().lower()
    return _BRAND_GUIDE.get(
        key, "; ".join(_BRAND_GUIDE.values()))
