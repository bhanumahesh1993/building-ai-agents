# crew/models.py
from __future__ import annotations

from pydantic import BaseModel


class StrategyBrief(BaseModel):
    audience: str
    angle: str
    key_messages: list[str]


class SocialVariant(BaseModel):
    channel: str
    text: str


class DraftCopy(BaseModel):
    blog_title: str
    blog_body: str
    social_variants: list[SocialVariant]


class SeoReview(BaseModel):
    keywords: list[str]
    meta_description: str
    heading_notes: str


class EditorVerdict(BaseModel):
    approved: bool
    brand_voice_score: int
    factual_issues: list[str]
    notes: str


class ImageBrief(BaseModel):
    channel: str
    concept: str
    composition: str
    mood: str
    avoid: str


class ImageBriefSet(BaseModel):
    briefs: list[ImageBrief]


class CampaignKit(BaseModel):
    strategy: StrategyBrief
    copy: DraftCopy
    seo: SeoReview
    editor: EditorVerdict
    image_briefs: list[ImageBrief]
    revisions_used: int
