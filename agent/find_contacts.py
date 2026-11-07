#!/usr/bin/env python3
"""Backfill verified contacts on tracker jobs that have none.

Usage: python3 find_contacts.py <dir of job JSON files from ArtifactData out_dir> <out dir>
Writes <out dir>/<doc_id>.json (fields to merge with an ArtifactData update) and prints a summary.
Only addresses published on the posting itself are used, and only when the domain has a live mail server (MX).
Nothing is guessed: a job with no published, verified address is left as it is.
"""
import concurrent.futures as cf
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_jobs as S  # noqa: E402


def one(path):
    i = os.path.basename(path)[:-5]
    j = json.load(open(path))
    if j.get("status", "new") != "new" or j.get("contactEmail"):
        return i, None
    if i.startswith("dice-") and j.get("url"):
        page = S.get_html(j["url"])
        if not page:
            return i, None  # fetch failed: try again next run, do not mark
        c = S.dice_contact(page)
        if not c or (c.get("contactName") == j.get("contactName") and not c.get("contactEmail")):
            return i, None
        return i, c
    return i, None


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
    print(f"{found} jobs got a verified email; {none} more got the named recruiter (no email listed)")


if __name__ == "__main__":
    main()
