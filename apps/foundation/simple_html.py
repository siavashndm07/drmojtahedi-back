from __future__ import annotations

import html
import re

ALLOWED_TAGS = frozenset({"p", "strong", "em", "li", "ul", "ol", "br"})

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BLOCK_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_TAG_RE = re.compile(
    r"</?(?:iframe|object|embed|link|meta|form|input|button|svg|math|textarea|select)[^>]*>",
    re.IGNORECASE,
)
_A_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_BARE_A_RE = re.compile(r"</?a\b[^>]*>", re.IGNORECASE)
_TAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", re.IGNORECASE)
_HREF_RE = re.compile(
    r"""\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)


def _is_safe_href(href: str) -> bool:
    trimmed = (href or "").strip()
    if not trimmed:
        return False
    if trimmed.startswith("#") or trimmed.startswith("/"):
        return True
    lower = trimmed.lower()
    return lower.startswith(("http://", "https://", "mailto:", "tel:"))


def _extract_href(attrs: str) -> str:
    href_match = _HREF_RE.search(attrs or "")
    if not href_match:
        return ""
    return (
        href_match.group(1) or href_match.group(2) or href_match.group(3) or ""
    ).strip()


def sanitize_simple_html(value: str | None) -> str:
    """Keep only a small allowlist of HTML tags for admin-authored messages."""
    if not value:
        return ""
    text = _COMMENT_RE.sub("", str(value))
    text = _BLOCK_RE.sub("", text)
    text = _DANGEROUS_TAG_RE.sub("", text)

    kept_anchors: list[str] = []

    def replace_anchor(match: re.Match[str]) -> str:
        attrs = match.group(1) or ""
        inner = match.group(2) or ""
        href = _extract_href(attrs)
        if not _is_safe_href(href):
            return inner
        safe = html.escape(href, quote=True)
        if href.lower().startswith(("http://", "https://")):
            rebuilt = (
                f'<a href="{safe}" target="_blank" rel="noopener noreferrer">'
                f"{inner}</a>"
            )
        else:
            rebuilt = f'<a href="{safe}">{inner}</a>'
        token = f"@@SAFEA{len(kept_anchors)}@@"
        kept_anchors.append(rebuilt)
        return token

    text = _A_RE.sub(replace_anchor, text)
    text = _BARE_A_RE.sub("", text)

    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(1).lower()
        closing = match.group(0).startswith("</")
        if tag not in ALLOWED_TAGS:
            return ""
        if closing:
            return f"</{tag}>"
        if tag == "br":
            return "<br />"
        return f"<{tag}>"

    text = _TAG_RE.sub(replace_tag, text)
    for index, anchor in enumerate(kept_anchors):
        text = text.replace(f"@@SAFEA{index}@@", anchor)
    return text.strip()
