#!/usr/bin/env python3
"""Turn web-search results for public LinkedIn posts into dated, de-duplicated 'hiring post' candidates.

LinkedIn has no public API for searching posts, and its terms forbid scraping, so the scan never logs in to
LinkedIn or fetches linkedin.com pages. It only reads ordinary web-search results (title, url, snippet) that
point at public linkedin.com/posts/... pages, and this script dates each one from its activity id.

Usage: python3 linkedin_posts.py results.json [--days 14] [--existing ids.txt] > candidates.json
results.json: a JSON list of {"title", "url", "snippet"} collected from WebSearch.
Output: {"posts": [...], "people": [...]}.
  posts: public posts with id, url, postedAt (from the activity id), poster (from the title or URL), text.
  people: public profile results (linkedin.com/in/...) with name, headline (the text after the name in the
  result title, usually the company or job title) and url. These come from the search engine's title only;
  the run attaches them to roles at the matching company as "people to try", never as a verified contact.
The run then decides which posts are real US hiring posts for target roles, and writes a short DM draft for each.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone

PROFILE_RX = re.compile(r"https?://(?:[a-z]{2,3}\.)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9\-_%]+)/?$")
POST_RX = re.compile(r"https?://(?:[a-z]{2,3}\.)?(?:www\.)?linkedin\.com/posts/([A-Za-z0-9\-_%]+?)_[^/]*?activity-(\d{19})")
HIRING_RX = re.compile(r"hiring|we're looking|we are looking|join (my|our) team|open role|open position|looking for (an?|engineers?)|"
                       r"#hiring|now hiring|i'm hiring|im hiring|recruiting for", re.I)


def posted_at(activity_id):
    return datetime.fromtimestamp((int(activity_id) >> 22) / 1000, timezone.utc)


def poster_from(slug, title):
    m = re.match(r"\s*([^:|]+?) (?:on LinkedIn|posted on LinkedIn)", title or "")
    if m:
        return m.group(1).strip()
    words = [w for w in re.split(r"[-_]", slug) if w.isalpha()]
    return " ".join(w.title() for w in words[:2]) if len(words) >= 2 else ""


def main():
    a = sys.argv[1:]
    days = float(a[a.index("--days") + 1]) if "--days" in a else 14
    existing = set(open(a[a.index("--existing") + 1]).read().split()) if "--existing" in a else set()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    out, seen, people = [], set(), {}
    for r in json.load(open(a[0])):
        pm = PROFILE_RX.match((r.get("url") or "").split("?")[0])
        if pm:
            t = re.sub(r"\s*\|\s*LinkedIn\s*$", "", r.get("title") or "")
            if " - " in t:
                name, head = t.split(" - ", 1)
                name = name.strip()
                if 2 <= len(name.split()) <= 4 and re.fullmatch(r"[A-Za-z .,'-]+", name) and not re.search(r"jobs|hiring|linkedin", name, re.I):
                    people.setdefault(pm.group(1), {"name": re.sub(r",.*$", "", name).strip(), "headline": head.strip()[:120],
                                                    "url": "https://www.linkedin.com/in/" + pm.group(1)})
            continue
        m = POST_RX.search(r.get("url", ""))
        if not m:
            continue
        aid = m.group(2)
        pid = "lip-" + aid
        if pid in seen or pid in existing:
            continue
        seen.add(pid)
        when = posted_at(aid)
        text = (r.get("title", "") + " " + r.get("snippet", "")).strip()
        if when < since or when > datetime.now(timezone.utc) + timedelta(days=1):
            continue
        if not HIRING_RX.search(text):
            continue
        out.append({"id": pid, "url": r["url"].split("?")[0], "postedAt": when.date().isoformat(),
                    "poster": poster_from(m.group(1), r.get("title", "")), "text": text[:600]})
    json.dump({"posts": sorted(out, key=lambda x: x["postedAt"], reverse=True), "people": list(people.values())}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
