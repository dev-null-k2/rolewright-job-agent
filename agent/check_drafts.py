#!/usr/bin/env python3
"""Hard checks for outreach drafts, tailored resumes, cover letters and contacts.
Same rules as the Rolewright page, which refuses to offer anything that fails.
Reads profile.json (name, portfolio link, words never to mention) and RESUME_MASTER.md from this folder.

Usage: python3 check_drafts.py <dir of job JSON files from ArtifactData out_dir> [--json report.json]
Each file is one job doc (the file name is the doc id). Prints failures and exits 1 if any draft fails.
"""
import glob
import json
import os
import re
import sys

BANNED = [r"I applied for", r"reaching out", r"quick note", r"\bI saw\b", r"caught my eye", r"I'd love", r"\bexcited\b",
          r"passionate", r"happy to", r"leverage", r"\balign", r"still open", r"Hi there", r"model gateway", r"flow card",
          r"\bcritic\b", r"recall@", r"sub-agent", r"direct fit", r"matches what I do every day", r"I hope", r"synergy",
          r"\bkindly\b", r"\bdear\b", r"to whom", r"\bvisa\b", r"sponsor", r"\bH-?1B\b", r"\bCPT\b", r"\bOPT\b", r"relocat", r"without a move", r"\bcommute", r"I'm (in|based)", r"based in", r"Dallas-based"]
HERE = os.path.dirname(os.path.abspath(__file__))
try:
    PROFILE = json.load(open(os.path.join(HERE, "profile.json")))
except Exception:
    PROFILE = {}
NAME = PROFILE.get("name") or "Your Name"
PORTFOLIO = (PROFILE.get("portfolioLink") or "").strip()
# Words that must never appear in outreach (for example the city or state you live in).
BANNED += [r"\b" + re.escape(w) + r"\b" for w in PROFILE.get("neverMention", []) if w.strip()]
BANNED_RX = re.compile("|".join(BANNED), re.I)
# Every number in a draft must come from the master resume (or the company name / title), or be a small count or a year.
MASTER_NUMS = set()


def allowed_number(token):
    for g in re.findall(r"\d[\d,]*(?:\.\d+)?", token):
        g = g.replace(",", "")
        if g in MASTER_NUMS or (g.isdigit() and (int(g) <= 10 or 1990 <= int(g) <= 2100)):
            continue
        return False
    return True
STAFFING_ATS = {"dice", "phenom"}


def first_sentence(d):
    return re.split(r"(?<=[.?!])\s+", d.strip(), maxsplit=1)[0]


