import unittest
from pathlib import Path

from startup_intel.core import build_report, canonical_url, parse_feed, rank_items, render_markdown


class PipelineTests(unittest.TestCase):
    def test_canonical_link_keeps_story_ids_but_drops_tracking(self):
        self.assertEqual(canonical_url("https://example.org/item?id=1&utm_source=mail"), "https://example.org/item?id=1")
        self.assertNotEqual(canonical_url("https://example.org/item?id=1"), canonical_url("https://example.org/item?id=2"))

    def test_fixture_filters_deduplicates_and_cites(self):
        feed = Path(__file__).resolve().parents[1] / "examples" / "demo-feed.xml"
        items = parse_feed(feed.read_bytes(), "https://example.org/feed.xml", "AI agent")
        ranked = rank_items(items)
        self.assertEqual(len(ranked), 4)
        self.assertEqual(len([item for item in ranked if item.url.endswith("agent-api")]), 1)
        self.assertEqual(next(item.category for item in ranked if "vectorworks" in item.url), "open-source")
        report = build_report(ranked, "AI agent", "2026-10-11T00:00:00+00:00")
        markdown = render_markdown(report)
        self.assertIn("https://example.org/articles/agent-api", markdown)
        self.assertNotIn("garden", markdown)


if __name__ == "__main__":
    unittest.main()
