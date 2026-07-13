# crew/tasks.py
from __future__ import annotations

from crewai import Task

from .agents import (
    strategist, copywriter, seo_specialist, editor,
    art_director,
)
from .models import (
    StrategyBrief, DraftCopy, SeoReview,
    EditorVerdict,
)

strategy_task = Task(
    description=(
        "Read this product brief:\n{brief_json}\n\n"
        "Identify the primary audience, a one-line "
        "campaign angle, and 3-5 key messages the "
        "rest of the crew will build on."
    ),
    expected_output=(
        "A StrategyBrief: audience, angle, and a "
        "short list of key messages."
    ),
    agent=strategist,
    output_pydantic=StrategyBrief,
)

copy_task = Task(
    description=(
        "Using the strategist's angle and key "
        "messages, write one ~500-word blog post "
        "and three social variants (instagram, "
        "tiktok, x). Call Brand Guide Lookup for "
        "voice before you write. Do not invent facts "
        "beyond this brief:\n{brief_json}"
    ),
    expected_output=(
        "A DraftCopy: blog_title, blog_body, and "
        "three SocialVariant entries."
    ),
    agent=copywriter,
    context=[strategy_task],
    output_pydantic=DraftCopy,
)

seo_task = Task(
    description=(
        "Using Keyword Research, pull realistic "
        "keywords for the blog post's topic, write a "
        "meta description (120-160 characters), and "
        "note any heading fix the post needs for "
        "search visibility."
    ),
    expected_output=(
        "A SeoReview: keywords, meta_description, "
        "and heading_notes."
    ),
    agent=seo_specialist,
    context=[copy_task],
    output_pydantic=SeoReview,
)

editor_task = Task(
    description=(
        "Check the draft copy and SEO review "
        "against the brand guide and this brief's "
        "key_facts - ground truth, nothing else is "
        "a fact:\n{brief_json}\n\n"
        "Score brand-voice fit 1-5, list any claim "
        "not backed by key_facts, and either approve "
        "or write specific revision notes."
    ),
    expected_output=(
        "An EditorVerdict: approved, "
        "brand_voice_score, factual_issues, notes."
    ),
    agent=editor,
    context=[strategy_task, copy_task, seo_task],
    output_pydantic=EditorVerdict,
)
