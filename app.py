import hashlib
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from workflow_support import (
    EVENT_COLUMNS, MAX_FILE_BYTES, MAX_BACKUP_BYTES, action_evidence, event_fingerprint, event_frame,
    import_problems, project_registrations, read_registration_csv,
    safe_export_frame, validate_saved_session,
)


# =========================
# EZ BRACKETS - v1.5.0
# Trust fixes: data-completeness state, kg units, belt ladders, Masters ages,
# approved-only filter, Copy vs Move event state, per-athlete group actions
# =========================

st.set_page_config(
    page_title="EZ Brackets",
    page_icon="🥋",
    layout="wide",
)

SKILL_ORDER = {
    "White": 0, "Grey": 1, "Gray": 1, "Yellow": 2, "Orange": 3, "Green": 4,
    "Novice": 10, "Beginner": 11, "Intermediate": 12, "Advanced": 13,
    "Blue": 20, "Purple": 21, "Brown": 22, "Black": 23,
}


AGE_ORDER_HINTS = [
    ("Mighty Mite", 1),
    ("Pee Wee", 2),
    ("Kindergarten", 3),
    # Specific Youth bands must stay distinct — generic "Youth" is a fallback only.
    ("Youth 6-7", 4),
    ("Youth 8-9", 5),
    ("Youth 10-11", 6),
    ("Youth 12-13", 7),
    ("Youth 14-15", 8),
    ("Youth 16-17", 9),
    ("Youth", 6),
    ("Pre Teen", 10),
    ("Junior Teen", 11),
    ("Teen", 12),
    ("Juvenile", 13),
    ("Adult", 20),
    ("Master 1", 21),
    ("Master 2", 22),
    ("Master 3", 23),
    ("Master 4", 24),
    ("Master 5", 25),
]

GENDER_TOKENS = {
    "male", "female", "m", "f", "men", "women",
    "boy", "boys", "girl", "girls", "man", "woman",
}
MALE_GENDER_TOKENS = {"male", "m", "men", "man", "boy", "boys"}
FEMALE_GENDER_TOKENS = {"female", "f", "women", "woman", "girl", "girls"}

# Younger youth stay mixed; separation starts at Youth 14-15.
MIXED_GENDER_AGE_HINTS = (
    "mighty mite", "pee wee", "kindergarten",
    "youth 6-7", "youth 8-9", "youth 10-11", "youth 12-13",
)


def find_col(df, possible_names):
    clean_map = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        key = name.strip().lower()
        if key in clean_map:
            return clean_map[key]
    for c in df.columns:
        low = str(c).strip().lower()
        for name in possible_names:
            if name.strip().lower() in low:
                return c
    return None


def normalize_academy_name(name):
    a = str(name or "").strip()
    if not a:
        return ""
    if a.lower() in {"nan", "none", "null", "n/a", "na", "-", "--", "unknown"}:
        return ""
    return a


def resolve_athlete_names(df):
    """Build athlete display names from Smoothcomp Firstname/Lastname when present."""
    first_col = find_col(df, ["firstname", "first name"])
    last_col = find_col(df, ["lastname", "last name"])
    if first_col and last_col:
        first = df[first_col].fillna("").astype(str).map(lambda x: x.strip() if str(x).lower() != "nan" else "")
        last = df[last_col].fillna("").astype(str).map(lambda x: x.strip() if str(x).lower() != "nan" else "")
        full = (first + " " + last).str.strip()
        if full.str.len().gt(0).any():
            return full

    # Avoid bare "name" first — it substring-matches Firstname/Middle name.
    name_col = find_col(df, ["full name", "athlete", "competitor", "name"])
    if name_col:
        return df[name_col].fillna("").astype(str).str.strip().replace({"nan": ""})
    return pd.Series("", index=df.index, dtype=str)


def resolve_academy_series(df):
    """Resolve academy/club for Smoothcomp CSVs that include both Club and Team.

    Smoothcomp: **Club** is the academy (usually filled). **Team** is optional and
    often sparse. Preferring Team first left most athletes with blank academies,
    which falsely crushed same-skill Adult weight moves under same-academy penalties.
    """
    club_col = find_col(df, ["club", "academy", "affiliation", "school"])
    team_col = find_col(df, ["team"])

    def _clean_col(col):
        if col is None:
            return pd.Series([""] * len(df), index=df.index)
        return df[col].map(normalize_academy_name)

    club = _clean_col(club_col)
    team = _clean_col(team_col)
    # Prefer Club/academy; fill gaps from Team.
    if club_col is not None and team_col is not None and club_col != team_col:
        return club.where(club.astype(str).str.len().gt(0), team)
    if club_col is not None:
        return club
    return team


def is_explicitly_mixed_gender_label(text):
    """True for open/mixed labels like (male/female), male & female, co-ed."""
    raw = str(text or "").strip().lower()
    if not raw:
        return False
    compact = re.sub(r"[\s_\-]+", "", raw)
    if "malefemale" in compact or "femalemale" in compact:
        return True
    if re.search(r"\bmale\s*/\s*female\b|\bfemale\s*/\s*male\b", raw):
        return True
    if re.search(r"\b(co[- ]?ed|mixed\s*gender)\b", raw):
        return True
    return False


def extract_gender(text):
    """Return 'male', 'female', or '' from division/entry labels.

    Supports slash tokens (Male/Female) and entry prefixes (Men No-Gi, Women Gi).
    Checks female markers before male so 'women' is not misread as 'men'.
    Explicit mixed labels (male/female) return '' (unknown / open).
    """
    raw = str(text or "").strip().lower()
    if not raw:
        return ""
    if is_explicitly_mixed_gender_label(raw):
        return ""
    # Exact slash/segment tokens first
    for part in re.split(r"[/]", raw):
        token = part.strip().lower()
        if is_explicitly_mixed_gender_label(token):
            return ""
        if token in FEMALE_GENDER_TOKENS:
            return "female"
        if token in MALE_GENDER_TOKENS:
            return "male"
        # Entry-style "women no-gi" / "men gi"
        for word in re.split(r"[\s_\-]+", token):
            if word in FEMALE_GENDER_TOKENS:
                return "female"
            if word in MALE_GENDER_TOKENS:
                return "male"
    if re.search(r"\b(women|female|girls?|woman)\b", raw):
        return "female"
    if re.search(r"\b(men|male|boys?|man)\b", raw):
        return "male"
    return ""


def age_requires_gender_separation(age_label):
    """True when opposite-gender matches must be hard-excluded."""
    a = str(age_label or "").lower()
    if not a:
        return False
    for hint in MIXED_GENDER_AGE_HINTS:
        if hint in a:
            return False
    if "youth" in a:
        nums = [int(n) for n in re.findall(r"\d+", a)]
        if nums:
            return (sum(nums) / len(nums)) >= 14
        return False  # bare "Youth" without ages → treat as mixed kids
    for key in ("teen", "juvenile", "adult", "master", "senior"):
        if key in a:
            return True
    return False


def genders_compatible(
    single_gender,
    single_age,
    cand_gender,
    cand_age,
    single_label="",
    cand_label="",
):
    """Hard gender gate. Younger youth may mix; 14+ / Teen+ may not.

    Also blocks moving a gendered 14+ athlete into an explicitly mixed
    (male/female) division, and the reverse.
    """
    needs_sep = age_requires_gender_separation(single_age) or age_requires_gender_separation(cand_age)
    if not needs_sep:
        return True
    src_mixed = is_explicitly_mixed_gender_label(single_label) or is_explicitly_mixed_gender_label(single_age)
    tgt_mixed = is_explicitly_mixed_gender_label(cand_label) or is_explicitly_mixed_gender_label(cand_age)
    if single_gender and tgt_mixed:
        return False
    if cand_gender and src_mixed:
        return False
    if single_gender and cand_gender and single_gender != cand_gender:
        return False
    return True


def split_group_path(group):
    """Split a Smoothcomp group path on '/' but NOT inside parentheses.

    Critical for labels like ``Youth (male/female) (8 - 9yrs)`` — a naive
    ``.split('/')`` turns that into ``Youth (male`` + ``female) (8 - 9yrs)``
    and corrupts age/gender parsing.
    """
    parts = []
    buf = []
    depth = 0
    for ch in str(group or ""):
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "/" and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
    part = "".join(buf).strip()
    if part:
        parts.append(part)
    return parts


def parse_group(group):
    """Split a Smoothcomp-style group into entry/skill/age/weight/gender.

    Gender tokens (Male/Female/etc.) are removed from field slots so 5-part paths
    like ``Gi / Blue / Male / Adult / 150 - 159 lbs`` still parse correctly, but
    gender is returned separately for compatibility checks.
    """
    gender = extract_gender(group)
    parts = split_group_path(group)
    parts = [p for p in parts if p.lower() not in GENDER_TOKENS]

    entry = parts[0] if len(parts) > 0 else ""
    skill = parts[1] if len(parts) > 1 else ""
    age = parts[2] if len(parts) > 2 else ""
    weight = parts[3] if len(parts) > 3 else ""

    # If an extra segment remains, prefer the last weight-looking token.
    if len(parts) > 4:
        weight_idx = None
        for i, p in enumerate(parts):
            low = p.lower()
            if "lb" in low or "kg" in low or re.search(r"\d+\s*-\s*\d+", p):
                weight_idx = i
        if weight_idx is not None and weight_idx >= 3:
            weight = parts[weight_idx]
            age = parts[weight_idx - 1] if weight_idx - 1 >= 2 else age
            skill = parts[1] if len(parts) > 1 else skill

    # Entry prefixes like "Men No-Gi" still carry gender even after slash stripping.
    if not gender:
        gender = extract_gender(entry)
    if not gender:
        gender = extract_gender(age)

    return entry, skill, age, weight, gender


def rank_scored_candidates(scored):
    """Prefer reviewable options over equal-score Do Not Match rows.

    Complete-data rows rank ahead of rows with missing division data, which in
    turn rank ahead of rule-blocked rows.
    """
    return sorted(
        scored,
        key=lambda x: (
            1 if str(x.get("Safety Flag", "")).strip() else 0,
            1 if str(x.get("Data Gaps", "")).strip() else 0,
            -int(x.get("Match Score", 0) or 0),
        ),
    )


def event_has_gender_data(df):
    """True when any division in the file states a gender (path or entry)."""
    if df is None or df.empty:
        return False
    if "gender_clean" in df.columns and df["gender_clean"].astype(str).str.strip().ne("").any():
        return True
    for col in ("group_clean", "entry_clean"):
        if col in df.columns and df[col].astype(str).map(extract_gender).ne("").any():
            return True
    return False


def with_event_context(scoring_settings, df):
    """Attach file-level facts the scorer needs (currently: does gender appear anywhere)."""
    merged = dict(scoring_settings or {})
    merged.setdefault("event_has_gender_data", event_has_gender_data(df))
    return merged


def recommendation_is_safe(rec_row):
    """Safe = passes the rules AND has complete data. Missing data is never safe."""
    if rec_row is None:
        return False
    if str(rec_row.get("Safety Flag", "") or "").strip():
        return False
    if str(rec_row.get("Data Gaps", "") or "").strip():
        return False
    return True


def apply_approved_filter(working, only_approved):
    """Apply the approved-only filter even when it leaves zero rows.

    Silently falling back to all rows analysed athletes who were not eligible
    yet. Callers show an explicit empty state instead.
    """
    if only_approved and "approved_clean" in working.columns:
        approved_mask = working["approved_clean"].astype(str).str.lower().eq("approved")
        return working[approved_mask]
    return working


def skill_value(skill):
    s = str(skill)
    for key, value in SKILL_ORDER.items():
        if key.lower() in s.lower():
            return value
    return 999


# Distinct ranking systems. A "level" only means something inside one ladder.
ADULT_BELT_LADDER = ["white", "blue", "purple", "brown", "black"]
YOUTH_BELT_LADDER = ["white", "grey", "gray", "yellow", "orange", "green"]
EXPERIENCE_LADDER = ["novice", "beginner", "intermediate", "advanced", "expert"]
CROSS_LADDER_SKILL_STEPS = 3


def skill_rank(skill, age_label=""):
    """Return (ladder, index) for a skill label, or (None, None) if unknown.

    ``white`` is shared by the adult and youth belt ladders; the age label
    decides which ladder applies so White→Blue (adult) is one belt, not 20.
    """
    s = str(skill or "").strip().lower()
    if not s:
        return None, None
    for i, name in enumerate(EXPERIENCE_LADDER):
        if name in s:
            return "experience", i
    youth_context = is_youth_kids_age(age_label) or is_juvenile_16_17(age_label)
    youth_only = [n for n in YOUTH_BELT_LADDER if n != "white"]
    adult_only = [n for n in ADULT_BELT_LADDER if n != "white"]
    for name in youth_only:
        if name in s:
            idx = YOUTH_BELT_LADDER.index(name)
            # grey/gray share a slot
            if name in ("grey", "gray"):
                idx = 1
            elif idx > 2:
                idx -= 1
            return "youth_belt", idx
    for name in adult_only:
        if name in s:
            return "adult_belt", ADULT_BELT_LADDER.index(name)
    if "white" in s:
        return ("youth_belt", 0) if youth_context else ("adult_belt", 0)
    return None, None


def skill_step_difference(src_skill, tgt_skill, src_age="", tgt_age=""):
    """Skill gap in ladder steps.

    Returns (steps, note). ``steps`` is 999 when either side is unknown.
    Belt vs experience-level systems cannot be compared numerically, so a
    cross-ladder pair returns a fixed review-level gap with an explanatory note.
    """
    s_lad, s_idx = skill_rank(src_skill, src_age)
    t_lad, t_idx = skill_rank(tgt_skill, tgt_age)
    if s_lad is None or t_lad is None:
        return 999, ""
    if s_lad == t_lad:
        return abs(s_idx - t_idx), ""
    # White belt appears in both belt ladders — treat white↔white as equal.
    if {s_lad, t_lad} == {"adult_belt", "youth_belt"} and s_idx == 0 and t_idx == 0:
        return 0, ""
    return CROSS_LADDER_SKILL_STEPS, "belt vs experience-level systems differ — director must judge"


def strip_masters_tokens(text):
    """Remove 'Master 1/2/3' style tokens so the digit is never read as an age."""
    return re.sub(r"masters?\s*\d+", " ", str(text or ""), flags=re.IGNORECASE)


def age_year_midpoint(age):
    """Return midpoint of explicit year bands (e.g. 14-15 → 14.5), else None."""
    nums = [int(n) for n in re.findall(r"\d+", strip_masters_tokens(age))]
    if not nums:
        return None
    # Ignore non-age numbers that sometimes appear in labels (rare).
    age_nums = [n for n in nums if 3 <= n <= 75]
    if not age_nums:
        return None
    if len(age_nums) >= 2:
        return sum(age_nums[:2]) / 2.0
    return float(age_nums[0])


