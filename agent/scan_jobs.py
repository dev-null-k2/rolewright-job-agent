#!/usr/bin/env python3
"""Rolewright job scan: AI, forward-deployed, software and data roles in the areas you choose (profile.json "search"), or US remote.

Reads public job-board APIs (Greenhouse, Lever, Ashby, Workday, big-tech careers, HN, Dice, Phenom staffing sites), keeps roles whose title
matches the target families and whose location fits, flags postings that refuse visa sponsorship, and
writes JSON. Usage: python3 scan_jobs.py [--days 3] [--out jobs.json] [--profile profile.json]
"""
import argparse
import concurrent.futures as cf
import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (personal job scan)"}
# Areas you are searching. Each is a name and a regex over the posting's location text. "Remote" is always added.
AREAS = [("NYC", r"new york|nyc|\bny\b|brooklyn|jersey city"),
         ("SF Bay Area", r"san francisco|\bsf\b|bay area|palo alto|mountain view|menlo park|san mateo|redwood city|sunnyvale|"
                         r"san jose|oakland|berkeley|cupertino|santa clara|foster city|emeryville"),
         ("Dallas-Fort Worth", r"dallas|fort worth|irving|plano|frisco|richardson|addison|las colinas|westlake|southlake|arlington, tx|dfw"),
         ("Texas", r"austin|houston|san antonio|\btx\b|texas")]
GOOGLE_CITIES = [("New York", "New York, NY, USA"), ("San Francisco", "San Francisco, CA, USA"), ("Dallas", "Dallas, TX, USA")]

BOARDS = {
    "greenhouse": "affirm airtable alloy anthropic asana assemblyai brex c3iot chainguard chime cloudflare coinbase coreweave cresta databricks datadog dataiku descript devrev eudia eve faire figma figure fivetran galileo gleanwork gusto heygen imbue intercom invisible labelbox lightmatter lovable make mercury mongodb nebius netlify pathai planetscale ramp robinhood scaleai sigmacomputing snorkelai stackblitz stripe suki tenstorrent togetherai turing typeface vectara vercel warp workato xai",
    "lever": "alloy finch fly neon outreach palantir secureframe shieldai waabi zilliz",
    "ashby": "abridge airbyte alloy ambiencehealthcare anyscale applied attio baseten benchling bland braintrust browserbase cartesia cerebras cleric clickhouse coderabbit cognition cohere crusoe cursor decagon deepgram distyl drata dust e2b elevenlabs etched factory faculty finch gamma granola greptile handshake harvey hex hightouch ideogram insitro krea lambda lancedb langchain legora letta linear llamaindex lovable magic maven mercor midjourney modal motherduck n8n nabla neon notion openai openevidence owkin parloa patronus perplexity persona physicalintelligence pika pinecone plaid poolside posthog railway ramp reducto reka relevanceai render replit resolveai rilla rogo runpod runway sardine saronic secureframe semgrep sentry sierra snowflake snyk socure suno supabase synthesia tavus temporal tenexlabs thinkingmachines traversal turbopuffer unstructured vanta vapi warp weaviate writer zapier",
}

TITLE_IN = re.compile(
    r"forward[- ]deployed|deployment (engineer|strategist)|applied (ai|ml|machine learning)|"
    r"\bai\b|\bml\b|machine learning|\bllm|generative|genai|agent|solutions? (engineer|architect)|"
    r"customer engineer|founding engineer|ai engineer|inference|evals?\b|"
    r"software (engineer|developer)|\bswe\b|backend|back[- ]end|full[- ]?stack|python (engineer|developer)|"
    r"data engineer|data platform|platform engineer|site reliability|\bsre\b|production engineer", re.I)
TITLE_OUT = re.compile(
    r"intern\b|internship|director|head of|\bvp\b|vice president|principal|staff|distinguished|manager|"
    r"recruit|sales|account executive|marketing|counsel|legal|designer|research scientist|phd|"
    r"hardware|datacenter|data center|technician|\bsdr\b|\bbdr\b|finance|accountant|"
    r"\blead\b|quality operations|customer success|support agent|team agent|call center|customer service|service agent|insurance agent|leasing|adoption|transformation|silicon|c\+\+|firmware|security engineer|analyst|\bios\b|android|mobile|embedded|game|frontend|front[- ]end engineer|salesforce developer|mainframe|cobol|trainer|annotat|tutor|rater|labeling|creative|video|physical design|asic|\brtl\b|wi-fi|wireless|baseband|sap\b", re.I)
LOC_IN = re.compile(
    r"new york|nyc|\bny\b|brooklyn|jersey city|san francisco|\bsf\b|bay area|palo alto|mountain view|"
    r"menlo park|san mateo|redwood city|sunnyvale|san jose|oakland|berkeley|cupertino|santa clara|foster city|emeryville|austin|houston|san antonio|remote|dallas|fort worth|irving|plano|frisco|richardson|addison|las colinas|westlake|southlake|arlington, tx|dfw|\btx\b|texas", re.I)
