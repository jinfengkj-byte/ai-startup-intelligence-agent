import json
import os
import unittest
from unittest.mock import patch

from startup_intel.analysis import analyze


class MockResponse:
    def __init__(self, result):
        self.result = result

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return json.dumps(self.result).encode()


class AnalysisTests(unittest.TestCase):
    def test_rejects_citation_not_in_collected_sources(self):
        report = {"topic": "AI agent", "signals": [{"title": "Demo", "url": "https://example.org/source", "source": "Demo", "summary": "Demo", "company": None}]}
        text = json.dumps({"brief": "Brief", "insights": [{"claim": "Claim", "url": "https://wrong.example/claim"}]})
        result = {"output": [{"content": [{"type": "output_text", "text": text}]}]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("urllib.request.urlopen", return_value=MockResponse(result)):
            with self.assertRaisesRegex(ValueError, "outside the collected evidence"):
                analyze(report)


if __name__ == "__main__":
    unittest.main()