def age_value(age):
    """Return a sortable age rank. Longer label matches win (Youth 8-9 > Youth).

    When an explicit year band is present (12-13, 14-15, etc.), use that
    midpoint so Teen 14-15 is never treated as the same age as Junior Teen 12-13.
    """
    a = str(age or "").strip()
    if not a:
        return 999
    year_mid = age_year_midpoint(a)
    # Prefer year bands for kids/teens when present.
    if year_mid is not None and year_mid <= 17:
        return year_mid
    a_low = a.lower()
    matches = [(key, value) for key, value in AGE_ORDER_HINTS if key.lower() in a_low]
    if matches:
        matches.sort(key=lambda kv: len(kv[0]), reverse=True)
        best_key, best_val = matches[0]
        # Generic "Youth" with numbers but no explicit band → use age midpoints.
        if best_key.lower() == "youth":
            if year_mid is not None:
                return year_mid
        return best_val
    if year_mid is not None:
        return year_mid
    return 999


def age_step_difference(src_age, tgt_age):
    """Return age gap in practical steps, or 999 if unknown.

    Important: unknown vs unknown must NOT count as the same age (0).
    """
    sv = age_value(src_age)
    tv = age_value(tgt_age)
    if sv == 999 or tv == 999:
        return 999
    gap = abs(sv - tv)
    # Adult / Masters ranks are category indexes (Adult 20, Master 1 21, ...):
    # one index = one age group, so Master 1 → Master 3 is 2 steps, not "2 years".
    if sv >= 20 and tv >= 20:
        return int(round(gap))
    # Year-based ranks (e.g. 12.5 vs 14.5) → map to age-group steps.
    if gap <= 0.01:
        return 0
    if gap <= 2.25:
        return 1
    if gap <= 4.5:
        return 2
    if gap <= 7:
        return 3
    return max(4, int(round(gap / 2.0)))


KG_TO_LBS = 2.20462


def weight_unit(weight):
    """Return 'kg', 'lbs', or '' (no explicit unit in the label)."""
    w = str(weight or "").lower()
    if re.search(r"\bkgs?\b|kilo", w):
        return "kg"
    if re.search(r"\blbs?\b|pounds?", w):
        return "lbs"
    return ""


def weight_mid(weight):
    """Midpoint of a weight-class label, always returned in pounds.

    Kilogram labels are converted so a 60–65 kg vs 80–85 kg pair is a ~44 lb
    gap, not 20. Labels without a unit are assumed to be pounds (the import
    check reports how many divisions lack an explicit unit).
    """
    w = str(weight).lower()
    nums = re.findall(r"\d+\.?\d*", w)
    unit = weight_unit(w)
    mid = None
    if "over" in w and nums:
        mid = float(nums[0]) + (5 if unit == "kg" else 10)
    elif len(nums) >= 2:
        mid = (float(nums[0]) + float(nums[1])) / 2
    elif len(nums) == 1:
        mid = float(nums[0])
    if mid is None:
        return None
    if unit == "kg":
        return round(mid * KG_TO_LBS, 1)
    return mid


def normalize_entry_type(entry):
    """Normalize Gi / No-Gi spellings across Smoothcomp entry prefixes.

    ``Juvenile Gi``, ``Men Gi``, ``Kids & Teens Gi``, and bare ``Gi`` must all
    count as the same entry type — otherwise Juvenile Gi 16–17 can never see
    Adult Men Gi divisions (hard-excluded before scoring).
    """
    raw = str(entry).strip().lower()
    compact = re.sub(r"[\s_\-]+", "", raw)
    if "nogi" in compact:
        return "no-gi"
    # Word-boundary gi so "Juvenile Gi (male)" / "Men Gi" match, but not random text.
    if compact == "gi" or re.search(r"\bgi\b", raw):
        return "gi"
    return raw


def normalize_dataframe(raw_df):
    df = raw_df.copy()

    group_col = find_col(df, ["group", "division", "bracket", "category"])
    approved_col = find_col(df, ["approved", "status"])

    if group_col is None:
        st.error("Could not find a division/group column in this CSV.")
        st.stop()

    df["athlete_name"] = resolve_athlete_names(df)
    df["approved_clean"] = df[approved_col].astype(str).str.strip() if approved_col else "Approved"
    df["academy_clean"] = resolve_academy_series(df)
    df["group_clean"] = df[group_col].fillna("").astype(str).str.strip()

    parsed = df["group_clean"].apply(parse_group)
    df["entry_clean"] = parsed.apply(lambda x: x[0])
    df["skill_clean"] = parsed.apply(lambda x: x[1])
    df["age_clean"] = parsed.apply(lambda x: x[2])
    df["weight_clean"] = parsed.apply(lambda x: x[3])
    df["gender_clean"] = parsed.apply(lambda x: x[4])

    return df


def normalize_mapped_dataframe(raw_df, mapping):
    df = raw_df.copy()

    def mapped_series(field, default=""):
        col = mapping.get(field, "")
        if col and col in df.columns:
            return df[col].fillna("").astype(str).str.strip()
        return pd.Series([default] * len(df), index=df.index)

    df["athlete_name"] = mapped_series("name", "")
    df["approved_clean"] = mapped_series("status", "Approved")
    df["academy_clean"] = mapped_series("academy", "").map(normalize_academy_name)
    df["entry_clean"] = mapped_series("entry", "")
    df["skill_clean"] = mapped_series("skill", "")
    df["age_clean"] = mapped_series("age", "")
    df["weight_clean"] = mapped_series("weight", "")
    df["gender_clean"] = df["entry_clean"].apply(extract_gender)

    group_col = mapping.get("group", "")
    if group_col and group_col in df.columns:
        df["group_clean"] = df[group_col].fillna("").astype(str).str.strip()
        parsed = df["group_clean"].apply(parse_group)
        df["entry_clean"] = df["entry_clean"].where(df["entry_clean"].str.strip().ne(""), parsed.apply(lambda x: x[0]))
        df["skill_clean"] = df["skill_clean"].where(df["skill_clean"].str.strip().ne(""), parsed.apply(lambda x: x[1]))
        df["age_clean"] = df["age_clean"].where(df["age_clean"].str.strip().ne(""), parsed.apply(lambda x: x[2]))
        df["weight_clean"] = df["weight_clean"].where(df["weight_clean"].str.strip().ne(""), parsed.apply(lambda x: x[3]))
        df["gender_clean"] = df["gender_clean"].where(df["gender_clean"].astype(str).str.strip().ne(""), parsed.apply(lambda x: x[4]))
    else:
        df["group_clean"] = (
            df["entry_clean"].astype(str)
            + " / "
            + df["skill_clean"].astype(str)
            + " / "
            + df["age_clean"].astype(str)
            + " / "
            + df["weight_clean"].astype(str)
        )

    return df


ACADEMY_FIELD_JOIN = " || "


def split_academies_field(target_academies):
    """Split a group_summary academies field into individual academy names.

    Uses ' || ' as the canonical delimiter so academy names may contain commas.
    Falls back to comma-split only for legacy saved strings without ' || '.
    """
    s = str(target_academies or "").strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return []
    if ACADEMY_FIELD_JOIN in s:
        parts = s.split(ACADEMY_FIELD_JOIN)
    elif " + " in s and "," not in s:
        # Display-style mix strings occasionally flow back in
        parts = s.split(" + ")
    else:
        # Legacy comma join — ambiguous when names contain commas
        parts = s.split(",")
    return [p for p in (normalize_academy_name(x) for x in parts) if p]


def group_summary(df):
    rows = []
    for group, g in df.groupby("group_clean", dropna=False):
        sample = g.iloc[0]
        academies = sorted(set(
            a for a in (normalize_academy_name(x) for x in g["academy_clean"].tolist()) if a
        ))
        gender = str(sample.get("gender_clean", "") or "").strip()
        if not gender:
            gender = extract_gender(group) or extract_gender(sample.get("entry_clean", ""))
        # Recover age/skill/weight from the full group path when cleaned fields are blank.
        parsed_entry, parsed_skill, parsed_age, parsed_weight, parsed_gender = parse_group(group)
        age = str(sample.get("age_clean", "") or "").strip() or parsed_age
        skill = str(sample.get("skill_clean", "") or "").strip() or parsed_skill
        weight = str(sample.get("weight_clean", "") or "").strip() or parsed_weight
        entry = str(sample.get("entry_clean", "") or "").strip() or parsed_entry
        if not gender:
            gender = parsed_gender
        rows.append({
            "group": group,
            "athletes": len(g),
            "entry": entry,
            "skill": skill,
            "age": age,
            "weight": weight,
            "gender": gender,
            "names": ", ".join(g["athlete_name"].astype(str).tolist()),
            "academies": ACADEMY_FIELD_JOIN.join(academies),
            "academy_count": len(academies),
        })
    columns = ["group", "athletes", "entry", "skill", "age", "weight", "gender", "names", "academies", "academy_count"]
    return pd.DataFrame(rows, columns=columns).sort_values(["athletes", "group"]).reset_index(drop=True)


def same_entry(a, b):
    return normalize_entry_type(a) == normalize_entry_type(b)


def academy_mix_after_move(single_academy, target_academies, target_academy_count=None, target_athletes=None):
    """Return (mix_label, unique_count, status).

    status:
      - "mixed": 2+ known academies after move
      - "same": only one known academy after move (true same-academy risk)
      - "unknown": target has athletes but no reliable academy data — do NOT
        claim same-academy (this was a real false-positive in event review)
    """
    target_list = split_academies_field(target_academies)
    single = normalize_academy_name(single_academy)
    known_target = len(target_list)
    if target_academy_count is not None:
        try:
            known_target = max(known_target, int(target_academy_count))
        except (TypeError, ValueError):
            pass
    try:
        tgt_n = int(target_athletes) if target_athletes is not None else 0
    except (TypeError, ValueError):
        tgt_n = 0

    # Target has people but we don't know their academies → cannot assert same-academy.
    if known_target == 0 and not target_list and tgt_n >= 1:
        label = single or "Unknown academy"
        return label, 0, "unknown"

    academies = list(target_list)
    if single:
        academies.append(single)
    unique = sorted(set(academies))
    if len(unique) >= 2:
        return " + ".join(unique), len(unique), "mixed"
    if len(unique) == 1:
        return unique[0], 1, "same"
    return "Unknown academy", 0, "unknown"


DEFAULT_SCORING_SETTINGS = {
    "entry_crossover_penalty": 30,
    "unknown_weight_penalty": 10,
    "moderate_weight_penalty": 12,
    "large_weight_penalty": 25,
    "very_large_weight_penalty": 45,
    "one_skill_penalty": 10,
    "some_skill_penalty": 25,
    "major_skill_penalty": 45,
    "one_age_penalty": 10,
    "some_age_penalty": 22,
    "major_age_penalty": 40,
    "same_academy_penalty": 35,
    "mixed_academy_bonus": 4,
    "adjacent_class_penalty": 6,
    "target_size_two_bonus": 2,
    "target_size_three_plus_bonus": 5,
    "max_safe_weight_diff": 20,
    "max_safe_age_diff": 1,
    "max_safe_skill_diff": 1,
    # Organizer rule, not a universal truth: count Juvenile 16-17 → Adult as one
    # age step. Off by default; presets that follow FG practice turn it on.
    "juvenile_adult_step_up": False,
}


SCORING_PRESETS = {
    "Kids Conservative": {
        "max_safe_weight_diff": 10,
        "max_safe_age_diff": 0,
        "max_safe_skill_diff": 0,
        "same_academy_penalty": 45,
        "entry_crossover_penalty": 45,
        "juvenile_adult_step_up": False,
    },
    "Adult Standard": {
        "max_safe_weight_diff": 20,
        "max_safe_age_diff": 1,
        "max_safe_skill_diff": 1,
        "same_academy_penalty": 35,
        "entry_crossover_penalty": 30,
        "juvenile_adult_step_up": True,
    },
    "Emergency Merge Mode": {
        "max_safe_weight_diff": 35,
        "max_safe_age_diff": 2,
        "max_safe_skill_diff": 2,
        "same_academy_penalty": 20,
        "entry_crossover_penalty": 20,
        "juvenile_adult_step_up": True,
    },
    "Freestyle Grapplerz Rules": {
        "max_safe_weight_diff": 20,
        "max_safe_age_diff": 1,
        "max_safe_skill_diff": 1,
        "same_academy_penalty": 40,
        "entry_crossover_penalty": 35,
        "juvenile_adult_step_up": True,
    },
}

NEEDS_DATA_LABEL = "Needs Data Review"


def quality_label(score, safety_flag="", data_gaps=""):
    if safety_flag:
        return "Do Not Match"
    if data_gaps:
        return NEEDS_DATA_LABEL
    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Review"
    if score >= 40:
        return "Last resort"
    return "No strong match"


def risk_badge(score, safety_flag="", data_gaps=""):
    if safety_flag:
        return "Do Not Match"
    if data_gaps:
        return NEEDS_DATA_LABEL
    if score >= 85:
        return "Safe Match"
    if score >= 70:
        return "Needs Review"
    if score >= 45:
        return "Emergency Only"
    return "Do Not Match"


def action_text(action_type, source, target, quality):
    if quality == "Do Not Match":
        return f"Do not move {source} into {target} without director approval."
    if quality == NEEDS_DATA_LABEL:
        return f"Verify missing division data before moving {source} into {target}."
    if action_type == "single":
        return f"Move athlete from {source} into {target}."
    return f"Merge problem division {source} into {target}."


def before_after_text(source_label, source_count, target_label, target_count):
    after_count = int(source_count) + int(target_count)
    return f"Before: {source_label} has {source_count}; {target_label} has {target_count}. After: {target_label} would have {after_count}."


def is_juvenile_16_17(age_label, context_label=""):
    """Juvenile / Youth bands that are effectively 16-17.

    Smoothcomp often splits this as:
      group: ``Juvenile No-Gi (male) / Intermediate / 16 - 17 years old / ...``
    so the age slot is only ``16 - 17 years old`` (no word Juvenile).
    Pass the full group/entry as ``context_label`` so those still count.
    """
    a = str(age_label or "").lower().strip()
    ctx = str(context_label or "").lower().strip()
    blob = f"{a} {ctx}".strip()
    mid = age_year_midpoint(age_label)
    years_16_17 = mid is not None and 16 <= mid < 18

    if "juvenile" in a or "juvenile" in ctx:
        if mid is None:
            return True
        return mid >= 16
    if "youth" in a or ("youth" in ctx and "juvenile" not in ctx):
        return bool(years_16_17)
    # Bare year band used inside Juvenile divisions: "16 - 17 years old" / "16-17yrs"
    if years_16_17 and ("years old" in a or "yrs" in a or "year old" in a):
        return True
    return False


def is_adult_age(age_label):
    a = str(age_label or "").lower()
    return "adult" in a and "master" not in a and "pre" not in a


def age_midpoint_years(age_label):
    nums = [int(n) for n in re.findall(r"\d+", str(age_label or ""))]
    if not nums:
        return None
    return sum(nums) / len(nums)


def is_youth_kids_age(age_label):
    """Youth / kids roughly ages 4–13 (not 14+, Juvenile, Adult, Masters)."""
    a = str(age_label or "").lower().strip()
    if not a:
        return False
    if any(k in a for k in ("juvenile", "adult", "master", "senior")):
        return False
    mid = age_midpoint_years(a)
    if "youth" in a or "kid" in a or "child" in a:
        if mid is not None:
            return mid < 14
        return True
    # Numeric kid bands without the word Youth (e.g. "8 - 9yrs")
    if mid is not None and 4 <= mid < 14:
        return True
    return False


