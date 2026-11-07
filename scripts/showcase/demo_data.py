#!/usr/bin/env python3
"""Fictional demo data for the README screenshots. Every person and company here is made up.

Usage: python3 demo_data.py > demo.json
"""
import json
from datetime import date, timedelta

TODAY = date(2026, 11, 9)
d = lambda n: (TODAY - timedelta(days=n)).isoformat()
NAME = "Maya Chen"

RESUME = """## Summary
Software engineer with 4+ years building production ML and data systems. I ship a first version in days and improve it with the people who use it.

## Experience
### Senior Software Engineer, Fieldstone Analytics (2023 to present)
- Built an LLM support assistant used by 120+ analysts, cutting average ticket time from 5 hours to 90 minutes
- Designed a retrieval pipeline over 2M+ documents with evals run on every change
- Cut p95 API latency 42% by moving hot paths to async Python and caching
- Led a team of 4 engineers through the rollout and on-call

### Software Engineer, Brightwell Logistics (2021 to 2023)
- Built Spark pipelines processing 3B+ events a month for routing models
- Shipped a demand-forecasting service that saved 1,200+ planner hours a year
- Moved 30+ batch jobs to Airflow with alerting and retries

## Skills
Python, TypeScript, FastAPI, PostgreSQL, Spark, Airflow, AWS, Docker, LLM evals, retrieval

## Education
B.S. Computer Science, Lakeshore University (2021)
"""

PROFILE = {
    "name": NAME, "email": "maya.chen@example.com", "linkedin": "linkedin.com/in/maya-chen-demo",
    "github": "github.com/maya-chen-demo", "portfolioLink": "github.com/maya-chen-demo/support-assistant",
    "tagline": "AI, backend and data roles · Seattle, Austin, US remote", "timezone": "America/Los_Angeles",
    "neverMention": [], "neverClaim": [],
    "areas": [["Seattle", "seattle|bellevue|redmond|kirkland"], ["Austin", "austin|round rock"]],
}

LEAD = {
    "ai": "I already build this. At Fieldstone I shipped an LLM support assistant that 120+ analysts use, and it cut average ticket time from 5 hours to 90 minutes. I run evals on every change, so quality goes up, not sideways.",
    "data": "I build the pipelines models depend on. At Brightwell I ran Spark jobs over 3B+ events a month and shipped a forecasting service that saved 1,200+ planner hours a year.",
    "backend": "I make APIs fast and boring. At Fieldstone I cut p95 latency 42% by moving hot paths to async Python and caching, and I led 4 engineers through the rollout and on-call.",
}
ASK = ["Worth a short call this week?", "Could we talk Thursday or Friday?", "Open to a short call this week?"]

ROLES = [
    # company, title, location, kind, score, status, salary, salaryMin, fit, contact
    ("Northwind AI", "Forward Deployed Engineer", "Seattle, WA", "ai", 5, "new", "$165k to $205k", 165000, 3, ("Dana", "Dana Okafor", "Technical Recruiter")),
    ("Lumen Labs", "Applied AI Engineer", "Remote, US", "ai", 5, "new", "$170k to $210k", 170000, 3, None),
    ("Harborline Health", "AI Engineer, Clinical Workflows", "Austin, TX", "ai", 5, "new", "$155k to $190k", 155000, 3, ("Priya", "Priya Raman", "Engineering Manager")),
    ("Quarry Data", "Senior Data Engineer", "Seattle, WA", "data", 4, "new", "$160k to $195k", 160000, 1, None),
    ("Arclight Systems", "Backend Engineer, Platform", "Remote, US", "backend", 4, "new", "$150k to $185k", 150000, 1, ("Leo", "Leo Martins", "Recruiter")),
    ("Pinecrest Robotics", "ML Engineer, Perception Data", "Austin, TX", "data", 4, "new", "", 0, 2, None),
    ("Tidewater Bank", "Software Engineer, GenAI", "Seattle, WA", "ai", 4, "new", "$145k to $175k", 145000, 2, None),
    ("Keystone Talent", "Python Developer (W2 contract)", "Remote, US", "backend", 3, "new", "$70 to $85 an hour", 145600, 1, ("Sam", "Sam Patel", "Technical Recruiter")),
    ("Fieldnote", "Full Stack Engineer, AI Features", "Remote, US", "ai", 4, "new", "$140k to $170k", 140000, 2, None),
    ("Copperleaf Energy", "Data Platform Engineer", "Austin, TX", "data", 3, "new", "$135k to $160k", 135000, 1, None),
    ("Orchard Learning", "Backend Engineer", "Seattle, WA", "backend", 3, "new", "", 0, 1, None),
    ("Saltmarsh Insurance", "Machine Learning Engineer", "Remote, US", "ai", 3, "new", "$150k to $180k", 150000, 2, None),
    ("Bluejay Commerce", "Software Engineer II, Search", "Seattle, WA", "backend", 3, "new", "$140k to $165k", 140000, 1, None),
    ("Granite Cloud", "Site Reliability Engineer", "Austin, TX", "backend", 2, "new", "", 0, 1, None),
    ("Meridian Freight", "Data Engineer", "Remote, US", "data", 3, "new", "$130k to $155k", 130000, 1, None),
    ("Sparrow Health", "Applied Scientist, LLMs", "Seattle, WA", "ai", 4, "messaged", "$175k to $215k", 175000, 3, ("Alex", "Alex Kim", "Recruiter")),
    ("Redwood Analytics", "AI Solutions Engineer", "Remote, US", "ai", 5, "applied", "$160k to $190k", 160000, 3, None),
    ("Cobalt Payments", "Backend Engineer, Risk", "Austin, TX", "backend", 4, "applied", "$150k to $180k", 150000, 1, None),
    ("Lattice Grid", "Data Engineer, Forecasting", "Seattle, WA", "data", 4, "interviewing", "$155k to $185k", 155000, 1, ("Jordan", "Jordan Ellis", "Hiring Manager")),
    ("Beacon Legal AI", "Forward Deployed Engineer", "Remote, US", "ai", 5, "interviewing", "$170k to $200k", 170000, 3, None),
    ("Stonebridge Retail", "Software Engineer", "Austin, TX", "backend", 2, "rejected", "", 0, 1, None),
    ("Wavecrest Media", "ML Platform Engineer", "Remote, US", "ai", 3, "messaged", "", 0, 2, None),
]

