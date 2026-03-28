"""
HTML to clean plain text.

Uses stdlib html.parser — no external dependencies.

Skips tags that never contain policy text: <script>, <style>, <nav>,
<footer>, <header>, <aside>, <form>, <button>, <svg>.

The output is suitable for feeding into the rubric extraction prompt and
for red-flag pattern matching.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

_SKIP_TAGS = frozenset({
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "form", "button", "svg", "canvas", "img", "picture",
})

# Block-level tags that should produce a newline in the output
_BLOCK_TAGS = frozenset({
    "p", "div", "section", "article", "li", "h1", "h2", "h3",
    "h4", "h5", "h6", "br", "hr", "td", "th", "dt", "dd",
})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS and self._parts:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def html_to_text(html: str) -> str:
    """Convert HTML to clean plain text.

    - Strips navigation, scripts, styles
    - Preserves paragraph/heading structure as blank lines
    - Collapses excess whitespace
    """
    extractor = _TextExtractor()
    extractor.feed(html)
    text = extractor.get_text()

    # Normalise whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
