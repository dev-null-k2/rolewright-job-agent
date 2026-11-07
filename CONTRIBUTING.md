# Contributing to Rolewright

Thanks for helping. Rolewright is small on purpose, so a short issue before a large change saves everyone time.

## Good first contributions
- A job board or careers site the scanner misses (add it to `agent/scan_jobs.py`).
- A false positive or false negative in the draft checker (`agent/check_drafts.py`), with the draft that triggered it.
- Clearer wording anywhere in the tracker page (`app/rolewright.html`) or the docs.

## Ground rules
- **Never invent facts.** Anything Rolewright writes must come from the user's own files. Changes that loosen the
  checker need a clear reason.
- **Never send for the user.** No code path may send email, submit an application or message anyone.
- **No scraping behind logins.** Use public pages, public APIs and the user's own read-only email.
- **No personal data in the repo.** Use the `config/*.example.*` templates for anything personal.

## Making a change
1. Fork the repository and create a branch.
2. Keep the scripts runnable with the Python 3 standard library only.
3. Run `python3 -m py_compile agent/*.py` and open `app/rolewright.html` in a browser to check nothing broke.
4. Open a pull request that says what changed and how you checked it.
