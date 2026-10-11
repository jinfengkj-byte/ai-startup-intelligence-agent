import unittest
from pathlib import Path

from startup_intel.core import build_report, parse_feed, rank_items, render_markdown


class PipelineTests(unittest.TestCase):
    def test_fixture_filters_deduplicates_and_cites(self):
        feed = Path(__file__).resolve().parents[1] / "examples" / "demo-feed.xml"
        items = parse_feed(feed.read_bytes(), "https://example.org/feed.xml", "AI agent")
        ranked = rank_items(items)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].category, "product")
        report = build_report(ranked, "AI agent", "2026-10-11T00:00:00+00:00")
        markdown = render_markdown(report)
        self.assertIn("https://example.org/articles/agent-api", markdown)
        self.assertNotIn("garden", markdown)


if __name__ == "__main__":
    unittest.main()
