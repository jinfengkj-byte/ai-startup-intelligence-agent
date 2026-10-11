# AI Startup Intelligence Agent

Turn a research topic and public RSS/Atom feeds into a source-linked startup intelligence brief. The first release fetches feed entries, filters by topic, deduplicates links, groups signals into funding, product, open source, and other, and writes Markdown plus JSON. It uses transparent keyword heuristics; no model API key is required.

This open source edition adapts the **research categories and report workflow** of the author's AI 创业雷达 project. The private daily PDF delivery pipeline, personal configuration, and historical reports are intentionally outside this repository.

## Quickstart

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
startup-intel --topic "AI agent" --fixture examples/demo-feed.xml --output output
```

Open `output/report.md`. The bundled fixture is synthetic and works offline.

For live research:

```bash
startup-intel --topic "AI startup" --config config.example.json --output output
```

Edit `config.example.json` or make your own JSON config with a `feeds` array. Every feed needs `name` and `url`. Feed availability and licensing are controlled by their publishers.

## What the report means

- Every item links to the original source. The source name and feed publication string are kept when supplied.
- Relevance is a simple keyword count. Categories are keyword rules. Neither is an investment recommendation or an independently verified fact.
- Missing items may result from publisher feed coverage, feed errors, or the topic filter. Partial feed failures are printed to stderr and recorded in `report.json`.
- The tool does not infer founders, funding amounts, valuations, or trend scores without source evidence.

## GitHub Actions

CI tests the local fixture on every push and pull request. Run **Research report** manually from Actions, enter a topic, and download the generated report artifact. The workflow uses public feeds and does not commit reports to the repository.

## Project layout

```text
src/startup_intel/   Feed parsing, ranking, report generation, CLI
examples/            Offline synthetic demo feed
tests/               Pipeline behavior test
docs/                Architecture and contribution notes
.github/workflows/   CI and manual research run
```

## Roadmap

- Add optional source verification and entity extraction with a user supplied model provider.
- Add company profiles and time series with clear source provenance.
- Add export adapters, including a portable PDF design.

These are planned features, not part of the current release.

## License

MIT. See [LICENSE](LICENSE).