LOC_OUT = re.compile(r"remote\s*[-–(,]?\s*(canada|uk|eu|europe|emea|apac|india|latam|mexico|brazil|germany)|"
                     r"\b(london|dublin|toronto|paris|berlin|bangalore|bengaluru|singapore|tokyo|sydney|uae|saudi|middle east|dubai|riyadh)\b", re.I)
NO_VISA = re.compile(
    r"(unable|not able|cannot|can ?not|will not|won't|do not|does not|don't|doesn't)\s+(to\s+)?"
    r"(offer|provide|support|sponsor)[^.]{0,40}(sponsor|visa)|no (visa )?sponsorship|"
    r"without (the need for )?(current or future )?(visa )?sponsorship|"
    r"must be (a )?(u\.?s\.? citizen|authorized to work[^.]{0,60}without)|security clearance|"
    r"\bclearance required|us citizenship (is )?required|public trust|top secret|secret clearance|ts/sci|"
    r"\b(usc|u\.?s\.? citizens?)\s*(/|or|and|&)\s*(gc|green card)|green card holders? only|\bgc only|"
    r"\bno\s+(h-?1b|opt|cpt|ead|visa)|(citizens?|usc|gc)\s+only|"
    r"\bc2c only|corp[- ]to[- ]corp only|1099 only|only (on )?c2c", re.I)
YES_VISA = re.compile(r"(visa|h-?1b|immigration) sponsorship (is )?(available|offered|provided)|"
                      r"we (do |will )?sponsor|open to sponsor", re.I)


def get(url):
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(1.5)
    return None


