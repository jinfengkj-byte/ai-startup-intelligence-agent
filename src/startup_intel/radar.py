"""Persistent, evidence-linked startup signal tracking."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from contextlib import closing
from pathlib import Path

from .core import Item, fetch_feed, parse_feed, rank_items, utc_now


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("feeds"), list) or not config["feeds"]:
        raise ValueError("Config needs a nonempty feeds array")
    for feed in config["feeds"]:
        if not isinstance(feed, dict) or not isinstance(feed.get("url"), str):
            raise ValueError("Each feed needs a URL")
    companies = config.get("companies", [])
    if not isinstance(companies, list):
        raise ValueError("companies must be an array")
    for company in companies:
        if not isinstance(company, dict) or not isinstance(company.get("name"), str):
            raise ValueError("Each company needs a name")
    config["companies"] = companies
    return config


def match_company(item: Item, companies: list[dict]) -> str | None:
    # The title takes precedence. Feed summaries often mention several companies.
    for text in (item.title, item.summary):
        matches = []
        for company in companies:
            aliases = [company["name"], *company.get("aliases", [])]
            for alias in aliases:
                if alias and re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.IGNORECASE):
                    matches.append((len(alias), company["name"]))
        if matches:
            return max(matches)[1]
    return None


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            fingerprint TEXT PRIMARY KEY,
            company TEXT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT NOT NULL,
            published TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS events_company_seen ON events(company, first_seen);
    """)
    return connection


def store_items(connection: sqlite3.Connection, items: list[Item], companies: list[dict], seen_at: str) -> list[dict]:
    signals = []
    with connection:
        for item in items:
            fingerprint = hashlib.sha256(item.url.encode("utf-8")).hexdigest()[:24]
            company = match_company(item, companies)
            previous = connection.execute("SELECT first_seen FROM events WHERE fingerprint = ?", (fingerprint,)).fetchone()
            if previous:
                connection.execute("UPDATE events SET last_seen = ? WHERE fingerprint = ?", (seen_at, fingerprint))
            else:
                connection.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    fingerprint, company, item.title, item.url, item.source, item.published,
                    item.summary, item.category, seen_at, seen_at,
                ))
            signals.append({
                "id": fingerprint, "company": company, "title": item.title, "url": item.url,
                "source": item.source, "published": item.published or None,
                "summary": item.summary, "category": item.category,
                "relevance": item.relevance, "first_seen": previous["first_seen"] if previous else seen_at,
                "is_new": previous is None,
            })
    return signals


def company_history(connection: sqlite3.Connection, companies: list[dict], limit: int = 8) -> list[dict]:
    profiles = []
    for company in companies:
        name = company["name"]
        rows = connection.execute(
            "SELECT title, url, source, category, first_seen FROM events WHERE company = ? ORDER BY first_seen DESC LIMIT ?",
            (name, limit),
        ).fetchall()
        profiles.append({"name": name, "website": company.get("website", ""), "signals": [dict(row) for row in rows]})
    return profiles


def scan(config: dict, db_path: Path, *, fixture: Path | None = None, limit: int = 30) -> dict:
    topic = str(config.get("topic", "AI startup")).strip()
    collected: list[Item] = []
    errors = []
    feeds = config["feeds"]
    for feed in feeds:
        try:
            data = fixture.read_bytes() if fixture else fetch_feed(feed["url"])
            collected.extend(parse_feed(data, feed["url"], topic))
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
            errors.append(f"{feed.get('name', feed.get('url', 'feed'))}: {error}")
    if len(errors) == len(feeds):
        raise RuntimeError("All feeds failed: " + "; ".join(errors))
    items = rank_items(collected, limit=limit)
    now = utc_now()
    with closing(connect(db_path)) as connection:
        signals = store_items(connection, items, config["companies"], now)
        profiles = company_history(connection, config["companies"])
    return {
        "product": "Open Startup Radar", "topic": topic, "generated_at": now,
        "demo": fixture is not None,
        "sources_checked": len(feeds), "feed_errors": errors,
        "new_count": sum(signal["is_new"] for signal in signals),
        "signals": signals, "companies": profiles,
        "method": "Feed entries are evidence, not verified facts. Company matching and categories are rules; AI analysis is optional.",
    }


def write_json(report: dict, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    target = output / "report.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
