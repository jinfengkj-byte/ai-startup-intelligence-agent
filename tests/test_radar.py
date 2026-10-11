import tempfile
import unittest
from pathlib import Path

from startup_intel.dashboard import render_html, render_markdown
from startup_intel.radar import load_config, scan


ROOT = Path(__file__).resolve().parents[1]


class RadarTests(unittest.TestCase):
    def test_first_scan_then_repeat_tracks_only_new_links(self):
        config = load_config(ROOT / "examples" / "demo-config.json")
        fixture = ROOT / "examples" / "demo-feed.xml"
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "history.sqlite"
            first = scan(config, db, fixture=fixture)
            second = scan(config, db, fixture=fixture)
        self.assertEqual(first["new_count"], 4)
        self.assertEqual(second["new_count"], 0)
        self.assertIn("Example AI", {signal["company"] for signal in first["signals"]})
        self.assertEqual(len(second["companies"][0]["signals"]), 1)
        self.assertIn("https://example.org/articles/agent-api", render_markdown(first))
        self.assertIn("Example AI", render_html(first))

    def test_report_escapes_feed_markup(self):
        config = load_config(ROOT / "examples" / "demo-config.json")
        hostile = b'<rss><channel><title>Feed</title><item><title>AI agent &lt;script&gt;alert(1)&lt;/script&gt;</title><link>https://example.org/safe</link></item></channel></rss>'
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "feed.xml"
            fixture.write_bytes(hostile)
            report = scan(config, Path(folder) / "history.sqlite", fixture=fixture)
        page = render_html(report)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("AI agent alert(1)", page)


if __name__ == "__main__":
    unittest.main()
