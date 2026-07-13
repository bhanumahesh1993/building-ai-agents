# tests/test_registry.py — registry parsing, fully in-memory
from __future__ import annotations

from monitor.registry import PageKind, Registry, Target, default_registry


def test_add_appends_a_target_with_defaults():
    r = Registry()
    r.add("Acme Corp", PageKind.PRICING,
          "https://acme.example.com/pricing")
    assert len(r.targets) == 1
    t = r.targets[0]
    assert t == Target(
        competitor="Acme Corp", kind=PageKind.PRICING,
        url="https://acme.example.com/pricing",
        content_selector="main, article, body")


def test_add_honors_a_custom_selector():
    r = Registry()
    r.add("Acme Corp", PageKind.BLOG,
          "https://acme.example.com/blog",
          content_selector="#post-body")
    assert r.targets[0].content_selector == "#post-body"


def test_for_competitor_filters_correctly():
    r = Registry()
    r.add("Acme Corp", PageKind.PRICING, "https://acme.example.com/p")
    r.add("Acme Corp", PageKind.CHANGELOG, "https://acme.example.com/c")
    r.add("Rival Labs", PageKind.PRICING, "https://rival.example.com/p")

    acme = r.for_competitor("Acme Corp")
    assert len(acme) == 2
    assert all(t.competitor == "Acme Corp" for t in acme)


def test_for_competitor_returns_empty_for_unknown_name():
    r = Registry()
    r.add("Acme Corp", PageKind.PRICING, "https://acme.example.com/p")
    assert r.for_competitor("Nobody") == []


def test_default_registry_covers_every_page_kind():
    registry = default_registry()
    kinds = {t.kind for t in registry.targets}
    assert kinds == set(PageKind)


def test_default_registry_has_no_duplicate_urls():
    registry = default_registry()
    urls = [t.url for t in registry.targets]
    assert len(urls) == len(set(urls))


def test_default_registry_urls_use_https():
    registry = default_registry()
    assert all(t.url.startswith("https://")
               for t in registry.targets)


def test_default_registry_is_deterministic():
    first = default_registry()
    second = default_registry()
    assert [t.url for t in first.targets] == \
        [t.url for t in second.targets]


def test_page_kind_values_are_stable_strings():
    # These strings flow into prompts and scored-change
    # dicts, so their literal values are part of the
    # contract, not an implementation detail.
    assert PageKind.PRICING.value == "pricing"
    assert PageKind.CHANGELOG.value == "changelog"
    assert PageKind.CAREERS.value == "careers"
    assert PageKind.BLOG.value == "blog"
