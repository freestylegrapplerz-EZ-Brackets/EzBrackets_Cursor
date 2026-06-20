import hashlib
import re
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st


# =========================
# EZ BRACKETS - DEV v2
# =========================

st.set_page_config(
    page_title="EZ Brackets",
    page_icon="🥋",
    layout="wide",
)

st.markdown(
    '''
<style>
    .stApp {
        background: linear-gradient(135deg, #07111f 0%, #0f172a 45%, #111827 100%);
        color: #f8fafc;
    }

    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #f8fafc !important;
    }

    .ez-hero {
        padding: 28px 32px;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(34,197,94,0.18), rgba(59,130,246,0.12));
        border: 1px solid rgba(255,255,255,0.14);
        box-shadow: 0 20px 50px rgba(0,0,0,0.35);
        margin-bottom: 22px;
    }

    .ez-logo-row {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .ez-logo {
        position: relative;
        width: 64px;
        height: 64px;
        border-radius: 18px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 34px;
        font-weight: 900;
        color: white;
        box-shadow: 0 10px 30px rgba(34,197,94,0.35);
    }

    .ez-logo-tm {
        position: absolute;
        top: 7px;
        right: 7px;
        font-size: 8px;
        line-height: 1;
        font-weight: 900;
        color: #ffffff;
        opacity: 0.95;
    }

    .ez-title {
        font-size: 54px;
        line-height: 1;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: -1.5px;
        margin: 0;
    }

    .ez-subtitle {
        font-size: 18px;
        color: #cbd5e1 !important;
        margin-top: 10px;
        max-width: 950px;
    }

    .ez-badge {
        display: inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(34,197,94,0.16);
        color: #bbf7d0 !important;
        border: 1px solid rgba(34,197,94,0.35);
        font-size: 13px;
        font-weight: 700;
        margin-top: 16px;
        margin-right: 8px;
    }

    .metric-card {
        padding: 22px 24px;
        border-radius: 20px;
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 12px 35px rgba(0,0,0,0.28);
        margin-bottom: 16px;
    }

    .metric-label {
        color: #94a3b8 !important;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 6px;
    }

    .metric-value {
        color: #22c55e !important;
        font-size: 44px;
        font-weight: 900;
        line-height: 1;
    }

    .metric-help {
        color: #cbd5e1 !important;
        font-size: 13px;
        margin-top: 8px;
    }

    .section-card {
        padding: 22px;
        border-radius: 20px;
        background: rgba(15,23,42,0.66);
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-top: 16px;
        margin-bottom: 16px;
    }

    .warning-card {
        padding: 18px 20px;
        border-radius: 16px;
        background: rgba(239,68,68,0.13);
        border: 1px solid rgba(239,68,68,0.35);
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .success-card {
        padding: 18px 20px;
        border-radius: 16px;
        background: rgba(34,197,94,0.13);
        border: 1px solid rgba(34,197,94,0.35);
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .small-muted {
        color: #94a3b8 !important;
        font-size: 14px;
    }

    section[data-testid="stSidebar"] {
        background-color: #060b16 !important;
        border-right: 1px solid rgba(255,255,255,0.10);
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
    }

    div[data-baseweb="select"] * {
        color: #111827 !important;
    }

    ul[role="listbox"] {
        background-color: white !important;
    }

    ul[role="listbox"] * {
        color: #111827 !important;
    }

    li[role="option"] {
        color: #111827 !important;
        background-color: white !important;
    }

    li[role="option"]:hover {
        background-color: #e5e7eb !important;
        color: #111827 !important;
    }

    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.97) !important;
        border-radius: 16px;
        padding: 6px;
    }

    [data-testid="stFileUploader"] * {
        color: #111827 !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.12);
    }

    button[kind="secondary"] {
        border-radius: 12px !important;
        border: 1px solid rgba(34,197,94,0.45) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        background-color: rgba(255,255,255,0.06);
        color: #f8fafc !important;
        padding: 10px 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(34,197,94,0.18) !important;
        border-bottom: 3px solid #22c55e !important;
    }

    .ez-compact-header {
        padding: 10px 20px;
        border-radius: 14px;
        background: rgba(15,23,42,0.88);
        border: 1px solid rgba(255,255,255,0.12);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 14px;
    }
    .ez-compact-logo {
        font-size: 18px;
        font-weight: 900;
        color: #22c55e;
        margin-right: 2px;
    }
    .ez-compact-pill {
        padding: 3px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.07);
        color: #94a3b8;
        font-size: 13px;
        white-space: nowrap;
    }
    .ez-compact-pill b { color: #f8fafc; }

    .ez-health-panel {
        padding: 18px 22px;
        border-radius: 20px;
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 16px;
    }
    .ez-health-number {
        font-size: 36px;
        font-weight: 900;
        line-height: 1;
    }
    .ez-health-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .07em;
        margin-top: 4px;
    }
    .ez-card-accept { margin-top: 8px; }
</style>
''',
    unsafe_allow_html=True,
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
    ("Youth", 4),
    ("Pre Teen", 5),
    ("Junior Teen", 6),
    ("Teen", 7),
    ("Juvenile", 8),
    ("Adult", 20),
    ("Master 1", 21),
    ("Master 2", 22),
    ("Master 3", 23),
    ("Master 4", 24),
    ("Master 5", 25),
]


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


def parse_group(group):
    parts = [p.strip() for p in str(group).split("/")]
    return (
        parts[0] if len(parts) > 0 else "",
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else "",
        parts[3] if len(parts) > 3 else "",
    )


def skill_value(skill):
    s = str(skill)
    for key, value in SKILL_ORDER.items():
        if key.lower() in s.lower():
            return value
    return 999


def age_value(age):
    a = str(age)
    for key, value in AGE_ORDER_HINTS:
        if key.lower() in a.lower():
            return value
    nums = re.findall(r"\d+", a)
    return int(nums[0]) if nums else 999


def weight_mid(weight):
    w = str(weight).lower()
    nums = re.findall(r"\d+\.?\d*", w)
    if "over" in w and nums:
        return float(nums[0]) + 10
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2
    if len(nums) == 1:
        return float(nums[0])
    return None


def normalize_dataframe(raw_df):
    df = raw_df.copy()

    group_col = find_col(df, ["group", "division", "bracket", "category"])
    name_col = find_col(df, ["name", "athlete", "competitor", "full name"])
    approved_col = find_col(df, ["approved", "status"])
    academy_col = find_col(df, ["academy", "affiliation", "team", "club", "school"])

    if group_col is None:
        st.error("Could not find a division/group column in this CSV.")
        st.stop()

    df["athlete_name"] = df[name_col].astype(str).str.strip() if name_col else df.index.astype(str)
    df["approved_clean"] = df[approved_col].astype(str).str.strip() if approved_col else "Approved"
    df["academy_clean"] = df[academy_col].astype(str).str.strip() if academy_col else ""
    df["group_clean"] = df[group_col].astype(str).str.strip()

    parsed = df["group_clean"].apply(parse_group)
    df["entry_clean"] = parsed.apply(lambda x: x[0])
    df["skill_clean"] = parsed.apply(lambda x: x[1])
    df["age_clean"] = parsed.apply(lambda x: x[2])
    df["weight_clean"] = parsed.apply(lambda x: x[3])

    return df


