# Tournament Director Notes — Real Event Review

Notes captured while reviewing a real Smoothcomp CSV.  
**Status:** Notes 1–14 implemented. Keep adding notes below as bracket work continues.

---

## Note 1 — Juvenile 16–17 moving into Adult divisions

**Date captured:** 2026-08-09  
**Status:** Implemented

### Observation
Current recommendation logic may treat moving a Juvenile 16–17 athlete into an Adult division too negatively.

### Director philosophy
- A 16–17-year-old moving into Adult is only **one practical age step** because Adult begins at 18.
- Athletes in Juvenile 16–17 are generally more comfortable competing up into Adult than younger kids are moving up age groups.
- Therefore, an Adult match can be preferable to a **large weight jump** within Juvenile.

### Example scenario
Alone athlete: **Juvenile 16–17 / Beginner / 130–139 lbs**

Rough preferred decision order:

1. Juvenile 16–17 / Beginner / same weight class  
2. Juvenile 16–17 / Beginner / 1 weight class up or down (10 lbs)  
3. Adult / Novice / same weight class  
4. Adult / Novice / 1 weight class lower (~10 lb advantage for the Juvenile athlete)  
5. Adult / Beginner / same weight class  
6. Adult / Beginner / 1 weight class lower (~10 lb advantage for the Juvenile athlete)  
7. Juvenile 16–17 / Beginner / 2 weight classes away (20 lbs)

### Implementation
- Treat Juvenile 16–17 → Adult as one age step (not a hard age-safety block).
- Prefer Adult Novice over Adult Beginner for a Juvenile Beginner (waive one-level skill penalty + small advantage).
- Soften lighter Adult class vs heavier Adult class.
- Keep Adult options below Juvenile ±10 lbs and above Juvenile ±20 lbs.

---

## Note 2 — Never recommend cross-gender matches for Adult / Teen / Juvenile / Masters

**Date captured:** 2026-08-09  
**Status:** Implemented

### Bad recommendation found in real event
- **Current:** `Men No-Gi / Advanced / Adult / 130–139.9 lbs`
- **Suggested:** `Women No-Gi / Advanced / Master 1 / 130–139.9 lbs`
- Scored well on age/skill/weight alignment, but is **never acceptable**.

### Director rule
Gender is a **hard compatibility rule** once divisions are gender-separated:

**Mixed OK (do not force gender split):**
- Younger **Youth** divisions (typically under 14)
- These usually just say “Youth …” with boys/girls together — not separated in Smoothcomp

**Hard exclude opposite gender (never recommend Male ↔ Female):**
- Starts at **Youth 14–15** (when the event begins separating boys/girls)
- Continues through older youth / Teen / Juvenile / Adult / Masters
- Do **not** soft-score this as Needs Review / Last Resort — **exclude** it from the list entirely (same pattern as Gi vs No-Gi exclusion when crossover is off)

### Implementation
- Extract gender from slash-path (`Male`/`Female`) and entry prefixes (`Men No-Gi`, `Women Gi`).
- Hard-exclude opposite gender before scoring when either side requires gender separation.
- Younger Youth without 14+ ages may still mix.

---

## Note 3 — Easy save / resume progression (blocking for real event use)

**Date captured:** 2026-08-09  
**Status:** Implemented

### Problem hit during real event review
Director was mid-review (not finished accepting everyone), closed/left the app, and could not find a clear way to pick up where they left off — felt like starting over.

### Product requirement
Need an **obvious, easy** way to:
1. Save progress while working through decisions
2. Come back later and resume at the same place (moves planned, skipped, manual review, current Focus decision)

### Implementation
- Prominent **Save Progress** / **Resume Progress** panel in the main workflow (under the sticky progress bar)
- Resume Progress also on the landing screen before loading a CSV
- Sidebar mirrors the same Save/Resume controls
- Save enabled when any progress exists (accepted, skipped, or manual review) — not only after Accept
- Session JSON stores `focus_index`, guided layout, moves, skipped, manual review, preset, csv hash
- Clear success message: “Resumed progress — X move(s) planned…”

