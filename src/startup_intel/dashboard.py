"""Portable, self-contained report views."""

from __future__ import annotations

import html
from pathlib import Path


def render_markdown(report: dict) -> str:
    lines = [
        "# Open Startup Radar", "", f"**Topic:** {report['topic']}",
        f"**Generated:** {report['generated_at']}",
        f"**New signals:** {report['new_count']} / {len(report['signals'])}", "",
        report["method"], "",
    ]
    if report.get("demo"):
        lines += ["**DEMO DATA: all companies and events below are fictional.**", ""]
    if report.get("analysis"):
        analysis = report["analysis"]
        lines += ["## Analyst brief", "", analysis["brief"], ""]
        for insight in analysis["insights"]:
            lines += [f"- **{insight['claim']}** — [source]({insight['url']})", ""]
    lines += ["## New signals", ""]
    new = [signal for signal in report["signals"] if signal["is_new"]]
    if not new:
        lines += ["No new source links in this scan.", ""]
    for signal in new:
        title = signal["title"].replace("[", "\\[").replace("]", "\\]")
        lines += [f"### [{title}]({signal['url']})", "", f"{signal['company'] or 'Unassigned'} · {signal['category']} · {signal['source']}", "", signal["summary"] or "No feed summary.", ""]
    lines += ["## Watchlist", ""]
    for company in report["companies"]:
        lines += [f"### {company['name']}", ""]
        if company["signals"]:
            lines += [f"- [{event['title']}]({event['url']}) — first seen {event['first_seen']}" for event in company["signals"]]
        else:
            lines += ["- No matching source links yet."]
        lines += [""]
    if report["feed_errors"]:
        lines += ["## Feed errors", "", *[f"- {error}" for error in report["feed_errors"]], ""]
    lines += ["## Evidence policy", "", "A feed entry is a lead. Open the cited source before relying on a claim. Funding, valuation, and identity details are never inferred from keywords.", ""]
    return "\n".join(lines)


def render_html(report: dict) -> str:
    esc = lambda value: html.escape(str(value or ""), quote=True)
    signal_cards = []
    for signal in report["signals"]:
        category = esc(signal["category"])
        company = esc(signal["company"] or "Unassigned")
        status = '<span class="new">NEW</span>' if signal["is_new"] else '<span class="seen">SEEN</span>'
        signal_cards.append(
            f'<article class="card" data-category="{category}" data-search="{esc((signal["title"] + " " + (signal["company"] or "") + " " + signal["summary"]).lower())}">'
            f'<div class="meta"><span>{category}</span>{status}<span>{company}</span></div>'
            f'<h3><a href="{esc(signal["url"])}" target="_blank" rel="noopener noreferrer">{esc(signal["title"])}</a></h3>'
            f'<p>{esc(signal["summary"] or "No feed summary available.")}</p>'
            f'<footer>{esc(signal["source"])} · {esc(signal["published"] or "date not provided")}</footer></article>'
        )
    company_cards = []
    for company in report["companies"]:
        events = "".join(
            f'<li><a href="{esc(event["url"])}" target="_blank" rel="noopener noreferrer">{esc(event["title"])}</a><small>{esc(event["first_seen"][:10])}</small></li>'
            for event in company["signals"]
        ) or "<li>No matching signals yet.</li>"
        company_cards.append(f'<section class="company"><h3>{esc(company["name"])}</h3><ul>{events}</ul></section>')
    analysis = report.get("analysis")
    ai_section = ""
    if analysis:
        insights = "".join(f'<li>{esc(row["claim"])} <a href="{esc(row["url"])}" target="_blank" rel="noopener noreferrer">Evidence ↗</a></li>' for row in analysis["insights"])
        ai_section = f'<section class="panel"><span class="eyebrow">OPTIONAL AI ANALYSIS</span><h2>Analyst brief</h2><p>{esc(analysis["brief"])}</p><ul>{insights}</ul></section>'
    cards = "".join(signal_cards) or '<p class="empty">No matching signals. Try a broader topic or additional feeds.</p>'
    watchlist = "".join(company_cards) or '<p class="empty">Add companies to the config to build a watchlist.</p>'
    errors = '<p class="warning">Some feeds failed. Check report.json for details.</p>' if report["feed_errors"] else ""
    demo = '<div class="demo-banner">DEMO DATA · All companies and events on this page are fictional.</div>' if report.get("demo") else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>Open Startup Radar · {esc(report['topic'])}</title><style>
