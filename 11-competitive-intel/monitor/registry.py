# monitor/registry.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PageKind(str, Enum):
    """The four page types this system understands."""
    PRICING = "pricing"
    CHANGELOG = "changelog"
    CAREERS = "careers"
    BLOG = "blog"


@dataclass
class Target:
    """One page, on one competitor, worth watching."""
    competitor: str
    kind: PageKind
    url: str
    # CSS selector for the main content block;
    # keeps nav/footer boilerplate out of the diff.
    content_selector: str = "main, article, body"


@dataclass
class Registry:
    """The full list of competitors and pages."""
    targets: list[Target] = field(default_factory=list)

    def add(self, competitor: str, kind: PageKind,
            url: str, content_selector: str = "main, article, body"
            ) -> None:
        self.targets.append(Target(
            competitor=competitor, kind=kind,
            url=url, content_selector=content_selector))

    def for_competitor(self, name: str) -> list[Target]:
        return [t for t in self.targets
                if t.competitor == name]


def default_registry() -> Registry:
    """A small, illustrative starting registry."""
    r = Registry()
    r.add("Acme Corp", PageKind.PRICING,
          "https://acme.example.com/pricing")
    r.add("Acme Corp", PageKind.CHANGELOG,
          "https://acme.example.com/changelog")
    r.add("Rival Labs", PageKind.PRICING,
          "https://rivallabs.example.com/pricing")
    r.add("Rival Labs", PageKind.CHANGELOG,
          "https://rivallabs.example.com/changelog")
    r.add("Rival Labs", PageKind.CAREERS,
          "https://rivallabs.example.com/careers")
    r.add("Northwind", PageKind.BLOG,
          "https://northwind.example.com/blog")
    return r
