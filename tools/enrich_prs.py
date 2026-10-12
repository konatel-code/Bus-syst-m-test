#!/usr/bin/env python3
"""Doplní k otvoreným PR detaily (head, posledná zmena, commity, súbory, draft, mergeable) cez gh api."""
import json, subprocess, sys

OWNER = "konatel-code"

def api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

path = sys.argv[1]
data = json.load(open(path))
for r in data:
    for p in r["open_prs"]:
        d = api(f"repos/{OWNER}/{r['repo']}/pulls/{p['n']}") or {}
        p.update({
            "head": (d.get("head") or {}).get("ref"),
            "updated": (d.get("updated_at") or "")[:10],
            "commits": d.get("commits"), "files": d.get("changed_files"),
            "additions": d.get("additions"), "draft": d.get("draft"),
            "mergeable": d.get("mergeable_state"),
        })
    print("..", r["repo"], len(r["open_prs"]), file=sys.stderr)
json.dump(data, open(path, "w"), ensure_ascii=False, indent=1)
