# EZ Brackets: product readiness assessment

September 9, 2026. Baseline: GitHub `main` at `9fa3b94` (PR #19, v1.4.0). Implementation: local v1.5 branch, `codex/novice-readiness`.

## Product judgment

The strongest promise is **help a tournament director resolve problem divisions faster, with understandable reasons and a reliable staff checklist**. The app can teach a beginner the workflow while escalating eligibility and exception decisions to the director.

There is a plausible paid use case, but willingness to pay has not been established. Evidence still needed: real event time saved, fewer missed/incorrect decisions, reliable recovery, and customers choosing to pay after using it.

Smoothcomp already provides registration and bracket management, with published pay-as-you-go pricing of €1.25 per athlete credit and bulk discounts. EZ Brackets must earn an additional purchase through a specific time-saving workflow. Positioning it as a companion for difficult division decisions is my inference from that overlap, not market validation. [Smoothcomp platform and pricing](https://smoothcomp.com/en)

CSV export and Copy/Move remain manual handoffs, documented by Smoothcomp. This version does not apply changes automatically. [CSV export](https://support.smoothcomp.com/article/109-download-registrations-as-a-csv-file), [Copy and Move](https://support.smoothcomp.com/article/84-how-to-search-filter-edit-move-and-copy-a-fighter)

## Implemented in v1.5

| Previous problem | Result |
| --- | --- |
| Automatic sample load and competing dashboards | Explicit practice/upload/restore, then Review → Apply → Finish |
| Beginner terminology and excessive visible controls | Plain definitions, one decision at a time, comparison details on demand, advanced reports under Finish |
| Restoring needed both JSON and CSV | One backup with registrations, rules, notes, and decisions; legacy files supported |
| Sample changes could carry event progress | Explicit event switching and separation of practice and real-event plans |
| Suggestions ignored prior roster changes | Later suggestions use the projected roster after accepted actions |
| Fresh exports could double-count copies | Projection checks actual athlete/division membership and applies each change once |
| A source division's existence could be mistaken for an athlete match | Exact registration evidence; unmatched actions stop further planning |
| Duplicate athlete registrations could be their own opponent | Source/target name overlap excluded |
| Manual-review items became hard to retrieve at completion | Manual items remain unfinished and can return to Review from Finish |
| Some alternatives bypassed missing-data acknowledgment | All options use the same acceptance checks; acknowledgment is tied to the specific option and rules |
| Entire files without gender labels relied on a general notice | Relevant Teen/Adult/Masters suggestions require a data check unless explicitly mixed |
| Weight gaps implied invented class counts or incorrect limit failures | Actual midpoint gaps; blocking follows selected rules |
| Malformed CSVs could crash or misalign fields | Actionable errors, strict row widths, encoding/delimiter support, import preview |
| Missing names became row numbers; duplicates distorted counts | Missing and ambiguous identities block import |
| Navigation could discard rule widgets and stale notes could be saved | Settings persist; note changes update before backup generation |
| Review completion confused with applied changes | Separate review/application/export checks and an unfinished-decision handoff |
| No repeatable regression suite | Tested dependency versions, regression tests, CI configuration |

The original June DEV v2 files in the parent folder were preserved. Nothing was published or deployed.

## Before paid self-service

| Priority | Remaining work | Customer outcome / release evidence |
| --- | --- | --- |
| P0 | Durable autosave and private event ownership | Close the browser, restart the server, and recover the last action; prove users cannot access each other's events |
| P0 | Versioned backups and recovery history | Restore an earlier event revision without overwriting current work; perform recovery drills |
| P0 | Director-approved rule profiles and real export fixtures | Review representative age, belt, weight, gender, approval and exception cases from actual events |
| P0 | Explicit import units and stable registration IDs | Remove unit-less weight assumptions; distinguish identical names and changed names |
| P0 | Production hosting and event-day operations | Monitored deployment, rollback, outage playbook, connectivity testing, realistic concurrency/load tests |
| P0 | Defined privacy, retention, deletion, and support practices | Review athlete-data flows, publish accurate policies, test deletion/export, and set support expectations |
| P1 | Staff accounts, roles, and concurrent-edit protection | Prevent duplicate application and lost edits; maintain an attributable history |
| P1 | Structured coach/director approvals | Record who approved what, when, why, and under which rules; a checkbox and note alone do not establish identity |
| P1 | Complete billing and access flow | Test payment, access, receipts, cancellation, and refunds before production charging |
| P1 | Whole-event alternatives and stale-plan checks | Compare plans; flag affected accepted actions after rules or eligibility change |
| P1 | Revisit copied originals after late arrivals | Identify originals that gained suitable opponents and explicitly review earlier copies |
| P2 | Reusable organizer profiles and event history | Reuse tested rules/mappings while keeping events separate |
| P2 | Product analytics and feedback | Learn where beginners stop without collecting unnecessary athlete information |

A supported pilot can precede self-service once a director validates its rules and the backup process. Adding billing alone would not make the app ready.

## Pilot to test demand

1. Recruit 3–5 directors with upcoming events, including organizers outside Freestyle Grapplerz.
2. Observe a first-time staff member loading, explaining a suggestion, postponing, saving, restoring, and handing off. Record every point where you have to coach them.
3. Time their existing workflow and EZ Brackets on the same representative problem set. Have a director audit the resulting decisions independently.
4. Pilot on real events under director supervision. Keep the original export, backup, applied checklist, and verification export.
5. Offer a paid next-event option. Test per-event pricing first because many organizers do not run monthly events. Choose price hypotheses from measured value and support effort; this assessment does not establish a final price.

Suggested thresholds to validate, not measured outcomes:

- First useful decision within 3 minutes, without coaching.
- A beginner can explain Current vs Suggested, Copy vs Move, and Applied vs Verified.
- Zero accepted rule-blocked actions, self-pairings, duplicate applications, or lost confirmed work during the pilot.
- Every unfinished decision reaches the staff handoff.
- At least 30% lower median review time on a comparable problem set, with no worse director-audited accuracy.
- At least three pilot directors choose a paid subsequent event; record objections and support effort too.

## Verification and limits

- 32 regression tests passed locally on Windows with Python 3.12. They cover imports, corrupt/legacy/portable backups, rules, projected counts, group actions, matching exclusions, missing data, spreadsheet exports, and Streamlit review/apply/restore navigation. The new CI workflow has not run remotely because the branch has not been pushed.
- Phase 1 kg conversion, belt steps, Masters ages, and approved-only behavior are retained in regression checks.
- A synthetic local benchmark of 510 registrations in 150 divisions generated 90 suggestions in about 1.9 seconds. This is not a production load test or a performance promise at the 25,000-registration input limit. Unchanged reports are cached within a user's session.
- Browser checks confirmed CSV upload (46 registrations / 25 divisions), the desktop workflow, and a 390-pixel mobile layout without horizontal overflow. Restore paths are covered by Streamlit's AppTest suite. Observed novice usability sessions still remain.
- No customer interviews, paid conversions, durable storage, billing integration, production security assessment, or deployment occurred.
- Validation uses shipped sample and synthetic data. Real-event fixtures and rule approval remain necessary.

## Development location

Repository: `freestylegrapplerz-EZ-Brackets/EzBrackets_Cursor`.

Checkout: `C:\Users\gmunr\EZ_Brackets\EzBrackets_Cursor`.

The parent folder was a June DEV v2 copy with no Git metadata. This checkout was cloned from the verified GitHub commit before implementation. Its `Launch_Current_EZ_Brackets.bat` opens v1.5; the parent launcher still opens the June app.
