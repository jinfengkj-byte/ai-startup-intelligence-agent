# Architecture and trust boundaries

```text
Config → RSS/Atom fetch → XML parser → topic filter → URL dedupe
      → company matcher → SQLite history → JSON / Markdown / local HTML
                                      ↘ optional source-constrained AI brief
```

`core.py` reads limited-size public feed payloads, rejects DTD/entity declarations, canonicalizes HTTP(S) links while retaining meaningful query parameters, and extracts only short feed summaries. `radar.py` validates configuration, matches configured company names and aliases against titles and summaries, and stores a fingerprint of each source URL in SQLite. A repeat run updates `last_seen` and does not count the same link as new. `dashboard.py` escapes feed content into self-contained HTML and Markdown. `analysis.py` is invoked only with `--ai`; it sends up to 20 evidence items to the OpenAI Responses API and rejects cited URLs absent from the input evidence.

The local server binds to `127.0.0.1`. API keys come only from the process environment and are never written to reports. Generated reports, SQLite files, and `.env` are ignored by Git. GitHub Actions uses public feeds and uploads a report artifact; it does not publish user data.

## Limits of the evidence

- A feed item is a lead, not verification of the underlying claim.
- Keyword matching is intentionally explainable but cannot reliably resolve every company or event.
- Distinct URLs describing the same event may appear separately. A later release may cluster them with an auditable rule.
- The optional AI brief checks that citations are in the supplied set. It cannot prove that a cited source actually supports every sentence.
- Source licenses, rate limits, and publication quality remain the source publisher's responsibility.

## Extending the product

Add a source adapter that returns `Item` records with canonical HTTP(S) URLs, source names, and publication strings. Add evidence and attribution tests before adding new derived fields. Keep private delivery integrations and personal paths outside the public package.