---

## Note 4 — Youth kids (4–13): prefer same belt before skill changes

**Date captured:** 2026-08-09  
**Status:** Implemented

### Bad recommendation found in real event
- Athlete: **Adalynn** (Black Tie Brazilian Jiu Jitsu)
- **Current:** `Kids & Teens Gi / White / Youth (8 - 9yrs) / 60 - 69.9 lbs`
- **Suggested:** `Kids & Teens Gi / Grey / Youth (8 - 9yrs) / 60 - 69.9 lbs`
- Scored like a near-perfect match (~99) with same age/weight — but directors avoid belt changes for young kids when possible.

### Director rule
For **Youth / kids about 4–13** (especially **White belt**):

1. Same skill + same age + **same weight**
2. Same skill + same age + **±10 lbs**
3. Same skill + same age + **±20 lbs**
4. Only then consider a **different skill** (e.g. White → Grey) → treat as **Needs Review**
5. Among cross-skill options for White Youth: prefer **~10 lb weight advantage** into the higher belt, then **same weight**, then heavier

### Implementation
- Detect Youth/kids ages with midpoint under 14
- Apply a Youth same-belt priority penalty on any skill/belt change so same-belt ±20 outranks White→Grey
- Soft weight advantage ordering for White Youth moving into a higher belt
- Cross-skill remains available later; trust UI marks skill gaps as Needs Review

---

## Note 5 — False “Same academy” / Teen vs Junior Teen labels

**Date captured:** 2026-08-09  
**Status:** Implemented

### Bad recommendation found in real event
- **Current:** `Kids & Teens No-Gi / Intermediate / Teen (female) (14 -15yrs) / 110 - 119.9 lbs.`
- **Suggested:** `Kids & Teens No-Gi / Intermediate / Junior Teen (male/female) (12 - 13yrs) / 120 - 129.9 lbs.`
- UI claimed **Same academy**, but Smoothcomp showed **different academies**.

### Root causes addressed
1. **Approved-only academy view:** pending athletes from other academies were ignored, so a division looked same-academy when it wasn’t.
2. **Missing academy data** was treated as same-academy (only the moving athlete’s academy counted).
3. **`(male/female)`** labels were misread as female; gendered Teen 14–15 must not merge into open mixed Junior Teen.
4. Age compare now uses **year bands** (14–15 vs 12–13) so those are never “Same age.”

### Implementation
- Academy mix uses **all registrations** in the division, not only Approved
- Unknown academy data → “Unknown academy data” (never false “Same academy”)
- Explicit mixed gender labels blocked against gendered 14+ divisions
- Safer academy field delimiter (` || `) so academy names may contain commas

---

## Note 6 — Caleb: Adult Intermediate weight moves lost to Master / wrong Club column

**Date captured:** 2026-08-09  
**Status:** Implemented  
**CSV:** `registrations-2026-08-09-14_34_20_261a.csv`

### Bad recommendation found in real event
- Athlete: **Caleb Watson** — `Men No-Gi / Intermediate / Adult / 170 - 179.9 lbs.`
- App suggested: `Men No-Gi / Beginner / Master 1 / 180 - 189.9 lbs.`
- Manual check: Intermediate Adult **160–169** and **180–189** both exist and should be preferred.

### Root cause / fix
Prefer Smoothcomp **Club** over sparse **Team**; Adult same-skill priority for ±10/±20 weight moves.

---

## Note 7 — Aiden Lee: Juvenile 16–17 → Adult marked Do Not Match

**Date captured:** 2026-08-09  
**Status:** Implemented

### Bad recommendation found in real event
- Athlete: **Aiden Lee** — `Juvenile No-Gi (male) / Intermediate / 16 - 17 years old / 160 - 169.9 lbs.`
- Manual good option: `Men No-Gi / Intermediate / Adult / 160 - 169.9 lbs.`
- App listed it #1 but as **Do Not Match** (“no safe matches”) because of age gap.

