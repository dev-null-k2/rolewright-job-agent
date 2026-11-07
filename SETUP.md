# Setting up Rolewright

## 1. Fill in your facts (10 minutes)
Copy the three templates in `config/` and fill them in:

| Template | Save as | What goes in it |
|---|---|---|
| `config/profile.example.json` | `profile.json` | Name, contact line, portfolio link, the cities you're searching, words never to mention |
| `config/profile.example.md` | `profile.md` | Your strongest claim for each kind of role, your stack, post topics |
| `config/RESUME_MASTER.example.md` | `RESUME_MASTER.md` | Your current resume in plain markdown |

Rolewright only ever uses what is in these files. If a number isn't on your resume, it will never appear in a
message.

## 2. Create a Claude Project
In Claude, create a project (for example "Job search") and add these files to it, all under a folder named
`rolewright/`:
- everything in `agent/` (`RUNBOOK.md`, the four `.py` files, `h1b_sponsors.json`)
- your `profile.json`, `profile.md` and `RESUME_MASTER.md`

## 3. Connect Gmail
In Claude, connect the Gmail connector. Rolewright only reads mail; it never sends, labels or deletes.

## 4. Ask Claude to finish the setup
Open the Claude desktop app in that project, attach this repository (or the files `app/rolewright.html`,
`config/answers.example.json` and the three files in `scheduled_tasks/`), and paste:

> Set up Rolewright for me:
> 1. Publish `app/rolewright.html` as an artifact named Rolewright with capabilities
>    `{"db": {}, "user": {}, "sample": {}, "downloads": true, "mcp": {"servers": [{"server": "Gmail", "tools": ["search_threads", "get_thread"]}, {"server": "Claude Code Remote", "tools": ["fire_trigger"]}]}}`.
> 2. In its database, set `meta/resume` to `{"text": <my RESUME_MASTER.md>}` and `meta/answers` from
>    `config/answers.example.json`, drafting every answer that is not "fill once" or "answer yourself" from my
>    resume and profile.md only (never invent a story or a number).
> 3. Create the three scheduled tasks in `scheduled_tasks/` in my time zone, replacing `<TRACKER_URL>` with the
>    artifact URL, attaching this project and the Gmail and Claude Code Remote connectors.
> 4. Put the artifact URL and the job-scan and inbox-watch task ids into my `profile.json` (`trackerUrl`,
>    `scanTaskId`, `inboxTaskId`), save it back to the project, and set `meta/profile` to the same JSON with
>    `areas` copied from `search.areas`.
> 5. Run the job scan once now.

When the first scan finishes (about 20 minutes), open the Rolewright artifact. Press `F` for Today's 10.

## 5. Optional, once
- **Warm intros:** on LinkedIn go to Settings, Data privacy, Get a copy of your data, Connections. Upload the
  `Connections.csv` on the Outreach tab.
- **More roles:** turn on LinkedIn and Indeed job-alert emails for your target roles. The scan reads them.
- **Fill once:** salary, start date and work setup on the Apply kit tab.

## Updating your resume
Replace `rolewright/RESUME_MASTER.md` in the project and ask Claude to update `meta/resume` in the tracker.
Tailored resumes made afterwards follow the new version, and the change view compares against it.
