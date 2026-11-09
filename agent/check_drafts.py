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



# ---- One-page check: the same layout the tracker uses for the PDF (Carlito = Calibri metrics, sizes from the original PDF) ----
_RWW = {"R": {"c": " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ‒–—―‘’‚‛“”•…→≤≥", "w": [463, 667, 821, 1020, 1038, 1464, 1397, 452, 621, 621, 1020, 1020, 511, 627, 517, 791, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 548, 548, 1020, 1020, 1020, 949, 1831, 1185, 1114, 1092, 1260, 1000, 941, 1292, 1276, 516, 653, 1064, 861, 1751, 1322, 1356, 1058, 1378, 1112, 941, 998, 1314, 1162, 1822, 1063, 998, 959, 628, 791, 628, 1020, 1020, 596, 981, 1076, 866, 1076, 1019, 625, 964, 1076, 470, 490, 931, 470, 1636, 1076, 1080, 1076, 1076, 714, 801, 686, 1076, 925, 1464, 887, 927, 809, 644, 943, 644, 1020, 463, 667, 1020, 1038, 1020, 1038, 1020, 1020, 804, 1709, 824, 1049, 1020, 1038, 807, 694, 1020, 688, 685, 598, 1126, 1200, 517, 629, 504, 865, 1049, 1303, 1375, 1383, 949, 1185, 1185, 1185, 1185, 1185, 1185, 1563, 1092, 1000, 1000, 1000, 1000, 516, 516, 516, 516, 1279, 1322, 1356, 1356, 1356, 1356, 1356, 1020, 1359, 1314, 1314, 1314, 1314, 998, 1058, 1080, 981, 981, 981, 981, 981, 981, 1583, 866, 1019, 1019, 1019, 1019, 470, 470, 470, 470, 1076, 1076, 1080, 1080, 1080, 1080, 1080, 1020, 1084, 1076, 1076, 1076, 1076, 927, 1076, 927, 1038, 1020, 1854, 1854, 511, 511, 511, 511, 857, 857, 1020, 1414, 1854, 1020, 1020]}, "B": {"c": " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ‒–—―‘’‚‛“”•…→≤≥", "w": [463, 667, 898, 1020, 1038, 1493, 1443, 478, 638, 638, 1020, 1020, 528, 627, 547, 880, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 565, 565, 1020, 1020, 1020, 949, 1840, 1241, 1148, 1084, 1291, 999, 940, 1305, 1292, 546, 678, 1120, 866, 1790, 1349, 1385, 1090, 1405, 1153, 968, 1014, 1337, 1211, 1856, 1128, 1064, 979, 665, 880, 665, 1020, 1020, 615, 1011, 1099, 857, 1099, 1031, 648, 971, 1099, 503, 523, 983, 503, 1666, 1099, 1101, 1099, 1099, 728, 817, 710, 1099, 969, 1526, 941, 970, 814, 704, 973, 704, 1020, 463, 667, 1020, 1038, 1020, 1038, 1020, 1020, 849, 1709, 852, 1103, 1020, 1038, 799, 701, 1020, 692, 688, 616, 1154, 1224, 548, 621, 517, 891, 1103, 1347, 1415, 1437, 949, 1241, 1241, 1241, 1241, 1241, 1241, 1588, 1084, 999, 999, 999, 999, 546, 546, 546, 546, 1309, 1349, 1385, 1385, 1385, 1385, 1385, 1020, 1394, 1337, 1337, 1337, 1337, 1064, 1090, 1136, 1011, 1011, 1011, 1011, 1011, 1011, 1587, 857, 1031, 1031, 1031, 1031, 503, 503, 503, 503, 1099, 1099, 1101, 1101, 1101, 1101, 1101, 1020, 1114, 1099, 1099, 1099, 1099, 970, 1099, 970, 1038, 1020, 1854, 1854, 528, 528, 528, 528, 891, 891, 1020, 1457, 1854, 1020, 1020]}, "I": {"c": " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ‒–—―‘’‚‛“”•…→≤≥", "w": [463, 667, 821, 1020, 1038, 1464, 1397, 452, 621, 621, 1020, 1020, 511, 627, 517, 794, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 548, 548, 1020, 1020, 1020, 949, 1831, 1185, 1114, 1070, 1260, 1000, 941, 1292, 1276, 516, 653, 1064, 861, 1751, 1320, 1340, 1058, 1360, 1112, 926, 998, 1314, 1162, 1823, 1063, 998, 959, 628, 787, 628, 1020, 1020, 596, 1053, 1053, 852, 1053, 978, 625, 1053, 1053, 470, 490, 931, 470, 1620, 1053, 1051, 1053, 1053, 702, 797, 686, 1053, 913, 1464, 887, 916, 809, 644, 943, 644, 1020, 463, 667, 1020, 1038, 1020, 1038, 1020, 1020, 804, 1709, 882, 1049, 1020, 1038, 807, 694, 1020, 688, 685, 598, 1102, 1200, 517, 629, 504, 865, 1049, 1303, 1375, 1383, 949, 1185, 1185, 1185, 1185, 1185, 1185, 1563, 1070, 1000, 1000, 1000, 1000, 516, 516, 516, 516, 1279, 1320, 1340, 1340, 1340, 1340, 1340, 1020, 1347, 1314, 1314, 1314, 1314, 998, 1058, 1080, 1053, 1053, 1053, 1053, 1053, 1053, 1545, 852, 978, 978, 978, 978, 470, 470, 470, 470, 1076, 1053, 1051, 1051, 1051, 1051, 1051, 1020, 1084, 1053, 1053, 1053, 1053, 916, 1053, 916, 1038, 1020, 1854, 1854, 511, 511, 511, 511, 857, 857, 1020, 1413, 1854, 1020, 1020]}}
_RWT = {k: dict(zip(v["c"], v["w"])) for k, v in _RWW.items()}
_RWCONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}|linkedin\.com/in/", re.I)
_RWDATE = re.compile(r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}\s*[\u2013\u2014-]\s*(((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}|Present|Current|Now)|^\s*((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}\s*$", re.I)


def _rw_w(s, f, size):
    t = _RWT[f]
    return sum(t.get(ch, t["?"]) for ch in s) * size / 2048


def _rw_clean(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s or "")
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"[^\x20-\x7E\u00A0-\u00FF\u2010-\u2015\u2018-\u201D\u2022\u2026\u2192\u2264\u2265]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _rw_parse(md):
    out, sec, last, after = [], "", None, False
    for l in (x.strip() for x in (md or "").split("\n")):
        if not l or _RWCONTACT.search(l):
            continue
        if l.startswith("## "):
            sec = l[3:].strip(); out.append({"k": "sec"}); last, after = None, False; continue
        if not sec:
            continue
        S = sec.lower()
        if re.match(r"^#{1,3} ", l):
            t = _rw_clean(re.sub(r"^#+\s*", "", l)); sub = ""
            m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", t)
            if m and not _RWDATE.search(m.group(2)):
                t, sub = m.group(1), m.group(2)
            elif m:
                t = m.group(1) + " \u00b7 " + m.group(2)
            parts = re.split(r"\s+[\u00b7|]\s+", t); dates = ""
            if len(parts) > 1 and _RWDATE.search(parts[-1]):
                dates = parts.pop()
            last = {"k": "entry", "left": "  \u00b7  ".join(parts), "dates": dates, "sub": re.sub(r"\s+\|\s+", "  |  ", sub), "proj": "project" in S}
            out.append(last); after = True; continue
        if l.startswith("- "):
            t = _rw_clean(l[2:]); after = False
            m = re.match(r"^([^:]{1,40}):\s*(.*)$", t)
            if "skill" in S and m:
                out.append({"k": "skill", "runs": [(m.group(1) + ": ", "B"), (m.group(2), "R")]}); continue
            if re.search(r"education|certif", S):
                m2 = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", t)
                body, dates = (m2.group(1), m2.group(2)) if m2 and _RWDATE.search(m2.group(2)) else (t, "")
                p = re.split(r"\s+[\u2014\u2013]\s+", body)
                out.append({"k": "edu", "runs": [(p[0], "B"), ("  \u2014  " + " \u2014 ".join(p[1:]) if len(p) > 1 else "", "R")], "dates": dates}); continue
            out.append({"k": "bul", "s": t}); continue
        t = _rw_clean(l)
        m = re.match(r"^([^:]{1,40}):\s*(.*)$", t)
        if "skill" in S and m:
            out.append({"k": "skill", "runs": [(m.group(1) + ": ", "B"), (m.group(2), "R")]}); continue
        if after and last and last["proj"]:
            out.append({"k": "sub", "s": re.sub(r"\.$", "", t) + ("  |  " + last["sub"] if last["sub"] else "")}); last["sub"] = ""; after = False; continue
        after = False; out.append({"k": "para", "s": t})
    res = []
    for b in out:
        res.append(b)
        if b["k"] == "entry" and b["sub"]:
            res.append({"k": "sub", "s": b["sub"]})
    return res


def _rw_lines(runs, max_w, size):
    toks = []
    for s, f in runs:
        for w in re.split(r"( +)", s):
            if w:
                toks.append((w, f, w.strip() == ""))
    n, cur, w = 0, 0, 0.0
    for s, f, sp in toks:
        tw = _rw_w(s, f, size)
        if sp and not cur:
            continue
        if not sp and cur and w + tw > max_w:
            n += 1; cur, w = 0, 0.0
        cur += 1; w += tw
    return n + (1 if cur else 0)


def resume_layout(md, k=1.0, fs=9.5):
    """(pages, bottom of the last line in points) for a resume laid out like the original PDF."""
    L, R, WR, BOT = 32, 580, 584, 764
    ADV = {"para": 11.0, "bul": 10.65, "skill": 11.0, "sub": 11.0, "edu": 11.0, "entry": 11.0}
    FIRST = {"para": 20.6, "skill": 15.2, "entry": 17.3, "edu": 16.1, "bul": 17.3, "sub": 17.3}

    def gap(a, b):
        if b == "sec": return 15.4
        if b == "entry": return 14.2
        if b == "sub": return 11.6 if a == "entry" else 12
        if b == "para": return 11.6 if a in ("entry", "sub") else 12.4
        if b == "bul": return 12.0 if a == "bul" else 11.5 if a == "sub" else 13.35
        if b == "skill": return 12.15
        if b == "edu": return 12.6
        return 12
    y, prev, sec_top, page = None, None, None, 0

    def room(top, n):
        nonlocal page
        if top + (n - 1) * ADV["para"] + fs > BOT:
            page += 1; return 36
        return top
    for b in _rw_parse(md):
        if b["k"] == "sec":
            top = 71.0 if y is None else y + gap(prev, "sec") * k
            top = room(top, 3); sec_top = top; y = top; prev = "sec"; continue
        if prev == "sec" and sec_top is not None:
            top = sec_top + FIRST[b["k"]] * k; sec_top = None
        else:
            top = 71.0 if y is None else y + gap(prev, b["k"]) * k
        adv = max(10.2, ADV[b["k"]] * k)
        if b["k"] == "entry":
            dw = _rw_w(b["dates"], "B", fs) + 12 if b["dates"] else 0
            n = _rw_lines([(b["left"], "B")], R - L - dw, fs); top = room(top, n + 2)
        elif b["k"] == "sub":
            n = _rw_lines([(b["s"], "I")], WR - L, 8.5); top = room(top, n)
        elif b["k"] == "para":
            n = _rw_lines([(b["s"], "R")], WR - L, fs); top = room(top, n)
        elif b["k"] == "bul":
            n = _rw_lines([(b["s"], "R")], WR - 47.8, fs); top = room(top, n)
        elif b["k"] == "skill":
            n = _rw_lines(b["runs"], WR - L, fs); top = room(top, n)
        else:
            dw = _rw_w(b["dates"], "R", 8.5) + 12 if b["dates"] else 0
            n = _rw_lines(b["runs"], R - L - dw, fs); top = room(top, n)
        y = top + (n - 1) * adv; prev = b["k"]
    return page + 1, (y or 0) + fs


def resume_fit(md):
    """(fits on one page, bottom in points). The tracker may tighten spacing down to 88%%; past that it holds the version back."""
    for k in (1, .97, .94, .91, .88):
        pages, bottom = resume_layout(md, k)
        if pages == 1 and bottom <= 764:
            return True, bottom
    return False, resume_layout(md)[1]


def check_resume(doc, master):
    """Problems with doc['resumeVersion'] versus the master resume: new numbers or new proper nouns/tools."""
    rv = doc.get("resumeVersion") or ""
    if not rv:
        return []
    p = []
    # the name and contact lines are fixed, not claims
    rv = "\n".join(l for l in rv.splitlines() if not (_RWCONTACT.search(l) or re.search(r"^\W*" + re.escape(NAME) + r"\W*$", l, re.I)))
    m_fit, m_bottom = resume_fit(master)
    if m_fit:  # the master fits one page in the tracker's layout, so every tailored version must too
        fit, bottom = resume_fit(rv)
        if not fit:
            p.append("runs past one page in the resume layout: drop the least relevant bullet")
        elif bottom < m_bottom - 60:
            p.append("much shorter than the original (bottom of the page left empty): keep every bullet from the master, reordered")
    mh = [l.strip() for l in master.splitlines() if l.startswith("### ")]
    for l in rv.splitlines():
        if l.startswith("### ") and l.strip() not in mh:
            p.append(f'job line changed from the master: "{l.strip()[4:60]}" (copy ### lines exactly)')
    for h in mh:
        if h not in [l.strip() for l in rv.splitlines()]:
            p.append(f'job line missing: "{h[4:60]}"')
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
