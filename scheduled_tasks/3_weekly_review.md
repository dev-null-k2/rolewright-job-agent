# Scheduled task: Rolewright weekly review

Schedule: Sunday evening, for example `CRON_TZ=<your time zone> 23 18 * * 0`. Turn on push notifications.
Connectors: Gmail (read-only). Attach the Claude Project that holds the `rolewright/` files.

## Prompt (replace <TRACKER_URL>)

Weekly review of the job search. Work unattended; read-only on Gmail; never send anything.

1. Read `rolewright/RUNBOOK.md` from the attached project for context.
2. With the ArtifactData tool (load via ToolSearch "select:ArtifactData"), read the `jobs` and `contacts` collections of <TRACKER_URL> (list with out_dir, page with cursor).
3. Compute for the last 7 days and all time: roles found, messaged, applied, replies (contacts replied/scheduled or jobs moved to interviewing), interviews, rejections, offers; reply rate by source (direct employer vs staffing), by role type, by area, and by draft style (opening sentence pattern). List skip reasons by count.
4. Write `meta/weekly` (set; get it first and pass if_version if it exists) with fields date (today) and text: at most 12 short plain lines: the funnel, what is working (highest reply-rate segments), what is not, 3 concrete changes for next week, and the 5 best roles still unmessaged (company, title, score).
5. If a change is clearly supported by the numbers (at least 10 messages in each compared group), add it as a dated bullet under a "## Learned from results" section at the end of `rolewright/RUNBOOK.md` (project_read, append, project_write the whole file). Never change any other part of the runbook.
6. Reply with the same 12 lines.
