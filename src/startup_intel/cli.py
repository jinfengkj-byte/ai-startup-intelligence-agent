"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_report, fetch_feed, parse_feed, rank_items, save_report, utc_now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a source-linked AI startup intelligence report")
    parser.add_argument("--topic", required=True, help="Research topic or keywords, e.g. 'AI agent'")
    parser.add_argument("--config", type=Path, default=Path("config.example.json"), help="JSON config with feed URLs")
    parser.add_argument("--output", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--fixture", type=Path, help="Use local RSS/Atom XML for a reproducible demo")
    args = parser.parse_args(argv)

    if args.fixture:
        feeds = [{"name": "demo", "url": "https://example.org/feed.xml"}]
    else:
        try:
            config = json.loads(args.config.read_text(encoding="utf-8"))
            feeds = config["feeds"]
            if not isinstance(feeds, list) or not feeds:
                raise ValueError("config needs a nonempty feeds array")
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.error(f"cannot load config: {error}")

    collected = []
    errors = []
    for feed in feeds:
        try:
            data = args.fixture.read_bytes() if args.fixture else fetch_feed(feed["url"])
            collected.extend(parse_feed(data, feed["url"], args.topic))
        except Exception as error:
            errors.append(f"{feed.get('name', feed.get('url', 'feed'))}: {error}")
    if not collected and errors:
        print("All feeds failed: " + "; ".join(errors), file=sys.stderr)
        return 1
    report = build_report(rank_items(collected), args.topic, utc_now())
    report["feed_errors"] = errors
    paths = save_report(report, args.output)
    print(f"Wrote {len(report['items'])} items: {paths[0]} and {paths[1]}")
    if errors:
        print("Some feeds failed: " + "; ".join(errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