:root{{--bg:#0b1120;--panel:#121d30;--panel2:#17243a;--line:#2b3a52;--text:#edf4ff;--muted:#9cb0cc;--accent:#70e0bf;--orange:#ffc47d}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 80% 0,#173b49 0,transparent 32%),var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}a{{color:inherit}}.wrap{{max-width:1160px;margin:auto;padding:32px 22px 80px}}.brand{{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding-bottom:16px}}.logo{{font-weight:800;letter-spacing:.02em}}.logo b{{color:var(--accent)}}.brand small,.muted{{color:var(--muted)}}.hero{{padding:62px 0 38px}}.eyebrow{{color:var(--accent);font-size:12px;font-weight:800;letter-spacing:.18em}}h1{{font-size:clamp(36px,6vw,70px);line-height:1.05;letter-spacing:-.05em;margin:14px 0}}h2{{font-size:25px;margin:0 0 15px}}h3{{font-size:18px;line-height:1.3;margin:12px 0}}p{{color:var(--muted)}}.hero p{{max-width:720px;font-size:18px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:25px 0 38px}}.stat,.panel,.card,.company{{background:var(--panel);border:1px solid var(--line);border-radius:17px}}.stat{{padding:20px}}.stat strong{{display:block;font-size:30px;color:var(--accent)}}.stat span{{color:var(--muted);font-size:13px}}.panel{{padding:24px;margin-bottom:28px}}.panel li{{margin:8px 0}}.panel li a{{color:var(--accent)}}.tools{{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 20px}}input,select{{background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit}}input{{min-width:260px;flex:1}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.card{{padding:22px;min-width:0}}.card h3 a{{text-decoration:none}}.card h3 a:hover,.company a:hover{{color:var(--accent)}}.card p{{font-size:14px;max-height:88px;overflow:hidden}}.meta{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}}.new,.seen{{border-radius:20px;padding:3px 8px}}.new{{background:#124836;color:var(--accent)}}.seen{{background:#2a3446;color:var(--muted)}}footer{{border-top:1px solid var(--line);padding-top:12px;color:var(--muted);font-size:12px}}.section{{margin:48px 0 18px}}.company{{padding:18px;margin:12px 0}}.company ul{{list-style:none;padding:0;margin:0}}.company li{{display:flex;justify-content:space-between;gap:18px;padding:7px 0;border-top:1px solid var(--line);font-size:14px}}.company small{{white-space:nowrap;color:var(--muted)}}.warning{{color:var(--orange)}}.empty{{padding:25px;background:var(--panel);border-radius:12px}}@media(max-width:700px){{.stats,.grid{{grid-template-columns:1fr}}.hero{{padding-top:40px}}.brand small{{display:none}}}}
.demo-banner{{margin-top:22px;background:#43301c;color:var(--orange);border:1px solid #74502b;border-radius:10px;padding:10px 14px;font-size:13px}}
</style></head><body><main class="wrap"><header class="brand"><div class="logo">◉ OPEN STARTUP <b>RADAR</b></div><small>Evidence-linked intelligence · Local-first</small></header>
{demo}<section class="hero"><span class="eyebrow">STARTUP SIGNAL BRIEF</span><h1>Know what changed.<br>Follow the evidence.</h1><p>Tracking <strong>{esc(report['topic'])}</strong>. Public source links, a persistent watchlist, and clear new-versus-seen signals.</p></section>
<div class="stats"><div class="stat"><strong>{len(report['signals'])}</strong><span>matching signals</span></div><div class="stat"><strong>{report['new_count']}</strong><span>new this scan</span></div><div class="stat"><strong>{len(report['companies'])}</strong><span>watched companies</span></div></div>
{ai_section}<div class="section"><span class="eyebrow">SOURCE-LED DISCOVERY</span><h2>Signals</h2><p class="muted">{esc(report['generated_at'])} · {report['sources_checked']} feeds checked</p>{errors}</div>
<div class="tools"><input id="search" aria-label="Search signals" placeholder="Search signals or companies"><select id="category" aria-label="Filter category"><option value="">All categories</option><option value="funding">Funding</option><option value="product">Product</option><option value="open-source">Open source</option><option value="other">Other</option></select></div><div id="signals" class="grid">{cards}</div>
<div class="section"><span class="eyebrow">CONTINUOUS TRACKING</span><h2>Watchlist</h2></div>{watchlist}
<div class="section"><span class="eyebrow">METHOD</span><h2>What this report proves</h2><p>{esc(report['method'])} Feed entries are leads; open the original article before relying on a claim. Funding and valuations are never inferred from keywords.</p></div>
</main><script>const q=document.getElementById('search'),c=document.getElementById('category');function filter(){{for(const e of document.querySelectorAll('.card'))e.hidden=!(e.dataset.search.includes(q.value.toLowerCase())&&(!c.value||e.dataset.category===c.value))}}q.addEventListener('input',filter);c.addEventListener('change',filter);</script></body></html>'''


def write_views(report: dict, output: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    md = output / "report.md"
    page = output / "index.html"
    md.write_text(render_markdown(report), encoding="utf-8")
    page.write_text(render_html(report), encoding="utf-8")
    return md, page
