# monitor/prompts.py

DIFF_SYSTEM = """You compare two versions of the same
web page and judge whether the MEANING changed, not
just the wording.

Ignore: rephrasing, reordering, typo fixes, date or
timestamp changes, cosmetic formatting.
Flag: price changes, feature additions or removals,
new job postings, policy changes, anything a reader
would act on differently after reading the new
version.

If nothing meaningful changed, reply with exactly:
NO_MEANINGFUL_CHANGE

Otherwise, write one tight paragraph (60-100 words)
describing exactly what changed and why it matters.

OLD VERSION:
{old_text}

NEW VERSION:
{new_text}"""

SCORE_SYSTEM = """You are a competitive-intelligence
analyst. Score this confirmed change 1-5 for how
newsworthy it is to a product and marketing team.

Consider three axes:
- Buying-decision impact: would a prospect's choice
  change because of this?
- Competitive-position impact: does it close, widen,
  or create a gap with our own roadmap?
- Hiring or strategy signal: does it reveal a
  direction (e.g. new job titles, new focus areas)?

Page kind: {kind}
Confirmed change: {summary}

Return ONLY JSON:
{{"score": n, "reason": "one sentence"}}"""

DIGEST_SYSTEM = """You are writing a Monday-morning
competitive-intelligence digest for a product
marketing team. Group the changes below by
competitor. For each item, write one crisp bullet
(20-35 words) stating what changed and why it
matters, ending with the source URL in parentheses.
Skip nothing you were given; invent nothing you
weren't. Open with a one-line summary of how many
competitors had notable movement this run.

Scored changes (JSON):
{changes}"""
