#!/usr/bin/env python3
"""Backfill verified contacts on tracker jobs that have none.

Usage: python3 find_contacts.py <dir of job JSON files from ArtifactData out_dir> <out dir>
Writes <out dir>/<doc_id>.json (fields to merge with an ArtifactData update) and prints a summary.
Only addresses published on the posting itself are used, and only when the domain has a live mail server (MX).
Nothing is guessed: a job with no published, verified address is left as it is.
"""
import concurrent.futures as cf
import functools
import glob
import json
import os
import html
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_jobs as S  # noqa: E402


# Mailboxes that appear on careers pages but are not a hiring contact.
NOT_HIRING = re.compile(r"^(press|media|security|support|legal|ir|investors?|privacy|help|billing|sales|marketing|partners?|"
                        r"compliance|ethics|dpo|gdpr|feedback|benefits|payroll|verify|verification|fraud|disability|ada)@", re.I)


APPLY = re.compile(r"\b(send|email|e-mail|submit|forward)\b[^.]{0,80}\b(resume|cv|application|portfolio|profile)|\bto apply\b|\bapply (by|via) email\b|"
                   r"\binterested\b[^.]{0,80}\b(email|reach|contact)|\b(reach out|contact) (me|us|our recruit\w*|the hiring)", re.I)
BOILER = re.compile(r"accommodat|disabilit|assistive|imperson|scam|fraud|phish|legitimate|opt.?out|technical support|"
                    r"use of ai|privacy|equal opportunit|claiming to be", re.I)


@functools.lru_cache(maxsize=None)
def _ashby(slug):
    return S.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}") or {}


def posting_text(i, j):
    """The posting's own description, from the job board's public API. Never LinkedIn (no scraping)."""
    url = j.get("url") or ""
    try:
        if i.startswith("gh-"):
            slug, jid = re.match(r"gh-(.+)-(\d+)$", i).groups()
            d = S.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}") or {}
            return html.unescape(d.get("content") or "")
        if i.startswith("ab-"):
            m = re.match(r"ab-(.+?)-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", i)
            if not m:
                return ""
            d = _ashby(m.group(1))
            for x in d.get("jobs", []):
                if x.get("id") == m.group(2):
                    return (x.get("descriptionHtml") or "") + " " + (x.get("descriptionPlain") or "")
            return ""
        if i.startswith("lv-"):
            m = re.search(r"jobs\.lever\.co/([^/]+)/([0-9a-f-]{36})", url)
            return json.dumps(S.get(f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}") or {}) if m else ""
        if i.startswith("wd-"):
            m = re.match(r"(https://([^.]+)\.[^/]+)/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)(/job/.+)$", url)
            if not m:
                return ""
            base, ten, site, path = m.groups()
            d = (S.get(f"{base}/wday/cxs/{ten}/{site}{path}") or {}).get("jobPostingInfo", {})
            return html.unescape(d.get("jobDescription") or "")
        if i.startswith("li-") or "linkedin.com" in url or not url:
            return ""
        return html.unescape(S.get_html(url) or "")
    except Exception:
        return ""


def one(path):
    i = os.path.basename(path)[:-5]
    j = json.load(open(path))
    if j.get("closed") or j.get("status", "new") not in ("new", "messaged", "applied", "interviewing"):
        return i, None
    i, c = _one(i, j)
    if not c:
        return i, None
    if j.get("contactEmail"):
        # keep the contact already chosen; only add the other published addresses as extra buttons
        have = {(x.get("email") or "").lower() for x in j.get("contacts") or []} | {j["contactEmail"].lower()}
        extra = [x for x in c.get("contacts") or [] if x["email"].lower() not in have]
        if not extra:
            return i, None
        first = {"email": j["contactEmail"], "name": j.get("contactName") or "", "title": j.get("contactTitle") or "",
                 "kind": j.get("contactKind") or "recruiter", "source": j.get("contactSource") or "", "url": j.get("contactProfile") or ""}
        return i, {"contacts": ([first] + [x for x in j.get("contacts") or [] if x.get("email", "").lower() != first["email"].lower()] + extra)[:3]}
    return i, c


def _one(i, j):
    if i.startswith("dice-") and j.get("url"):
        page = S.get_html(j["url"])
        if not page:
            return i, None  # fetch failed: try again next run, do not mark
        c = S.dice_contact(page)
        if not c or (c.get("contactName") == j.get("contactName") and not c.get("contactEmail")):
            return i, None
        return i, c
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", posting_text(i, j)))
    emails = []
    for m in S.EMAIL_RX.finditer(txt):
        e, before = m.group(0), txt[max(0, m.start() - 220):m.start()]
        # only an address the posting gives for applying or reaching the hiring team, never boilerplate
        # (accommodation, scam warnings, technical support, AI opt-out) or a page-script placeholder
        if NOT_HIRING.search(e) or re.search(r"disabilit|accommodat|accessib|privacy|fraud", e.split("@")[0], re.I) or BOILER.search(before[-160:]) or not APPLY.search(before):
            continue
        emails.append(e)
    if not emails:
        return i, None
    c = S.verified_contact(emails, "", "", "", j.get("companyName") or j.get("company") or "", "the posting")
    return i, (c if c and c.get("contactEmail") else None)


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    found = none = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for i, c in ex.map(one, glob.glob(os.path.join(src, "*.json"))):
            if c is None:
                continue
            json.dump(c, open(os.path.join(out, i + ".json"), "w"))
            if "contactEmail" in c:
                found += 1
            else:
                none += 1
    print(f"{found} jobs got a verified email; {none} more got extra published addresses or a named recruiter")


if __name__ == "__main__":
    main()
