# Rolewright

An AI job-search agent that runs on your own Claude subscription. Twice a day it scans about 270 job boards,
writes a message for every role that fits, finds the recruiter's published email, tailors your resume and
cover letter without inventing anything, and keeps a tracker you can work through in ten minutes a day.
It never sends anything for you: every email and application goes out only when you click.

Built by [Karthik Kasukurti](https://github.com/dev-null-k2).

## What it does

**Finds roles**
- Scans Greenhouse, Lever, Ashby, Workday, Amazon, Microsoft, Google, Apple, Oracle, JPMorgan, Hacker News
  "Who is hiring", Dice and the TEKsystems / Actalent / Aston Carter staffing sites, twice a day.
- Reads your LinkedIn, Indeed and Glassdoor job-alert emails (read-only) so those roles land in the tracker too.
- Scores every role 1–5 against your resume and explains the score. Roles that match 4/5 or better come first.
- Shows pay when the posting lists it, contract vs full time, and the employer's past H-1B filings
  (US Department of Labor data) for people who need sponsorship.
- One switch for **direct employers** vs **staffing & contract** roles.

**Writes for you, from your facts only**
- A short, specific message for every role, plus follow-ups, referral asks, interview prep, a cover letter
  and a "Why this company?" answer for the best ones.
- A tailored resume per top role. Every change against your original is marked on the page itself
  (green added, red removed, moved lines tagged), and one click switches a role back to your original.
- A checker blocks anything with a number that isn't on your resume, clichés, your location, visa or
  work-authorization mentions, or a wrong signature. The page will not offer a message that fails it.

**Finds the right person**
- Uses the recruiter email the posting itself publishes, and only after checking the domain has a working
  mail server. Nothing is guessed.
- For big employers that don't publish emails, lists recruiters and hiring managers found through public web
  search, for you to message on LinkedIn yourself.
- Matches people from your LinkedIn connections export for warm introductions.

**Keeps you moving**
- **Today's 10**: your best roles one at a time. Email, copy to LinkedIn, skip with a reason, next.
  Press `F` to start, `?` for all keyboard shortcuts.
- An hourly inbox check updates statuses from recruiter emails and drafts replies.
- A pipeline view, a weekly review with reply rates, and an **Ask** box that can search, explain and update
  everything in plain English.
- An **Apply kit** with ready answers to the questions application forms always ask.

## What it will not do
- Send email, submit applications or message anyone. You press Send.
- Log in to or scrape LinkedIn. LinkedIn has no public API for this, and scraping breaks its terms.
- Answer work-authorization questions. Those are always yours.

## How it runs
Everything runs inside your Claude account:
- **The tracker** is a private Claude artifact (`app/rolewright.html`) with its own small database.
- **The agent** is three Claude scheduled tasks (`scheduled_tasks/`) that follow `agent/RUNBOOK.md` and use the
  Python scripts in `agent/`.
- **Your facts** live in your Claude Project: `profile.json`, `profile.md` and `RESUME_MASTER.md`.

You need a Claude plan with the desktop app (Cowork or Claude Code), artifacts, scheduled tasks and the Gmail
connector. Each scan uses your normal Claude usage.

## Set up (about 15 minutes)
See [SETUP.md](SETUP.md). In short: fill in your profile and resume, then ask Claude to set it up.

## Repository layout
| Path | What it is |
|---|---|
| `app/rolewright.html` | The tracker page (publish it as a Claude artifact) |
| `agent/RUNBOOK.md` | What the scheduled scan does, step by step |
| `agent/scan_jobs.py` | The job-board scanner |
| `agent/find_contacts.py` | Finds published recruiter emails and checks their mail servers |
| `agent/linkedin_posts.py` | Dates and filters public LinkedIn posts found by web search |
| `agent/check_drafts.py` | The checker every message, resume and cover letter must pass |
| `agent/h1b_sponsors.json` | Past H-1B filings by employer (public US Department of Labor data) |
| `config/` | Templates for your profile, resume and application answers |
| `scheduled_tasks/` | The three scheduled-task prompts |

## License
MIT. See [LICENSE](LICENSE).