def is_white_belt_skill(skill):
    return "white" in str(skill or "").lower()


def score_candidate(single, cand, allow_entry_crossover=False, scoring_settings=None):
    settings = {**DEFAULT_SCORING_SETTINGS, **(scoring_settings or {})}

    if not allow_entry_crossover and not same_entry(single.get("entry_clean", ""), cand.get("entry", "")):
        return None

    # Hard gender exclusion (before scoring), same pattern as Gi/No-Gi gate.
    single_gender = (
        str(single.get("gender_clean", "") or "").strip()
        or extract_gender(single.get("group_clean", ""))
        or extract_gender(single.get("entry_clean", ""))
    )
    cand_gender = (
        str(cand.get("gender", "") or "").strip()
        or extract_gender(cand.get("group", ""))
        or extract_gender(cand.get("entry", ""))
    )
    src_skill = str(single.get("skill_clean", "") or "").strip()
    tgt_skill = str(cand.get("skill", "") or "").strip()
    src_age = str(single.get("age_clean", "") or "").strip()
    tgt_age = str(cand.get("age", "") or "").strip()
    src_weight = str(single.get("weight_clean", "") or "").strip()
    tgt_weight = str(cand.get("weight", "") or "").strip()

    # Recover fields from full division paths when cleaned columns are blank.
    if (not src_age or not src_skill or not src_weight) and single.get("group_clean"):
        pe, ps, pa, pw, _pg = parse_group(single.get("group_clean", ""))
        src_skill = src_skill or ps
        src_age = src_age or pa
        src_weight = src_weight or pw
        if not single_gender:
            single_gender = _pg or single_gender
    if (not tgt_age or not tgt_skill or not tgt_weight) and cand.get("group"):
        pe, ps, pa, pw, _pg = parse_group(cand.get("group", ""))
        tgt_skill = tgt_skill or ps
        tgt_age = tgt_age or pa
        tgt_weight = tgt_weight or pw
        if not cand_gender:
            cand_gender = _pg or cand_gender

    if not genders_compatible(
        single_gender,
        src_age,
        cand_gender,
        tgt_age,
        single_label=str(single.get("group_clean", "") or ""),
        cand_label=str(cand.get("group", "") or ""),
    ):
        return None

    skill_diff, skill_note = skill_step_difference(src_skill, tgt_skill, src_age, tgt_age)
    raw_age_diff = age_step_difference(src_age, tgt_age)

    sw = weight_mid(src_weight)
    cw = weight_mid(tgt_weight)
    weight_diff = abs(sw - cw) if sw is not None and cw is not None else 999

    src_context = str(single.get("group_clean", "") or single.get("entry_clean", "") or "")
    # Organizer option: Juvenile 16-17 → Adult counts as one practical age step
    # (Adult starts at 18). It is still checked against max_safe_age_diff.
    juv_to_adult = (
        bool(settings.get("juvenile_adult_step_up"))
        and is_juvenile_16_17(src_age, src_context)
        and is_adult_age(tgt_age)
    )
    age_diff = 1 if juv_to_adult else raw_age_diff

    # Data completeness is separate from rule eligibility and preference score.
    # Missing required information can never be labelled Safe.
    data_gaps = []
    if sw is None or cw is None:
        data_gaps.append("weight class missing")
    if skill_diff == 999:
        data_gaps.append("skill/belt missing")
    if raw_age_diff == 999 and not juv_to_adult:
        data_gaps.append("age group missing")
    if age_requires_gender_separation(src_age) or age_requires_gender_separation(tgt_age):
        src_mixed = is_explicitly_mixed_gender_label(single.get("group_clean", "")) or \
            is_explicitly_mixed_gender_label(src_age)
        tgt_mixed = is_explicitly_mixed_gender_label(cand.get("group", "")) or \
            is_explicitly_mixed_gender_label(tgt_age)
        src_unknown = not single_gender and not src_mixed
        tgt_unknown = not cand_gender and not tgt_mixed
        # Missing gender needs an explicit check on each relevant decision,
        # including exports that omit gender everywhere. Explicit mixed labels
        # still identify divisions that do not separate genders.
        if src_unknown or tgt_unknown:
            data_gaps.append("gender not stated for a gender-separated division")

    score = 100
    reasons = []
    breakdown = ["Start: 100"]
    safety_flags = []
    if skill_note:
        reasons.append(skill_note)

    if not same_entry(single.get("entry_clean", ""), cand.get("entry", "")):
        penalty = settings["entry_crossover_penalty"]
        score -= penalty
        reasons.append("Gi/No-Gi crossover")
        breakdown.append(f"Entry crossover: -{penalty}")

    if weight_diff == 999:
        penalty = settings["unknown_weight_penalty"]
        score -= penalty
        reasons.append("weight class missing — verify before matching")
        breakdown.append(f"Unknown weight: -{penalty}")
    elif weight_diff == 0:
        reasons.append("same weight class")
        breakdown.append("Weight: 0")
    elif weight_diff <= 10:
        penalty = settings["adjacent_class_penalty"]
        score -= penalty
        reasons.append("1 weight class apart")
        breakdown.append(f"1 weight class apart: -{penalty}")
    elif weight_diff <= 20:
        penalty = settings["moderate_weight_penalty"]
        score -= penalty
        reasons.append("2 weight classes apart")
        breakdown.append(f"2 weight classes apart: -{penalty}")
    elif weight_diff <= 30:
        penalty = settings["large_weight_penalty"]
        score -= penalty
        reasons.append("3 weight classes apart")
        breakdown.append(f"3 weight classes apart: -{penalty}")
    else:
        penalty = settings["very_large_weight_penalty"]
        score -= penalty
        reasons.append("4+ weight classes apart")
        breakdown.append(f"4+ weight classes apart: -{penalty}")

    if weight_diff != 999 and weight_diff > settings["max_safe_weight_diff"]:
        safety_flags.append(f"Weight gap over {settings['max_safe_weight_diff']} lbs")

    if skill_diff == 999:
        reasons.append("skill/belt missing — verify before matching")
        breakdown.append("Unknown skill/belt: 0 (flagged for data review)")
    elif skill_diff == 0:
        reasons.append("same skill/belt")
        breakdown.append("Skill/Belt: 0")
    elif skill_diff == 1:
        penalty = settings["one_skill_penalty"]
        score -= penalty
        reasons.append("one skill/belt level difference")
        breakdown.append(f"One skill/belt level: -{penalty}")
    elif skill_diff <= 3:
        penalty = settings["some_skill_penalty"]
        score -= penalty
        reasons.append("skill/belt difference")
        breakdown.append(f"Skill/belt difference: -{penalty}")
    else:
        penalty = settings["major_skill_penalty"]
        score -= penalty
        reasons.append("major skill/belt difference")
        breakdown.append(f"Major skill/belt difference: -{penalty}")

    if skill_diff != 999 and skill_diff > settings["max_safe_skill_diff"]:
        safety_flags.append(f"Skill gap over {settings['max_safe_skill_diff']} level(s)")

    if age_diff == 999:
        reasons.append("age group missing — verify before matching")
        breakdown.append("Unknown age: 0 (flagged for data review)")
    elif age_diff == 0:
        reasons.append("same age group")
        breakdown.append("Age: 0")
    elif juv_to_adult:
        # Same ballpark as a normal one-age-group step (Adult starts at 18).
        penalty = settings["one_age_penalty"]
        score -= penalty
        reasons.append("Juvenile 16-17 into Adult (organizer step-up rule — confirm approval)")
        breakdown.append(f"Juvenile→Adult age step: -{penalty}")
    elif age_diff == 1:
        penalty = settings["one_age_penalty"]
        score -= penalty
        reasons.append("one age group difference")
        breakdown.append(f"One age group: -{penalty}")
    elif age_diff <= 3:
        penalty = settings["some_age_penalty"]
        score -= penalty
        reasons.append("age group jump")
        breakdown.append(f"Age group jump: -{penalty}")
    else:
        penalty = settings["major_age_penalty"]
        score -= penalty
        reasons.append("major age group jump")
        breakdown.append(f"Major age group jump: -{penalty}")

    # The Juvenile→Adult step counts as 1 and is still subject to the configured limit.
    if age_diff != 999 and age_diff > settings["max_safe_age_diff"]:
        safety_flags.append(f"Age gap over {settings['max_safe_age_diff']} group(s)")

    # Director preference (Juvenile 16-17 → Adult):
    # - Prefer Adult Novice (slightly easier) over Adult Beginner
    # - Prefer same-weight Adult over heavier; lighter Adult is acceptable
    # - Adult options should beat a 20 lb Juvenile jump, but not a 10 lb Juvenile jump
    if juv_to_adult:
        _s_lad, src_sv = skill_rank(src_skill, src_age)
        _t_lad, tgt_sv = skill_rank(tgt_skill, tgt_age)
        same_ladder = _s_lad is not None and _s_lad == _t_lad
        if same_ladder and tgt_sv < src_sv and (src_sv - tgt_sv) <= 1:
            # Moving into a slightly easier Adult skill is intentional — do not
            # keep the normal one-level skill penalty.
            if skill_diff == 1:
                refund = settings["one_skill_penalty"]
                score += refund
                breakdown.append(f"Juvenile→Adult skill penalty waived: +{refund}")
            score += 3
            reasons.append("younger athlete gets skill advantage into Adult")
            breakdown.append("Juvenile→Adult skill advantage: +3")
        if sw is not None and cw is not None:
            if 0 < (sw - cw) <= 10:
                # Soften the adjacent-class penalty for a helpful lighter Adult class.
                if weight_diff <= 10:
                    soften = max(0, settings["adjacent_class_penalty"] - 3)
                    score += soften
                    breakdown.append(f"Juvenile→Adult lighter-class soften: +{soften}")
                score += 2
                reasons.append("younger athlete gets ~1 class weight advantage into Adult")
                breakdown.append("Juvenile→Adult weight advantage: +2")
            elif 0 < (cw - sw) <= 10:
                score -= 2
                reasons.append("Adult target is 1 weight class heavier")
                breakdown.append("Juvenile→Adult heavier target: -2")

    # Director preference (Youth / kids ~4–13): keep same belt/skill whenever possible.
    # Same-belt ±10 / ±20 should outrank a belt change (e.g. White → Grey).
    # Cross-skill remains available as a later Needs Review option.
    youth_kids_move = is_youth_kids_age(src_age) and is_youth_kids_age(tgt_age)
    if youth_kids_move and skill_diff >= 1 and skill_diff != 999:
        extra = 18
        score -= extra
        reasons.append("Youth skill/belt change — prefer same belt when possible")
        breakdown.append(f"Youth same-belt priority: -{extra}")

    # Adult same-skill priority: Intermediate ±10/±20 should beat Beginner/Advanced
    # same-weight targets that only win via target-size bonuses (Caleb case).
    adult_move = is_adult_age(src_age) and is_adult_age(tgt_age)
    if adult_move and skill_diff >= 1 and skill_diff != 999:
        extra = 8
        score -= extra
        reasons.append("Adult skill/belt change — prefer same skill when possible")
        breakdown.append(f"Adult same-skill priority: -{extra}")

        # White Youth into a higher belt: prefer ~10 lb advantage, then same weight,
        # then heavier (still after all same-belt weight options).
        _s_lad, src_sv = skill_rank(src_skill, src_age)
        _t_lad, tgt_sv = skill_rank(tgt_skill, tgt_age)
        if (
            is_white_belt_skill(src_skill)
            and _s_lad is not None
            and _s_lad == _t_lad
            and tgt_sv > src_sv
            and sw is not None
            and cw is not None
        ):
            if 0 < (sw - cw) <= 10:
                if weight_diff <= 10:
                    soften = settings["adjacent_class_penalty"]
                    score += soften
                    breakdown.append(f"Youth White→higher belt lighter-class soften: +{soften}")
                score += 2
                reasons.append("White Youth gets ~10 lb advantage into higher belt")
                breakdown.append("Youth White→higher belt weight advantage: +2")
            elif 0 < (cw - sw) <= 10:
                score -= 3
                reasons.append("White Youth into heavier higher-belt class")
                breakdown.append("Youth White→higher belt heavier: -3")

    academy_mix, academy_count, academy_status = academy_mix_after_move(
        single.get("academy_clean", ""),
        cand.get("academies", ""),
        target_academy_count=cand.get("academy_count"),
        target_athletes=cand.get("athletes"),
    )

    target_size = int(cand.get("athletes", 1))
    academy_warning = ""
    if academy_status == "same" and target_size >= 1:
        penalty = settings["same_academy_penalty"]
        score -= penalty
        academy_warning = "All same academy"
        reasons.append("would create/keep all-same-academy bracket")
        breakdown.append(f"All same academy: -{penalty}")
    elif academy_status == "mixed":
        bonus = settings["mixed_academy_bonus"]
        score += bonus
        reasons.append("mixed academy bracket")
        breakdown.append(f"Mixed academy: +{bonus}")
    elif academy_status == "unknown":
        # Distinct from "All same academy" so UI never claims a false academy conflict.
        academy_warning = "Unknown academy data"
        reasons.append("target academy data missing — verify manually")
        breakdown.append("Target academy data missing: 0 (not marked same-academy)")

    if target_size >= 3:
        bonus = settings["target_size_three_plus_bonus"]
        score += bonus
        reasons.append("target has 3+ athletes")
        breakdown.append(f"Target has 3+ athletes: +{bonus}")
    elif target_size == 2:
        bonus = settings["target_size_two_bonus"]
        score += bonus
        reasons.append("target has 2 athletes")
        breakdown.append(f"Target has 2 athletes: +{bonus}")

    score = max(0, min(100, int(round(score))))
    safety_flag = "; ".join(safety_flags)
    data_gap_text = "; ".join(data_gaps)

    return (
        score, "; ".join(reasons), " | ".join(breakdown), safety_flag,
        weight_diff, age_diff, skill_diff, academy_warning, academy_mix, data_gap_text,
    )


def _academy_lookup_from_df(df):
    """Map group → academy fields using ALL registrations (not only approved).

    Approved-only filtering can hide other academies that still exist in the
    division in Smoothcomp, which previously caused false "Same academy" flags.
    """
    if df is None or df.empty:
        return {}
    full = group_summary(df)
    lookup = {}
    for _, row in full.iterrows():
        lookup[str(row["group"])] = {
            "academies": row.get("academies", ""),
            "academy_count": int(row.get("academy_count", 0) or 0),
        }
    return lookup


def _cand_with_full_academies(cand, academy_lookup):
    """Return a candidate Series/dict enriched with full-file academy data."""
    data = cand.to_dict() if hasattr(cand, "to_dict") else dict(cand)
    info = academy_lookup.get(str(data.get("group", "")), None)
    if info:
        data["academies"] = info["academies"]
        data["academy_count"] = info["academy_count"]
    return data