def text(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ts(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def from_greenhouse(slug):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true") or {}
    for j in d.get("jobs", []):
        yield dict(ats="greenhouse", company=slug, id=f"gh-{slug}-{j['id']}", title=j.get("title", ""),
                   location=(j.get("location") or {}).get("name", ""), url=j.get("absolute_url", ""),
                   posted=ts(j.get("first_published") or j.get("updated_at")), desc=text(j.get("content")))


def from_lever(slug):
    d = get(f"https://api.lever.co/v0/postings/{slug}?mode=json") or []
    for j in d if isinstance(d, list) else []:
        cats = j.get("categories") or {}
        loc = ", ".join([cats.get("location") or ""] + (cats.get("allLocations") or []))
        yield dict(ats="lever", company=slug, id=f"lv-{slug}-{j['id']}", title=j.get("text", ""), location=loc,
                   url=j.get("hostedUrl", ""), posted=ts(j.get("createdAt")),
                   desc=text(j.get("descriptionPlain") or j.get("description")) + " " +
                   " ".join(text(l.get("content")) for l in j.get("lists", [])))


def from_ashby(slug):
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true") or {}
    for j in d.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        if j.get("isRemote"):
            locs.append("Remote")
        yield dict(ats="ashby", company=slug, id=f"ab-{slug}-{j['id']}", title=j.get("title", ""),
                   location=", ".join(l for l in locs if l), url=j.get("jobUrl", ""), posted=ts(j.get("publishedAt")),
                   desc=(j.get("descriptionPlain") or text(j.get("descriptionHtml"))) + " SALARY: " +
                   str((j.get("compensation") or {}).get("scrapeableCompensationSalarySummary") or ""))


QUERIES = ["AI engineer", "applied AI", "forward deployed", "machine learning engineer", "generative AI", "agent",
           "software engineer python", "data engineer", "backend engineer", "python developer",
           "full stack engineer", "LLM", "ML engineer", "platform engineer"]
CITIES = ["New York", "San Francisco", "Dallas"]
WORKDAY = ("nvidia.wd5:nvidia:NVIDIAExternalCareerSite salesforce.wd12:salesforce:External_Career_Site "
           "adobe.wd5:adobe:external_experienced workday.wd5:workday:Workday mastercard.wd1:mastercard:CorporateCareers "
           "blackrock.wd1:blackrock:BlackRock_Professional citi.wd5:citi:2 ghr.wd1:ghr:Lateral-US intel.wd1:intel:External "
           "paypal.wd1:paypal:jobs spgi.wd5:spgi:SPGI_Careers pfizer.wd1:pfizer:PfizerCareers ms.wd5:ms:External "
           "capitalone.wd12:capitalone:Capital_One att.wd1:att:ATTGeneral fmr.wd1:fmr:FidelityCareers "
           "mckesson.wd3:mckesson:External_Careers sabre.wd1:sabre:SabreJobs usaa.wd1:usaa:USAAJOBSWD "
           "statestreet.wd1:statestreet:Global tiaa.wd1:tiaa:Search verizon.wd12:verizon:verizon-careers travelers.wd5:travelers:External")
WD_NAMES = {"ghr": "bankofamerica", "ms": "morganstanley", "spgi": "s&p global", "fmr": "fidelity", "att": "at&t"}


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**UA, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except Exception:
        return None


def from_amazon(_):
    seen = set()
    for q in QUERIES[:5] + QUERIES[6:]:
        for city in CITIES:
            d = get("https://www.amazon.jobs/en/search.json?" + urllib.parse.urlencode(
                {"base_query": q, "loc_query": city, "result_limit": 50, "sort": "recent"})) or {}
            for j in d.get("jobs", []):
                if j.get("id_icims") in seen:
                    continue
                seen.add(j.get("id_icims"))
                try:
                    p = datetime.strptime(re.sub(r"\s+", " ", j.get("posted_date", "")), "%B %d, %Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    p = None
                yield dict(ats="amazon", company="amazon", id=f"amz-{j.get('id_icims')}", title=j.get("title", ""),
                           location=j.get("normalized_location") or j.get("location", ""),
                           url="https://www.amazon.jobs" + j.get("job_path", ""), posted=p,
                           desc=text(j.get("description")) + " " + text(j.get("preferred_qualifications")))


def from_microsoft(_):
    seen = set()
    for q in QUERIES[:5] + QUERIES[6:]:
        for city in CITIES:
            d = get("https://apply.careers.microsoft.com/api/pcsx/search?" + urllib.parse.urlencode(
                {"domain": "microsoft.com", "query": q, "location": city, "start": 0, "sort_by": "timestamp"})) or {}
            for j in (d.get("data") or {}).get("positions", []):
                if j.get("id") in seen:
                    continue
                seen.add(j.get("id"))
                yield dict(ats="microsoft", company="microsoft", id=f"msft-{j.get('displayJobId')}", title=j.get("name", ""),
                           location="; ".join(j.get("locations") or []),
                           url="https://apply.careers.microsoft.com" + (j.get("positionUrl") or ""),
                           posted=datetime.fromtimestamp(int(j.get("postedTs") or 0), tz=timezone.utc) if j.get("postedTs") else None,
                           desc="")


def _wd_posted(s):
    s = (s or "").lower()
    if "today" in s:
        return datetime.now(timezone.utc)
    if "yesterday" in s:
        return datetime.fromtimestamp(time.time() - 86400, tz=timezone.utc)
    m = re.search(r"(\d+)\+? days", s)
    return datetime.fromtimestamp(time.time() - int(m.group(1)) * 86400, tz=timezone.utc) if m else None


def from_workday(spec):
    host, ten, site = spec.split(":")
    base = f"https://{host}.myworkdayjobs.com"
    seen = set()
    for q in QUERIES:
        d = post(f"{base}/wday/cxs/{ten}/{site}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q}) or {}
        for j in d.get("jobPostings", []):
            path = j.get("externalPath", "")
            if not path or path in seen or not TITLE_IN.search(j.get("title", "")) or TITLE_OUT.search(j.get("title", "")):
                continue
            seen.add(path)
            info = (get(f"{base}/wday/cxs/{ten}/{site}{path}") or {}).get("jobPostingInfo", {})
            locs = [info.get("location") or j.get("locationsText", "")] + (info.get("additionalLocations") or [])
            yield dict(ats="workday", company=WD_NAMES.get(ten, ten), id=f"wd-{ten}-{path.rsplit('_', 1)[-1]}",
                       title=j.get("title", ""), location="; ".join(l for l in locs if l),
                       url=f"{base}/en-US/{site}{path}", posted=ts(info.get("startDate")) or _wd_posted(j.get("postedOn")),
                       desc=text(info.get("jobDescription")))


def from_google(_):
    seen = set()
    for q in QUERIES[:5] + QUERIES[6:]:
        for city, loc in GOOGLE_CITIES:
            try:
                req = urllib.request.Request("https://www.google.com/about/careers/applications/jobs/results?" +
                                             urllib.parse.urlencode({"q": q, "location": loc}), headers=UA)
                page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
            except Exception:
                continue
            for jid, slug in re.findall(r"jobs/results/(\d{6,})-([a-z0-9-]+)", page):
                if jid in seen:
                    continue
                seen.add(jid)
                yield dict(ats="google", company="google", id=f"goog-{jid}", title=slug.replace("-", " ").title(),
                           location=loc, url=f"https://www.google.com/about/careers/applications/jobs/results/{jid}-{slug}",
                           posted=datetime.now(timezone.utc), desc="")


def from_hn(_):
    s = get("https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&query=who%20is%20hiring&hitsPerPage=5") or {}
    story = next((h for h in s.get("hits", []) if "who is hiring" in h.get("title", "").lower()), None)
    if not story:
        return
    tree = get(f"https://hn.algolia.com/api/v1/items/{story['objectID']}") or {}
    for c in tree.get("children", []):
        raw = c.get("text") or ""
        first = text(raw.split("<p>")[0])
        body = text(raw)
        if not first or "|" not in first:
            continue
        emails = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", html.unescape(raw).replace(" [at] ", "@").replace("(at)", "@"))))
        yield dict(ats="hn", company=first.split("|")[0].strip()[:60], id=f"hn-{c['id']}", title=first[:160],
                   location=first + " " + body[:400], url=f"https://news.ycombinator.com/item?id={c['id']}",
                   posted=ts(c.get("created_at")), desc=body + (" CONTACT: " + ", ".join(emails) if emails else ""),
                   contact=", ".join(emails), **verified_contact(emails, source="Hacker News post"))


BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}


def get_html(url):
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=BROWSER), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(1.5)
    return ""


def _age_days(s):
    s = (s or "").lower()
    if "today" in s or re.search(r"\d+\s*(h|m|min|hour|minute)s?\b", s):
        return 0
    if "yesterday" in s:
        return 1
    m = re.search(r"(\d+)\s*d", s)
    return int(m.group(1)) if m else 99


# Dice carries most staffing / contract postings (Robert Half, Kforce, Insight Global, Apex, Motion, Jobot,
# CyberCoders, Randstad, consulting firms). One task per location; the search card is filtered first and only
# matching cards get a detail fetch (JSON-LD gives the date and full description for the visa check).
DICE_LOCS = ["New York, NY", "San Francisco, CA", "Dallas, TX", "remote"]
DICE_DAYS = 3


# ---- Contact finder: only addresses the poster published, never guessed; every domain must have a live mail server (MX). ----
EMAIL_RX = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])")
EMAIL_BAD = re.compile(r"no-?reply|do-?not-?reply|donotreply|example\.|privacy|accommodat|accessib|\beeo\b|unsubscribe|abuse@|"
                       r"postmaster|webmaster|@dice\.com|sentry|wixpress|@w3\.org|\.(png|jpg|gif|svg)$", re.I)