def normalize_mapped_dataframe(raw_df, mapping):
    df = raw_df.copy()

    def mapped_series(field, default=""):
        col = mapping.get(field, "")
        if col and col in df.columns:
            return df[col].astype(str).str.strip()
        return pd.Series([default] * len(df), index=df.index)

    df["athlete_name"] = mapped_series("name", "").replace("", pd.NA)
    df["athlete_name"] = df["athlete_name"].fillna(pd.Series(df.index.astype(str), index=df.index))
    df["approved_clean"] = mapped_series("status", "Approved")
    df["academy_clean"] = mapped_series("academy", "")
    df["entry_clean"] = mapped_series("entry", "")
    df["skill_clean"] = mapped_series("skill", "")
    df["age_clean"] = mapped_series("age", "")
    df["weight_clean"] = mapped_series("weight", "")

    group_col = mapping.get("group", "")
    if group_col and group_col in df.columns:
        df["group_clean"] = df[group_col].astype(str).str.strip()
        parsed = df["group_clean"].apply(parse_group)
        df["entry_clean"] = df["entry_clean"].where(df["entry_clean"].str.strip().ne(""), parsed.apply(lambda x: x[0]))
        df["skill_clean"] = df["skill_clean"].where(df["skill_clean"].str.strip().ne(""), parsed.apply(lambda x: x[1]))
        df["age_clean"] = df["age_clean"].where(df["age_clean"].str.strip().ne(""), parsed.apply(lambda x: x[2]))
        df["weight_clean"] = df["weight_clean"].where(df["weight_clean"].str.strip().ne(""), parsed.apply(lambda x: x[3]))
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


def group_summary(df):
    rows = []
    for group, g in df.groupby("group_clean", dropna=False):
        sample = g.iloc[0]
        academies = sorted(set([a for a in g["academy_clean"].dropna().astype(str).tolist() if a.strip()]))
        rows.append({
            "group": group,
            "athletes": len(g),
            "entry": sample.get("entry_clean", ""),
            "skill": sample.get("skill_clean", ""),
            "age": sample.get("age_clean", ""),
            "weight": sample.get("weight_clean", ""),
            "names": ", ".join(g["athlete_name"].astype(str).tolist()),
            "academies": ", ".join(academies),
            "academy_count": len(academies),
        })
    return pd.DataFrame(rows).sort_values(["athletes", "group"]).reset_index(drop=True)


def same_entry(a, b):
    a = str(a).lower()
    b = str(b).lower()
    a_nogi = "no-gi" in a or "no gi" in a
    b_nogi = "no-gi" in b or "no gi" in b
    if "gi" in a and "gi" in b:
        return a_nogi == b_nogi
    return a == b


def academy_mix_after_move(single_academy, target_academies):
    academies = []
    if str(target_academies).strip():
        academies += [a.strip() for a in str(target_academies).split(",") if a.strip()]
    if str(single_academy).strip():
        academies.append(str(single_academy).strip())
    unique = sorted(set([a for a in academies if a]))
    return " + ".join(unique), len(unique)


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
}


SCORING_PRESETS = {
    "Kids Conservative": {
        "max_safe_weight_diff": 10,
        "max_safe_age_diff": 0,
        "max_safe_skill_diff": 0,
        "same_academy_penalty": 45,
        "entry_crossover_penalty": 45,
    },
    "Adult Standard": {
        "max_safe_weight_diff": 20,
        "max_safe_age_diff": 1,
        "max_safe_skill_diff": 1,
        "same_academy_penalty": 35,
        "entry_crossover_penalty": 30,
    },
    "Emergency Merge Mode": {
        "max_safe_weight_diff": 35,
        "max_safe_age_diff": 2,
        "max_safe_skill_diff": 2,
        "same_academy_penalty": 20,
        "entry_crossover_penalty": 20,
    },
    "Freestyle Grapplerz Rules": {
        "max_safe_weight_diff": 20,
        "max_safe_age_diff": 1,
        "max_safe_skill_diff": 1,
        "same_academy_penalty": 40,
        "entry_crossover_penalty": 35,
    },
}


def quality_label(score, safety_flag=""):
    if safety_flag:
        return "Do Not Match"
    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Review"
    if score >= 40:
        return "Last resort"
    return "No strong match"


def risk_badge(score, safety_flag=""):
    if safety_flag:
        return "Do Not Match"
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
    if action_type == "single":
        return f"Move athlete from {source} into {target}."
    return f"Merge problem division {source} into {target}."


def before_after_text(source_label, source_count, target_label, target_count):
    after_count = int(source_count) + int(target_count)
    return f"Before: {source_label} has {source_count}; {target_label} has {target_count}. After: {target_label} would have {after_count}."


def score_candidate(single, cand, allow_entry_crossover=False, scoring_settings=None):
    settings = {**DEFAULT_SCORING_SETTINGS, **(scoring_settings or {})}

    if not allow_entry_crossover and not same_entry(single.get("entry_clean", ""), cand.get("entry", "")):
        return None

    skill_diff = abs(skill_value(single.get("skill_clean", "")) - skill_value(cand.get("skill", "")))
    age_diff = abs(age_value(single.get("age_clean", "")) - age_value(cand.get("age", "")))

    sw = weight_mid(single.get("weight_clean", ""))
    cw = weight_mid(cand.get("weight", ""))
    weight_diff = abs(sw - cw) if sw is not None and cw is not None else 999

    score = 100
    reasons = []
    breakdown = ["Start: 100"]
    safety_flags = []

    if not same_entry(single.get("entry_clean", ""), cand.get("entry", "")):
        penalty = settings["entry_crossover_penalty"]
        score -= penalty
        reasons.append("Gi/No-Gi crossover")
        breakdown.append(f"Entry crossover: -{penalty}")

    if weight_diff == 999:
        penalty = settings["unknown_weight_penalty"]
        score -= penalty
        reasons.append("unknown weight difference")
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

    if skill_diff == 0:
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

    if age_diff == 0:
        reasons.append("same age group")
        breakdown.append("Age: 0")
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

    if age_diff != 999 and age_diff > settings["max_safe_age_diff"]:
        safety_flags.append(f"Age gap over {settings['max_safe_age_diff']} group(s)")

    academy_mix, academy_count = academy_mix_after_move(single.get("academy_clean", ""), cand.get("academies", ""))

    target_size = int(cand.get("athletes", 1))
    academy_warning = ""
    if academy_count <= 1 and target_size >= 1:
        penalty = settings["same_academy_penalty"]
        score -= penalty
        academy_warning = "All same academy"
        reasons.append("would create/keep all-same-academy bracket")
        breakdown.append(f"All same academy: -{penalty}")
    elif academy_count >= 2:
        bonus = settings["mixed_academy_bonus"]
        score += bonus
        reasons.append("mixed academy bracket")
        breakdown.append(f"Mixed academy: +{bonus}")

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

    return score, "; ".join(reasons), " | ".join(breakdown), safety_flag, weight_diff, age_diff, skill_diff, academy_warning, academy_mix


