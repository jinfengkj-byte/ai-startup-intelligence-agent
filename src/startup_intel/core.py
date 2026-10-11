"""Fetch feeds, deduplicate entries, and build source-linked reports."""

from __future__ import annotations

import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

USER_AGENT = "OpenStartupRadar/0.2.1 (+https://github.com/jinfengkj-byte/open-startup-radar)"
ATOM = "{http://www.w3.org/2005/Atom}"
TAGS = {
    "funding": ("funding", "raised", "series a", "series b", "investment", "acquisition"),
    "open-source": ("open source", "open-source", "github", "repository"),
    "product": ("launch", "release", "product", "api", "model", "agent"),
}


@dataclass(frozen=True)
class Item:
    title: str
    url: str
    source: str
    published: str
    summary: str
    category: str
    relevance: int
    company_hint: str | None = None


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def canonical_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    query = urlencode(sorted((key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}))
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/") or "/", "", query, ""))


def fetch_feed(url: str, timeout: int = 15) -> bytes:
    if not canonical_url(url):
        raise ValueError(f"Invalid feed URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"Feed returned HTTP {response.status}: {url}")
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError(f"Feed exceeds the 2 MB limit: {url}")
        return data


def parse_feed(data: bytes, feed_url: str, topic: str) -> list[Item]:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Feed XML must not contain a DTD or entity declaration")
    root = ET.fromstring(data)
    source = clean(root.findtext("./channel/title") or root.findtext(f"./{ATOM}title") or urlparse(feed_url).netloc)
    result = []
    nodes = root.findall("./channel/item") if root.tag.lower() == "rss" else root.findall(f"./{ATOM}entry")
    for node in nodes:
        is_atom = node.tag.startswith(ATOM)
        prefix = ATOM if is_atom else ""
        title = clean(node.findtext(f"{prefix}title"))
        summary = clean(node.findtext(f"{prefix}summary") or node.findtext(f"{prefix}content") or node.findtext("description"))
        link = node.findtext("link") if not is_atom else next((e.attrib.get("href", "") for e in node.findall(f"{ATOM}link") if e.attrib.get("rel", "alternate") == "alternate"), "")
        url = canonical_url(link or "")
        published = clean(node.findtext(f"{prefix}published") or node.findtext(f"{prefix}updated") or node.findtext("pubDate"))
        if not title or not url:
            continue
        haystack = f"{title} {summary}".lower()
        terms = [term.lower() for term in re.findall(r"[\w-]+", topic) if len(term) >= 2 and term.lower() not in {"and", "the", "for", "with", "from"}]
        if terms and not all(term in haystack for term in terms):
            continue
        score = sum(3 if term in title.lower() else 1 for term in terms if term in haystack)
        category = next((name for name, words in TAGS.items() if any(word in haystack for word in words)), "other")
        result.append(Item(title, url, source, published, summary[:500], category, score))
    return result


def rank_items(items: list[Item], limit: int = 20) -> list[Item]:
    seen: set[str] = set()
    unique = []
    for item in sorted(items, key=lambda x: (-x.relevance, x.title.casefold())):
        key = item.url or re.sub(r"\W+", "", item.title.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:limit]


def build_report(items: list[Item], topic: str, generated_at: str) -> dict:
    return {
        "topic": topic,
        "generated_at": generated_at,
        "method": "Feed keyword matching; category and relevance are heuristics, not verified conclusions.",
        "items": [asdict(item) for item in items],
    }


def render_markdown(report: dict) -> str:
    lines = [f"# AI Startup Intelligence: {report['topic']}", "", f"Generated: {report['generated_at']}", "", f"{report['method']}", "", f"Items: {len(report['items'])}", ""]
    for category in ("funding", "product", "open-source", "other"):
        group = [item for item in report["items"] if item["category"] == category]
        if not group:
            continue
        lines.extend([f"## {category.title()}", ""])
        for item in group:
            title = item["title"].replace("[", "\\[").replace("]", "\\]")
            lines.extend([f"### [{title}]({item['url']})", "", f"Source: {item['source']} | Published: {item['published'] or 'not provided'} | Relevance: {item['relevance']}", "", item["summary"] or "No summary provided by the feed.", ""])
    lines.extend(["## Reading notes", "", "Open each source before relying on a claim. Funding amounts, company identity, and dates are not independently verified by this tool.", ""])
    return "\n".join(lines)


def save_report(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
