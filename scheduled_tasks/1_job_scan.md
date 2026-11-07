# Scheduled task: Rolewright job scan

Schedule: twice a day, for example `CRON_TZ=<your time zone> 47 5,14 * * *` (5:47 AM and 2:47 PM).
Connectors: Gmail (read-only use), Claude Code Remote. Attach the Claude Project that holds the `rolewright/` files.

## Prompt (paste as the task's message; replace <TRACKER_URL>)

You are running the Rolewright job scan (it runs twice a day). Work unattended; do not ask questions.

1. From the attached Claude project, read `rolewright/RUNBOOK.md` (Projects tool, project_read) and follow its daily steps exactly, including step 2b (job-alert emails from Gmail, read-only). Step 1 of the runbook says which project files to save locally and the exact scanner command to run.
2. The tracker is the artifact <TRACKER_URL>. Read and write its database only with the ArtifactData tool (load it with ToolSearch "select:ArtifactData"): list `jobs` (limit 1000, page with cursor) to skip ids already present; create new docs in `jobs` with a set (no if_version for new docs); update `meta/scan` (get it first and pass its version as if_version) with lastScan, lastScanAt (exact UTC finish time from `date -u +%Y-%m-%dT%H:%M:%SZ`, taken right before the write), boards, newToday (roles added today across both runs) and total. Use batch writes (up to 50 entries each). Never change the `status` of a job unless it is "new" (the user and the inbox watch own status changes); on non-new jobs you may only add the runbook's helper fields (prep, followUpDraft, resumeVersion, resumeChanges, coverLetter, whyCompany, referralTo/referralUrl/referralDraft, closed/closedAt, linkedinPeople). Never rewrite the `draft` or `subject` of a job that has `draftEditedAt` (the user edited it in the page), unless it fails check_drafts.py. The only deletions allowed are the housekeeping deletions in runbook step 5b. Never republish or edit the page itself.
3. Use only the facts in `rolewright/profile.md` and `rolewright/RESUME_MASTER.md`. Never invent numbers, employers or skills. Never mention visa status or where the candidate lives (city, state or time zone) in outreach.
4. On Mondays also add one LinkedIn post draft to `posts` as the runbook describes, only if `posts` has no draft dated today yet.
5. Gmail is read-only: never send, reply, draft, label, archive or delete. Do not send any message, application or connection request anywhere. Drafts only.
6. MANDATORY before finishing: the runbook's Hard check step. Dump `jobs` and `hiringPosts` with out_dir, run check_drafts.py, fix every failure (drafts, tailored resumes, cover letters, contacts) and repeat until it prints "0 of N drafts fail". Write meta/scan after this check, so lastScanAt is the real finish time.
7. End with a short summary: how many new roles were added and from which sources, the top 5 by score (company and title), follow-ups due today from `contacts`, the final checker line, and the tracker link. If a source, the scan or the database fails, say what failed.