def make_recommendations(
    df,
    only_approved=True,
    min_target_size=1,
    top_n=3,
    allow_entry_crossover=False,
    scoring_settings=None,
):
    working = apply_approved_filter(df.copy(), only_approved)
    academy_lookup = _academy_lookup_from_df(df)
    if working.empty:
        return pd.DataFrame()
    scoring_settings = with_event_context(scoring_settings, df)

    summary = group_summary(working)
    singles_groups = summary[summary["athletes"] == 1]["group"].tolist()
    target_groups = summary[summary["athletes"] >= min_target_size].copy()
    names_by_group = working.groupby("group_clean")["athlete_name"].agg(set).to_dict()

    rows = []

    for group in singles_groups:
        single = working[working["group_clean"] == group].iloc[0]
        candidates = target_groups[target_groups["group"] != group].copy()

        scored = []
        for _, cand in candidates.iterrows():
            # A second registration for the same athlete is not an opponent.
            target_names = names_by_group.get(cand["group"], set())
            if single["athlete_name"] in target_names:
                continue
            cand_for_score = _cand_with_full_academies(cand, academy_lookup)
            result = score_candidate(single, cand_for_score, allow_entry_crossover, scoring_settings)
            if result is None:
                continue

            (score, why, breakdown, safety_flag, weight_diff, age_diff, skill_diff,
             academy_warning, academy_mix, data_gaps) = result

            risk = risk_badge(score, safety_flag, data_gaps)
            scored.append({
                "Rank": 0,
                "Athlete": single["athlete_name"],
                "Quality": quality_label(score, safety_flag, data_gaps),
                "Risk Badge": risk,
                "Action Plan": action_text("single", group, cand["group"], risk),
                "Match Score": score,
                "Current Division": group,
                "Suggested Division": cand["group"],
                "Before / After": before_after_text(group, 1, cand["group"], cand["athletes"]),
                "Target Athletes": cand["athletes"],
                "Safety Flag": safety_flag,
                "Data Gaps": data_gaps,
                "Academy Warning": academy_warning,
                "Academy Mix": academy_mix,
                "Weight Difference": round(weight_diff, 1) if weight_diff != 999 else "",
                "Age Difference": age_diff if age_diff != 999 else "",
                "Skill Difference": skill_diff if skill_diff != 999 else "",
                "Scoring Breakdown": breakdown,
                "Why": why,
                "Current Entry": single.get("entry_clean", ""),
                "Suggested Entry": cand.get("entry", ""),
                "Current Skill/Belt": single.get("skill_clean", ""),
                "Suggested Skill/Belt": cand.get("skill", ""),
                "Current Age": single.get("age_clean", ""),
                "Suggested Age": cand.get("age", ""),
                "Current Weight": single.get("weight_clean", ""),
                "Suggested Weight": cand.get("weight", ""),
            })

        scored = rank_scored_candidates(scored)[:top_n]

        for rank, row in enumerate(scored, start=1):
            row["Rank"] = rank
            rows.append(row)

    recs = pd.DataFrame(rows)
    if recs.empty:
        return recs

    first_cols = [
        "Rank", "Athlete", "Quality", "Risk Badge", "Action Plan", "Match Score",
        "Current Division", "Suggested Division", "Before / After", "Target Athletes",
        "Safety Flag", "Data Gaps", "Academy Warning", "Academy Mix", "Weight Difference",
        "Age Difference", "Skill Difference", "Scoring Breakdown", "Why",
    ]
    rest = [c for c in recs.columns if c not in first_cols]
    return recs[first_cols + rest]


def score_conflict_candidate(problem, cand, allow_entry_crossover=False, scoring_settings=None):
    problem_as_single = {
        "entry_clean": problem.get("entry", ""),
        "skill_clean": problem.get("skill", ""),
        "age_clean": problem.get("age", ""),
        "weight_clean": problem.get("weight", ""),
        "academy_clean": problem.get("academies", ""),
        "gender_clean": problem.get("gender", ""),
        "group_clean": problem.get("group", ""),
    }
    return score_candidate(problem_as_single, cand, allow_entry_crossover, scoring_settings)


def make_academy_conflict_recommendations(
    df,
    only_approved=True,
    min_target_size=1,
    top_n=3,
    allow_entry_crossover=False,
    scoring_settings=None,
):
    working = apply_approved_filter(df.copy(), only_approved)
    academy_lookup = _academy_lookup_from_df(df)
    if working.empty:
        return pd.DataFrame()
    scoring_settings = with_event_context(scoring_settings, df)

    summary = group_summary(working)
    # Use full-file academy counts so a division isn't flagged as academy-only
    # just because other academies are still pending approval.
    if academy_lookup:
        summary = summary.copy()
        summary["academies"] = summary["group"].map(
            lambda g: academy_lookup.get(str(g), {}).get("academies", "")
        )
        summary["academy_count"] = summary["group"].map(
            lambda g: academy_lookup.get(str(g), {}).get("academy_count", 0)
        )
    conflict_groups = summary[(summary["athletes"] >= 2) & (summary["academy_count"] == 1)].copy()
    target_groups = summary[summary["athletes"] >= min_target_size].copy()
    names_by_group = working.groupby("group_clean")["athlete_name"].agg(set).to_dict()

    rows = []
    for _, problem in conflict_groups.iterrows():
        candidates = target_groups[target_groups["group"] != problem["group"]].copy()
        scored = []

        for _, cand in candidates.iterrows():
            source_names = names_by_group.get(problem["group"], set())
            target_names = names_by_group.get(cand["group"], set())
            if source_names & target_names:
                continue
            cand_for_score = _cand_with_full_academies(cand, academy_lookup)
            result = score_conflict_candidate(problem, cand_for_score, allow_entry_crossover, scoring_settings)
            if result is None:
                continue

            (score, why, breakdown, safety_flag, weight_diff, age_diff, skill_diff,
             academy_warning, academy_mix, data_gaps) = result
            if int(cand_for_score.get("academy_count", 0)) >= 2:
                score = min(100, score + 8)
                why = why + "; target already has mixed academies"
                breakdown = breakdown + " | Mixed target bracket: +8"
            elif int(cand_for_score.get("academy_count", 0)) <= 1:
                score = max(0, score - 10)
                why = why + "; target is also same-academy or missing academy variety"
                breakdown = breakdown + " | Target lacks academy variety: -10"

            risk = risk_badge(score, safety_flag, data_gaps)
            scored.append({
                "Rank": 0,
                "Issue": "All same academy",
                "Quality": quality_label(score, safety_flag, data_gaps),
                "Risk Badge": risk,
                "Action Plan": action_text("conflict", problem["group"], cand["group"], risk),
                "Match Score": score,
                "Problem Division": problem["group"],
                "Suggested Division": cand["group"],
                "Before / After": before_after_text(problem["group"], problem["athletes"], cand["group"], cand["athletes"]),
                "Problem Athletes": problem["athletes"],
                "Target Athletes": cand["athletes"],
                "Problem Academy": problem["academies"],
                "Academy Mix After Merge": academy_mix,
                "Safety Flag": safety_flag,
                "Data Gaps": data_gaps,
                "Weight Difference": round(weight_diff, 1) if weight_diff != 999 else "",
                "Age Difference": age_diff if age_diff != 999 else "",
                "Skill Difference": skill_diff if skill_diff != 999 else "",
                "Scoring Breakdown": breakdown,
                "Why": why,
                "Problem Names": problem["names"],
                "Target Names": cand["names"],
                "Problem Entry": problem.get("entry", ""),
                "Suggested Entry": cand.get("entry", ""),
                "Problem Skill/Belt": problem.get("skill", ""),
                "Suggested Skill/Belt": cand.get("skill", ""),
                "Problem Age": problem.get("age", ""),
                "Suggested Age": cand.get("age", ""),
                "Problem Weight": problem.get("weight", ""),
                "Suggested Weight": cand.get("weight", ""),
            })

        scored = rank_scored_candidates(scored)[:top_n]

        for rank, row in enumerate(scored, start=1):
            row["Rank"] = rank
            rows.append(row)

    recs = pd.DataFrame(rows)
    if recs.empty:
        return recs

    first_cols = [
        "Rank", "Issue", "Quality", "Risk Badge", "Action Plan", "Match Score",
        "Problem Division", "Suggested Division", "Before / After", "Problem Athletes",
        "Target Athletes", "Problem Academy", "Academy Mix After Merge",
        "Safety Flag", "Data Gaps", "Weight Difference", "Age Difference", "Skill Difference",
        "Scoring Breakdown", "Why",
    ]
    rest = [c for c in recs.columns if c not in first_cols]
    return recs[first_cols + rest]


def style_quality_rows(df):
    def row_style(row):
        warning = str(row.get("Academy Warning", "")).lower()
        quality = str(row.get("Quality", "")).lower()
        safety = str(row.get("Safety Flag", "")).lower()

        if safety or "do not match" in quality:
            color = "#fca5a5"
        elif "needs data" in quality:
            color = "#fde68a"
        elif "all same academy" in warning:
            color = "#fecaca"
        elif "excellent" in quality:
            color = "#bbf7d0"
        elif "good" in quality:
            color = "#dcfce7"
        elif "review" in quality:
            color = "#fef08a"
        elif "last" in quality:
            color = "#fecaca"
        elif "no strong" in quality:
            color = "#e5e7eb"
        else:
            color = "#f3f4f6"

        return [f"background-color: {color}; color: #111827;" for _ in row]

    return df.style.apply(row_style, axis=1)


def build_action_plan(recommendations, academy_conflicts=None):
    frames = []

    if recommendations is not None and not recommendations.empty:
        single_cols = [
            "Action Plan", "Risk Badge", "Quality", "Match Score", "Athlete",
            "Current Division", "Suggested Division", "Before / After", "Why",
        ]
        frames.append(recommendations[[c for c in single_cols if c in recommendations.columns]].copy())

    if academy_conflicts is not None and not academy_conflicts.empty:
        conflict_cols = [
            "Action Plan", "Risk Badge", "Quality", "Match Score", "Problem Division",
            "Suggested Division", "Before / After", "Problem Academy", "Why",
        ]
        frames.append(academy_conflicts[[c for c in conflict_cols if c in academy_conflicts.columns]].copy())

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def to_csv_bytes(df):
    return safe_export_frame(df).to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(recommendations, singles, summary, academy_conflicts=None):
    output = BytesIO()
    action_plan = build_action_plan(recommendations, academy_conflicts)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not action_plan.empty:
            safe_export_frame(action_plan).to_excel(writer, index=False, sheet_name="Recommendation report")
        safe_export_frame(recommendations).to_excel(writer, index=False, sheet_name="Recommendations")
        if academy_conflicts is not None and not academy_conflicts.empty:
            safe_export_frame(academy_conflicts).to_excel(writer, index=False, sheet_name="Academy Conflicts")
        safe_export_frame(singles).to_excel(writer, index=False, sheet_name="Singles")
        safe_export_frame(summary).to_excel(writer, index=False, sheet_name="All Groups")
    return output.getvalue()


def demo_raw_dataframe():
    return pd.read_csv(Path(__file__).with_name("smoothcomp_sample.csv"), keep_default_na=False)


def universal_demo_dataframe():
    return pd.DataFrame([
        {
            "Athlete Name": "Alex Rivera",
            "Team": "Freestyle Grapplerz",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Teen",
            "Weight Class": "120 - 130 lbs",
        },
        {
            "Athlete Name": "Jordan Lee",
            "Team": "Oliveira Grappling",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Youth 10-11",
            "Weight Class": "50 - 59 lbs",
        },
        {
            "Athlete Name": "Sam Patel",
            "Team": "Oliveira Grappling",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Youth 10-11",
            "Weight Class": "50 - 59 lbs",
        },
        {
            "Athlete Name": "Cameron Diaz",
            "Team": "West End Grappling",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Youth 10-11",
            "Weight Class": "60 - 69 lbs",
        },
        {
            "Athlete Name": "Devon Brooks",
            "Team": "Northside MMA",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Youth 10-11",
            "Weight Class": "60 - 69 lbs",
        },
        {
            "Athlete Name": "Eli Carter",
            "Team": "Mat Factory",
            "Registration Status": "Approved",
            "Match Type": "No-Gi",
            "Experience Level": "Beginner",
            "Age Group": "Youth 10-11",
            "Weight Class": "60 - 69 lbs",
        },
    ])


def sample_csv_bytes():
    with open("smoothcomp_sample.csv", "rb") as f:
        return f.read()


def get_pending_impact(group_name, approved_summary, full_summary):
    """Return pending-athlete impact info for a single-athlete division."""
    full_match = full_summary[full_summary["group"] == group_name]
    appr_match = approved_summary[approved_summary["group"] == group_name]
    if full_match.empty:
        return {"pending_count": 0, "impact": "none", "label": "—", "short": "—"}
    full_count = int(full_match.iloc[0]["athletes"])
    appr_count = int(appr_match.iloc[0]["athletes"]) if not appr_match.empty else 0
    pending_count = full_count - appr_count
    if pending_count <= 0:
        return {"pending_count": 0, "impact": "none", "label": "—", "short": "—"}
    academies_str = str(full_match.iloc[0]["academies"])
    unique_acad = len([a for a in academies_str.split(",") if a.strip()])
    combined = full_count
    if combined >= 2 and unique_acad >= 2:
        impact = "resolves"
        label = (
            f"✅ {pending_count} not-yet-approved athlete(s) in this division — "
            "if they get approved, this single may get a partner automatically"
        )
        short = f"✅ {pending_count} waiting on approval (may fix itself)"
    elif combined >= 2 and unique_acad < 2:
        impact = "conflict"
        label = (
            f"⚠️ {pending_count} not-yet-approved athlete(s) here, but all from the same academy — "
            "even after approval this may still be an academy conflict"
        )
        short = f"⚠️ {pending_count} waiting (same academy)"
    else:
        impact = "insufficient"
        label = f"⏳ {pending_count} not-yet-approved athlete(s) — not enough yet to fill this division"
        short = f"⏳ {pending_count} waiting on approval"
    return {"pending_count": pending_count, "impact": impact, "label": label, "short": short}


def format_action_plan_text(moves):
    """Return a clean paste-ready action plan string from accepted moves."""
    active = [m for m in moves if m.get("status") == "Active"]
    if not active:
        return ""
    lines = [
        "EZ Brackets — Action Plan (accepted actions only)",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total actions: {len(active)} (one line per athlete)",
        "",
    ]
    for i, m in enumerate(active, 1):
        verb = "Copy" if move_apply_method(m) == "copy" else "Move"
        lines.append(f"{i}. {verb} {m['athlete_name']}")
        if verb == "Copy":
            lines.append(f"   KEEP IN: {m['original_division']}")
            lines.append(f"   COPY TO: {m['new_division']}")
        else:
            lines.append(f"   FROM: {m['original_division']}")
            lines.append(f"   TO:   {m['new_division']}")
        lines.append(f"   Score: {m['score']}")
        if m.get("group_action_id"):
            lines.append("   Part of a whole-division action")
        if m.get("academy_warning"):
            lines.append(f"   ⚠️  {m['academy_warning']}")
        if m.get("director_notes"):
            lines.append(f"   Note: {m['director_notes']}")
        if m.get("applied"):
            lines.append("   Applied: yes")
        lines.append("")
    lines.append("Apply each move in Smoothcomp before publishing brackets.")
    return "\n".join(lines)


def migrate_moves_applied_fields(moves):
    """Ensure older saved moves have applied tracking fields."""
    if not isinstance(moves, list):
        return []
    for m in moves:
        if not isinstance(m, dict):
            continue
        m.setdefault("applied", False)
        m.setdefault("applied_at", "")
        m.setdefault("kind", "single")
        m.setdefault("group_action_id", "")
        # Older sessions were recorded when planned counts assumed a true move.
        m.setdefault("apply_method", "move")
    return moves