WHY = {
    "ai": "AI role building LLM features with customers; matches the support assistant and the eval work",
    "data": "Data engineering on large event pipelines; matches the Spark and forecasting work",
    "backend": "Backend API role; matches the latency and on-call work",
}


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


jobs = []
for i, (co, title, loc, kind, score, status, sal, smin, fit, contact) in enumerate(ROLES):
    first = contact[0] if contact else None
    hi = f"Hi {first}," if first else "Hi [Name],"
    staffing = co == "Keystone Talent"
    if staffing:
        draft = (f"{hi} The Python Developer contract fits my work. {LEAD['backend']} "
                 "Could you share the client and the rate range?")
    else:
        team = {"ai": "your team is putting LLM features in front of real users", "data": "your team owns the data that every model runs on",
                "backend": "your team runs the APIs everything else depends on"}[kind]
        draft = f"{hi} {team}. {LEAD[kind]} {ASK[i % 3]}"
    j = {
        "id": f"gh-{slug(co)}-{slug(title)}"[:70] if not staffing else f"dice-{slug(co)}-{slug(title)}"[:70],
        "company": slug(co), "companyName": co, "title": title, "location": loc,
        "posted": d(i % 6), "found": d(i % 4), "status": status, "fit": fit, "score": score,
        "scoreWhy": {5: "Asks for exactly what she has shipped: production LLM work with users, evals, Python", 4: "Strong overlap on stack and scope; one gap in domain", 3: "Good stack match; role is broader than her focus", 2: "Partial match"}[score],
        "why": WHY[kind] + (" (staffing firm, W2 contract)" if staffing else ""),
        "url": f"https://example.com/jobs/{slug(co)}/{i}", "visa": "unknown", "ats": "dice" if staffing else "greenhouse",
        "type": "contract" if staffing else "full time",
        "draft": draft, "draftV": 3, "subject": f"{title.replace(' (W2 contract)', '')} – {NAME}",
        "resumeTip": "Lead with the support assistant result and the evals",
        "contactSearch": f"https://www.linkedin.com/search/results/people/?keywords={slug(co)}%20recruiter",
    }
    if sal:
        j["salary"], j["salaryMin"] = sal, smin
    if contact:
        j.update(contactName=contact[1], contactTitle=contact[2], contactKind="person",
                 contactEmail=f"{contact[1].split()[0].lower()}@{slug(co).replace('-', '')}.example.com",
                 contactSource="Greenhouse posting", contactVerified=d(0))
    if status != "new":
        j["statusAt"] = d(3)
    if status in ("messaged", "applied"):
        j["followUp"] = d(-2)
    jobs.append(j)

