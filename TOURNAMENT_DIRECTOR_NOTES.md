# Tournament Director Notes — Real Event Review

Notes captured while reviewing a real Smoothcomp CSV.  
**Status:** Notes 1–5 implemented. Keep adding notes below as bracket work continues.

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

## Additional notes

_(Add Note 4, etc. below as the event review continues.)_
