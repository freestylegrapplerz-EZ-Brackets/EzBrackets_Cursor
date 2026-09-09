# EZ Brackets · v1.5

A guided workspace for finding alone-athlete and team-only divisions, reviewing alternatives, and handing staff a clear action plan.

## The director workflow

1. **Load:** try the practice event, import a Smoothcomp CSV, map another system's columns, or restore a saved event.
2. **Review:** compare one decision at a time. Add an option to the plan, decide later, or ask a director. Missing information requires acknowledgment; options outside the selected rules cannot be accepted.
3. **Apply:** follow the per-athlete Copy or Move checklist in Smoothcomp, then mark the action applied.
4. **Finish:** check unfinished decisions, download the staff checklist, save the event, and load an updated export to verify actions.

EZ Brackets does not update Smoothcomp or generate/publish its brackets. Scores rank options; they are not safety guarantees. Tournament directors remain responsible for event rules, eligibility, required approvals, and publication.

## Run locally

Use **Python 3.12**. From this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On Windows, `Launch_Current_EZ_Brackets.bat` uses an existing local environment. It also recognizes the development environment at `..\.venv-codex` on the original workstation.

The older launcher in the parent `EZ_Brackets` folder launches a different, older `app.py`. Use this checkout and its launcher for v1.5.

## Importing registrations

- CSV imports accept comma, semicolon, and tab separators; UTF-8, UTF-16 with a byte-order mark, and Windows-1252 text.
- Include athlete name, division, team/academy, and approval status. Firstname + Lastname are recognized for Smoothcomp files.
- For another system, map a full division field or its four parts: entry type, belt/experience, age, and weight.
- Missing names/divisions and repeated names within one division block import to prevent ambiguous actions and incorrect counts. Distinguish different athletes with identical names before importing.
- Kilogram labels convert to pounds. Labels without units are assumed to be pounds; verify those labels in the source.
- Files are limited to 15 MB and 25,000 registrations. This is an input limit, not a performance guarantee at that size.
- Missing age, weight, belt/experience, or relevant gender information is flagged on the suggestion. Explicit mixed-gender divisions remain supported.

See [Smoothcomp's CSV export instructions](https://support.smoothcomp.com/article/109-download-registrations-as-a-csv-file).

## Saving and event changes

**Save event & progress** downloads a JSON backup containing normalized registrations, rules, accepted actions, notes, and unfinished decisions. New backups restore without a separate CSV. Legacy v1.0 progress files remain supported and require the matching registration CSV.

This version has **no automatic durable save, accounts, or shared staff workspace**. Streamlit keeps active work in server session memory, which can be lost on disconnect/restart. Download a backup before leaving. Backups contain athlete names and registration details; store and share them appropriately.

Loading another file with progress offers **Same event · keep decisions** or **New event · start fresh**. Practice and real-event plans cannot be combined. Actions already present in a fresh export are not counted twice. Unmatched actions stop further planning until resolved.

**Planned**, **Applied**, and **Verified in export** have different meanings. Applied is your acknowledgment; verification checks the loaded registrations for the expected Copy/Move result.

## Reports

- Staff checklist: accepted actions, Copy/Move instructions, notes, and unfinished decisions.
- Accepted-actions CSV: one row per athlete with application and export-verification status.
- Advanced Excel report: suggestions, alone-athlete divisions, team-only suggestions, and projected division summary. Suggestions are not accepted instructions.
- Spreadsheet exports keep formula-like uploaded text literal.

## Development checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite tests imports, backup validation, projected counts, Copy/Move verification, matching exclusions, export handling, and Streamlit review/apply/restore flows. GitHub Actions runs it on push and pull requests once this branch is pushed.

See [PRODUCT_READINESS.md](PRODUCT_READINESS.md) for the assessment, validation limits, and paid-launch work.
