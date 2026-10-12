#!/usr/bin/env python3
"""Generuje HTML report zo snímku repos.json, hodnotenia state/assessment.json a týždenných poznámok
state/weekly_notes.json (sekcie „Čo sa zmenilo“ a „Čo potrebuje tvoje rozhodnutie“).

Spustenie z priečinka tools/:  python3 report.py [RRRR-MM-DD]   (bez argumentu = dnešný dátum)
Výstup: ../reports/Stav_aplikacii_RRRR-MM-DD.html
"""
import json, datetime, html, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()

d = {r["repo"]: r for r in json.load(open(os.path.join(HERE, "repos.json")))}
A = json.load(open(os.path.join(ROOT, "state", "assessment.json")))
N = json.load(open(os.path.join(ROOT, "state", "weekly_notes.json")))

KAT = {
 "AKTIVNY": ("Aktívny vývoj", "#669B41", "commity za posledných 7 dní"),
 "AUTO": ("Beží automaticky", "#1B3665", "naplánované behy, bez ručnej práce"),
 "CAKA_TEBA": ("Hotové, čaká na teba", "#E0A100", "práca je v otvorenom PR, chýba rozhodnutie alebo nasadenie"),
 "NASADENE": ("Hotové / bez aktivity", "#5B6B8A", "zlúčené alebo v prevádzke, viac ako 30 dní bez zmeny"),
 "ZAMRZNUTE": ("Zamrznuté", "#C0392B", "dlhšie bez pohybu a nejasné pokračovanie"),
 "PRAZDNE": ("Prázdne", "#999", "bez obsahu"),
}
order = ["AKTIVNY", "AUTO", "CAKA_TEBA", "ZAMRZNUTE", "NASADENE", "PRAZDNE"]
counts = {k: sum(1 for v in A.values() if v["kat"] == k) for k in order}
total_prs = sum(len(r["open_prs"]) for r in d.values())
draft_prs = sum(1 for r in d.values() for p in r["open_prs"] if p.get("draft"))
c7 = sum(r["commits_7d"] for r in d.values())
c30 = sum(r["commits_30d"] for r in d.values())
week_ago = (today - datetime.timedelta(days=7)).isoformat()
failed_runs = sum(1 for r in d.values() for x in r["recent_runs"]
                  if x["conclusion"] in ("failure", "cancelled", "timed_out") and x["date"] >= week_ago)

def e(s):
    return html.escape(str(s)).replace("–", "-").replace("—", "-")

def card(repo):
    r, a = d[repo], A[repo]
    name, color, _ = KAT[a["kat"]]
    prs = "".join(f'<li>PR #{p["n"]} <em>{e(p["title"])}</em> - {p.get("commits","?")} commitov, {p.get("files","?")} súborov, posledná zmena {p.get("updated","?")}{" (draft)" if p.get("draft") else ""}</li>' for p in r["open_prs"])
    runs = ", ".join(f'{e(x["name"])}: {e(x["conclusion"] or x["status"])} ({x["date"]})' for x in r["recent_runs"][:2]) or "bez CI"
    commits = "".join(f'<li><span class="d">{c["date"]}</span> {e(c["msg"])}</li>' for c in r["last_commits"][:3])
    return f'''
<article class="card" style="border-left-color:{color}">
  <header><h3><a href="{r["url"]}" target="_blank">{e(a["nazov"])}</a> <span class="repo">{e(repo)}</span></h3>
  <span class="badge" style="background:{color}">{e(name)}</span></header>
  <p class="typ">{e(a["typ"])} · oblasť: {e(a["oblast"])}</p>
  <div class="kpi"><span>posledný push <b>{r["pushed"]}</b> ({r["days_since_push"]} d)</span><span>commity 7 / 30 dní <b>{r["commits_7d"]} / {r["commits_30d"]}</b></span><span>otvorené PR <b>{len(r["open_prs"])}</b></span><span>vetvy <b>{len(r["branches"])}</b></span><span>CI: {runs}</span></div>
  <p><b>Stav:</b> {e(a["stav"])}</p>
  <p><b>Na čo sa čaká:</b> {e(a["caka"])}</p>
  <p class="krok"><b>Ďalší krok:</b> {e(a["krok"])}</p>
  {"<ul class='prs'>"+prs+"</ul>" if prs else ""}
  <details><summary>Posledné commity</summary><ul class="commits">{commits}</ul></details>
</article>'''

sections = ""
for k in order:
    items = [repo for repo in A if A[repo]["kat"] == k]
    items.sort(key=lambda x: d[x]["days_since_push"])
    if not items:
        continue
    name, color, desc = KAT[k]
    sections += f'<section><h2 style="color:{color}">{e(name)} <small>{len(items)} · {e(desc)}</small></h2>{"".join(card(x) for x in items)}</section>'

