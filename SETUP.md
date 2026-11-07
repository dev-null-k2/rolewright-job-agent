# Setting up Rolewright

About 15 minutes, and no coding. Claude does the technical steps. You give it your resume and answer a few
questions.

## What you need
- A paid Claude plan (Pro, Max, Team or Enterprise) with the **Claude desktop app** (Mac or Windows). Rolewright
  uses Cowork, Claude Projects, artifacts and scheduled tasks, which all come with the desktop app.
- A **Gmail** account that gets your job emails. Rolewright only reads it.
- Your current resume (PDF, Word or text).

Each scan uses your normal Claude usage, like any other task. There is nothing else to pay for.

---

## Step 1. Nothing to download
Claude fetches Rolewright from GitHub itself in step 4. If it ever can't, download it here: the green **Code**
button on [the GitHub page](https://github.com/dev-null-k2/rolewright-job-agent), then **Download ZIP**, and attach
the ZIP in step 4.

## Step 2. Connect Gmail to Claude
1. In the Claude desktop app open **Settings → Connectors**.
2. Find **Gmail**, click **Connect** and sign in with the Gmail account that gets your job emails.
3. Allow the read permissions it asks for.

Rolewright uses Gmail only to read recruiter replies and job-alert emails. It never sends, replies, labels or deletes
anything.

Optional: if **Claude Code Remote** is listed under Connectors, connect it too. It adds the "Run now" buttons to
the tracker. Everything else works without it.

## Step 3. Create a Claude Project
1. In Claude open **Projects → New project**. Name it **Job search**.
2. Leave it empty. Claude adds the files in the next step.

## Step 4. Let Claude set everything up (one prompt)
1. In the desktop app open **Cowork**, start a **new task**, and choose the **Job search** project for it.
2. Attach **your resume**.
3. Paste this message and send it:

```text
Set up Rolewright for me end to end. Get it from https://github.com/dev-null-k2/rolewright-job-agent
(clone it, or ask me to attach the ZIP if you can't reach GitHub). Read SETUP.md and do everything under
"What Claude does in step 4": ask me the few questions it lists, write my profile from my attached resume
only, save the files to this project, publish my Rolewright tracker, create the three scheduled tasks in my
time zone, run the first job scan, and open the tracker for me when it's done. Never invent anything that
isn't on my resume.
```

Claude asks a few short questions (your target roles, cities or remote, time zone, links, and anything it must
never mention). Then it does the rest by itself. It takes about 20 minutes, mostly the first scan.

When it finishes, Claude opens your **Rolewright** tracker. Press **F** for Today's 10.

## Step 5. Optional extras (recommended)
- **LinkedIn, Indeed and Glassdoor jobs.** Rolewright never logs in to these sites. Turn on their **job-alert
  emails** for your target titles and cities, sent to the Gmail you connected. Every scan reads those emails and adds
  the roles to your tracker.
  - LinkedIn: search a job title, set the location, then turn on **Set alert**. Choose daily email.
  - Indeed and Glassdoor: search a title and location, then **Get new jobs for this search by email**.
- **Warm introductions from your LinkedIn network.** On LinkedIn go to **Settings & Privacy → Data privacy → Get a
  copy of your data**, choose **Connections**, and request it. LinkedIn emails you a link, usually within 10
  minutes. Download the file, then on the tracker's **Outreach** tab upload `Connections.csv`. Rolewright then shows
  who you know at each company and drafts the referral ask.
- **LinkedIn hiring posts.** Nothing to set up. Each scan finds recent public "we're hiring" posts through web search
  and drafts a message to the poster for you to send yourself.
- **Apply kit.** On the tracker's **Apply kit** tab, add the phone number for your email signature (it stays in your browser only), and fill in salary, start date and work setup once. They are then
  ready to copy into any application form.

---

## Using it day to day
- **Each morning (about 10 minutes):** open the tracker and press **F**. For each role you can email the recruiter
  (it opens Gmail with the message already written), copy the LinkedIn message, open the posting, or skip with a
  reason. Nothing is sent until you press Send yourself.
- **Two scans a day** add new roles automatically, at about 5:47 AM and 2:47 PM in your time zone. The **inbox
  watch** checks Gmail every hour and moves roles to "interviewing" or "rejected" when recruiters reply. On Sunday
  evening you get a **weekly review** with your reply rates.
- **Ask box:** type anything in plain English, for example "show contract roles that pay over 150k" or
  "mark Stripe as applied".

## Changing things later
Open a Cowork task in the **Job search** project and ask Claude in plain words:
- "Add Chicago and Austin to my Rolewright search", or "Only remote roles from now on."
- "Here is my updated resume. Update Rolewright with it." Tailored resumes and the change view follow the new version.
- "Pause Rolewright", "Resume Rolewright", or "Run a Rolewright scan now."

## Troubleshooting
| What you see | What to do |
|---|---|
| The tracker says **Finish setup** | Setup stopped before it saved your profile. Open the setup task and ask Claude to finish step 4. |
| No roles after the first scan | Open **Scheduled tasks** in the app, open **Rolewright job scan**, and check the latest run for errors. Ask Claude to run it again. |
| No "Run now" buttons | Claude Code Remote isn't connected. It's optional. You can also ask Claude "Run a Rolewright scan now." |
| Statuses don't update from email | Make sure Gmail is connected (Settings → Connectors) and the **Rolewright inbox watch** task is turned on. |
| A message mentions something you don't want | Add the word to `neverMention` by asking Claude "Never mention X in Rolewright." The checker then blocks it. |

## Privacy
Everything stays in your own Claude account: the tracker is a private artifact, and your profile and resume live in
your private project. Rolewright has no server. Gmail access is read-only. It never logs in to LinkedIn or any job
site, and never sends anything for you.

---

## What Claude does in step 4
These are the instructions Claude follows when you paste the setup message. You don't need to read them.

0. **Get the files**: `git clone https://github.com/dev-null-k2/rolewright-job-agent` (or unzip the attached ZIP) and work from that folder.

1. **Ask the candidate** (one short message, multiple choice where possible): target role types in order; cities
   and/or US remote; time zone; LinkedIn, GitHub and best-project links (optional); anything never to mention
   (their city and state are always included). Use their answers and the attached resume only. Never invent a role,
   number, skill or story.
2. **Write the facts files** from the resume and answers:
   - `RESUME_MASTER.md`: the resume converted to markdown exactly as written (follow
     `config/RESUME_MASTER.example.md` for shape; change no facts or numbers).
   - `profile.md`: fill `config/profile.example.md`. Each "strongest claim" uses only facts and numbers from the
     resume.
   - `profile.json`: fill `config/profile.example.json`. Set `search.queries` from the target roles,
     `search.diceLocations`, `search.googleCities` and `search.areas` from the cities (always keep remote), `timezone`,
     and `neverMention` with their city, state and anything else they listed.
   Show the candidate a short summary and fix anything they correct.
3. **Save to the project** with the Projects tool (`project_write`, explicit paths): `rolewright/RUNBOOK.md`,
   `rolewright/scan_jobs.py`, `rolewright/find_contacts.py`, `rolewright/linkedin_posts.py`,
   `rolewright/check_drafts.py`, `rolewright/h1b_sponsors.json` (all from `agent/`), and `rolewright/profile.json`,
   `rolewright/profile.md`, `rolewright/RESUME_MASTER.md`. Use `local_path` for large files.
4. **Publish the tracker**: publish `app/rolewright.html` as an artifact titled **Rolewright** with capabilities
   `{"db": {}, "user": {}, "sample": {}, "downloads": true, "mcp": {"servers": [{"server": "Gmail", "tools": ["search_threads", "get_thread"]}, {"server": "Claude Code Remote", "tools": ["fire_trigger"]}]}}`.
   Leave out the Claude Code Remote entry if that connector isn't available.
5. **Fill the tracker database** (ArtifactData): `meta/resume` = `{"text": <RESUME_MASTER.md>}`; `meta/answers` from
   `config/answers.example.json`, drafting every answer that is not `fillOnce` or `yours` from the resume and
   profile.md only.
6. **Create the three scheduled tasks** from `scheduled_tasks/` in the candidate's time zone. Replace `<TRACKER_URL>`
   with the artifact URL, attach the **Job search** project and the Gmail connector (plus Claude Code Remote if
   connected), and turn on push notifications for the weekly review.
7. **Finish the profile**: put the artifact URL and the job-scan and inbox-watch task ids into `profile.json`
   (`trackerUrl`, `scanTaskId`, `inboxTaskId`), save it back to `rolewright/profile.json`, and set `meta/profile` in
   the tracker to the same JSON with `areas` copied from `search.areas`.
8. **Run the job scan once now** (fire the job-scan task, or follow its prompt directly in this session). When it finishes, open the tracker for the candidate with the Artifact tool and tell them in two lines how
   to use it: press F for Today's 10, and fill the Apply kit once.