### Root cause
Smoothcomp puts Juvenile in the entry/group prefix and only `16 - 17 years old` in the age slot. The Juvenile→Adult rule only looked at the age field for the word “Juvenile”, so it never applied; age was treated as a 2-group jump and hard-blocked.

### Implementation
- Detect Juvenile 16–17 from age year bands (`16 - 17 years old`) and/or Juvenile in the full group path
- Then Adult same-skill/same-weight is a normal step-up (not Do Not Match)

---

## Note 8 — Youth (male/female) path parse + Do Not Match ranking above real options

**Date captured:** 2026-08-09  
**Status:** Implemented (PR #12)

### Summary
Fixed `(male/female)` splitting group paths and stopped equal-score Do Not Match rows from ranking above reviewable nearby options.

---

## Note 9 — Planned-state singles: accepting A→B should clear both alone divisions

**Date captured:** 2026-08-13  
**Status:** Implemented

### Workflow issue
Accepting a move from Single A into Single B’s division left Athlete B in the unresolved queue / Event Health alone count, even though the planned bracket was already 2 athletes.

### Implementation
- Keep original CSV state unchanged
- Derive **planned athlete counts** from CSV + Active accepted moves
- Unresolved singles / Focus / Queue / Event Health Alone use planned counts
- Destination singles with planned size ≥ 2 drop out of the queue
- Revert restores both singles
- Action Plan still lists only the accepted move (no invented move for B)
- Scoring / recommendation rankings unchanged

---

## Note 10 — Aiden Lee Gi Blue: Adult Gi never considered (entry mismatch)

**Date captured:** 2026-08-13  
**Status:** Implemented

### Issue
`Juvenile Gi (male) / Blue / Juvenile (16 - 17yrs) / 160 - 169.9 lbs.` showed **No safe match**, even when Adult Gi divisions may exist.

### Root cause
`normalize_entry_type()` only treated bare `Gi` / leading `gi` as gi.  
`Juvenile Gi` and `Men Gi` stayed as different strings → hard-excluded before scoring (same bug class as No-Gi already handled via `nogi` substring).

### Implementation
- Normalize any entry containing word-boundary `gi` (and not no-gi) to `"gi"`
- Juvenile Gi 16–17 → Men Gi / Blue / Adult same weight becomes a normal step-up
- Blue → Adult Intermediate/Beginner still skill-flags (belt vs experience ladder) — expected

---

## Note 11 — Apply Mode + compact Smoothcomp companion

**Date captured:** 2026-08-18  
**Status:** Implemented

### Problem
After accepting moves, directors still had high friction applying them in Smoothcomp: jump between apps, re-type athlete names and destinations, lose track of what was already applied, and treat the Action Plan as the only checklist.

### Product requirement
1. **Apply Mode** — workflow-ordered list of accepted moves with Copy Athlete / Copy Destination / Mark Applied
2. Progress: Planned / Applied / Remaining (clear that Smoothcomp is not auto-updated)
3. Save/Resume keeps Applied status + optional Smoothcomp event URL (Open only — no credentials)
4. **Compact companion** for side-by-side use with Smoothcomp (next unapplied move large)

### Implementation
- `applied` / `applied_at` on move records (migrated for older session files)
- Workflow sort: Kids/Teens Gi → Kids/Teens No-Gi → Adult Gi → … (FROM division)
- Focus/Queue uses the same cohort + entry order (not alphabetical by athlete name)
- Apply panel after completion (and collapsed expander mid-review)
- Session JSON stores `smoothcomp_event_url` and applied flags
- Scoring / recommendation ranking unchanged

---

## Note 12 — Don’t jump Adam Gi → Adam No-Gi before other Gi kids

**Date captured:** 2026-08-18  
**Status:** Implemented

### Observation
Starting review/apply, Adam Newman Gi was followed immediately by Adam Newman No-Gi instead of finishing the rest of Kids/Teens Gi first.

### Cause
Focus/Queue sorted by athlete name after priority, so the same person’s Gi and No-Gi decisions sat back-to-back.

### Fix
Shared workflow order for Focus/Queue and Apply Mode: age cohort → Gi before No-Gi → safer priority → finer age/gender → division → name.

---

## Note 13 — Smoothcomp Copy workflow (dropdowns + notes)

**Date captured:** 2026-08-18  
**Status:** Implemented

### Real workflow
1. Find athlete → check box  
2. **Copy** (not Move) — keep original if someone else signs up  
3. Admin note = paste original division  
4. Copy Registrations modal: Entry → Skill → Age → Weight  
5. Copy registrations → verify in destination  
6. Public note e.g. “Moved, alone in division”

### Apply Mode update
- Split destination into Entry / Skill / Age / Weight copy fields  
- Ready-to-paste admin note (original) + editable public note template  
- Checklist wording matches Copy (keep original), not Move  
- Scoring unchanged

---

## Note 14 — Market-readiness review: Phase 1 “trust the decisions” fixes

**Date captured:** 2026-09-06  
**Status:** Implemented (source-reproduced at commit `75cefc4`, all confirmed)

### Confirmed findings → fixes
| # | Finding (reproduced) | Fix |
|---|---|---|
| C1 | Unknown source weight scored 94 / Excellent / Safe Match / Looks Safe | New **Data Gaps** state: missing weight/skill/age (or gender where it matters) → **Needs Data Review** / “Missing information”; never Safe; ranks after complete-data rows; Focus offers *Accept — I verified in Smoothcomp* instead of a normal Accept |
| C2 | 60–65 kg vs 80–85 kg treated as a 20 lb gap → Safe Match | `weight_mid` detects **kg** and converts to lbs (≈44 lb gap → Do Not Match). Import check reports kg / unit-less labels (unit-less = assumed lbs) |
| C3 | Apply Mode says Copy (keep original) but planned counts subtracted from source | Actions now carry `apply_method` (**copy**/**move**, sidebar setting). Copy keeps original count; source division is *handled* (athlete has a planned opponent) rather than pretended empty. Action Plan / Apply Mode say Copy · KEEP IN vs Move · FROM |
| C4 | Academy-conflict accept stored `"a, b, c"` as one athlete → counts 2 left / 3 at destination | Group accept expands to **one record per athlete** (shared `group_action_id`); counts, checklist and Apply Mode are per athlete; revert reverts the whole group |
| H1 | White→Blue = “20 skill levels”; Master 2→Master 3 = “10 age groups” (Master 3 parsed as age 3!) | Distinct **adult belt / youth belt / experience** ladders (White→Blue = 1; belt vs experience = fixed review gap with note). `Master N` digits stripped before age parsing; Adult/Masters compared by category index |
| H2 | “Only analyze approved athletes” silently analysed all rows when 0 approved | Filter always applies; explicit empty state tells the director to change the setting |
| H3 | Unknown gender in Adult division scored 100 / Looks Safe | Unknown ≠ compatible: gap flagged when one side is gendered and the other not, or when the file encodes gender elsewhere. Files with no gender anywhere get one import-check notice |
| H4 | Juvenile 16–17 → Adult bypassed the age limit globally | Now an explicit **organizer setting** (`juvenile_adult_step_up`; on in FG / Adult Standard / Emergency, off in Kids Conservative). Counts as 1 step and is **still checked** against the age limit; wording says “confirm approval” |

### Additional gaps closed
- Session save/restore now stores **all rule/filter values** (weight/age/skill limits, penalties, approved-only, min target, top-N, crossover, Juvenile rule) + apply method
- New CSV while actions exist → **“Same event — keep” / “Different event — start fresh”** with a reconciliation preview (matched, already in destination, athlete/division not found)
- Rank-1 suggestions export renamed **Recommendation report** (not “Action Plan”); Action Plan = accepted actions only
- Completion panel distinguishes *suggestions reviewed* / *applied in Smoothcomp N/M* / *verify with fresh export*

### Not in this PR (later phases)
Accounts, billing, autosave/DB, shared staff access, whole-event plan comparison, hosting/uptime — product decisions for the paid pilot.

---

## Additional notes

_(Add Note 15, etc. below as the event review continues.)
