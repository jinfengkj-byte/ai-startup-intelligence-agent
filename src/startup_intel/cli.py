"""Open Startup Radar command line interface."""

from __future__ import annotations

import argparse
import http.server
import json
import sys
from functools import partial
from pathlib import Path

from .analysis import analyze
from .dashboard import write_views
from .radar import load_config, scan, write_json

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="startup-radar", description="Follow startup signals with source links and a persistent watchlist")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "demo"):
        command = commands.add_parser(name, help="Research public feeds" if name == "scan" else "Run the offline synthetic demo")
        command.add_argument("--output", type=Path, default=Path("output"))
        command.add_argument("--db", type=Path, help="SQLite history path (defaults inside output)")
        command.add_argument("--ai", action="store_true", help="Opt in to OpenAI analysis; requires OPENAI_API_KEY and incurs API cost")
        command.add_argument("--model", default="gpt-4o-mini", help="OpenAI model for --ai")
        if name == "scan":
            command.add_argument("--config", type=Path, default=Path("config.example.json"))
            command.add_argument("--topic", help="Override the topic in the config")
    serve = commands.add_parser("serve", help="Show a generated report on localhost")
    serve.add_argument("--output", type=Path, default=Path("output"))
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.command == "serve":
        if not (args.output / "index.html").is_file():
            parser.error(f"No report in {args.output}; run scan or demo first")
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(args.output.resolve()))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"Open http://127.0.0.1:{args.port}/")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0

    try:
        if args.command == "demo":
            config = load_config(ROOT / "examples" / "demo-config.json")
            fixture = ROOT / "examples" / "demo-feed.xml"
        else:
            config = load_config(args.config)
            fixture = None
            if args.topic:
                config["topic"] = args.topic
        report = scan(config, args.db or args.output / "history.sqlite", fixture=fixture)
        if args.ai:
            report["analysis"] = analyze(report, args.model)
        write_json(report, args.output)
        write_views(report, args.output)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"startup-radar: {error}", file=sys.stderr)
        return 1
    print(f"{len(report['signals'])} signals; {report['new_count']} new. Open {args.output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