ROUTING = re.compile(r"submissions?@|ceipal|jobdiva|bullhorn|resumes?@|applications?@|apply@|jobs@|careers?@|talent@|hr@|"
                     r"recruit(ing|ment)?@|hiring@|info@|contact@", re.I)
_MX = {}


def mx_ok(domain):
    """True only if the domain publishes MX records (checked over DNS-over-HTTPS; cached)."""
    d = domain.lower().strip(".")
    if d not in _MX:
        ok = False
        for url in (f"https://dns.google/resolve?name={urllib.parse.quote(d)}&type=MX",
                    f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(d)}&type=MX"):
            try:
                req = urllib.request.Request(url, headers={**UA, "accept": "application/dns-json"})
                r = json.loads(urllib.request.urlopen(req, timeout=15).read())
                ok = r.get("Status") == 0 and any(a.get("type") == 15 and a.get("data", "").strip(". ").split(" ")[-1] not in ("", ".")
                                                  for a in r.get("Answer") or [])
                break
            except Exception:
                continue
        _MX[d] = ok
    return _MX[d]


PLACEHOLDER_NAME = re.compile(r"\b(user|batch|admin|administrator|recruiter|recruiting|hr|team|talent|jobs?|careers?|info|support|"
                              r"account|dice|test|hiring|staffing|desk|manager|resume|resumes|submissions?)\b", re.I)


def _clean_name(n):
    n = re.sub(r"[^A-Za-z' -]", "", n or "").strip()
    if not n or PLACEHOLDER_NAME.search(n) or len(n) < 2:
        return ""
    return n.title() if n.isupper() or n.islower() else n


def _name_from_local(local):
    """'veeresh.murugan' or 'Anuj.Mishra.53013.4073' -> ('Veeresh', 'Murugan'). Single words and anything else -> no name."""
    m = re.fullmatch(r"([A-Za-z]{2,15})[._]([A-Za-z]{2,20})(?:[._]\d[\d.]*)?", local)
    return (m.group(1).title(), m.group(2).title()) if m else ("", "")