def apply_mode_stats(moves):
    """Counts for Apply Mode progress: planned / applied / remaining."""
    migrate_moves_applied_fields(moves)
    active = [m for m in moves if m.get("status") == "Active"]
    applied = sum(1 for m in active if m.get("applied"))
    planned = len(active)
    return {
        "planned": planned,
        "applied": applied,
        "remaining": planned - applied,
    }


def entry_workflow_rank(entry):
    """Gi before No-Gi for Smoothcomp apply / review order."""
    norm = normalize_entry_type(entry)
    if norm == "gi":
        return 0
    if norm == "no-gi":
        return 1
    return 2


def gender_workflow_rank(gender):
    """Mixed/open first (kids), then female, then male."""
    g = str(gender or "").strip().lower()
    if not g or "male/female" in g or g in {"mixed", "open", "any"}:
        return 0
    if g in FEMALE_GENDER_TOKENS or "female" in g or "women" in g or "girl" in g:
        return 1
    if g in MALE_GENDER_TOKENS or "male" in g or "men" in g or "boy" in g:
        return 2
    return 3


def apply_age_cohort(age, group_text=""):
    """Kids/Teens (0) → Adult (1) → Masters (2) for tournament workflow order."""
    text = f"{age} {group_text}".lower()
    if "master" in text:
        return 2
    av = age_value(age)
    if isinstance(av, (int, float)) and av <= 17:
        return 0
    youth_hints = (
        "youth", "teen", "juvenile", "mighty mite", "pee wee",
        "kindergarten", "kids", "pre teen", "junior teen",
    )
    if any(h in text for h in youth_hints):
        return 0
    if "adult" in text:
        return 1
    if isinstance(av, (int, float)) and av < 999:
        return 1 if av >= 18 else 0
    return 1


def workflow_sort_key_for_group(group):
    """Shared bracket order: Kids/Teens Gi → Kids/Teens No-Gi → Adult Gi → …

    Uses the division path the athlete is in now (or the problem division).
    Does not change scoring — queue/apply display only.
    """
    group = str(group or "")
    entry, _skill, age, _weight, gender = parse_group(group)
    return (
        apply_age_cohort(age, group),
        entry_workflow_rank(entry),
        age_value(age),
        gender_workflow_rank(gender),
        group.lower(),
    )


def workflow_sort_key_for_move(move):
    """Apply Mode order from the FROM division so all Gi kids finish before No-Gi.

    Falls back to destination when the source entry type is unknown.
    """
    src = str(move.get("original_division", "") or "")
    dest = str(move.get("new_division", "") or "")
    key = workflow_sort_key_for_group(src)
    if key[1] >= 2:
        dest_key = workflow_sort_key_for_group(dest)
        if dest_key[1] < 2:
            key = dest_key
    return key + (
        dest.lower(),
        str(move.get("athlete_name", "") or "").lower(),
    )


def decision_queue_sort_key(item):
    """Focus/Queue order: stay on Gi kids/teens before jumping to No-Gi.

    Priority (safer first) applies inside the same cohort + entry bucket so
    Adam Newman Gi and Adam Newman No-Gi are not adjacent ahead of other Gi kids.
    """
    cohort, entry_r, age_r, gender_r, group_l = workflow_sort_key_for_group(item.get("group", ""))
    return (
        cohort,
        entry_r,
        int(item.get("priority", 9) or 9),
        age_r,
        gender_r,
        group_l,
        str(item.get("name", "") or "").lower(),
    )


def sorted_active_moves_with_index(moves):
    """Active moves as (original_index, move) sorted for Apply Mode workflow."""
    migrate_moves_applied_fields(moves)
    indexed = [
        (i, m) for i, m in enumerate(moves)
        if isinstance(m, dict) and m.get("status") == "Active"
    ]
    indexed.sort(key=lambda pair: workflow_sort_key_for_move(pair[1]))
    return indexed


def format_apply_why(move):
    """Short why line for Apply Mode companion cards."""
    bits = [f"Score {move.get('score', '?')}/100"]
    aw = str(move.get("academy_warning") or "").strip()
    if aw:
        bits.append(aw if len(aw) <= 70 else aw[:67] + "…")
    notes = str(move.get("director_notes") or "").strip()
    if notes:
        bits.append(notes if len(notes) <= 70 else notes[:67] + "…")
    return " · ".join(bits)


DEFAULT_PUBLIC_NOTE = "Moved, alone in division"


def smoothcomp_copy_fields(division):
    """Split a division path into Smoothcomp Copy Registrations dropdown values."""
    entry, skill, age, weight, _gender = parse_group(division)
    return {
        "entry": str(entry or "").strip(),
        "skill": str(skill or "").strip(),
        "age": str(age or "").strip(),
        "weight": str(weight or "").strip(),
        "full": str(division or "").strip(),
    }


def admin_note_for_move(move):
    """Admin-note paste: original division (where they still sit after Copy)."""
    return str(move.get("original_division", "") or "").strip()