# Tailored resumes, cover letters and people to try for the top roles
top = [j for j in jobs if j["score"] == 5]
for j in top:
    j["resumeVersion"] = RESUME.replace(
        "## Summary\nSoftware engineer with 4+ years building production ML and data systems.",
        "## Summary\nSoftware engineer with 4+ years shipping production LLM and data systems with the people who use them.").replace(
        "- Moved 30+ batch jobs to Airflow with alerting and retries\n", "").replace(
        "Python, TypeScript, FastAPI, PostgreSQL, Spark, Airflow, AWS, Docker, LLM evals, retrieval",
        "Python, LLM evals, retrieval, FastAPI, TypeScript, PostgreSQL, Spark, Airflow, AWS, Docker")
    j["resumeChanges"] = "Summary aimed at applied AI; skills reordered to lead with LLM evals and retrieval"
    j["coverLetter"] = (f"Dear Hiring Team,\n\nYour team at {j['companyName']} is putting AI in front of real users, and that is the work I do today. "
                        "At Fieldstone I built an LLM support assistant that 120+ analysts use every day, and I worked side by side with them "
                        "to decide what it should do first, then improved it every week from what they told me.\n\n"
                        "The result that matters most for this role: average ticket time fell from 5 hours to 90 minutes, and I run evals on every "
                        "change so quality keeps going up as the system grows. I also cut p95 API latency 42% and led 4 engineers through the rollout and on-call. "
                        "Before that I built Spark pipelines over 3B+ events a month at Brightwell and shipped a forecasting service that saved 1,200+ planner hours a year.\n\n"
                        f"I would like to talk about how I can help your customers ship AI they trust. Could we find time for a short call this week?\n\n{NAME}")
    j["whyCompany"] = f"{j['companyName']} is building the kind of AI product I already ship, with real users and real evals."
    j["linkedinPeople"] = [{"name": "Riley Moore", "headline": f"Technical Recruiter at {j['companyName']}", "url": "https://www.linkedin.com/in/example"}]

for j in jobs:
    if j["companyName"] == "Beacon Legal AI":
        j["prep"] = ("What they build: AI assistants for legal teams, deployed inside each customer.\n"
                     "Likely questions: 1) A system you shipped with users. Use the support assistant. 2) How you measure quality. Use the evals. "
                     "3) A time latency mattered. Use the 42% p95 cut.\nAsk them: how they pick the first customer workflow, how they run evals per customer.")

contacts = [
    {"id": "c1", "name": "Jordan Ellis", "company": "Lattice Grid", "role": "Hiring Manager", "email": "jordan@latticegrid.example.com",
     "status": "scheduled", "lastAt": d(1), "summary": "Invited you to a technical interview on Wednesday at 11:00.",
     "reply": "Hi Jordan,\n\nWednesday at 11:00 works well. Looking forward to it.\n\nMaya"},
    {"id": "c2", "name": "Alex Kim", "company": "Sparrow Health", "role": "Recruiter", "email": "alex@sparrowhealth.example.com",
     "status": "replied", "lastAt": d(2), "summary": "Asked for your availability for a 30-minute intro call.",
     "reply": "Hi Alex,\n\nThanks for getting back to me. Tuesday or Thursday afternoon both work. Which suits you?\n\nMaya"},
]

hiring = [
    {"id": "lip-7392000000000000001", "url": "https://www.linkedin.com/posts/example-activity-7392000000000000001", "postedAt": d(1),
     "poster": "Chris Lane", "company": "Northwind AI", "role": "Applied AI Engineer", "area": "Seattle", "status": "new", "found": d(0),
     "text": "We're hiring applied AI engineers in Seattle to build agents with our customers.",
     "draft": "Hi Chris, your post about building agents with customers is exactly my work. At Fieldstone I shipped an LLM support assistant that 120+ analysts use, cutting ticket time from 5 hours to 90 minutes. Worth 15 minutes this week?"},
]

network = [{"id": "chunk-0", "rows": [{"n": "Taylor Brooks", "c": "Northwind AI", "p": "Staff Engineer", "u": "https://www.linkedin.com/in/example-tb"},
                                    {"n": "Morgan Diaz", "c": "Redwood Analytics", "p": "Product Manager", "u": "https://www.linkedin.com/in/example-md"}]}]

meta = {
    "profile": PROFILE,
    "resume": {"text": RESUME},
    "scan": {"lastScan": d(0), "lastScanAt": f"{d(0)}T13:47:12Z", "boards": 271, "newToday": 15, "total": len(jobs)},
    "inbox": {"lastCheckAt": f"{d(0)}T15:13:40Z", "summary": "2 recruiter replies: Lattice Grid interview Wednesday, Sparrow Health intro call."},
    "weekly": {"week": d(1), "text": "This week: 14 messages sent, 5 replies (36%), 2 interviews. Best reply rate: AI roles with a published recruiter email."},
    "answers": {"updated": d(0), "items": [
        {"id": "about", "q": "Tell us about yourself", "a": "I'm a software engineer with 4+ years building production ML and data systems. At Fieldstone I built an LLM support assistant that 120+ analysts use."},
        {"id": "salary", "q": "Salary expectations", "a": "", "fillOnce": True, "hint": "Fill this once."},
        {"id": "workauth", "q": "Work authorization / sponsorship questions", "a": "", "yours": True, "hint": "Always answer these yourself."}]},
}

json.dump({"jobs": jobs, "contacts": contacts, "hiringPosts": hiring, "posts": [], "network": network, "meta": meta}, __import__("sys").stdout, indent=1)