def verified_contact(emails, first="", last="", title="", company="", source="", profile=""):
    """Pick the best published email. Personal address of the named poster > other personal > routing inbox.
    Returns {} when nothing passes, so a wrong address is never filled in."""
    cands = []
    for e in emails:
        e = (e or "").strip().strip(".,;:<>()[]").replace("mailto:", "")
        if not e or not EMAIL_RX.fullmatch(e) or EMAIL_BAD.search(e) or len(e) > 80:
            continue
        if e.lower() not in [c.lower() for c in cands]:
            cands.append(e)
    first, last = _clean_name(first), _clean_name(last)

    def info(e):
        local = e.split("@")[0]
        lo = re.sub(r"[^a-z]", "", local.lower())
        f, l = re.sub(r"[^a-z]", "", (first.split() or [""])[0].lower()), re.sub(r"[^a-z]", "", last.lower().split(" ")[-1] if last else "")
        mine = bool(f) and (lo.startswith(f) or (len(f) >= 4 and f in lo) or (len(l) >= 3 and (lo.startswith(l) or lo.startswith(f[0] + l))))
        lf, ll = _name_from_local(local)
        routing = bool(ROUTING.search(e)) or (not mine and not lf and bool(re.search(r"\d", local)))
        return local, lf, ll, mine, routing

    def rank(e):
        _, lf, _, mine, routing = info(e)
        return 0 if mine else 1 if lf else 2 if not routing else 3
    ok = [e for e in sorted(cands, key=rank) if mx_ok(e.split("@")[1])]
    # every published, working address on the page (up to 3), so the page can offer one button per person
    allc = []
    for e in ok[:3]:
        _, _, _, mine, routing = info(e)
        allc.append({"email": e, "name": f"{first} {last}".strip() if first and (mine or (routing and len(ok) == 1)) else "",
                     "title": title if first and mine else "", "kind": "apply inbox" if routing and not mine else "recruiter",
                     "source": source, "url": profile})
    for e in ok[:1]:
        local, lf, ll, mine, routing = info(e)
        # Name rules: the poster's own address or the posting's inbox -> poster's name; anything else -> no name ("Hi,").
        # One person's name never goes on another person's email.
        # (A name read off an address like mistry.kavya@ could be surname-first, so it is never used.)
        name = f"{first} {last}".strip() if first and (mine or routing) else ""
        return {"contactEmail": e, "contactName": name, "contactTitle": title if first and (mine or routing) else "",
                "contactKind": "apply inbox" if routing and not mine else "recruiter", "contactSource": source,
                "contactProfile": profile, "contactVerified": datetime.now(timezone.utc).date().isoformat(), "contacts": allc}
    return {}


def dice_contact(page):
    """Recruiter name/title and the apply-to email Dice shows on a job page (structured data, not guessed)."""
    raw = page.replace('\\"', '"')
    first = last = title = co = rid = ""
    m = re.search(r'"recruiterId":"([0-9a-f-]{20,})","initialData":\{', raw)
    if m:
        rid = m.group(1)
        blk = raw[m.end(): m.end() + 6000]
        g = lambda k: (re.search(r'"%s":"([^"]{0,80})"' % k, blk) or [None, ""])[1]
        first, last, title = g("firstName"), g("lastName"), g("jobTitle")
        co = (re.search(r'"company":\{"name":"([^"]{0,80})"', blk) or [None, ""])[1]
    emails = re.findall(r'"applicationDetail":\{"type":"APPLY_TO_EMAIL","url":[^,]*,"email":"([^"]+)"(?:,"ccEmail":"([^"]+)")?', raw)
    flat = [x for t in emails for x in t if x]
    desc = re.search(r'"description":\s*"(.*?)",\s*"datePosted"', raw, re.S)
    flat += EMAIL_RX.findall(html.unescape(desc.group(1)) if desc else "")
    who = (_clean_name(title) + (" @ " + co if co else "")).strip(" @")
    prof = f"https://www.dice.com/recruiter-profile/{rid}" if rid else ""
    c = verified_contact(flat, first, last, who, co, "Dice posting", prof)
    if not c and _clean_name(first) and _clean_name(last):
        # No usable email, but the poster is a named person: give his LinkedIn search that person, not a generic one.
        n = f"{_clean_name(first)} {_clean_name(last)}"
        c = {"contactName": n, "contactTitle": who, "contactKind": "recruiter (no email listed)", "contactSource": "Dice posting",
             "contactProfile": prof, "contactSearch": "https://www.linkedin.com/search/results/people/?keywords="
             + urllib.parse.quote(n + " " + re.sub(r",?\s*(inc|llc|corp|ltd)\.?$", "", co, flags=re.I))}
    return c