def normalize_smoothcomp_event_url(url):
    """Return a safe http(s) Smoothcomp event URL, or empty string."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        raw = "https://" + raw
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        return ""
    return raw






def build_safety_bullets(rec_row):
    """Return a list of ✅/⚠️ bullet strings for a recommendation row."""
    bullets = []

    def _safe_float(val):
        try:
            return float(val) if val != "" else None
        except (TypeError, ValueError):
            return None

    def _safe_int(val):
        try:
            return int(val) if val != "" else None
        except (TypeError, ValueError):
            return None

    wd = _safe_float(rec_row.get("Weight Difference", ""))
    sd = _safe_int(rec_row.get("Skill Difference", ""))
    ad = _safe_int(rec_row.get("Age Difference", ""))
    aw = str(rec_row.get("Academy Warning", "")).strip()

    if wd is None:
        bullets.append("⚠️ Unknown weight difference")
    elif wd == 0:
        bullets.append("✅ Same weight class")
    else:
        bullets.append(f"⚠️ {wd:g} lbs between weight-class midpoints")

    if sd is None:
        bullets.append("⚠️ Unknown skill level")
    elif sd == 0:
        bullets.append("✅ Same skill/belt level")
    elif sd == 1:
        bullets.append("⚠️ 1 skill level apart")
    else:
        bullets.append(f"⚠️ {sd} skill levels apart")

    if ad is None:
        bullets.append("⚠️ Unknown age group")
    elif ad == 0:
        bullets.append("✅ Same age group")
    elif ad == 1:
        bullets.append("⚠️ 1 age group apart")
    else:
        bullets.append(f"⚠️ {ad} age groups apart")

    aw_low = aw.lower()
    if "unknown academy" in aw_low:
        bullets.append("⚠️ Academy data missing — verify manually")
    elif "same academy" in aw_low:
        bullets.append("⚠️ Same-academy bracket")
    elif aw:
        bullets.append(f"⚠️ {aw}")
    else:
        bullets.append("✅ Mixed academy result")

    return bullets


def trust_summary(rec_row):
    """Plain-language trust summary. Does not change scoring — display only."""
    bullets = build_safety_bullets(rec_row)
    flag = str(rec_row.get("Safety Flag", "")).strip()
    quality = str(rec_row.get("Quality", "")).strip().lower()

    def _num(val):
        try:
            return float(val) if val != "" else None
        except (TypeError, ValueError):
            return None

    wd = _num(rec_row.get("Weight Difference", ""))
    sd = _num(rec_row.get("Skill Difference", ""))
    ad = _num(rec_row.get("Age Difference", ""))
    aw = str(rec_row.get("Academy Warning", "")).strip()

    clean_lines = []
    for b in bullets:
        text = b
        for prefix in ("✅ ", "⚠️ ", "⛔ "):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        text = text.replace("Same skill/belt level", "Same skill")
        text = text.replace("Same age group", "Same age")
        text = text.replace("Mixed academy result", "Mixed academies")
        text = text.replace("Same-academy bracket", "Same academy")
        text = text.replace("Academy data missing — verify manually", "Academy data missing — verify in Smoothcomp")
        text = text.replace("1 skill level apart", "One skill level apart")
        text = text.replace("1 age group apart", "One age group apart")
        text = text.replace("1 weight class apart", "One weight class apart")
        clean_lines.append(text)

    if flag or quality == "do not match":
        return {
            "state": "not-safe",
            "title": "Outside the selected rules",
            "lines": ["Blocked by current safety rules."] + clean_lines[:3],
        }

    data_gaps = str(rec_row.get("Data Gaps", "") or "").strip()
    if data_gaps or wd is None or sd is None or ad is None:
        gap_lines = [g.strip().capitalize() for g in data_gaps.split(";") if g.strip()]
        return {
            "state": "review",
            "title": "Missing information",
            "lines": (gap_lines or ["Required division data is missing."])
            + ["Score is a preference only — not a safety rating.", "Verify in Smoothcomp before moving."],
        }

    # One weight class apart can still be Looks Safe; age/skill gaps or academy warnings need review.
    aw_low = aw.lower()
    needs_review = (
        "review" in quality
        or "last resort" in quality
        or (sd is not None and sd >= 1)
        or (ad is not None and ad >= 1)
        or ("same academy" in aw_low)
        or ("unknown academy" in aw_low)
        or (wd is not None and wd > 10)
    )
    if needs_review:
        lines = clean_lines[:4]
        if "Please verify manually." not in lines:
            lines = lines + ["Please verify manually."]
        return {
            "state": "review",
            "title": "Needs Review",
            "lines": lines,
        }

    return {
        "state": "safe",
        "title": "Fits your selected rules",
        "lines": clean_lines[:4],
    }


def decision_id(kind, group):
    return f"{kind}::{group}"


def parse_decision_id(did):
    did = str(did)
    if "::" in did:
        kind, group = did.split("::", 1)
        return kind, group
    return "single", did


def widget_key_slug(value):
    """Stable Streamlit widget key fragment from a decision id."""
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value))[:96]


def normalize_id_set(values):
    """Normalize skipped/manual sets to decision IDs (supports legacy bare group names)."""
    out = set()
    for v in values or []:
        s = str(v)
        if "::" in s:
            out.add(s)
        else:
            out.add(decision_id("single", s))
            out.add(decision_id("conflict", s))
    return out


def active_moves_only(moves):
    """Return Active (non-reverted) moves."""
    return [m for m in (moves or []) if m.get("status") == "Active"]


def move_apply_method(move):
    """'copy' (keep original registration) or 'move' (remove from original)."""
    method = str((move or {}).get("apply_method", "") or "").strip().lower()
    return "move" if method == "move" else "copy"


def planned_athlete_counts(summary_df, moves):
    """Project Smoothcomp division sizes after Active actions (CSV unchanged).

    One record = one athlete. A *move* removes the athlete from
    ``original_division`` and adds them to ``new_division``. A *copy* keeps the
    original registration, so only the destination grows — matching what staff
    actually see in Smoothcomp after Copy registrations.
    """
    counts = {}
    if summary_df is not None and not summary_df.empty:
        for _, row in summary_df.iterrows():
            counts[str(row["group"])] = int(row["athletes"])
    for m in active_moves_only(moves):
        src = str(m.get("original_division", "") or "").strip()
        dst = str(m.get("new_division", "") or "").strip()
        if src and move_apply_method(m) == "move":
            counts[src] = max(0, int(counts.get(src, 0)) - 1)
        if dst:
            counts[dst] = int(counts.get(dst, 0)) + 1
    return counts


def planned_handled_groups(moves):
    """Source divisions that already have an Active planned action.

    After a *copy* the athlete still sits alone in the original division in
    Smoothcomp, but they have a proposed opponent elsewhere — so the division
    is handled, not still open.
    """
    return {
        str(m.get("original_division", "") or "").strip()
        for m in active_moves_only(moves)
        if str(m.get("original_division", "") or "").strip()
    }


def filter_planned_singles(singles_df, planned_counts, handled_groups=None):
    """Keep only divisions that are still alone AND have no planned action."""
    if singles_df is None or singles_df.empty:
        return singles_df
    handled = set(handled_groups or set())
    mask = singles_df["group"].astype(str).map(
        lambda g: int(planned_counts.get(g, 0)) == 1 and g not in handled
    )
    return singles_df.loc[mask].copy()


def filter_planned_conflict_groups(conflict_df, planned_counts, handled_groups=None):
    """Drop academy-conflict groups that are resolved or already have a planned action."""
    if conflict_df is None or conflict_df.empty:
        return conflict_df
    handled = set(handled_groups or set())
    mask = conflict_df["group"].astype(str).map(
        lambda g: int(planned_counts.get(g, 0)) >= 2 and g not in handled
    )
    return conflict_df.loc[mask].copy()


def athletes_in_group(df, group):
    """Athlete names registered in ``group`` (one entry per registration)."""
    if df is None or df.empty or "group_clean" not in df.columns:
        return []
    rows = df[df["group_clean"].astype(str) == str(group)]
    return [str(n) for n in rows["athlete_name"].astype(str).tolist()]


def revert_move(moves, idx):
    """Revert one action. Group actions (same ``group_action_id``) revert together."""
    if idx is None or idx < 0 or idx >= len(moves):
        return 0
    gid = str(moves[idx].get("group_action_id", "") or "")
    reverted = 0
    for m in moves:
        if m is moves[idx] or (gid and str(m.get("group_action_id", "") or "") == gid):
            if m.get("status") == "Active":
                m["status"] = "Reverted"
                reverted += 1
    return reverted


def build_decision_queue(
    singles_df,
    academy_conflict_groups_df,
    recommendations_df,
    academy_conflict_recommendations_df,
    active_moves,
    skipped_ids,
    manual_ids,
    pending_impacts,
):
    """Build a stable ordered decision queue for Focus / Queue guided views.

    ``singles_df`` / conflict frames should already reflect planned-state
    filtering (destination singles solved by an accepted inbound move removed).
    """
    active_divs = {m["original_division"] for m in active_moves if m.get("status") == "Active"}
    skipped_ids = normalize_id_set(skipped_ids)
    manual_ids = normalize_id_set(manual_ids)

    items = []

    for _, row in singles_df.iterrows():
        group = row["group"]
        did = decision_id("single", group)
        if group in active_divs or did in manual_ids:
            continue
        rec_rows = (
            recommendations_df[
                (recommendations_df["Current Division"] == group)
                & (recommendations_df["Rank"] == 1)
            ]
            if not recommendations_df.empty
            else pd.DataFrame()
        )
        has_rec = not rec_rows.empty
        best = rec_rows.iloc[0] if has_rec else None
        safe = recommendation_is_safe(best) if has_rec else False
        pi = pending_impacts.get(group, {})
        if safe and pi.get("impact") != "resolves":
            priority = 1
        elif safe:
            priority = 2
        else:
            priority = 3
        items.append({
            "id": did,
            "kind": "single",
            "group": group,
            "name": row["names"],
            "academy": row["academies"],
            "best": best,
            "has_rec": has_rec,
            "safe": safe,
            "pending": pi,
            "priority": priority,
            "skipped": did in skipped_ids or decision_id("single", group) in skipped_ids,
        })

    for _, row in academy_conflict_groups_df.iterrows():
        group = row["group"]
        did = decision_id("conflict", group)
        if group in active_divs or did in manual_ids:
            continue
        rec_rows = (
            academy_conflict_recommendations_df[
                (academy_conflict_recommendations_df["Problem Division"] == group)
                & (academy_conflict_recommendations_df["Rank"] == 1)
            ]
            if not academy_conflict_recommendations_df.empty
            else pd.DataFrame()
        )
        has_rec = not rec_rows.empty
        best = rec_rows.iloc[0] if has_rec else None
        safe = recommendation_is_safe(best) if has_rec else False
        priority = 1 if safe else 3
        items.append({
            "id": did,
            "kind": "conflict",
            "group": group,
            "name": row["names"],
            "academy": row["academies"],
            "best": best,
            "has_rec": has_rec,
            "safe": safe,
            "pending": {"pending_count": 0, "impact": "none", "label": ""},
            "priority": priority,
            "skipped": did in skipped_ids,
        })

    active_items = [i for i in items if not i["skipped"]]
    skipped_items = [i for i in items if i["skipped"]]
    # Kids/Teens Gi before Kids/Teens No-Gi (not alphabetical by athlete name).
    active_items.sort(key=decision_queue_sort_key)
    # Skipped go to end of queue
    return active_items + skipped_items


def append_accepted_move(
    athlete_name,
    original_division,
    new_division,
    score,
    academy_warning="",
    *,
    kind="single",
    group_action_id="",
    apply_method=None,
):
    method = apply_method or st.session_state.get("apply_method", "copy")
    st.session_state.setdefault("moves", []).append({
        "athlete_name": athlete_name,
        "original_division": original_division,
        "new_division": new_division,
        "score": int(score),
        "academy_warning": academy_warning or "",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "director_notes": "",
        "status": "Active",
        "applied": False,
        "applied_at": "",
        "kind": kind,
        "group_action_id": group_action_id or "",
        "apply_method": "move" if str(method).lower() == "move" else "copy",
    })


def append_group_move(athlete_names, original_division, new_division, score, academy_warning=""):
    """Accept a whole-division action as one record per athlete.

    Storing ``"a, b, c"`` as a single athlete made headcounts and the staff
    checklist disagree with the recommendation. Each athlete becomes a task.
    """
    names = [str(n).strip() for n in (athlete_names or []) if str(n).strip()]
    if not names:
        return 0
    gid = f"grp-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    for name in names:
        append_accepted_move(
            name, original_division, new_division, score, academy_warning,
            kind="conflict", group_action_id=gid,
        )
    return len(names)


def build_session_payload():
    """Build the current progress payload for Save Progress."""
    migrate_moves_applied_fields(st.session_state.get("moves", []))
    active = [m for m in st.session_state.get("moves", []) if m.get("status") == "Active"]
    skipped = st.session_state.get("guided_skipped", set())
    manual = st.session_state.get("manual_review", set())
    return {
        "ez_brackets_version": "1.0",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "moves": st.session_state.get("moves", []),
        "guided_skipped": list(skipped) if skipped else [],
        "manual_review": list(manual) if manual else [],
        "last_preset": st.session_state.get("last_preset", ""),
        "view_mode": st.session_state.get("view_mode_radio", "🃏 Guided Mode"),
        "guided_layout": st.session_state.get("guided_layout_radio", "Focus Mode"),
        "focus_index": int(st.session_state.get("focus_index", 0) or 0),
        "csv_hash": st.session_state.get("csv_hash", ""),
        "smoothcomp_event_url": st.session_state.get("smoothcomp_event_url", ""),
        "apply_public_note_template": st.session_state.get(
            "apply_public_note_template", DEFAULT_PUBLIC_NOTE
        ),
        "apply_method": st.session_state.get("apply_method", "copy"),
        "rules": collect_rule_settings(),
        "active_moves": len(active),
        "skipped_count": len(skipped),
        "manual_count": len(manual),
        "applied_count": sum(1 for m in active if m.get("applied")),
    }


RULE_SETTING_KEYS = (
    "set_only_approved", "set_min_target_size", "set_top_n", "set_allow_entry_crossover",
    "set_max_safe_weight_diff", "set_max_safe_age_diff", "set_max_safe_skill_diff",
    "set_juvenile_adult_step_up", "set_same_academy_penalty", "set_entry_crossover_penalty",
)


def collect_rule_settings():
    """Snapshot every rule/filter widget so a restored session reproduces the same decisions."""
    out = {}
    for k in RULE_SETTING_KEYS:
        if k in st.session_state:
            v = st.session_state[k]
            out[k] = bool(v) if isinstance(v, bool) else v
    return out


def restore_rule_settings(rules, preset_name=""):
    """Apply saved rule values; mark them as seeded so the preset does not overwrite them."""
    if not isinstance(rules, dict):
        return False
    applied = False
    for k in RULE_SETTING_KEYS:
        if k in rules:
            st.session_state[k] = rules[k]
            applied = True
    if applied and preset_name:
        st.session_state["_rules_seeded_for_preset"] = preset_name
    return applied


def session_has_progress():
    """True when there is anything worth saving/resuming."""
    moves = st.session_state.get("moves", [])
    if any(m.get("status") == "Active" for m in moves):
        return True
    if st.session_state.get("guided_skipped"):
        return True
    if st.session_state.get("manual_review"):
        return True
    return False


def session_to_json(moves, guided_skipped, preset, view_mode, csv_hash="", manual_review=None, guided_layout="", focus_index=0, smoothcomp_event_url="", apply_public_note_template=""):
    """Serialize session state to a JSON-safe dict."""
    migrate_moves_applied_fields(moves)
    return {
        "ez_brackets_version": "1.0",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "moves": moves,
        "guided_skipped": list(guided_skipped) if guided_skipped else [],
        "manual_review": list(manual_review) if manual_review else [],
        "last_preset": preset,
        "view_mode": view_mode,
        "guided_layout": guided_layout or "",
        "focus_index": int(focus_index or 0),
        "csv_hash": csv_hash or "",
        "smoothcomp_event_url": smoothcomp_event_url or "",
        "apply_public_note_template": apply_public_note_template or DEFAULT_PUBLIC_NOTE,
    }


def restore_session_from_json(data):
    """Validate and unpack a session dict. Returns (ok: bool, result_or_error)."""
    if not isinstance(data, dict):
        return False, "File is not a valid EZ Brackets session."
    if data.get("ez_brackets_version") != "1.0":
        return False, "Unrecognized session file version."
    moves = data.get("moves", [])
    if not isinstance(moves, list):
        return False, "Session file is corrupted (moves field invalid)."
    required = {"athlete_name", "original_division", "new_division",
                "score", "academy_warning", "timestamp", "director_notes", "status"}
    for m in moves:
        if not isinstance(m, dict) or not required.issubset(m.keys()):
            return False, "Session file contains invalid move records."
    migrate_moves_applied_fields(moves)
    return True, data


def apply_restored_session(result):
    """Apply validated session data into Streamlit session_state."""
    moves = result["moves"]
    migrate_moves_applied_fields(moves)
    st.session_state["moves"] = moves
    st.session_state["guided_skipped"] = set(result.get("guided_skipped", []))
    st.session_state["manual_review"] = set(result.get("manual_review", []))
    st.session_state["smoothcomp_event_url"] = str(result.get("smoothcomp_event_url", "") or "")
    _pub = str(result.get("apply_public_note_template", "") or "").strip()
    st.session_state["apply_public_note_template"] = _pub or DEFAULT_PUBLIC_NOTE
    _method = str(result.get("apply_method", "") or "").strip().lower()
    if _method in ("copy", "move"):
        st.session_state["apply_method"] = _method
    saved_preset = result.get("last_preset", "")
    if saved_preset in SCORING_PRESETS:
        st.session_state["rule_preset_select"] = saved_preset
        st.session_state["last_preset"] = saved_preset
    restore_rule_settings(result.get("rules"), saved_preset if saved_preset in SCORING_PRESETS else "")
    saved_view = result.get("view_mode", "")
    # Migrate legacy Table Mode label
    if saved_view == "📋 Table Mode":
        saved_view = "📋 Advanced Table View"
    if saved_view in ("🃏 Guided Mode", "📋 Advanced Table View"):
        st.session_state["view_mode_radio"] = saved_view
    else:
        st.session_state["view_mode_radio"] = "🃏 Guided Mode"
    saved_layout = result.get("guided_layout", "")
    if saved_layout in ("Focus Mode", "Queue View"):
        st.session_state["guided_layout_radio"] = saved_layout
    else:
        st.session_state["guided_layout_radio"] = "Focus Mode"
    try:
        st.session_state["focus_index"] = max(0, int(result.get("focus_index", 0) or 0))
    except (TypeError, ValueError):
        st.session_state["focus_index"] = 0
    st.session_state["restore_key_counter"] = st.session_state.get("restore_key_counter", 0) + 1
    st.session_state["restore_csv_hash"] = result.get("csv_hash", "")
    active_n = sum(1 for m in moves if m.get("status") == "Active")
    applied_n = sum(1 for m in moves if m.get("status") == "Active" and m.get("applied"))
    skipped_n = len(result.get("guided_skipped", []) or [])
    manual_n = len(result.get("manual_review", []) or [])
    st.session_state["restore_notice"] = (
        f"Resumed progress — {active_n} move(s) planned"
        + (f" ({applied_n} already applied)" if applied_n else "")
        + f", {skipped_n} skipped, {manual_n} manual review"
        + (f" (saved {result.get('saved_at', '')})" if result.get("saved_at") else "")
        + ". Continue in Focus Mode below."
    )


def try_restore_uploaded_session(uploaded_file):
    """Validate/apply an uploaded session file. Returns error string or None."""
    try:
        data = json.load(uploaded_file)
    except (json.JSONDecodeError, Exception) as exc:
        return f"Could not read session file: {exc}"
    ok, result = restore_session_from_json(data)
    if not ok:
        return result
    apply_restored_session(result)
    return None


def check_move_back_alerts(moves, current_summary):
    alerts = []
    for move in moves:
        if move["status"] != "Active":
            continue
        original_div = move["original_division"]
        athlete = move["athlete_name"]
        match = current_summary[current_summary["group"] == original_div]
        if match.empty:
            continue
        athlete_count = int(match.iloc[0]["athletes"])
        if athlete_count >= 2:
            alerts.append(
                f"Move Alert \u2014 {athlete} was moved out of \u201c{original_div}\u201d. "
                f"That division now has {athlete_count} athlete(s) and may be viable without the move. "
                "Review in the Move Log below."
            )
    return alerts


def reconcile_moves_with_file(moves, df):
    """Compare planned actions with a (new) registration file.

    Returns dict with ``matched`` (athlete still registered in original division),
    ``missing_athlete`` (athlete not found anywhere), ``missing_division``
    (original division no longer in file), ``already_in_destination``.
    """
    out = {"matched": [], "missing_athlete": [], "missing_division": [], "already_in_destination": []}
    if df is None or df.empty or "group_clean" not in df.columns:
        return out
    groups = set(df["group_clean"].astype(str))
    pairs = set(zip(df["athlete_name"].astype(str), df["group_clean"].astype(str)))
    names = set(df["athlete_name"].astype(str))
    for m in active_moves_only(moves):
        name = str(m.get("athlete_name", ""))
        src = str(m.get("original_division", ""))
        dst = str(m.get("new_division", ""))
        if (name, dst) in pairs:
            out["already_in_destination"].append(m)
        elif (name, src) in pairs:
            out["matched"].append(m)
        elif name not in names:
            out["missing_athlete"].append(m)
        elif src not in groups:
            out["missing_division"].append(m)
        else:
            out["matched"].append(m)
    return out




def workflow_backup():
    payload = build_session_payload()
    payload["app_version"] = "1.5.0"
    if "event_df" in st.session_state:
        payload["event"] = {
            "name": st.session_state.get("event_name", "My event"),
            "practice": st.session_state.get("practice", False),
            "registrations": event_frame(st.session_state["event_df"]).to_dict("records"),
        }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def download_backup(key):
    st.download_button(
        "Save event & progress", data=workflow_backup(),
        file_name=f"ez_brackets_{'practice_' if st.session_state.get('practice') else ''}{datetime.now():%Y%m%d_%H%M}.json",
        mime="application/json", key=key,
        help="One file with the registrations, event rules, notes, and every decision. Keep it to resume later.",
    )


def adopt_event(candidate, keep=False):
    if not keep:
        st.session_state["moves"] = []
        st.session_state["guided_skipped"] = set()
        st.session_state["manual_review"] = set()
        st.session_state["smoothcomp_event_url"] = ""
        st.session_state["apply_public_note_template"] = DEFAULT_PUBLIC_NOTE
        st.session_state["focus_index"] = 0
        for key in list(st.session_state):
            if key.startswith(("decision_", "apply_check_", "undo_check_", "plan_note_")):
                del st.session_state[key]
    frame = event_frame(candidate["frame"])
    st.session_state["event_df"] = frame
    st.session_state["event_name"] = candidate["name"].strip() or "My event"
    st.session_state["practice"] = candidate.get("practice", False)
    st.session_state["csv_hash"] = candidate.get("csv_hash") or event_fingerprint(frame)
    st.session_state["has_data"] = True
    st.session_state["show_load"] = False
    st.session_state["workflow_page"] = "2 · Review"
    if not keep:
        has_youth = frame["age_clean"].map(is_youth_kids_age).any()
        st.session_state["rule_preset_select"] = "Kids Conservative" if has_youth else "Adult Standard"
        st.session_state.pop("_rules_seeded_for_preset", None)
        for key in RULE_SETTING_KEYS:
            st.session_state.pop(key, None)
        st.session_state["apply_method"] = "copy"
    for move in active_moves_only(st.session_state.get("moves", [])):
        if action_evidence(move, frame) == "Verified in export":
            move["applied"] = True
            move["applied_at"] = move.get("applied_at") or datetime.now().isoformat(timespec="minutes")
    st.session_state.pop("pending_event", None)


def stage_event(candidate):
    changed = (
        candidate.get("csv_hash") != st.session_state.get("csv_hash")
        or candidate.get("practice", False) != st.session_state.get("practice", False)
    )
    if session_has_progress() and changed:
        st.session_state["pending_event"] = candidate
    else:
        adopt_event(candidate, keep=not changed)
    st.rerun()


def render_load():
    st.caption("EZ BRACKETS · 1 · LOAD YOUR EVENT")
    st.title("Help every athlete find an opponent.")
    st.write("Find divisions that need attention, compare options, and leave with a checklist your staff can follow.")
    cols = st.columns(3)
    for col, title, body in zip(cols, ("Load", "Review", "Apply"), (
        "Bring a registration CSV or use our practice event.",
        "See one decision at a time, with the reason for each suggestion.",
        "Follow the checklist in Smoothcomp and verify the result.",
    )):
        with col:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(body)
    with st.container(border=True):
        st.subheader("New to bracketing? Start here.")
        st.write("A division is a group of athletes with similar age, weight, and experience. An athlete alone in a division has no opponent. We'll help you find options.")
        if st.button("Try a practice event", type="primary", key="start_practice"):
            frame = normalize_dataframe(demo_raw_dataframe())
            stage_event({"frame": frame, "name": "Practice event", "practice": True, "csv_hash": "sample:" + event_fingerprint(frame)})
        st.caption("Practice uses sample registrations. EZ Brackets does not change Smoothcomp.")
    st.subheader("Load your own event")
    source = st.radio("Registration file format", ["Smoothcomp CSV", "Another registration system"], horizontal=True, key="import_source")
    with st.expander("Where do I get this file?"):
        st.write("Open your event's registrations in Smoothcomp and export a CSV containing names, divisions, teams, and registration status. Use a current export of the full event so potential opponents aren't missing.")
        st.link_button("Smoothcomp export help", "https://support.smoothcomp.com/article/109-download-registrations-as-a-csv-file")
        st.download_button("Download a sample CSV", sample_csv_bytes(), "ez_brackets_sample.csv", "text/csv", key="load_template")
    uploaded = st.file_uploader("Choose your registrations CSV", type=["csv"], key="event_csv_upload", max_upload_size=15)
    if uploaded is not None:
        try:
            raw = read_registration_csv(uploaded.getvalue())
        except ValueError as exc:
            st.error(str(exc))
            raw = None
        if raw is not None:
            frame = None
            if source == "Smoothcomp CSV":
                if find_col(raw, ["group", "division", "bracket", "category"]) is None:
                    st.error("We couldn't find a division column. Choose 'Another registration system' above to tell us which columns to use.")
                else:
                    frame = normalize_dataframe(raw)
            else:
                st.write("Match your column names below. Use a full division column, or map all four division fields.")
                mapping = {}
                columns = ["Not in this file"] + list(raw.columns)
                labels = {
                    "name": "Athlete name", "academy": "Team / academy", "status": "Approval status",
                    "group": "Full division", "entry": "Gi / No-Gi", "skill": "Belt / experience",
                    "age": "Age group", "weight": "Weight class",
                }
                map_cols = st.columns(2)
                for i, (field, label) in enumerate(labels.items()):
                    with map_cols[i % 2]:
                        value = st.selectbox(label, columns, key=f"mapping_{field}")
                        mapping[field] = "" if value == columns[0] else value
                selected = [v for v in mapping.values() if v]
                ready = mapping["name"] and (mapping["group"] or all(mapping[k] for k in ("entry", "skill", "age", "weight")))
                if len(set(selected)) != len(selected):
                    st.error("Use a different CSV column for each field.")
                elif ready:
                    frame = normalize_mapped_dataframe(raw, mapping)
                else:
                    st.info("Choose an athlete name and either a full division or all four division fields.")
            if frame is not None:
                errors, notices = import_problems(frame)
                for error in errors:
                    st.error(error)
                for notice in notices:
                    st.info(notice)
                if find_col(raw, ["approved", "status"]) is None:
                    st.info("No approval-status column was found. All registrations in this file will be included.")
                name = st.text_input("Event name", value=Path(uploaded.name).stem.replace("_", " "), key="import_event_name")
                st.caption(f"{len(frame)} registrations · {frame['group_clean'].nunique()} divisions. An athlete entered in Gi and No-Gi has two registrations.")
                with st.expander("Check the first 10 registrations"):
                    st.dataframe(frame[["athlete_name", "academy_clean", "group_clean", "approved_clean"]].head(10), hide_index=True, width="stretch")
                if st.button("Review this event", type="primary", disabled=bool(errors), key="start_uploaded"):
                    stage_event({"frame": frame, "name": name, "practice": False, "csv_hash": hashlib.md5(uploaded.getvalue()).hexdigest() + ":" + event_fingerprint(frame)})
    with st.expander("Continue a saved event", expanded=bool(st.session_state.get("legacy_restore_pending"))):
        st.write("New backups contain your registrations and progress in one file. Older backups also need the original CSV.")
        backup = st.file_uploader("Choose a progress file (.json)", type=["json"], key="backup_import", max_upload_size=100)
        if backup is not None and st.button("Restore saved event", key="restore_backup"):
            try:
                if len(backup.getvalue()) > MAX_BACKUP_BYTES:
                    raise ValueError("The progress file exceeds 100 MB.")
                payload = validate_saved_session(json.loads(backup.getvalue()), SCORING_PRESETS)
                # Restoring is staged as a whole event, so existing progress is never overwritten implicitly.
                st.session_state["pending_restore"] = payload
                st.rerun()
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
    if st.session_state.get("legacy_restore_pending"):
        st.info("Progress restored. Load the matching registration CSV above to continue; it will be checked against your saved actions.")
    if "event_df" in st.session_state and st.button("Back to current event", key="cancel_load"):
        st.session_state["show_load"] = False
        st.rerun()


def render_event_change():
    restore = st.session_state.get("pending_restore")
    if restore is not None:
        st.subheader("Restore this saved event?")
        st.write(f"The backup contains {len(restore['moves'])} recorded actions. Your current work can be saved below before replacing it.")
        if "event_df" in st.session_state:
            download_backup("before_restore")
        if st.button("Use this backup", type="primary", key="confirm_restore"):
            event = restore.get("event")
            if event:
                adopt_event({"frame": pd.DataFrame(event["registrations"]), "name": event["name"], "practice": event.get("practice", False), "csv_hash": restore.get("csv_hash")})
            else:
                st.session_state.pop("event_df", None)
                st.session_state["show_load"] = True
                st.session_state["has_data"] = False
                st.session_state["legacy_restore_pending"] = True
                st.session_state["practice"] = False
            apply_restored_session(restore)
            st.session_state["csv_hash"] = restore.get("csv_hash", "")
            st.session_state["workflow_page"] = "2 · Review"
            st.session_state.pop("pending_restore", None)
            st.rerun()
        if st.button("Cancel", key="cancel_restore"):
            st.session_state.pop("pending_restore", None)
            st.rerun()
        return True
    candidate = st.session_state.get("pending_event")
    if candidate is None:
        return False
    st.subheader("Keep this event's decisions, or start a new event?")
    st.write("An updated export should keep your decisions. A different event should start with a blank plan.")
    download_backup("before_event_change")
    active = active_moves_only(st.session_state.get("moves", []))
    if active:
        evidence = pd.DataFrame([{"Athlete": m["athlete_name"], "New file check": action_evidence(m, candidate["frame"])} for m in active])
        st.dataframe(evidence, hide_index=True, width="stretch")
    practice_changed = candidate.get("practice", False) != st.session_state.get("practice", False)
    if practice_changed:
        st.info("Practice and real-event plans stay separate. Save your current plan, then start the new event.")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Same event · keep decisions", disabled=practice_changed, key="keep_event"):
            adopt_event(candidate, keep=True)
            st.session_state.pop("legacy_restore_pending", None)
            st.rerun()
    with c2:
        if st.button("New event · start fresh", key="new_event"):
            adopt_event(candidate)
            st.session_state.pop("legacy_restore_pending", None)
            st.rerun()
    with c3:
        if st.button("Cancel", key="cancel_event"):
            st.session_state.pop("pending_event", None)
            st.rerun()
    return True


def render_event_settings():
    with st.sidebar:
        st.title("EZ Brackets")
        st.caption("v1.5 · Director workspace")
        st.subheader(st.session_state["event_name"])
        download_backup("sidebar_backup")
        st.caption("Save before closing. Your download contains athlete names and registrations. This version does not autosave.")
        if st.button("Load / restore another file", key="change_event"):
            st.session_state["show_load"] = True
            st.rerun()
        st.divider()
        st.subheader("Rules for this event")
        preset_name = st.selectbox("Rules profile", list(SCORING_PRESETS), key="rule_preset_select")
        preset = SCORING_PRESETS[preset_name]
        if st.session_state.get("_rules_seeded_for_preset") != preset_name:
            for field, value in preset.items():
                st.session_state["set_" + field] = value
            st.session_state["_rules_seeded_for_preset"] = preset_name
        defaults = {"set_only_approved": True, "set_min_target_size": 1, "set_top_n": 3, "set_allow_entry_crossover": False}
        for field, value in defaults.items():
            st.session_state.setdefault(field, value)
        st.session_state["last_preset"] = preset_name
        st.caption("These are suggestion limits. Confirm them against your event's rules. Changing them affects new suggestions; existing decisions stay in your plan.")
        st.radio("When adding an athlete to another division", ["copy", "move"], key="apply_method", format_func=lambda v: "Copy · keep their original entry" if v == "copy" else "Move · remove their original entry")
        with st.expander("Adjust rules and filters"):
            st.checkbox("Only include approved registrations", key="set_only_approved")
            st.slider("Maximum weight gap (lbs)", 5, 60, step=5, key="set_max_safe_weight_diff")
            st.slider("Maximum age-group gap", 0, 5, key="set_max_safe_age_diff")
            st.slider("Maximum belt / experience gap", 0, 5, key="set_max_safe_skill_diff")
            st.checkbox("Allow Juvenile 16–17 → Adult as one age step", key="set_juvenile_adult_step_up")
            st.selectbox("Minimum registrations in a target division", [1, 2, 3], key="set_min_target_size")
            st.slider("Suggestions per decision", 1, 5, key="set_top_n")
            st.checkbox("Include Gi / No-Gi crossover options", key="set_allow_entry_crossover")
            st.slider("Team-only score penalty", 0, 60, step=5, key="set_same_academy_penalty")
            st.slider("Gi / No-Gi crossover score penalty", 0, 60, step=5, key="set_entry_crossover_penalty")
        with st.expander("Bracketing basics"):
            st.markdown("**Division:** athletes grouped by event type, age, weight, and experience.\n\n**Team-only:** everyone in a division trains at the same academy. A director may prefer another opponent.\n\n**Add to plan:** record a decision here.\n\n**Applied:** you completed that action in Smoothcomp.\n\n**Verified:** a later export shows the expected registrations.")
    return {key: st.session_state["set_" + key] for key in preset}


def current_review_data(settings):
    original = st.session_state["event_df"]
    projected, issues = project_registrations(original, st.session_state.get("moves", []), parse_group)
    approved = st.session_state["set_only_approved"]
    working = apply_approved_filter(projected, approved)
    summary = group_summary(working)
    handled = planned_handled_groups(st.session_state.get("moves", []))
    singles = summary[(summary["athletes"] == 1) & ~summary["group"].isin(handled)].copy()
    conflicts = summary[(summary["athletes"] >= 2) & (summary["academy_count"] == 1) & ~summary["group"].isin(handled)].copy()
    # Score the actual eligible, projected roster. Pending athletes are context, not opponents.
    options = dict(only_approved=False, min_target_size=st.session_state["set_min_target_size"], top_n=st.session_state["set_top_n"], allow_entry_crossover=st.session_state["set_allow_entry_crossover"], scoring_settings=with_event_context(settings, original))
    cache_key = event_fingerprint(working) + json.dumps(options, sort_keys=True)
    cache = st.session_state.get("_reports_cache", {})
    if cache.get("key") != cache_key:
        with st.spinner("Checking divisions against your event rules…"):
            cache = {"key": cache_key, "recs": make_recommendations(working, **options), "conflict_recs": make_academy_conflict_recommendations(working, **options)}
        st.session_state["_reports_cache"] = cache
    recs, conflict_recs = cache["recs"], cache["conflict_recs"]
    approved_original = group_summary(apply_approved_filter(original, approved))
    full_original = group_summary(original)
    pending = {r["group"]: get_pending_impact(r["group"], approved_original, full_original) for _, r in singles.iterrows()}
    queue = build_decision_queue(singles, conflicts, recs, conflict_recs, st.session_state.get("moves", []), st.session_state.get("guided_skipped", set()), st.session_state.get("manual_review", set()), pending)
    problem_ids = {decision_id("single", g) for g in singles["group"]} | {decision_id("conflict", g) for g in conflicts["group"]}
    manual = normalize_id_set(st.session_state.get("manual_review", set())) & problem_ids
    return {"working": working, "summary": summary, "singles": singles, "conflicts": conflicts, "recs": recs, "conflict_recs": conflict_recs, "queue": queue, "manual": manual, "issues": issues}


def accept_review_option(item, row, context, acknowledged, notes):
    if str(row.get("Safety Flag", "") or "").strip() or str(row.get("Quality", "")) == "Do Not Match":
        st.error("This option is outside the selected rules and cannot be added.")
        return
    review_needed = trust_summary(row)["state"] != "safe"
    if review_needed and not acknowledged:
        st.error("Check the flagged details and acknowledge the review before adding this action.")
        return
    names = athletes_in_group(context["working"], item["group"])
    old_count = len(st.session_state.get("moves", []))
    if item["kind"] == "conflict":
        append_group_move(names, item["group"], str(row["Suggested Division"]), int(row["Match Score"]), str(row.get("Academy Warning", "")))
    else:
        append_accepted_move(names[0], item["group"], str(row["Suggested Division"]), int(row["Match Score"]), str(row.get("Academy Warning", "")))
    for move in st.session_state["moves"][old_count:]:
        move.update(director_notes=notes, data_gaps=str(row.get("Data Gaps", "")), review_acknowledged=bool(acknowledged), rules_profile=st.session_state["last_preset"])
    st.session_state["guided_skipped"].discard(item["id"])
    st.session_state["manual_review"].discard(item["id"])
    st.session_state["notice"] = f"Added {len(names)} {'action' if len(names) == 1 else 'actions'} to your plan. Apply them in Smoothcomp when ready."
    st.rerun()


def render_manual_items(context):
    if context["manual"]:
        with st.expander(f"Needs a director · {len(context['manual'])}", expanded=not context["queue"]):
            st.write("These divisions still need a decision. Ask the director or coach, then bring the item back to review.")
            for did in sorted(context["manual"]):
                _, group = parse_decision_id(did)
                st.write(group)
                if st.button("Return to review", key="manual_return_" + widget_key_slug(did)):
                    st.session_state["manual_review"].discard(did)
                    st.session_state["focus_index"] = 0
                    st.session_state["pending_workflow_page"] = "2 · Review"
                    st.rerun()


def render_review(context):
    st.header("Review the next decision.")
    st.caption("Adding a suggestion records your plan. It does not update Smoothcomp. A score ranks options; it is not a safety guarantee.")
    queue = context["queue"]
    if not queue:
        if context["manual"]:
            st.warning("The remaining divisions need a director's decision. Review is not finished yet.")
        else:
            st.success("No open alone-athlete or team-only decisions in this view.")
            st.write("Open Apply to work through your plan, then Finish to check the latest export.")
        render_manual_items(context)
        return
    index = min(max(st.session_state.get("focus_index", 0), 0), len(queue) - 1)
    st.session_state["focus_index"] = index
    item = queue[index]
    nav = st.columns([1, 3, 1])
    with nav[0]:
        if st.button("← Previous", disabled=index == 0, key="review_previous"):
            st.session_state["focus_index"] = index - 1
            st.rerun()
    with nav[1]:
        st.write(f"**Decision {index + 1} of {len(queue)}** · {'Team-only division' if item['kind'] == 'conflict' else 'Athlete without an opponent'}")
    with nav[2]:
        if st.button("Next →", disabled=index == len(queue) - 1, key="review_next"):
            st.session_state["focus_index"] = index + 1
            st.rerun()
    if item.get("skipped"):
        st.info("You postponed this decision. It still needs a plan or a director's review.")
    with st.container(border=True):
        st.subheader(item["name"])
        st.caption(item["academy"] or "Team not provided")
        st.write("**Current division**")
        st.write(item["group"])
        if item["kind"] == "conflict":
            st.info("These athletes all come from one team. Adding a suggestion creates a separate action for each athlete.")
        if item["pending"].get("pending_count", 0):
            st.info(item["pending"]["label"])
        source = context["recs"] if item["kind"] == "single" else context["conflict_recs"]
        field = "Current Division" if item["kind"] == "single" else "Problem Division"
        rows = source[source[field].eq(item["group"])].sort_values("Rank") if not source.empty else pd.DataFrame()
        if rows.empty:
            st.warning("No compatible suggestion with the current rules. Ask the director to check this division, wait for another registration, or discuss an alternative with the coach.")
        else:
            row_index = 0
            key = "decision_" + widget_key_slug(item["id"])
            if len(rows) > 1:
                row_index = st.selectbox("Suggested options", list(range(len(rows))), format_func=lambda i: f"Option {i+1} · {rows.iloc[i]['Suggested Division']}", key=key + "_option")
            row = rows.iloc[row_index]
            trust = trust_summary(row)
            st.write("**Suggested division**")
            st.subheader(str(row["Suggested Division"]))
            st.caption(f"{int(row['Target Athletes'])} current opponent registration(s)")
            blocked = bool(str(row.get("Safety Flag", "") or "").strip()) or row.get("Quality") == "Do Not Match"
            (st.error if blocked else st.info if trust["state"] == "review" else st.success)(trust["title"])
            for line in trust["lines"]:
                st.write("• " + line)
            with st.expander("Compare the divisions"):
                prefix = "Current" if item["kind"] == "single" else "Problem"
                comparison = pd.DataFrame({"Detail": ["Gi / No-Gi", "Belt / experience", "Age", "Weight class"], "Current": [row.get(prefix + " " + f, "") for f in ("Entry", "Skill/Belt", "Age", "Weight")], "Suggested": [row.get("Suggested " + f, "") for f in ("Entry", "Skill/Belt", "Age", "Weight")]})
                st.dataframe(comparison, hide_index=True, width="stretch")
                st.caption(f"Preference score: {int(row['Match Score'])}/100. This ranks options; it is not a safety rating.")
                st.caption(str(row.get("Why", "")))
            ack = False
            notes = ""
            if not blocked:
                if trust["state"] != "safe":
                    review_token = hashlib.sha256((str(row.to_dict()) + json.dumps(collect_rule_settings(), sort_keys=True)).encode()).hexdigest()[:12]
                    ack = st.checkbox("I checked the flagged details and any required coach / director approval.", key=key + "_ack_" + review_token)
                notes = st.text_input("Decision note (optional)", placeholder="For example: coach approved the age change", key=key + f"_note_{row_index}")
                method = st.session_state["apply_method"]
                st.caption("This plan will " + ("copy the athlete(s) and keep the original registration." if method == "copy" else "move the athlete(s) out of the original division."))
            if st.button("Add to plan", type="primary", disabled=blocked or (trust["state"] != "safe" and not ack), key=key + "_accept"):
                accept_review_option(item, row, context, ack, notes)
    left, right = st.columns(2)
    with left:
        if st.button("Decide later", key="review_skip"):
            st.session_state["guided_skipped"].add(item["id"])
            st.session_state["focus_index"] = 0
            st.rerun()
    with right:
        if st.button("Ask a director", key="review_manual"):
            st.session_state["manual_review"].add(item["id"])
            st.session_state["guided_skipped"].discard(item["id"])
            st.rerun()
    render_manual_items(context)
    with st.expander("All remaining decisions"):
        for i, other in enumerate(queue):
            st.write(f"{i+1}. {other['name']} · {'Postponed' if other.get('skipped') else 'To review'}")
            if st.button("Open this decision", key="open_decision_" + widget_key_slug(other["id"])):
                st.session_state["focus_index"] = i
                st.rerun()


def staff_plan_frame():
    return pd.DataFrame([{
        "Event": st.session_state["event_name"], "Practice": bool(st.session_state.get("practice")),
        "Athlete": m["athlete_name"], "Action": move_apply_method(m).title(),
        "Original division": m["original_division"], "Destination": m["new_division"],
        "Applied": "Yes" if m.get("applied") else "No",
        "Export check": action_evidence(m, st.session_state["event_df"]),
        "Director note": m.get("director_notes", ""),
        "Data checked": m.get("data_gaps", ""),
    } for m in active_moves_only(st.session_state.get("moves", []))])


def save_plan_note(idx, key):
    st.session_state["moves"][idx]["director_notes"] = st.session_state[key]


def render_plan_log():
    active = sorted_active_moves_with_index(st.session_state.get("moves", []))
    if not active:
        return
    with st.expander(f"Review / undo planned actions · {len(active)}"):
        for idx, move in active:
            st.markdown(f"**{move['athlete_name']}** · {move_apply_method(move).title()} to {move['new_division']}")
            st.caption("Applied in Smoothcomp" if move.get("applied") else "Planned only")
            note_key = f"plan_note_{idx}"
            st.session_state.setdefault(note_key, move.get("director_notes", ""))
            st.text_input("Director note", key=note_key, on_change=save_plan_note, args=(idx, note_key))
            group = [m for m in active_moves_only(st.session_state["moves"]) if m is move or (move.get("group_action_id") and m.get("group_action_id") == move["group_action_id"])]
            applied = any(m.get("applied") for m in group)
            verified = any(action_evidence(m, st.session_state["event_df"]) == "Verified in export" for m in group)
            undo_ok = not applied
            if verified:
                st.caption("To undo a change already shown in this CSV, reverse it in Smoothcomp and load an updated export first.")
            elif applied:
                undo_ok = st.checkbox("I reversed these changes in Smoothcomp first.", key=f"undo_check_{idx}")
            if len(group) > 1:
                st.caption(f"Undo affects all {len(group)} athletes in this group action.")
            if st.button("Undo this plan action", key=f"undo_plan_{idx}", disabled=verified or not undo_ok):
                revert_move(st.session_state["moves"], idx)
                st.rerun()


def render_apply(context):
    st.header("Apply your plan in Smoothcomp.")
    st.write("Keep this checklist beside Smoothcomp. Complete each action there, then mark it done here.")
    url = st.text_input("Smoothcomp event link (optional)", key="smoothcomp_event_url", placeholder="https://smoothcomp.com/en/event/…")
    normalized = normalize_smoothcomp_event_url(url)
    if normalized:
        st.link_button("Open event in Smoothcomp ↗", normalized)
    elif url:
        st.warning("Use an https://smoothcomp.com event link.")
    pending = [(i, m) for i, m in sorted_active_moves_with_index(st.session_state.get("moves", [])) if not m.get("applied")]
    if not active_moves_only(st.session_state.get("moves", [])):
        st.info("Your plan is empty. Add a suggestion from Review first.")
    elif not pending:
        st.success("Every planned action is marked applied. Open Finish to check a fresh export.")
    else:
        idx, move = pending[0]
        method = move_apply_method(move)
        verb = method.title()
        with st.container(border=True):
            st.subheader(f"{verb} {move['athlete_name']}")
            st.caption(f"{len(pending)} action(s) left to apply")
            st.markdown("**1. Find and select this athlete in Smoothcomp.**")
            st.code(move["athlete_name"], language=None)
            st.write("Original division")
            st.code(move["original_division"], language=None)
            st.markdown(f"**2. Choose {verb}.** " + ("Keep the original registration." if method == "copy" else "This removes the original registration."))
            st.markdown("**3. Choose this destination.**")
            st.code(move["new_division"], language=None)
            with st.expander("Individual dropdown values / copyable notes", expanded=True):
                entry, skill, age, weight, _ = parse_group(move["new_division"])
                for label, value in (("Entry", entry), ("Belt / experience", skill), ("Age", age), ("Weight", weight)):
                    st.caption(label)
                    st.code(value or "Check the full destination above", language=None)
                st.caption("Admin note · original division")
                st.code(move["original_division"], language=None)
                if move.get("director_notes"):
                    st.write("Director note: " + move["director_notes"])
            st.markdown(f"**4. Complete {verb} registrations and check the destination.**")
            st.caption("Add an appropriate public note in Smoothcomp so the athlete and coach know about the change.")
            checked = st.checkbox("I completed this in Smoothcomp and checked the destination.", key=f"apply_check_{idx}")
            if st.button("Mark applied · next athlete", type="primary", key="mark_applied", disabled=not checked):
                move["applied"] = True
                move["applied_at"] = datetime.now().isoformat(timespec="minutes")
                st.rerun()
    render_plan_log()


def render_finish(context):
    st.header("Check your work before publishing.")
    unresolved = len(context["queue"]) + len(context["manual"])
    stats = apply_mode_stats(st.session_state.get("moves", []))
    verified = sum(action_evidence(m, st.session_state["event_df"]) == "Verified in export" for m in active_moves_only(st.session_state.get("moves", [])))
    for done, message in (
        (not unresolved, f"Review decisions · {unresolved} still need attention" if unresolved else "Review decisions · no open items in this view"),
        (stats["remaining"] == 0, f"Apply in Smoothcomp · {stats['applied']} of {stats['planned']} actions marked applied"),
        (stats["planned"] > 0 and verified == stats["planned"], f"Verify the export · {verified} of {stats['planned']} actions confirmed in the loaded CSV"),
    ):
        st.write(("✓ " if done else "○ ") + message)
    st.caption("These checks cover your action plan and the divisions this tool reviews. Final event rules, bracket seeding, approvals, and publication remain with the tournament director.")
    if context["issues"]:
        st.error("Some saved actions do not match this roster. Resolve them in Apply before relying on this plan.")
    if unresolved:
        st.warning("There are unfinished decisions. Your handoff includes them so staff can follow up.")
    if st.button("Load a fresh export to verify", key="verify_export"):
        st.session_state["show_load"] = True
        st.rerun()
    render_manual_items(context)
    st.subheader("Save or hand off this event")
    st.write("Save the event file to resume later. Give staff the checklist for actions you have accepted.")
    download_backup("finish_backup")
    active = active_moves_only(st.session_state.get("moves", []))
    if active or unresolved:
        plan = format_action_plan_text(active) or "EZ Brackets — director follow-up\nNo actions accepted yet.\n"
        if st.session_state.get("practice"):
            plan = "PRACTICE EVENT — SAMPLE REGISTRATIONS\n\n" + plan
        plan += f"\n\nUnfinished decisions: {unresolved}\n"
        for item in context["queue"]:
            plan += f"- {'Postponed' if item.get('skipped') else 'To review'}: {item['name']} | {item['group']}\n"
        for did in sorted(context["manual"]):
            plan += "- Needs a director: " + parse_decision_id(did)[1] + "\n"
        st.download_button("Download staff checklist (.txt)", plan.encode("utf-8"), "ez_brackets_staff_checklist.txt", "text/plain", key="staff_txt")
        if active:
            st.download_button("Download accepted actions (.csv)", to_csv_bytes(staff_plan_frame()), "ez_brackets_accepted_actions.csv", "text/csv", key="staff_csv")
    with st.expander("Advanced reports / all registrations"):
        st.caption("Recommendation reports contain suggestions, including blocked options. Only the staff checklist contains your accepted plan.")
        st.dataframe(context["summary"], hide_index=True, width="stretch")
        if st.button("Prepare Excel recommendation report", key="prepare_report"):
            report = to_excel_bytes(context["recs"], context["singles"], context["summary"], context["conflict_recs"])
            st.download_button("Download Excel report", report, "ez_brackets_recommendations.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="excel_report")
        if not context["recs"].empty:
            st.dataframe(style_quality_rows(context["recs"]), hide_index=True, width="stretch")
    render_plan_log()


def run_director_workflow():
    # Persist event settings when their widgets are absent (Load/Restore/other pages).
    # Streamlit otherwise removes those widget keys at the end of that run.
    for key in (*RULE_SETTING_KEYS, "rule_preset_select", "apply_method", "workflow_page", "smoothcomp_event_url"):
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    st.markdown("""<style>
    .block-container {max-width: 1180px; padding-top: 4.5rem; padding-bottom: 4rem;}
    [data-testid="stMetricValue"] {font-size: 1.8rem;}
    [data-testid="stSidebar"] .block-container {padding-top: 1rem;}
    @media(max-width: 700px) {.block-container {padding: 4.5rem 1rem 2rem;} h1 {font-size: 2rem !important;}}
    </style>""", unsafe_allow_html=True)
    for key, default in (("moves", []), ("guided_skipped", set()), ("manual_review", set()), ("focus_index", 0), ("smoothcomp_event_url", ""), ("apply_method", "copy")):
        st.session_state.setdefault(key, default)
    if render_event_change():
        return
    if "event_df" not in st.session_state or st.session_state.get("show_load"):
        render_load()
        return
    settings = render_event_settings()
    context = current_review_data(settings)
    if st.session_state.get("practice"):
        st.info("PRACTICE EVENT · Sample registrations. Use Load / restore another file when you're ready for your own event.")
    st.caption(st.session_state["event_name"])
    if st.session_state.get("notice"):
        st.success(st.session_state.pop("notice"))
    stats = apply_mode_stats(st.session_state.get("moves", []))
    cols = st.columns(3)
    cols[0].metric("Decisions to finish", len(context["queue"]) + len(context["manual"]))
    cols[1].metric("Actions planned", stats["planned"])
    cols[2].metric("Applied in Smoothcomp", stats["applied"])
    if "pending_workflow_page" in st.session_state:
        st.session_state["workflow_page"] = st.session_state.pop("pending_workflow_page")
    st.session_state.setdefault("workflow_page", "2 · Review")
    page = st.radio("Your event workflow", ["2 · Review", "3 · Apply", "4 · Finish"], horizontal=True, key="workflow_page")
    if context["working"].empty:
        st.warning("No registrations match your filters. Turn off 'Only include approved registrations' in Rules → Adjust rules and filters, or load an export with approved athletes.")
        # A filtered-out roster must not imply that all review decisions are done.
        if page != "3 · Apply":
            download_backup("empty_backup")
            return
    if context["issues"] and page == "2 · Review":
        st.error("Some planned actions don't match this file. Open Apply to review or undo those actions, or load the correct event export before adding more decisions.")
        return
    if page == "2 · Review":
        with st.expander("Check the imported data and current rules"):
            frame = st.session_state["event_df"]
            st.write(f"{len(frame)} registrations · {len(context['working'])} included in the planned roster · {st.session_state['last_preset']} rules")
            if not event_has_gender_data(frame):
                st.warning("This file has no division gender labels. Check gender eligibility in Smoothcomp for every Teen / Adult / Masters suggestion.")
            units = frame["weight_clean"].map(weight_unit)
            if units.eq("kg").any():
                st.info("Kilogram weight labels are converted to pounds for comparisons.")
            if units.eq("").any():
                st.info("Weight labels without units are treated as pounds. Check the export if the event uses kilograms.")
            for notice in import_problems(frame)[1]:
                st.info(notice)
        render_review(context)
    elif page == "3 · Apply":
        render_apply(context)
    else:
        render_finish(context)


run_director_workflow()
