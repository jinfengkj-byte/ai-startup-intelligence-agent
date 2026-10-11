# Architecture

`startup-intel` reads RSS/Atom URLs from a local JSON config, downloads at most 2 MB per feed with a timeout, parses entries, and requires all topic keywords to occur in each title or summary. It canonicalizes HTTP links by removing query strings and fragments, deduplicates by canonical URL, and orders by relevance score. It writes `report.json` and `report.md` to the selected output directory.

No credentials, email delivery, desktop path, or background scheduler are used. The workflow action only uploads an artifact for the person who ran it. The demo fixture contains synthetic entries. This keeps the public project independent from the owner's private Windows report pipeline.

The first release is an evidence collection tool. It does not verify the truth of feed claims or synthesize unsupported company details.