def check(doc):
    """Return a list of problems with doc['draft'] (empty list = OK to send)."""
    d = (doc.get("draft") or "").strip()
    if doc.get("sameAs") or doc.get("status", "new") != "new":
        return []
    if not d:
        return ["no draft"]
    p = []
    title = doc.get("title", "")
    co = (doc.get("companyName") or "").strip()
    staffing = doc.get("ats") in STAFFING_ATS
    fulltime_direct = staffing and re.search(r"full time", title, re.I) and not re.search(r"contract", title, re.I)
    if not d.startswith("Hi [Name],") and not re.match(r"Hi [A-Z][a-z]+,", d):
        p.append('must start "Hi [Name],"')
    w = len(d.split())
    if w < 35 or w > 90:
        p.append(f"{w} words (35-90)")
    m = BANNED_RX.search(d)
    if m:
        p.append(f'banned phrase "{m.group(0)}"')
    if re.search(r"\.\.|;|—|\s{2,}|\[(?!Name\])|\(\s*\)", d):
        p.append("punctuation (.., ;, em dash, double space or stray bracket)")
    if re.search(r"6 hours to 1", d) and "800+" not in d and "3 days" not in d:
        p.append('"6 hours to 1" used as the only result')
    allowed_extra = set(re.findall(r"\d+", co + " " + title + " " + (doc.get("why") or "") + " " + (doc.get("summary") or "")))
    body = re.sub(r"github\.com/\S+|Fortune 500", "", d)
    for n in re.findall(r"(?<![\w-])\d[\d,.]*(?:\+|%|B\+)?(?:[–-]\d+%)?", body):
        n2 = n.rstrip(".,")
        if not allowed_number(n2) and re.sub(r"\D", "", n2) not in allowed_extra:
            p.append(f'number "{n2}" is not one of the known facts')
    if re.search(r"\((FDE|HLS|EDU|MLX\w*|full time|contractor)\)|\s-\s(NYC|SF|NY)\b", d):
        p.append("raw posting codes in the text")
    if staffing and "github.com" in d:
        p.append("repo link in a recruiter message")
    if fulltime_direct and re.search(r"\b(client|duration|rate)\b", d, re.I):
        p.append("asks client/rate on a full-time employer posting")
    last = re.split(r"(?<=[.?!])\s+", re.sub(r"\s*" + re.escape(PORTFOLIO) + r"\s*$", "", d) if PORTFOLIO else d)[-1]
    if not (last.endswith("?") or (staffing and re.search(r"resume", last, re.I))):
        p.append("must end with a question (repo link allowed after it)")
    jd = doc.get("jd") or ""
    if jd and not staffing and (doc.get("fit") or 0) >= 3:
        stop = set("""about above after again agent agents build built candidate company customer customers data engineer
            engineering engineers experience from have help into model models people platform product production python
            role roles systems their there these this through tools using which while will with work would years
            team teams worth minutes talk week could github hours saved estimated""".split())
        jw = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{4,}", jd + " " + title)} - stop
        dw = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{4,}", d)} - stop
        if not (jw & dw):
            p.append("nothing specific to this posting (fit 3 role)")
    ce = (doc.get("contactEmail") or "").strip()
    if ce and (not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", ce) or re.search(r"no-?reply|donotreply|example\.", ce, re.I)):
        p.append(f'contactEmail "{ce}" is not a usable address')
    cn = doc.get("contactName") or ""
    if cn and re.search(r"\b(user|batch|admin|recruiter|team|talent|jobs?|careers?|info|support|hiring|submissions?)\b", cn, re.I):
        p.append(f'contactName "{cn}" is a placeholder, not a person')
    su = doc.get("subject") or ""
    if not su or re.search(r"[()_]|\s-\s|full time", su, re.I) or NAME not in su:
        p.append(f'subject "{su}" is not clean')
    return p


def _words(t):
    return re.findall(r"[A-Za-z][A-Za-z0-9+#./&-]*|\d[\d,.]*[%+]?", t)


def check_resume(doc, master):
    """Problems with doc['resumeVersion'] versus the master resume: new numbers or new proper nouns/tools."""
    rv = doc.get("resumeVersion") or ""
    if not rv:
        return []
    p = []
    # the name and contact lines are fixed, not claims
    rv = "\n".join(l for l in rv.splitlines() if not re.search(r"@|linkedin\.com|^\W*" + re.escape(NAME) + r"\W*$", l, re.I))
    for w in PROFILE.get("neverClaim", []):
        if re.search(r"\b" + re.escape(w) + r"\b", rv):
            p.append(f"resume lists {w} (you removed it from your resume)")
    mw = {w.lower().strip(".,") for w in _words(master)} | {x.lower().strip(".,") for w in _words(master) for x in w.split("/")}
    mnums = set(re.findall(r"\d[\d,.]*[%+]?", master))
    for n in set(re.findall(r"\d[\d,.]*[%+]?", rv)):
        if n.rstrip(".,") not in mnums and n.rstrip(".,%+") not in {x.rstrip("%+") for x in mnums}:
            p.append(f'resume number "{n}" is not in the master resume')
    for line in rv.splitlines():
        body = line.lstrip("#- *")
        if not re.search(r"[a-z]", body):
            continue  # all-caps headline or section header: role labels, not claims (numbers still checked above)
        for mt in re.finditer(r"[A-Za-z][A-Za-z0-9+#./&-]*|\d[\d,.]*[%+]?", body):
            w2 = mt.group(0).strip(".,:;")
            before = body[:mt.start()]
            # a capitalised verb (-ed/-ing) or a known word at a sentence start is not a new term; a new name there is still caught
            starts = not before.strip(" *") or re.search(r"[.:!?][\"')\]*]*\s*$", before)
            if starts and re.fullmatch(r"[A-Z][a-z-]+", w2) and (re.search(r"(ed|ing)$", w2) or w2.lower() in mw):
                continue
            for part in w2.split("/"):
                if not part or not (part[:1].isupper() or re.search(r"[A-Z].*[A-Z]|\d", part[1:])):
                    continue
                if part.lower() not in mw and part.lower().strip("-") not in mw:
                    p.append(f'resume adds "{part}" (not in the master resume)')
    return sorted(set(p))


def check_cover(doc, master):
    """Cover letter and 'why this company' answer: same banned phrases, only numbers from the master resume."""
    p = []
    mnums = {x.rstrip(".,%+") for x in re.findall(r"\d[\d,.]*[%+]?", master or "")}
    extra = set(re.findall(r"\d+", (doc.get("companyName") or "") + " " + (doc.get("title") or "")))
    for field, lo, hi in (("coverLetter", 120, 260), ("whyCompany", 20, 90)):
        t = (doc.get(field) or "").strip()
        if not t:
            continue
        w = len(t.split())
        if w < lo or w > hi:
            p.append(f"{field}: {w} words ({lo}-{hi})")
        m = BANNED_RX.search(re.sub(r"(?i)^dear hiring team,", "", t))
        if m:
            p.append(f'{field}: banned phrase "{m.group(0)}"')
        if re.search(r"\[|\]|—|;", t):
            p.append(f"{field}: punctuation or placeholder")
        if field == "coverLetter" and not re.search(re.escape(NAME) + r"\s*$", t):
            p.append(f"coverLetter: must end with the signature {NAME}")
        body = re.sub(r"github\.com/\S+|linkedin\.com/\S+|Fortune 500", "", t)
        for n in re.findall(r"(?<![\w-])\d[\d,.]*[%+]?", body):
            k = n.rstrip(".,%+")
            if k not in mnums and k not in extra and not re.fullmatch(r"20\d\d", k):
                p.append(f'{field}: number "{n}" is not in the master resume')
        for w in PROFILE.get("neverClaim", []):
            if re.search(r"\b" + re.escape(w) + r"\b", t):
                p.append(f"{field}: mentions {w}")
    return p


def check_post(doc):
    """DM to the author of a LinkedIn hiring post: the outreach rules, without a subject line."""
    if doc.get("status", "new") != "new" or not doc.get("draft"):
        return []
    return [x for x in check(dict(doc, subject="Hiring post – " + NAME, status="new", sameAs=None))
            if not x.startswith("subject")]


def main():
    folder = sys.argv[1]
    docs = {}
    for f in glob.glob(os.path.join(folder, "*.json")):
        docs[os.path.basename(f)[:-5]] = json.load(open(f))
    report = {}
    openers = {}
    for i, doc in docs.items():
        if doc.get("draft") and not doc.get("sameAs") and doc.get("status", "new") == "new":
            openers.setdefault(first_sentence(doc["draft"]), []).append(i)
    master_path = os.path.join(HERE, "RESUME_MASTER.md")
    master = open(master_path).read() if os.path.exists(master_path) else ""
    MASTER_NUMS.update(g.replace(",", "") for g in re.findall(r"\d[\d,]*(?:\.\d+)?", master))
    for i, doc in docs.items():
        p = check(doc) + (check_resume(doc, master) if master else []) + check_cover(doc, master)
        o = doc.get("draft") and first_sentence(doc["draft"])
        if o and len(openers.get(o, [])) > 3:
            p.append(f"opening sentence used {len(openers[o])} times")
        if p:
            report[i] = p
    if "--posts" in sys.argv:
        for f in glob.glob(os.path.join(sys.argv[sys.argv.index("--posts") + 1], "*.json")):
            pp = check_post(json.load(open(f)))
            if pp:
                report["post:" + os.path.basename(f)[:-5]] = pp
    for i, p in sorted(report.items()):
        print(i, "|", "; ".join(p))
    total = sum(1 for d in docs.values() if d.get("status", "new") == "new" and not d.get("sameAs"))
    print(f"\n{len(report)} of {total} drafts fail the checks")
    if "--json" in sys.argv:
        json.dump(report, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    sys.exit(1 if report else 0)


if __name__ == "__main__":
    main()