tiles = "".join(f'<div class="tile" style="border-top:4px solid {KAT[k][1]}"><div class="n">{counts[k]}</div><div class="l">{e(KAT[k][0])}</div></div>' for k in order if counts[k])

def clean(s):
    return s.replace("–", "-").replace("—", "-")

zmeny = "".join(f"<li>{clean(x)}</li>" for x in N["zmeny"])
rozhodnutia = "".join(f"<li>{clean(x)}</li>" for x in N["rozhodnutia"])
pr_label = "všetky draft" if draft_prs == total_prs else f"{draft_prs} draft"

page = f'''<!doctype html><html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stav aplikácií - {today.strftime("%d.%m.%Y")}</title>
<style>
:root{{--navy:#1B3665;--green:#669B41;--bg:#f5f6f8;--ink:#1d2433;--muted:#5b6b8a}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}}
header.top{{background:var(--navy);color:#fff;padding:28px 24px;border-bottom:5px solid var(--green)}}
header.top h1{{margin:0;font-size:26px}}header.top p{{margin:6px 0 0;opacity:.85}}
main{{max-width:1100px;margin:0 auto;padding:20px 16px 60px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}}
.tile{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}.tile .n{{font-size:32px;font-weight:700}}.tile .l{{color:var(--muted);font-size:13px}}
.summary{{background:#fff;border-radius:10px;padding:18px 22px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px}}
.summary ol li,.summary ul li{{margin:8px 0}}
.summary.changes{{border-left:6px solid var(--green)}}.summary.decide{{border-left:6px solid #E0A100}}
.note{{color:var(--muted);font-size:13px;margin:0 0 8px}}
h2{{margin:34px 0 12px;font-size:21px}}h2 small{{font-weight:400;color:var(--muted);font-size:14px;margin-left:8px}}
.card{{background:#fff;border-radius:10px;border-left:6px solid;padding:16px 20px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.card header{{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}}
.card h3{{margin:0;font-size:18px}}.card h3 a{{color:var(--navy);text-decoration:none}}.repo{{font-weight:400;color:var(--muted);font-size:13px;margin-left:6px}}
.badge{{color:#fff;font-size:12px;padding:3px 10px;border-radius:999px;white-space:nowrap}}
.typ{{color:var(--muted);margin:4px 0 8px;font-size:14px}}
.kpi{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--muted);margin-bottom:8px}}.kpi b{{color:var(--ink)}}
.card p{{margin:6px 0}}.krok{{color:var(--green);font-weight:500}}.krok b{{color:var(--ink)}}
.prs{{font-size:13px;margin:6px 0;padding-left:18px}}details{{font-size:13px;margin-top:6px}}summary{{cursor:pointer;color:var(--muted)}}
.commits{{padding-left:18px}}.commits .d{{color:var(--muted);font-family:monospace;margin-right:6px}}
footer{{text-align:center;color:var(--muted);font-size:12px;padding:20px}}
@media print{{.card{{break-inside:avoid}}}}
</style></head><body>
<header class="top"><h1>Stav aplikácií postavených cez Claude Code</h1><p>Týždenný prehľad k {today.strftime("%d. %m. %Y")} · {len(d)} repozitárov pod kontom konatel-code · zdroj: GitHub API (commity, vetvy, PR, CI, README) a naplánované úlohy</p></header>
<main>
<div class="tiles">{tiles}<div class="tile" style="border-top:4px solid var(--green)"><div class="n">{c7} / {c30}</div><div class="l">commitov za 7 / 30 dní</div></div><div class="tile" style="border-top:4px solid #E0A100"><div class="n">{total_prs}</div><div class="l">otvorených PR ({pr_label})</div></div><div class="tile" style="border-top:4px solid #C0392B"><div class="n">{failed_runs}</div><div class="l">neúspešných CI behov za 7 dní</div></div></div>
<div class="summary changes"><h2 style="margin-top:0">Čo sa zmenilo od minulého týždňa</h2><p class="note">{e(N.get("porovnanie",""))}</p><ul>{zmeny}</ul></div>
<div class="summary decide"><h2 style="margin-top:0">Čo potrebuje tvoje rozhodnutie tento týždeň</h2><ol>{rozhodnutia}</ol></div>
{sections}
</main>
<footer>Report vygenerovaný automaticky - Claude pre CK DAKA · {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")} UTC · kategórie sú odvodené z aktivity v GitHube, z obsahu commitov a z naplánovaných úloh; pri položkách „z repozitára nevidno“ chýba informácia mimo kódu.</footer>
</body></html>'''
out = os.path.join(ROOT, "reports", f"Stav_aplikacii_{today.isoformat()}.html")
open(out, "w").write(page)
print(out, counts, "c7", c7, "c30", c30, "prs", total_prs, "failed", failed_runs)