def make_recommendations(
    df,
    only_approved=True,
    min_target_size=1,
    top_n=3,
    allow_entry_crossover=False,
    scoring_settings=None,
):
    working = df.copy()

    if only_approved and "approved_clean" in working.columns:
        approved_mask = working["approved_clean"].astype(str).str.lower().eq("approved")
        if approved_mask.any():
            working = working[approved_mask]

    summary = group_summary(working)
    singles_groups = summary[summary["athletes"] == 1]["group"].tolist()
    target_groups = summary[summary["athletes"] >= min_target_size].copy()

    rows = []

    for group in singles_groups:
        single = working[working["group_clean"] == group].iloc[0]
        candidates = target_groups[target_groups["group"] != group].copy()

        scored = []
        for _, cand in candidates.iterrows():
            result = score_candidate(single, cand, allow_entry_crossover, scoring_settings)
            if result is None:
                continue

            score, why, breakdown, safety_flag, weight_diff, age_diff, skill_diff, academy_warning, academy_mix = result

            risk = risk_badge(score, safety_flag)
            scored.append({
                "Rank": 0,
                "Athlete": single["athlete_name"],
                "Quality": quality_label(score, safety_flag),
                "Risk Badge": risk,
                "Action Plan": action_text("single", group, cand["group"], risk),
                "Match Score": score,
                "Current Division": group,
                "Suggested Division": cand["group"],
                "Before / After": before_after_text(group, 1, cand["group"], cand["athletes"]),
                "Target Athletes": cand["athletes"],
                "Safety Flag": safety_flag,
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

        scored = sorted(scored, key=lambda x: x["Match Score"], reverse=True)[:top_n]

        for rank, row in enumerate(scored, start=1):
            row["Rank"] = rank
            rows.append(row)

    recs = pd.DataFrame(rows)
    if recs.empty:
        return recs

    first_cols = [
        "Rank", "Athlete", "Quality", "Risk Badge", "Action Plan", "Match Score",
        "Current Division", "Suggested Division", "Before / After", "Target Athletes",
        "Safety Flag", "Academy Warning", "Academy Mix", "Weight Difference",
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
    working = df.copy()

    if only_approved and "approved_clean" in working.columns:
        approved_mask = working["approved_clean"].astype(str).str.lower().eq("approved")
        if approved_mask.any():
            working = working[approved_mask]

    summary = group_summary(working)
    conflict_groups = summary[(summary["athletes"] >= 2) & (summary["academy_count"] == 1)].copy()
    target_groups = summary[summary["athletes"] >= min_target_size].copy()

    rows = []
    for _, problem in conflict_groups.iterrows():
        candidates = target_groups[target_groups["group"] != problem["group"]].copy()
        scored = []

        for _, cand in candidates.iterrows():
            result = score_conflict_candidate(problem, cand, allow_entry_crossover, scoring_settings)
            if result is None:
                continue

            score, why, breakdown, safety_flag, weight_diff, age_diff, skill_diff, academy_warning, academy_mix = result
            if int(cand.get("academy_count", 0)) >= 2:
                score = min(100, score + 8)
                why = why + "; target already has mixed academies"
                breakdown = breakdown + " | Mixed target bracket: +8"
            elif int(cand.get("academy_count", 0)) <= 1:
                score = max(0, score - 10)
                why = why + "; target is also same-academy or missing academy variety"
                breakdown = breakdown + " | Target lacks academy variety: -10"

            risk = risk_badge(score, safety_flag)
            scored.append({
                "Rank": 0,
                "Issue": "All same academy",
                "Quality": quality_label(score, safety_flag),
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

        scored = sorted(scored, key=lambda x: x["Match Score"], reverse=True)[:top_n]

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
        "Safety Flag", "Weight Difference", "Age Difference", "Skill Difference",
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
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(recommendations, singles, summary, academy_conflicts=None):
    output = BytesIO()
    action_plan = build_action_plan(recommendations, academy_conflicts)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not action_plan.empty:
            action_plan.to_excel(writer, index=False, sheet_name="Action Plan")
        recommendations.to_excel(writer, index=False, sheet_name="Recommendations")
        if academy_conflicts is not None and not academy_conflicts.empty:
            academy_conflicts.to_excel(writer, index=False, sheet_name="Academy Conflicts")
        singles.to_excel(writer, index=False, sheet_name="Singles")
        summary.to_excel(writer, index=False, sheet_name="All Groups")
    return output.getvalue()


def demo_raw_dataframe():
    return pd.read_csv("smoothcomp_sample.csv")


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
        label = f"✅ {pending_count} pending — may self-resolve (mixed academy)"
        short = f"✅ {pending_count} pending"
    elif combined >= 2 and unique_acad < 2:
        impact = "conflict"
        label = f"⚠️ {pending_count} pending (same academy — conflict remains)"
        short = f"⚠️ {pending_count} pending (conflict)"
    else:
        impact = "insufficient"
        label = f"⏳ {pending_count} pending (not enough to resolve)"
        short = f"⏳ {pending_count} pending"
    return {"pending_count": pending_count, "impact": impact, "label": label, "short": short}


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


def metric_card(label, value, help_text):
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


if not st.session_state.get("has_data", False):
    st.markdown(
        '''
    <div class="ez-hero">
        <div class="ez-logo-row">
            <div class="ez-logo">EZ<span class="ez-logo-tm">TM</span></div>
            <div>
                <div class="ez-title">EZ Brackets</div>
                <div class="ez-subtitle">
                    Smart tournament division matching for Smoothcomp and universal CSVs. Find singles, rank merge options,
                    flag academy-only brackets, and export director-ready reports.
                </div>
                <span class="ez-badge">Single-athlete detection</span>
                <span class="ez-badge">Universal CSV mapping</span>
                <span class="ez-badge">Academy warnings</span>
                <span class="ez-badge">Director reports</span>
            </div>
        </div>
    </div>
    ''',
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download sample CSV template",
        data=sample_csv_bytes(),
        file_name="ez_brackets_sample_template.csv",
        mime="text/csv",
    )
else:
    _cs = st.session_state
    st.markdown(
        f'''<div class="ez-compact-header">
            <span class="ez-compact-logo">🥋 EZ Brackets</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_athlete_count", "—")}</b> athletes</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_singles_count", "—")}</b> singles</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_conflicts_count", "—")}</b> conflicts</span>
            <span class="ez-compact-pill">Preset: <b>{_cs.get("last_preset", "—")}</b></span>
        </div>''',
        unsafe_allow_html=True,
    )

import_mode = st.radio(
    "Choose how you want to load bracket data",
    ["Smoothcomp Auto-Detect", "Universal CSV Mapping", "Use Sample Smoothcomp Data", "Use Sample Universal Data"],
    horizontal=True,
)

uploaded = None
data_ready = False
df = None
hash_changed = False

if import_mode == "Use Sample Smoothcomp Data":
    raw_df = demo_raw_dataframe()
    df = normalize_dataframe(raw_df)
    data_ready = True
    st.info("Sample Smoothcomp-style data loaded. You can test scoring, academy conflicts, and exports without uploading a CSV.")
elif import_mode == "Use Sample Universal Data":
    raw_df = universal_demo_dataframe()
    mapping = {
        "name": "Athlete Name",
        "academy": "Team",
        "status": "Registration Status",
        "group": "",
        "entry": "Match Type",
        "skill": "Experience Level",
        "age": "Age Group",
        "weight": "Weight Class",
    }
    df = normalize_mapped_dataframe(raw_df, mapping)
    data_ready = True
    st.info("Sample universal data loaded. This shows how separate CSV columns can be mapped into EZ Brackets.")
else:
    uploaded = st.file_uploader("Upload registrations CSV", type=["csv"])

    if uploaded:
        _file_bytes = uploaded.getvalue()
        _new_hash = hashlib.md5(_file_bytes).hexdigest()
        _prev_hash = st.session_state.get("csv_hash", "")
        if _new_hash != _prev_hash and _prev_hash != "":
            hash_changed = True
        st.session_state["csv_hash"] = _new_hash
        raw_df = pd.read_csv(BytesIO(_file_bytes))

        if import_mode == "Smoothcomp Auto-Detect":
            df = normalize_dataframe(raw_df)
            data_ready = True
        else:
            columns = raw_df.columns.tolist()
            optional_columns = ["-- Not in CSV --"] + columns

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Map Your CSV Columns")
            st.caption("Choose which columns in your file match the fields EZ Brackets needs.")

            c1, c2 = st.columns(2)
            with c1:
                name_col = st.selectbox("Athlete name column", columns)
                academy_col = st.selectbox("Academy/team column", optional_columns)
                status_col = st.selectbox("Status column", optional_columns)
                group_col = st.selectbox("Existing division/group column", optional_columns)
            with c2:
                entry_col = st.selectbox("Entry type column, like Gi or No-Gi", optional_columns)
                skill_col = st.selectbox("Skill/belt column", optional_columns)
                age_col = st.selectbox("Age group column", optional_columns)
                weight_col = st.selectbox("Weight class column", optional_columns)

            def clean_mapping(value):
                return "" if value == "-- Not in CSV --" else value

            mapping = {
                "name": name_col,
                "academy": clean_mapping(academy_col),
                "status": clean_mapping(status_col),
                "group": clean_mapping(group_col),
                "entry": clean_mapping(entry_col),
                "skill": clean_mapping(skill_col),
                "age": clean_mapping(age_col),
                "weight": clean_mapping(weight_col),
            }

            has_group = bool(mapping["group"])
            has_parts = all(mapping[field] for field in ["entry", "skill", "age", "weight"])

            if has_group or has_parts:
                df = normalize_mapped_dataframe(raw_df, mapping)
                data_ready = True
                st.success("Column mapping looks ready. Recommendations will use these fields.")
            else:
                st.warning("Map either an existing division/group column or all four fields: entry type, skill/belt, age group, and weight class.")

            st.markdown("</div>", unsafe_allow_html=True)

if data_ready:
    if "moves" not in st.session_state:
        st.session_state["moves"] = []
    if "move_back_alerts" not in st.session_state:
        st.session_state["move_back_alerts"] = []
    if "guided_skipped" not in st.session_state:
        st.session_state["guided_skipped"] = set()
    if "has_data" not in st.session_state:
        st.session_state["has_data"] = False

    with st.sidebar:
        st.header("Settings")
        only_approved = st.checkbox("Only analyze approved athletes", value=True)
        min_target_size = st.selectbox(
            "Suggest moving singles into groups with at least:",
            [1, 2, 3],
            index=0,
        )
        top_n = st.slider("Top suggestions per single", min_value=1, max_value=5, value=3)
        allow_entry_crossover = st.checkbox("Show Gi/No-Gi crossover emergency options", value=False)
        st.divider()
        st.subheader("Rule Preset")
        rule_preset = st.selectbox(
            "Choose scoring preset",
            list(SCORING_PRESETS.keys()),
            index=1,
        )
        preset = SCORING_PRESETS[rule_preset]
        st.subheader("Safety Limits")
        max_safe_weight_diff = st.slider("Do Not Match if weight gap is over:", 5, 60, preset["max_safe_weight_diff"], 5)
        max_safe_age_diff = st.slider("Do Not Match if age gap is over:", 0, 5, preset["max_safe_age_diff"])
        max_safe_skill_diff = st.slider("Do Not Match if skill/belt gap is over:", 0, 5, preset["max_safe_skill_diff"])
        st.subheader("Scoring Weights")
        same_academy_penalty = st.slider("Same-academy penalty", 0, 60, preset["same_academy_penalty"], 5)
        entry_crossover_penalty = st.slider("Gi/No-Gi crossover penalty", 0, 60, preset["entry_crossover_penalty"], 5)

    scoring_settings = {
        "max_safe_weight_diff": max_safe_weight_diff,
        "max_safe_age_diff": max_safe_age_diff,
        "max_safe_skill_diff": max_safe_skill_diff,
        "same_academy_penalty": same_academy_penalty,
        "entry_crossover_penalty": entry_crossover_penalty,
    }

    working_df = df.copy()
    if only_approved and "approved_clean" in df.columns:
        approved_df = df[df["approved_clean"].astype(str).str.lower().eq("approved")]
        if not approved_df.empty:
            working_df = approved_df

    summary = group_summary(working_df)
    full_summary = group_summary(df)

    if hash_changed:
        if st.session_state.get("moves"):
            st.session_state["move_back_alerts"] = check_move_back_alerts(
                st.session_state["moves"], summary
            )
        else:
            st.session_state["move_back_alerts"] = []

    singles = summary[summary["athletes"] == 1].copy()

    recommendations = make_recommendations(
        df,
        only_approved=only_approved,
        min_target_size=min_target_size,
        top_n=top_n,
        allow_entry_crossover=allow_entry_crossover,
        scoring_settings=scoring_settings,
    )
    academy_conflict_recommendations = make_academy_conflict_recommendations(
        df,
        only_approved=only_approved,
        min_target_size=min_target_size,
        top_n=top_n,
        allow_entry_crossover=allow_entry_crossover,
        scoring_settings=scoring_settings,
    )

    academy_conflict_groups = summary[(summary["athletes"] >= 2) & (summary["academy_count"] == 1)].copy()

    # Cache stats for compact header (read next render before data_ready is set)
    st.session_state["has_data"] = True
    st.session_state["last_athlete_count"] = len(working_df)
    st.session_state["last_singles_count"] = len(singles)
    st.session_state["last_conflicts_count"] = len(academy_conflict_groups)
    st.session_state["last_preset"] = rule_preset

    # Pending impact for every single division
    _pending_impacts = {
        row["group"]: get_pending_impact(row["group"], summary, full_summary)
        for _, row in singles.iterrows()
    }
    _may_resolve_count = sum(1 for v in _pending_impacts.values() if v["impact"] == "resolves")

    rank1_recommendations = recommendations[recommendations["Rank"] == 1].copy() if not recommendations.empty else pd.DataFrame()
    rank1_conflicts = academy_conflict_recommendations[
        academy_conflict_recommendations["Rank"] == 1
    ].copy() if not academy_conflict_recommendations.empty else pd.DataFrame()
    action_plan = build_action_plan(rank1_recommendations, rank1_conflicts)
    high_confidence_count = 0
    do_not_match_count = 0
    for report in [rank1_recommendations, rank1_conflicts]:
        if not report.empty and "Risk Badge" in report.columns:
            high_confidence_count += report["Risk Badge"].astype(str).eq("Safe Match").sum()
            do_not_match_count += report["Risk Badge"].astype(str).eq("Do Not Match").sum()

    for _alert_msg in st.session_state.get("move_back_alerts", []):
        st.warning(_alert_msg)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Registrations", len(working_df), "Approved athletes currently analyzed")
    with c2:
        metric_card("Groups", len(summary), "Total active divisions/groups found")
    with c3:
        metric_card("Singles", len(singles), "Single-athlete divisions needing review")
    with c4:
        metric_card("Academy Conflicts", len(academy_conflict_groups), "2+ athlete divisions from one academy")

    # ── Event Health Dashboard ────────────────────────────────────────────────
    _active_moves_count = sum(1 for m in st.session_state.get("moves", []) if m["status"] == "Active")
    _total_problems = len(singles) + len(academy_conflict_groups)
    _remaining = _total_problems - _active_moves_count
    _progress_val = _active_moves_count / _total_problems if _total_problems > 0 else 0.0

    if _remaining == 0 and _total_problems > 0:
        _event_status = "✅ Event looks clean"
        _status_color = "#22c55e"
    elif _remaining <= max(1, _total_problems // 4):
        _event_status = "🟡 Almost ready — review remaining items"
        _status_color = "#fbbf24"
    else:
        _event_status = "🔴 Action required"
        _status_color = "#ef4444"

    st.markdown('<div class="ez-health-panel">', unsafe_allow_html=True)
    st.subheader("Event Health")
    st.progress(_progress_val, text=f"{_active_moves_count} of {_total_problems} problems resolved — {_event_status}")
    _h1, _h2, _h3, _h4 = st.columns(4)
    with _h1:
        _c = "#ef4444" if len(singles) > 0 else "#22c55e"
        st.markdown(f'<div class="ez-health-number" style="color:{_c}">{len(singles)}</div><div class="ez-health-label">Singles</div>', unsafe_allow_html=True)
    with _h2:
        _c = "#f97316" if len(academy_conflict_groups) > 0 else "#22c55e"
        st.markdown(f'<div class="ez-health-number" style="color:{_c}">{len(academy_conflict_groups)}</div><div class="ez-health-label">Conflicts</div>', unsafe_allow_html=True)
    with _h3:
        st.markdown(f'<div class="ez-health-number" style="color:#22c55e">{_active_moves_count}</div><div class="ez-health-label">Accepted Moves</div>', unsafe_allow_html=True)
    with _h4:
        _c = "#ef4444" if _may_resolve_count > 0 else "#94a3b8"
        st.markdown(f'<div class="ez-health-number" style="color:{_c}">{_may_resolve_count}</div><div class="ez-health-label">May Self-Resolve</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── View Mode Toggle ──────────────────────────────────────────────────────
    _view_mode = st.radio(
        "View:",
        ["🃏 Guided Mode", "📋 Table Mode"],
        horizontal=True,
        key="view_mode_radio",
    )
    _guided_mode = _view_mode == "🃏 Guided Mode"

    # ── Guided Mode ───────────────────────────────────────────────────────────
    if _guided_mode:
        _active_orig_divs = {
            m["original_division"] for m in st.session_state["moves"] if m["status"] == "Active"
        }
        _skipped = st.session_state.get("guided_skipped", set())

        # Build ordered card list: no-pending first, then pending-may-resolve, then no-safe-match
        _all_singles = singles.copy()
        _unresolved = _all_singles[~_all_singles["group"].isin(_active_orig_divs)]
        _active_not_skipped = _unresolved[~_unresolved["group"].isin(_skipped)]
        _active_skipped = _unresolved[_unresolved["group"].isin(_skipped)]

        def _single_priority(row):
            pi = _pending_impacts.get(row["group"], {})
            grp = row["group"]
            has_rec = not recommendations.empty and (recommendations["Current Division"] == grp).any()
            if pi.get("impact") == "resolves":
                return 2
            if not has_rec:
                return 3
            return 1

        if not _active_not_skipped.empty:
            _active_not_skipped = _active_not_skipped.copy()
            _active_not_skipped["_pri"] = _active_not_skipped.apply(_single_priority, axis=1)
            _active_not_skipped = _active_not_skipped.sort_values("_pri").drop(columns=["_pri"])

        _display_singles = pd.concat([_active_not_skipped, _active_skipped], ignore_index=True)

        # ── Singles cards ──────────────────────────────────────────────────
        if _display_singles.empty and len(academy_conflict_groups) == 0:
            st.markdown('<div class="success-card">All problems resolved for this session.</div>', unsafe_allow_html=True)
        else:
            if not _display_singles.empty:
                st.subheader(f"Singles — {len(_unresolved)} remaining")
            for _ci, (_, _sr) in enumerate(_display_singles.iterrows()):
                _grp = _sr["group"]
                _name = _sr["names"]
                _acad = _sr["academies"]
                _pi = _pending_impacts.get(_grp, {"pending_count": 0, "impact": "none", "label": "—"})
                _is_skipped = _grp in _skipped

                _rec_rows = recommendations[
                    (recommendations["Current Division"] == _grp) & (recommendations["Rank"] == 1)
                ] if not recommendations.empty else pd.DataFrame()
                _has_rec = not _rec_rows.empty
                _best = _rec_rows.iloc[0] if _has_rec else None

                if _pi["impact"] == "resolves":
                    _card_icon = "🟡"
                elif not _has_rec:
                    _card_icon = "⛔"
                elif _is_skipped:
                    _card_icon = "⏭️"
                else:
                    _card_icon = "🔴"

                _card_key = f"sc_{_ci}"
                with st.container(border=True):
                    _ca, _cb = st.columns([3, 1])
                    with _ca:
                        st.markdown(f"**{_card_icon} {_name}** · {_acad}")
                        st.caption(_grp)
                        if _pi["pending_count"] > 0:
                            st.caption(_pi["label"])
                        else:
                            st.caption("— No pending athletes in this division")
                    with _cb:
                        if _has_rec:
                            _q = str(_best["Quality"])
                            _q_color = "#22c55e" if "excellent" in _q.lower() else ("#fbbf24" if "good" in _q.lower() or "review" in _q.lower() else "#94a3b8")
                            st.markdown(f'<div style="text-align:right;font-size:13px;color:{_q_color};font-weight:700">{_q}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div style="text-align:right;font-size:20px;font-weight:900;color:#f8fafc">{int(_best["Match Score"])}</div>', unsafe_allow_html=True)

                    if _has_rec and str(_best.get("Safety Flag", "")).strip() == "":
                        st.markdown(f"**Move to:** {_best['Suggested Division']}")
                        _why_short = str(_best.get("Why", ""))[:120]
                        st.caption(_why_short)
                        if str(_best.get("Academy Warning", "")).strip():
                            st.caption(f"⚠️ Academy: {_best['Academy Warning']}")

                        with st.expander("See other options"):
                            _all_recs = recommendations[recommendations["Current Division"] == _grp].sort_values("Rank")
                            for _, _rr in _all_recs.iterrows():
                                _flag = str(_rr.get("Safety Flag", "")).strip()
                                _lbl = "⛔ Do Not Match" if _flag else f"Rank {int(_rr['Rank'])} · Score {int(_rr['Match Score'])} · {_rr['Quality']}"
                                st.markdown(f"**{_lbl}** → {_rr['Suggested Division']}")
                                st.caption(str(_rr.get("Why", ""))[:100])
                                if not _flag:
                                    if st.button(f"Accept rank {int(_rr['Rank'])}", key=f"{_card_key}_alt_{int(_rr['Rank'])}"):
                                        st.session_state["moves"].append({
                                            "athlete_name": _name,
                                            "original_division": _grp,
                                            "new_division": str(_rr["Suggested Division"]),
                                            "score": int(_rr["Match Score"]),
                                            "academy_warning": str(_rr.get("Academy Warning", "")),
                                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            "director_notes": "",
                                            "status": "Active",
                                        })
                                        st.session_state["guided_skipped"].discard(_grp)
                                        st.rerun()
                    elif _has_rec and str(_best.get("Safety Flag", "")).strip():
                        st.markdown("**⛔ No safe match available** — all options exceed safety limits.")
                        st.caption("Adjust safety sliders in the sidebar or check Table Mode for details.")
                    else:
                        st.markdown("**⛔ No recommendations generated** for this division.")

                    _btn_cols = st.columns([2, 1, 1])
                    with _btn_cols[1]:
                        _skip_label = "Un-skip" if _is_skipped else "Skip ›"
                        if st.button(_skip_label, key=f"{_card_key}_skip"):
                            if _is_skipped:
                                st.session_state["guided_skipped"].discard(_grp)
                            else:
                                st.session_state["guided_skipped"].add(_grp)
                            st.rerun()
                    with _btn_cols[2]:
                        if _has_rec and str(_best.get("Safety Flag", "")).strip() == "":
                            _accept_label = "Accept Anyway ✓" if _pi["impact"] == "resolves" else "✓ Accept"
                            if st.button(_accept_label, key=f"{_card_key}_accept", type="primary"):
                                st.session_state["moves"].append({
                                    "athlete_name": _name,
                                    "original_division": _grp,
                                    "new_division": str(_best["Suggested Division"]),
                                    "score": int(_best["Match Score"]),
                                    "academy_warning": str(_best.get("Academy Warning", "")),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "director_notes": "",
                                    "status": "Active",
                                })
                                st.session_state["guided_skipped"].discard(_grp)
                                st.rerun()

        # ── Academy Conflict cards ─────────────────────────────────────────
        _active_conflict_divs = {
            m["original_division"] for m in st.session_state["moves"] if m["status"] == "Active"
        }
        _unresolved_conflicts = academy_conflict_groups[
            ~academy_conflict_groups["group"].isin(_active_conflict_divs)
        ]
        if not _unresolved_conflicts.empty:
            st.subheader(f"Academy Conflicts — {len(_unresolved_conflicts)} remaining")
            for _cci, (_, _cr) in enumerate(_unresolved_conflicts.iterrows()):
                _cgrp = _cr["group"]
                _cnames = _cr["names"]
                _cacad = _cr["academies"]
                _crec_rows = academy_conflict_recommendations[
                    (academy_conflict_recommendations["Problem Division"] == _cgrp) &
                    (academy_conflict_recommendations["Rank"] == 1)
                ] if not academy_conflict_recommendations.empty else pd.DataFrame()
                _chas_rec = not _crec_rows.empty
                _cbest = _crec_rows.iloc[0] if _chas_rec else None
                _ckey = f"cc_{_cci}"
                with st.container(border=True):
                    _cca, _ccb = st.columns([3, 1])
                    with _cca:
                        st.markdown(f"**🟠 {_cnames}**")
                        st.caption(f"{_cgrp} · Academy: {_cacad}")
                    with _ccb:
                        if _chas_rec:
                            _cq = str(_cbest["Quality"])
                            _cq_color = "#22c55e" if "excellent" in _cq.lower() else "#fbbf24"
                            st.markdown(f'<div style="text-align:right;font-size:13px;color:{_cq_color};font-weight:700">{_cq}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div style="text-align:right;font-size:20px;font-weight:900;color:#f8fafc">{int(_cbest["Match Score"])}</div>', unsafe_allow_html=True)
                    if _chas_rec and str(_cbest.get("Safety Flag", "")).strip() == "":
                        st.markdown(f"**Merge into:** {_cbest['Suggested Division']}")
                        st.caption(str(_cbest.get("Why", ""))[:120])
                        if str(_cbest.get("Academy Mix After Merge", "")).strip():
                            st.caption(f"Result: {_cbest['Academy Mix After Merge']}")
                        _cbtn_cols = st.columns([3, 1])
                        with _cbtn_cols[1]:
                            if st.button("✓ Accept Merge", key=f"{_ckey}_accept", type="primary"):
                                st.session_state["moves"].append({
                                    "athlete_name": _cnames,
                                    "original_division": _cgrp,
                                    "new_division": str(_cbest["Suggested Division"]),
                                    "score": int(_cbest["Match Score"]),
                                    "academy_warning": str(_cbest.get("Academy Mix After Merge", "")),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "director_notes": "",
                                    "status": "Active",
                                })
                                st.rerun()
                    else:
                        st.markdown("**⛔ No safe merge available.**")

        # ── Resolved section ───────────────────────────────────────────────
        _resolved_moves = [m for m in st.session_state["moves"] if m["status"] == "Active"]
        if _resolved_moves:
            with st.expander(f"✅ Accepted this session — {len(_resolved_moves)} move(s)", expanded=False):
                for _ri, _rm in enumerate(_resolved_moves):
                    with st.container(border=True):
                        _rcol1, _rcol2 = st.columns([4, 1])
                        with _rcol1:
                            st.markdown(f"**{_rm['athlete_name']}** → {_rm['new_division']}")
                            st.caption(f"Score: {_rm['score']} · {_rm['timestamp']}")
                            if _rm["director_notes"]:
                                st.caption(f"📝 {_rm['director_notes']}")
                        with _rcol2:
                            _full_idx = next(
                                (i for i, m in enumerate(st.session_state["moves"]) if m is _rm), None
                            )
                            if _full_idx is not None and st.button("↩ Revert", key=f"g_revert_{_full_idx}"):
                                st.session_state["moves"][_full_idx]["status"] = "Reverted"
                                st.rerun()
                        _note_input = st.text_input(
                            "Add note:", key=f"g_note_{_full_idx}",
                            value=_rm["director_notes"],
                            placeholder="Director notes…",
                        )
                        if _note_input != _rm["director_notes"]:
                            if _full_idx is not None:
                                st.session_state["moves"][_full_idx]["director_notes"] = _note_input

        st.divider()

    # ── Table Mode sections (always rendered; primary view when not guided) ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Event Summary")
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Rank #1 Actions", len(action_plan))
    with summary_cols[1]:
        st.metric("Safe Matches", int(high_confidence_count))
    with summary_cols[2]:
        st.metric("Needs Director Review", int(do_not_match_count))
    with summary_cols[3]:
        st.metric("Rule Preset", rule_preset)
    st.caption("Use this as a quick pre-bracket checklist before publishing divisions.")
    if not action_plan.empty:
        with st.expander("Preview Director Action Plan", expanded=False):
            st.dataframe(action_plan, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Single-Athlete Divisions")
    if not singles.empty:
        _singles_display = singles[["group", "athletes", "entry", "skill", "age", "weight", "names", "academies"]].copy()
        _singles_display["Pending Impact"] = _singles_display["group"].map(
            lambda g: _pending_impacts.get(g, {}).get("short", "—")
        )
        st.dataframe(_singles_display, use_container_width=True)
    else:
        st.markdown('<div class="success-card">No single-athlete groups found.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Academy Conflict Divisions")
    st.caption("These are divisions with two or more athletes, but all listed athletes are from one academy.")
    if not academy_conflict_groups.empty:
        st.dataframe(
            academy_conflict_groups[["group", "athletes", "entry", "skill", "age", "weight", "names", "academies"]],
            use_container_width=True,
        )
    else:
        st.markdown('<div class="success-card">No same-academy conflict divisions found.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Recommended Merge Options")
    st.caption("Scores are suggestions only. Use coach/parent approval and safety judgment before moving athletes.")

    if recommendations.empty:
        st.warning("No recommendations generated.")
    else:
        safety_warning_count = recommendations["Safety Flag"].astype(str).str.strip().astype(bool).sum()
        if safety_warning_count:
            st.markdown(
                f'<div class="warning-card">{safety_warning_count} recommendation(s) exceed your safety limits and are marked Do Not Match.</div>',
                unsafe_allow_html=True,
            )

        academy_warning_count = recommendations["Academy Warning"].astype(str).str.contains("same academy", case=False, na=False).sum()
        if academy_warning_count:
            st.markdown(
                f'<div class="warning-card">{academy_warning_count} recommendation(s) include an academy-only bracket warning.</div>',
                unsafe_allow_html=True,
            )

        athlete_options = ["All Athletes"] + sorted(recommendations["Athlete"].dropna().unique().tolist())
        selected_athlete = st.selectbox("Filter by Athlete", athlete_options)

        filtered_recommendations = recommendations.copy()
        if selected_athlete != "All Athletes":
            filtered_recommendations = filtered_recommendations[
                filtered_recommendations["Athlete"] == selected_athlete
            ]

        if st.session_state.get("moves"):
            _active_move_keys = {
                (m["athlete_name"], m["original_division"])
                for m in st.session_state["moves"]
                if m["status"] == "Active"
            }
            filtered_recommendations = filtered_recommendations[
                ~filtered_recommendations.apply(
                    lambda r: (r["Athlete"], r["Current Division"]) in _active_move_keys,
                    axis=1,
                )
            ]

        best_matches = filtered_recommendations[filtered_recommendations["Rank"] == 1].copy()

        _basic_view = st.checkbox(
            "Simplified view",
            value=False,
            key="basic_view_checkbox",
            help="Show only Athlete, Current Division, Suggested Division, Why, and Quality.",
        )
        _BASIC_COLS = ["Athlete", "Current Division", "Suggested Division", "Why", "Quality"]

        tab1, tab2, tab3 = st.tabs(["Best Match Only", "All Suggestions", "Export"])

        with tab1:
            _disp_best = (
                best_matches[[c for c in _BASIC_COLS if c in best_matches.columns]]
                if _basic_view else best_matches
            )
            st.dataframe(style_quality_rows(_disp_best), use_container_width=True)

            if not best_matches.empty:
                st.divider()
                _accept_col1, _accept_col2 = st.columns([4, 1])
                _accept_options = ["— select athlete —"] + sorted(
                    best_matches["Athlete"].dropna().unique().tolist()
                )
                with _accept_col1:
                    _athlete_to_accept = st.selectbox(
                        "Accept a move:",
                        _accept_options,
                        key="accept_athlete_selectbox",
                    )
                with _accept_col2:
                    st.write("")
                    _accept_clicked = st.button(
                        "\u2713 Accept Move",
                        disabled=(_athlete_to_accept == "— select athlete —"),
                        key="accept_move_btn",
                    )
                if _accept_clicked and _athlete_to_accept != "— select athlete —":
                    _row = best_matches[best_matches["Athlete"] == _athlete_to_accept].iloc[0]
                    st.session_state["moves"].append({
                        "athlete_name": _athlete_to_accept,
                        "original_division": str(_row["Current Division"]),
                        "new_division": str(_row["Suggested Division"]),
                        "score": int(_row["Match Score"]),
                        "academy_warning": str(_row.get("Academy Warning", "")),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "director_notes": "",
                        "status": "Active",
                    })
                    st.rerun()

        with tab2:
            _disp_all = (
                filtered_recommendations[[c for c in _BASIC_COLS if c in filtered_recommendations.columns]]
                if _basic_view else filtered_recommendations
            )
            st.dataframe(style_quality_rows(_disp_all), use_container_width=True)

        with tab3:
            st.markdown("### Director Report")
            st.write("Download reports your staff can use to make bracket updates.")
            rank1_all = recommendations[recommendations["Rank"] == 1].copy()
            rank1_conflicts = academy_conflict_recommendations[
                academy_conflict_recommendations["Rank"] == 1
            ].copy() if not academy_conflict_recommendations.empty else pd.DataFrame()
            export_action_plan = build_action_plan(rank1_all, rank1_conflicts)

            if not export_action_plan.empty:
                st.download_button(
                    "Download Action Plan CSV",
                    data=to_csv_bytes(export_action_plan),
                    file_name="ez_brackets_action_plan.csv",
                    mime="text/csv",
                )

            st.download_button(
                "Download Rank #1 Excel Report",
                data=to_excel_bytes(
                    rank1_all,
                    singles,
                    summary,
                    rank1_conflicts,
                ),
                file_name="ez_brackets_rank1_recommendations.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.download_button(
                "Download All Suggestions CSV",
                data=to_csv_bytes(recommendations),
                file_name="ez_brackets_all_single_suggestions.csv",
                mime="text/csv",
            )

            if not academy_conflict_recommendations.empty:
                st.download_button(
                    "Download Academy Conflict CSV",
                    data=to_csv_bytes(academy_conflict_recommendations),
                    file_name="ez_brackets_academy_conflicts.csv",
                    mime="text/csv",
                )

            st.download_button(
                "Download Full Excel Report",
                data=to_excel_bytes(recommendations, singles, summary, academy_conflict_recommendations),
                file_name="ez_brackets_full_recommendations.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown(
            '<div class="small-muted">Color Key: Green = Excellent / Good | Yellow = Review | Red = Last Resort, Academy Warning, or Do Not Match | Gray = No Strong Match</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Academy Conflict Merge Options")
    st.caption("Use these when a bracket has 2+ athletes from one academy and may be better merged with a nearby mixed bracket.")

    if academy_conflict_recommendations.empty:
        st.warning("No academy conflict merge options generated.")
    else:
        conflict_options = ["All Problem Divisions"] + sorted(
            academy_conflict_recommendations["Problem Division"].dropna().unique().tolist()
        )
        selected_conflict = st.selectbox("Filter by Problem Division", conflict_options)

        filtered_conflicts = academy_conflict_recommendations.copy()
        if selected_conflict != "All Problem Divisions":
            filtered_conflicts = filtered_conflicts[
                filtered_conflicts["Problem Division"] == selected_conflict
            ]

        best_conflicts = filtered_conflicts[filtered_conflicts["Rank"] == 1].copy()
        conflict_tab1, conflict_tab2 = st.tabs(["Best Conflict Fixes", "All Conflict Suggestions"])

        with conflict_tab1:
            st.dataframe(style_quality_rows(best_conflicts), use_container_width=True)

        with conflict_tab2:
            st.dataframe(style_quality_rows(filtered_conflicts), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("moves"):
        _active_count = sum(1 for m in st.session_state["moves"] if m["status"] == "Active")
        _total_count = len(st.session_state["moves"])

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Move Log")
        st.caption(
            f"{_active_count} active move(s) \u00b7 {_total_count} total this session. "
            "Accepted moves are removed from the recommendation table until reverted."
        )

        _move_df = pd.DataFrame(st.session_state["moves"])
        _move_display = _move_df.rename(columns={
            "athlete_name": "Athlete",
            "original_division": "Original Division",
            "new_division": "New Division",
            "score": "Score",
            "academy_warning": "Academy Warning",
            "timestamp": "Accepted",
            "director_notes": "Notes",
            "status": "Status",
        })
        st.dataframe(
            _move_display[[
                "Athlete", "Original Division", "New Division",
                "Score", "Academy Warning", "Accepted", "Notes", "Status",
            ]],
            use_container_width=True,
        )

        st.divider()
        _note_labels = [
            f"{i + 1}. {m['athlete_name']} \u2192 {m['new_division']} ({m['timestamp']})"
            for i, m in enumerate(st.session_state["moves"])
        ]
        _note_col1, _note_col2, _note_col3 = st.columns([2, 3, 1])
        with _note_col1:
            _selected_note = st.selectbox("Add notes to:", _note_labels, key="notes_move_select")
        with _note_col2:
            _new_note = st.text_input(
                "Notes:",
                key="notes_text_input",
                placeholder="Type director notes and click Save\u2026",
            )
        with _note_col3:
            st.write("")
            if st.button("Save Notes", key="save_notes_btn"):
                _note_idx = _note_labels.index(_selected_note)
                st.session_state["moves"][_note_idx]["director_notes"] = _new_note
                st.session_state["notes_text_input"] = ""
                st.rerun()

        _active_moves_for_revert = [
            (i, m) for i, m in enumerate(st.session_state["moves"])
            if m["status"] == "Active"
        ]
        if _active_moves_for_revert:
            _revert_labels = [
                f"{_idx + 1}. {m['athlete_name']} \u2192 {m['new_division']}"
                for _idx, m in _active_moves_for_revert
            ]
            _revert_col1, _revert_col2 = st.columns([4, 1])
            with _revert_col1:
                _revert_choice = st.selectbox(
                    "Revert a move:", _revert_labels, key="revert_move_select"
                )
            with _revert_col2:
                st.write("")
                if st.button("Revert", key="revert_move_btn"):
                    for _ri, (_idx, _m) in enumerate(_active_moves_for_revert):
                        if _revert_labels[_ri] == _revert_choice:
                            st.session_state["moves"][_idx]["status"] = "Reverted"
                            break
                    st.rerun()

        st.divider()
        st.download_button(
            "Download Move Log CSV",
            data=to_csv_bytes(_move_display[[
                "Athlete", "Original Division", "New Division",
                "Score", "Academy Warning", "Accepted", "Notes", "Status",
            ]]),
            file_name="ez_brackets_move_log.csv",
            mime="text/csv",
            key="download_move_log_btn",
        )

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown(
        '<div class="section-card">Upload a Smoothcomp CSV, map columns from another registration system, or choose demo data to begin analyzing divisions.</div>',
        unsafe_allow_html=True,
    )