def from_dice(spec):
    loc, q = spec.split("|", 1)
    seen = set()
    period = "ONE" if DICE_DAYS <= 1 else ("THREE" if DICE_DAYS <= 3 else "SEVEN")
    for q in [q]:
        params = {"q": q, "filters.postedDate": period, "pageSize": 100}
        if loc == "remote":
            params["filters.isRemote"] = "true"
        else:
            params.update(location=loc, radius=50, radiusUnit="mi")
        cards = []
        for pg in range(1, 6):
            page = get_html("https://www.dice.com/jobs?" + urllib.parse.urlencode({**params, "page": pg}))
            got = page.split('data-testid="job-card"')[1:]
            cards += got
            if len(got) < 20:
                break
        for card in cards:
            card = card.split(">", 1)[-1]
            g = re.search(r'/job-detail/([0-9a-f-]{20,})', card)
            if not g or g.group(1) in seen:
                continue
            seen.add(g.group(1))
            bits = [b for b in (html.unescape(x).strip() for x in re.split(r"<[^>]+>", card[:8000])) if b and b != "•"]
            if len(bits) < 4 or not TITLE_IN.search(bits[0]) or TITLE_OUT.search(bits[0]):
                continue
            if _age_days(" ".join(bits[3:6])) > DICE_DAYS + 1:
                continue
            url = f"https://www.dice.com/job-detail/{g.group(1)}"
            d = {}
            page = get_html(url) or ""
            for m in re.finditer(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", page, re.S):
                try:
                    x = json.loads(m.group(1))
                except ValueError:
                    continue
                if x.get("@type") == "JobPosting":
                    d = x
                    break
            a = ((d.get("jobLocation") or {}) if isinstance(d.get("jobLocation"), dict) else {}).get("address", {})
            where = ", ".join(v for v in [a.get("addressLocality"), a.get("addressRegion")] if v) or bits[2]
            if loc == "remote" or re.search(r"remote", " ".join(bits[2:8]), re.I):
                where += " (Remote, United States)"
            etype = d.get("employmentType") or ""
            etype = ", ".join(etype) if isinstance(etype, list) else etype
            yield dict(ats="dice", company=((d.get("hiringOrganization") or {}).get("name") or bits[1]).lower(),
                       id=f"dice-{g.group(1)[:13]}", title=bits[0] + (f" ({etype.replace('_', ' ').lower()})" if etype else ""),
                       location=where, url=url, posted=ts(d.get("datePosted")),
                       desc=text(d.get("description")) + _ld_salary(d.get("baseSalary")),
                       **dice_contact(page))


# Allegis staffing brands run on Phenom career sites with a public search widget.
PHENOM = {"teksystems": ("careers.teksystems.com", "TESYUS"), "actalent": ("careers.actalentservices.com", "ALGRUS"),
          "aston carter": ("careers.astoncarter.com", "ASCAUS")}


def from_phenom(name):
    host, ref = PHENOM[name]
    seen = set()
    for q in QUERIES:
        body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results",
                "ddoKey": "refineSearch", "sortBy": "Most recent", "subsearch": "", "from": 0, "jobs": True,
                "counts": False, "all_fields": [], "size": 50, "clearAll": False, "jdsource": "facets",
                "isSliderEnable": False, "pageId": "page20", "siteType": "external", "keywords": q,
                "global": True, "selected_fields": {}, "locationData": {}, "refNum": ref}
        d = post(f"https://{host}/widgets", body) or {}
        for j in ((d.get("refineSearch") or {}).get("data") or {}).get("jobs", []):
            if j.get("jobId") in seen:
                continue
            seen.add(j.get("jobId"))
            yield dict(ats="phenom", company=name, id=f"{name.split()[0][:4]}-{j.get('jobId')}",
                       title=j.get("title", ""), location=j.get("location") or j.get("cityStateCountry", ""),
                       url=f"https://{host}/us/en/job/{j.get('jobId')}", posted=ts(j.get("postedDate")),
                       desc=text(j.get("descriptionTeaser")) + " " + " ".join(j.get("ml_skills") or []))



# Oracle Recruiting Cloud sites (JPMorgan Chase is big in Plano, NYC and Jersey City).
ORACLE = {"jpmorgan chase": ("jpmc.fa.oraclecloud.com", "CX_1001", "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/"),
          "oracle": ("eeho.fa.us2.oraclecloud.com", "CX_45001", "https://careers.oracle.com/jobs/#en/sites/jobsearch/job/")}


def from_oracle(name):
    host, site, link = ORACLE[name]
    seen = set()
    for q in QUERIES[:5] + QUERIES[6:]:
        u = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
             f"&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber={site},limit=100,"
             f"keyword=%22{urllib.parse.quote(q)}%22,sortBy=POSTING_DATES_DESC")
        d = get(u) or {}
        for r in (d.get("items") or [{}])[0].get("requisitionList", []):
            if r.get("Id") in seen:
                continue
            seen.add(r.get("Id"))
            locs = [r.get("PrimaryLocation") or ""] + [x.get("Name", "") for x in r.get("secondaryLocations") or []]
            yield dict(ats="oracle", company=name, id=f"orc-{name.split()[0]}-{r.get('Id')}", title=r.get("Title", ""),
                       location="; ".join(l for l in locs if l), url=link + str(r.get("Id")), posted=ts(r.get("PostedDate")),
                       desc=text(r.get("ShortDescriptionStr")))


