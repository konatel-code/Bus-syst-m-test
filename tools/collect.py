#!/usr/bin/env python3
"""Zber stavu repozitárov konatel-code cez GitHub API (gh api)."""
import json, subprocess, sys, base64, datetime, re

REPOS = """Medved Intime GhostDash CK-DAKA-app Mimicchain Textovka ckdaka-recommender Koleso-astia DJ-IMI
Web-aplik-cia Kviz Uctovnik Kontrola-fakt-r TV-v-autobusoch Bus-syst-m Kalinkovo-v-mobile Kalinkovo Efaktura
Bus-aukcia Tipy MCP-CK-DAKA Futbal Bazar Plaud baDAKAtel Task-app ckdaka-app banner-generator vyplaty QR-code
EOS Mobil Hry-CK-DAKA Ck-daka Bus-syst-m-test
porovnajceny.sk DAKAsoft Hostovnik AlergenMenu TurnusPlan Klubovna Voxpla CK-DAKA-FEED""".split()
OWNER = "konatel-code"
NOW = datetime.datetime.now(datetime.timezone.utc)

def api(path, ok404=True):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

def days_ago(iso):
    if not iso: return None
    d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (NOW - d).days

def file_text(repo, path, maxlen=4000):
    d = api(f"repos/{OWNER}/{repo}/contents/{path}")
    if not d or "content" not in d: return None
    try:
        t = base64.b64decode(d["content"]).decode("utf-8", "replace")
    except Exception:
        return None
    return t[:maxlen]

out = []
for repo in REPOS:
    print("..", repo, file=sys.stderr)
    meta = api(f"repos/{OWNER}/{repo}") or {}
    branch = meta.get("default_branch", "main")
    commits = api(f"repos/{OWNER}/{repo}/commits?per_page=100&sha={branch}") or []
    c7 = sum(1 for c in commits if days_ago(c["commit"]["author"]["date"]) is not None and days_ago(c["commit"]["author"]["date"]) < 7)
    c30 = sum(1 for c in commits if days_ago(c["commit"]["author"]["date"]) is not None and days_ago(c["commit"]["author"]["date"]) < 30)
    last_msgs = [{"date": c["commit"]["author"]["date"][:10], "msg": c["commit"]["message"].split("\n")[0][:140],
                  "author": c["commit"]["author"]["name"]} for c in commits[:8]]
    # bot vs human
    bot_like = sum(1 for c in commits[:30] if re.search(r"(automat|denn[áa] aktualiz|daily|bot|\[skip ci\])", c["commit"]["message"], re.I))
    issues = api(f"repos/{OWNER}/{repo}/issues?state=open&per_page=50") or []
    prs = [i for i in issues if "pull_request" in i]
    issues = [i for i in issues if "pull_request" not in i]
    branches = api(f"repos/{OWNER}/{repo}/branches?per_page=100") or []
    runs = api(f"repos/{OWNER}/{repo}/actions/runs?per_page=5") or {}
    wf = []
    for r in (runs.get("workflow_runs") or [])[:5]:
        wf.append({"name": r.get("name"), "status": r.get("status"), "conclusion": r.get("conclusion"),
                   "date": (r.get("updated_at") or "")[:10], "event": r.get("event")})
    workflows = api(f"repos/{OWNER}/{repo}/actions/workflows") or {}
    wf_names = [w.get("name") for w in (workflows.get("workflows") or [])]
    pages = None
    if meta.get("has_pages"):
        p = api(f"repos/{OWNER}/{repo}/pages")
        if p: pages = p.get("html_url")
    tree = api(f"repos/{OWNER}/{repo}/git/trees/{branch}?recursive=1") or {}
    paths = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"]
    root_files = [p for p in paths if "/" not in p]
    readme = file_text(repo, "README.md")
    todo = None
    for cand in ["TODO.md", "ROADMAP.md", "STATUS.md", "RUNBOOK.md", "CLAUDE.md", "NOTES.md", "docs/TODO.md"]:
        if cand in paths:
            todo = {"file": cand, "text": file_text(repo, cand, 3000)}
            break
    langs = api(f"repos/{OWNER}/{repo}/languages") or {}
    out.append({
        "repo": repo, "url": meta.get("html_url"), "description": meta.get("description"), "private": meta.get("private"),
        "created": (meta.get("created_at") or "")[:10], "pushed": (meta.get("pushed_at") or "")[:10],
        "days_since_push": days_ago(meta.get("pushed_at")), "default_branch": branch,
        "commits_total_sampled": len(commits), "commits_7d": c7, "commits_30d": c30, "bot_like_recent": bot_like,
        "last_commits": last_msgs, "open_issues": [{"n": i["number"], "title": i["title"]} for i in issues],
        "open_prs": [{"n": i["number"], "title": i["title"]} for i in prs],
        "branches": [b["name"] for b in branches], "workflows": wf_names, "recent_runs": wf, "pages": pages,
        "homepage": meta.get("homepage"), "files_count": len(paths), "root_files": root_files[:40],
        "languages": list(langs.keys())[:4], "readme": readme, "todo": todo,
    })

json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print("done", len(out), file=sys.stderr)
