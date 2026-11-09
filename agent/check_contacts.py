#!/usr/bin/env python3
"""Check addresses found on public pages or in Gmail before they go on a role. Nothing here builds or guesses an address.

Usage: python3 check_contacts.py <dir of job JSON files> <found.json> <out dir>
  found.json: [{"id": "<job doc id>", "email": "...", "name": "...", "title": "...", "source": "<where it is written>", "url": "<page>"}]
Keeps an address only if it is well formed, not a no-reply/boilerplate inbox, its domain has a working mail server,
and the page it came from is given. Writes <out dir>/<doc_id>.json = {"contacts": [...]} (existing contacts first, max 3).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_jobs as S  # noqa: E402

NOT_HIRING = re.compile(r"^(press|media|security|support|legal|ir|investors?|privacy|help|billing|sales|marketing|partners?|compliance|"
                        r"ethics|dpo|gdpr|feedback|benefits|payroll|verify|verification|fraud|abuse|noreply|no-reply|donotreply|info|contact|hello)@"
                        r"|disabilit|accommodat|accessib", re.I)


def main():
    src, found_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    found = json.load(open(found_path))
    by_id = {}
    for f in found:
        by_id.setdefault(f.get("id"), []).append(f)
    kept = dropped = 0
    for i, items in by_id.items():
        p = os.path.join(src, f"{i}.json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p))
        cur = list(j.get("contacts") or [])
        if j.get("contactEmail") and not any((c.get("email") or "").lower() == j["contactEmail"].lower() for c in cur):
            cur.insert(0, {"email": j["contactEmail"], "name": j.get("contactName") or "", "title": j.get("contactTitle") or "",
                           "kind": j.get("contactKind") or "recruiter", "source": j.get("contactSource") or "", "url": j.get("contactProfile") or ""})
        have = {(c.get("email") or "").lower() for c in cur}
        for f in items:
            e = (f.get("email") or "").strip().strip(".,;:<>()[]").replace("mailto:", "")
            ok = (S.EMAIL_RX.fullmatch(e) and not S.EMAIL_BAD.search(e) and not NOT_HIRING.search(e) and len(e) <= 80
                  and f.get("url") and e.lower() not in have and S.mx_ok(e.split("@")[1]))
            if not ok:
                dropped += 1
                continue
            have.add(e.lower())
            kept += 1
            cur.append({"email": e, "name": (f.get("name") or "").strip(), "title": (f.get("title") or "").strip(),
                        "kind": "apply inbox" if S.ROUTING.search(e) else "recruiter", "source": f.get("source") or "public page",
                        "url": f.get("url")})
        if cur[:3] != (j.get("contacts") or [])[:3]:
            json.dump({"contacts": cur[:3]}, open(os.path.join(out, f"{i}.json"), "w"))
    print(f"kept {kept} addresses, dropped {dropped}")


if __name__ == "__main__":
    main()