def from_apple(_):
    seen = set()
    for q in ["machine learning", "AI engineer", "generative AI", "software engineer python", "data engineer"]:
        for page in (1, 2):
            s = get_html("https://jobs.apple.com/en-us/search?" + urllib.parse.urlencode(
                {"search": q, "sort": "newest", "location": "united-states-USA", "page": page}))
            m = re.search(r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\((".*?")\);', s, re.S)
            if not m:
                break
            try:
                rows = json.loads(json.loads(m.group(1)))["loaderData"]["search"]["searchResults"]
            except (ValueError, KeyError, TypeError):
                break
            for x in rows:
                if x.get("positionId") in seen:
                    continue
                seen.add(x.get("positionId"))
                yield dict(ats="apple", company="apple", id=f"apl-{x.get('positionId')}", title=x.get("postingTitle", ""),
                           location="; ".join(l.get("name", "") for l in x.get("locations") or []),
                           url=f"https://jobs.apple.com/en-us/details/{x.get('positionId')}/{x.get('transformedPostingTitle', '')}",
                           posted=ts(x.get("postDateInGMT")), desc=text(x.get("jobSummary")))



def _ld_salary(b):
    try:
        v = b.get("value") or {}
        lo, hi, unit = v.get("minValue"), v.get("maxValue"), (v.get("unitText") or "YEAR").upper()
        if not lo:
            return ""
        per = "/hr" if unit.startswith("HOUR") else ""
        return f" SALARY: ${lo}{per}" + (f" - ${hi}{per}" if hi else "")
    except AttributeError:
        return ""


SAL = re.compile(r"\$\s?(\d{5,6}(?!\d)|\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d)?\s?[kK](?![a-z])|\d{2,3}(?:\.\d{1,2})?)(?:\s?(?:/\s?(?:hr|hour)|per hour|an hour))?"
                 r"(?:\s?(?:-|–|—|to)\s?\$?\s?(\d{5,6}(?!\d)|\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d)?\s?[kK](?![a-z])|\d{2,3}(?:\.\d{1,2})?))?"
                 r"(\s?(?:/\s?(?:hr|hour)|per hour|an hour|hourly))?", re.I)


def _num(x):
    x = x.replace(",", "").replace(" ", "").lower()
    return float(x[:-1]) * 1000 if x.endswith("k") else float(x)


def salary(desc):
    """Best salary range in the text as (label, annual_min_usd)."""
    best = None
    for m in SAL.finditer(desc or ""):
        try:
            lo = _num(m.group(1))
            hi = _num(m.group(2)) if m.group(2) else None
        except ValueError:
            continue
        if re.match(r"\s*(million|billion|mm\b|m\b|bn\b)", desc[m.end():m.end() + 10], re.I):
            continue
        hourly = bool(m.group(3)) or "/hr" in m.group(0).lower() or "hour" in m.group(0).lower()
        if hourly and 20 <= lo <= 250:
            ann, label = lo * 2080, f"${lo:g}" + (f"–{hi:g}" if hi else "") + "/hr"
        elif 40000 <= lo <= 900000:
            ann, label = lo, f"${lo/1000:.0f}k" + (f"–{hi/1000:.0f}k" if hi and hi >= lo else "")
        else:
            continue
        if best is None or (m.group(2) and not best[2]):
            best = (label, int(ann), bool(m.group(2)))
    return (best[0], best[1]) if best else ("", 0)


def job_type(title, desc):
    t = (title + " " + (desc or "")[:1500]).lower()
    if re.search(r"\(contractor|\bcontract(-to-hire| to hire)?\b|\bc2h\b|\bw2\b|\b1099\b|duration[: ]", t):
        return "contract-to-hire" if re.search(r"contract[- ]to[- ]hire|\bc2h\b|right to hire", t) else "contract"
    if re.search(r"part[- ]time", title.lower()):
        return "part time"
    return "full time"


def area(loc):
    l = loc.lower()
    for name, rx in AREAS:
        if re.search(rx, l):
            return name
    if "remote" in l:
        return "Remote"
    return "Other US"


def apply_profile(path):
    """Override the search (queries, Dice locations, Google cities, areas) from profile.json if present."""
    global QUERIES, DICE_LOCS, GOOGLE_CITIES, AREAS, LOC_IN
    try:
        srch = json.load(open(path)).get("search") or {}
    except Exception:
        srch = {}
    QUERIES = srch.get("queries") or QUERIES
    DICE_LOCS = srch.get("diceLocations") or DICE_LOCS
    GOOGLE_CITIES = [tuple(x) for x in srch.get("googleCities") or GOOGLE_CITIES]
    AREAS = [tuple(x) for x in srch.get("areas") or AREAS]
    LOC_IN = re.compile("|".join([rx for _, rx in AREAS] + ["remote"]), re.I)


SPONSORS, SPONSOR_KEYS, SPONSOR_SUF = {}, [], ""


def load_sponsors(path):
    global SPONSORS, SPONSOR_KEYS, SPONSOR_SUF
    try:
        d = json.load(open(path))
        SPONSORS, SPONSOR_SUF = d["employers"], d["suffix_regex"]
        SPONSOR_KEYS = sorted(SPONSORS)
    except (OSError, ValueError, KeyError):
        pass


def sponsor(company):
    """Past H-1B (LCA) filings for this employer from DOL data: [filings, last_fy, median_wage] or None."""
    if not SPONSORS:
        return None
    import bisect
    n = company.lower().replace("&", " and ")
    n = re.sub(SPONSOR_SUF, " ", re.sub(r"[^a-z0-9 ]", " ", n))
    w = n.split()
    for k in range(len(w), 0, -1):
        key = "".join(w[:k])
        if len(key) < 5:
            break
        if key in SPONSORS:
            return SPONSORS[key]
        i, best = bisect.bisect_left(SPONSOR_KEYS, key), None
        while i < len(SPONSOR_KEYS) and SPONSOR_KEYS[i].startswith(key):
            v = SPONSORS[SPONSOR_KEYS[i]]
            best = v if not best or v[0] > best[0] else best
            i += 1
        if best:
            return best
    return None


FETCH = {"greenhouse": from_greenhouse, "lever": from_lever, "ashby": from_ashby, "amazon": from_amazon,
         "microsoft": from_microsoft, "workday": from_workday, "google": from_google, "hn": from_hn,
         "dice": from_dice, "phenom": from_phenom,
         "oracle": from_oracle, "apple": from_apple}


FIT = [(re.compile(r"forward[- ]deployed|deployment engineer|applied ai|ai engineer|agent", re.I), 3),
       (re.compile(r"\bllm|generative|genai|\bai\b", re.I), 2),
       (re.compile(r"solutions? (engineer|architect)|customer engineer|founding engineer|machine learning|\bml\b|"
                   r"software|backend|back[- ]end|full[- ]?stack|python|data engineer|data platform|platform engineer|"
                   r"site reliability|\bsre\b|production engineer", re.I), 1)]


def fit(title):
    return max([w for rx, w in FIT if rx.search(title)] or [0])


def keep(j, since):
    probe = j["title"] + (" " + (j.get("desc") or "")[:700] if j["ats"] == "hn" else "")
    if re.search(r"\b(8|9|1\d)\+?\s*(years|yrs)", j["title"], re.I):
        return False
    if not TITLE_IN.search(probe) or TITLE_OUT.search(j["title"].split("|")[1] if j["ats"] == "hn" and "|" in j["title"] else j["title"]):
        return False
    if not LOC_IN.search(j["location"]) or (LOC_OUT.search(j["location"]) and not (
            any(re.search(rx, j["location"], re.I) for _, rx in AREAS) or re.search(r"united states|\bus\b|usa", j["location"], re.I))):
        return False
    return since is None or (j["posted"] and j["posted"] >= since)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=3)
    ap.add_argument("--out", default="jobs.json")
    ap.add_argument("--sponsors", default="h1b_sponsors.json")
    ap.add_argument("--profile", default="profile.json")
    a = ap.parse_args()
    apply_profile(a.profile)
    load_sponsors(a.sponsors)
    global DICE_DAYS
    DICE_DAYS = max(1, int(a.days + 0.99)) if a.days > 0 else 7
    since = datetime.now(timezone.utc).timestamp() - a.days * 86400
    since = datetime.fromtimestamp(since, tz=timezone.utc) if a.days > 0 else None
    tasks = [(ats, s) for ats, slugs in BOARDS.items() for s in slugs.split()]
    tasks += [("workday", s) for s in WORKDAY.split()] + [("amazon", "-"), ("microsoft", "-"), ("google", "-"), ("hn", "-")]
    tasks += [("dice", f"{l}|{q}") for l in DICE_LOCS for q in QUERIES] + [("phenom", n) for n in PHENOM]
    tasks += [("oracle", n) for n in ORACLE] + [("apple", "-")]
    jobs, failed = [], []
    with cf.ThreadPoolExecutor(32) as ex:
        futs = {ex.submit(lambda t: list(FETCH[t[0]](t[1])), t): t for t in tasks}
        for f in cf.as_completed(futs):
            try:
                rows = f.result()
            except Exception:
                rows = []
            if not rows:
                failed.append(futs[f][1])
            jobs += [j for j in rows if keep(j, since)]
    uniq = {}
    for j in jobs:
        uniq.setdefault(j["id"], j)
    jobs = list(uniq.values())
    out = []
    for j in sorted(jobs, key=lambda j: (fit(j["title"]), j["ats"] not in ("dice", "phenom"),
                                         j["posted"] or datetime.min.replace(tzinfo=timezone.utc)),
                    reverse=True):
        desc = j.pop("desc", "") or ""
        m = NO_VISA.search(desc)
        visa = "no-sponsorship" if m else ("sponsors" if YES_VISA.search(desc) else "unknown")
        j["fit"] = fit(j["title"])
        sal, salmin = salary(desc)
        sp = sponsor(WD_NAMES.get(j["company"], j["company"]))
        j.update(salary=sal, salaryMin=salmin, type=job_type(j["title"], desc), area=area(j["location"]),
                 h1bFilings=sp[0] if sp else 0, h1bLastFY=sp[1] if sp else 0)
        j.update(posted=j["posted"].date().isoformat() if j["posted"] else "", visa=visa,
                 visa_evidence=desc[max(0, m.start() - 60): m.end() + 60] if m else "",
                 summary=desc[:900], location=j["location"][:200])
        out.append(j)
    json.dump({"generated": datetime.now(timezone.utc).isoformat(), "days": a.days, "count": len(out),
               "boards_without_jobs": sorted(failed), "jobs": out}, open(a.out, "w"), indent=1)
    print(f"{len(out)} matching roles from {len(tasks)} boards ({len(failed)} empty or failed) -> {a.out}")


if __name__ == "__main__":
    main()
