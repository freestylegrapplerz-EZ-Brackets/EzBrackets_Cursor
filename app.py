import hashlib
import json
import re
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st


# =========================
# EZ BRACKETS - v1.3.2
# Apply Mode mirrors Smoothcomp Copy + dropdowns + notes
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

    h1, h2, h3, h4, h5, h6, p, label {
        color: #f8fafc !important;
    }

    /* Keep custom HTML spans light, but do not force button/widget text white */
    .ez-hero span,
    .ez-badge,
    .ez-compact-header span,
    .metric-card span,
    .section-card > span,
    .ez-health-panel span {
        color: inherit;
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

    /* Dark-theme friendly buttons — fix white boxes with invisible labels */
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stBaseButton-secondary"] > button,
    .stButton > button[kind="secondary"],
    button[kind="secondary"] {
        border-radius: 12px !important;
        background-color: rgba(15, 23, 42, 0.95) !important;
        border: 1px solid rgba(34, 197, 94, 0.55) !important;
        color: #bbf7d0 !important;
    }

    div[data-testid="stDownloadButton"] > button *,
    div[data-testid="stBaseButton-secondary"] > button *,
    .stButton > button[kind="secondary"] *,
    button[kind="secondary"] * {
        color: #bbf7d0 !important;
    }

    div[data-testid="stDownloadButton"] > button:hover,
    .stButton > button[kind="secondary"]:hover,
    button[kind="secondary"]:hover {
        background-color: rgba(34, 197, 94, 0.22) !important;
        border-color: rgba(34, 197, 94, 0.85) !important;
        color: #ecfdf5 !important;
    }

    div[data-testid="stDownloadButton"] > button:hover *,
    .stButton > button[kind="secondary"]:hover *,
    button[kind="secondary"]:hover * {
        color: #ecfdf5 !important;
    }

    .stButton > button[kind="primary"],
    button[kind="primary"] {
        border-radius: 12px !important;
        background-color: #16a34a !important;
        border: 1px solid #22c55e !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"] *,
    button[kind="primary"] * {
        color: #ffffff !important;
    }

    /* Radio / checkbox labels stay readable on dark background */
    div[data-testid="stRadio"] label p,
    div[data-testid="stCheckbox"] label p {
        color: #f8fafc !important;
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

    .ez-sticky-progress {
        position: sticky;
        top: 0;
        z-index: 40;
        padding: 10px 16px;
        border-radius: 14px;
        background: rgba(6, 11, 22, 0.94);
        border: 1px solid rgba(255,255,255,0.12);
        backdrop-filter: blur(8px);
        margin-bottom: 14px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px 12px;
        align-items: center;
    }
    .ez-sticky-progress .ez-pill {
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.07);
        color: #cbd5e1;
        font-size: 13px;
        font-weight: 600;
    }
    .ez-sticky-progress .ez-pill b { color: #f8fafc; }
    .ez-sticky-progress .ez-pill-green { background: rgba(34,197,94,0.16); color: #bbf7d0; }
    .ez-sticky-progress .ez-pill-amber { background: rgba(251,191,36,0.16); color: #fde68a; }
    .ez-sticky-progress .ez-pill-red { background: rgba(239,68,68,0.16); color: #fecaca; }

    .ez-save-panel {
        padding: 14px 16px;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(14, 116, 144, 0.22), rgba(15, 23, 42, 0.88));
        border: 1px solid rgba(56, 189, 248, 0.35);
        margin: 0 0 16px 0;
    }
    .ez-save-panel h4 {
        margin: 0 0 4px 0;
        color: #e0f2fe;
        font-size: 16px;
    }
    .ez-save-panel p {
        margin: 0 0 10px 0;
        color: #94a3b8;
        font-size: 13px;
    }

    .ez-focus-card {
        padding: 22px 24px 18px 24px;
        border-radius: 20px;
        background: rgba(15,23,42,0.88);
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 14px 40px rgba(0,0,0,0.35);
        margin: 8px 0 14px 0;
    }
    .ez-focus-card.safe {
        border-left: 5px solid #22c55e;
        background: linear-gradient(90deg, rgba(34,197,94,0.10), rgba(15,23,42,0.88) 40%);
    }
    .ez-focus-card.review {
        border-left: 5px solid #fbbf24;
        background: linear-gradient(90deg, rgba(251,191,36,0.10), rgba(15,23,42,0.88) 40%);
    }
    .ez-focus-card.not-safe {
        border-left: 5px solid #ef4444;
        background: linear-gradient(90deg, rgba(239,68,68,0.10), rgba(15,23,42,0.88) 40%);
    }
    .ez-focus-athlete {
        font-size: 22px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .ez-focus-meta {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 14px;
    }
    .ez-focus-from {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 6px;
    }
    .ez-focus-to {
        font-size: 26px;
        font-weight: 900;
        color: #86efac;
        line-height: 1.25;
        margin: 4px 0 14px 0;
    }
    .ez-trust-title {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 6px;
    }
    .ez-trust-title.safe { color: #4ade80; }
    .ez-trust-title.review { color: #fbbf24; }
    .ez-trust-title.not-safe { color: #f87171; }
    .ez-trust-line {
        color: #cbd5e1;
        font-size: 14px;
        margin-bottom: 2px;
    }
    .ez-score-box {
        text-align: right;
    }
    .ez-score-label {
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .ez-score-value {
        font-size: 34px;
        font-weight: 900;
        color: #f8fafc;
        line-height: 1;
    }
    .ez-manual-banner {
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.35);
        margin: 8px 0 12px 0;
    }
    .ez-compact-row {
        padding: 8px 12px;
        border-radius: 10px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
    }
    .ez-complete-panel {
        padding: 22px 24px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(34,197,94,0.16), rgba(15,23,42,0.9));
        border: 1px solid rgba(34,197,94,0.4);
        margin: 12px 0 18px 0;
    }
    .ez-apply-panel {
        padding: 22px 24px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(59,130,246,0.14), rgba(15,23,42,0.92));
        border: 1px solid rgba(59,130,246,0.35);
        margin: 12px 0 18px 0;
    }
    .ez-apply-next {
        padding: 18px 20px;
        border-radius: 16px;
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(34,197,94,0.45);
        margin: 10px 0 14px 0;
    }
    .ez-apply-athlete {
        font-size: 26px;
        font-weight: 900;
        color: #f8fafc;
        line-height: 1.2;
        margin: 0 0 8px 0;
    }
    .ez-apply-path {
        color: #cbd5e1;
        font-size: 14px;
        margin: 0 0 4px 0;
    }
    .ez-apply-to {
        color: #86efac;
        font-size: 16px;
        font-weight: 800;
        margin: 0 0 8px 0;
    }
    .ez-apply-why {
        color: #94a3b8;
        font-size: 13px;
        margin: 0;
    }
    .ez-apply-done-row {
        padding: 8px 12px;
        border-radius: 10px;
        background: rgba(34,197,94,0.08);
        border: 1px solid rgba(34,197,94,0.2);
        margin-bottom: 6px;
        color: #bbf7d0;
        font-size: 13px;
    }
    .ez-primary-cta {
        display: block;
        width: 100%;
    }
    /* Make primary accept buttons feel larger in focus mode */
    div[data-testid="column"] .stButton > button[kind="primary"] {
        min-height: 3rem;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }
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
            return full.where(full.str.len().gt(0), df.index.astype(str))

    # Avoid bare "name" first — it substring-matches Firstname/Middle name.
    name_col = find_col(df, ["full name", "athlete", "competitor", "name"])
    if name_col:
        return df[name_col].fillna("").astype(str).str.strip().replace({"nan": ""})
    return pd.Series(df.index.astype(str), index=df.index)


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
    """Prefer reviewable options over equal-score Do Not Match rows."""
    return sorted(
        scored,
        key=lambda x: (
            1 if str(x.get("Safety Flag", "")).strip() else 0,
            -int(x.get("Match Score", 0) or 0),
        ),
    )


def skill_value(skill):
    s = str(skill)
    for key, value in SKILL_ORDER.items():
        if key.lower() in s.lower():
            return value
    return 999


def age_year_midpoint(age):
    """Return midpoint of explicit year bands (e.g. 14-15 → 14.5), else None."""
    nums = [int(n) for n in re.findall(r"\d+", str(age or ""))]
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
    df["group_clean"] = df[group_col].astype(str).str.strip()

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
            return df[col].astype(str).str.strip()
        return pd.Series([default] * len(df), index=df.index)

    df["athlete_name"] = mapped_series("name", "").replace("", pd.NA)
    df["athlete_name"] = df["athlete_name"].fillna(pd.Series(df.index.astype(str), index=df.index))
    df["approved_clean"] = mapped_series("status", "Approved")
    df["academy_clean"] = mapped_series("academy", "").map(normalize_academy_name)
    df["entry_clean"] = mapped_series("entry", "")
    df["skill_clean"] = mapped_series("skill", "")
    df["age_clean"] = mapped_series("age", "")
    df["weight_clean"] = mapped_series("weight", "")
    df["gender_clean"] = df["entry_clean"].apply(extract_gender)

    group_col = mapping.get("group", "")
    if group_col and group_col in df.columns:
        df["group_clean"] = df[group_col].astype(str).str.strip()
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
    return pd.DataFrame(rows).sort_values(["athletes", "group"]).reset_index(drop=True)


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

    skill_diff = abs(skill_value(src_skill) - skill_value(tgt_skill))
    if skill_value(src_skill) == 999 and skill_value(tgt_skill) == 999:
        skill_diff = 999
    raw_age_diff = age_step_difference(src_age, tgt_age)

    sw = weight_mid(src_weight)
    cw = weight_mid(tgt_weight)
    weight_diff = abs(sw - cw) if sw is not None and cw is not None else 999

    src_context = str(single.get("group_clean", "") or single.get("entry_clean", "") or "")
    juv_to_adult = is_juvenile_16_17(src_age, src_context) and is_adult_age(tgt_age)
    # Juvenile 16-17 → Adult is one practical age step (Adult starts at 18).
    age_diff = 1 if juv_to_adult else raw_age_diff

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
    elif juv_to_adult:
        # Same ballpark as a normal one-age-group step (Adult starts at 18).
        penalty = settings["one_age_penalty"]
        score -= penalty
        reasons.append("Juvenile 16-17 into Adult (normal step up)")
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

    # Juvenile→Adult is an expected step; do not hard-block on age safety limit.
    if (not juv_to_adult) and age_diff != 999 and age_diff > settings["max_safe_age_diff"]:
        safety_flags.append(f"Age gap over {settings['max_safe_age_diff']} group(s)")

    # Director preference (Juvenile 16-17 → Adult):
    # - Prefer Adult Novice (slightly easier) over Adult Beginner
    # - Prefer same-weight Adult over heavier; lighter Adult is acceptable
    # - Adult options should beat a 20 lb Juvenile jump, but not a 10 lb Juvenile jump
    if juv_to_adult:
        src_sv = skill_value(src_skill)
        tgt_sv = skill_value(tgt_skill)
        if src_sv != 999 and tgt_sv != 999 and tgt_sv < src_sv and (src_sv - tgt_sv) <= 1:
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
        src_sv = skill_value(src_skill)
        tgt_sv = skill_value(tgt_skill)
        if (
            is_white_belt_skill(src_skill)
            and src_sv != 999
            and tgt_sv != 999
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

    return score, "; ".join(reasons), " | ".join(breakdown), safety_flag, weight_diff, age_diff, skill_diff, academy_warning, academy_mix


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
    working = df.copy()
    academy_lookup = _academy_lookup_from_df(df)

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
            cand_for_score = _cand_with_full_academies(cand, academy_lookup)
            result = score_candidate(single, cand_for_score, allow_entry_crossover, scoring_settings)
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
    working = df.copy()
    academy_lookup = _academy_lookup_from_df(df)

    if only_approved and "approved_clean" in working.columns:
        approved_mask = working["approved_clean"].astype(str).str.lower().eq("approved")
        if approved_mask.any():
            working = working[approved_mask]

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

    rows = []
    for _, problem in conflict_groups.iterrows():
        candidates = target_groups[target_groups["group"] != problem["group"]].copy()
        scored = []

        for _, cand in candidates.iterrows():
            cand_for_score = _cand_with_full_academies(cand, academy_lookup)
            result = score_conflict_candidate(problem, cand_for_score, allow_entry_crossover, scoring_settings)
            if result is None:
                continue

            score, why, breakdown, safety_flag, weight_diff, age_diff, skill_diff, academy_warning, academy_mix = result
            if int(cand_for_score.get("academy_count", 0)) >= 2:
                score = min(100, score + 8)
                why = why + "; target already has mixed academies"
                breakdown = breakdown + " | Mixed target bracket: +8"
            elif int(cand_for_score.get("academy_count", 0)) <= 1:
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
        "EZ Brackets — Action Plan",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total moves: {len(active)}",
        "",
    ]
    for i, m in enumerate(active, 1):
        lines.append(f"{i}. Move {m['athlete_name']}")
        lines.append(f"   FROM: {m['original_division']}")
        lines.append(f"   TO:   {m['new_division']}")
        lines.append(f"   Score: {m['score']}")
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


def render_smoothcomp_copy_kit(move, *, key_prefix, public_note):
    """Copy/paste kit matching Smoothcomp: athlete, admin note, 4 dropdowns, public note."""
    parts = smoothcomp_copy_fields(move.get("new_division", ""))
    st.caption("Athlete — find, check box, then Copy (not Move)")
    st.code(move.get("athlete_name", ""), language="")

    st.caption("Admin note — paste original division")
    st.code(admin_note_for_move(move) or "—", language="")

    st.caption("Copy Registrations dropdowns")
    _e1, _e2 = st.columns(2)
    with _e1:
        st.caption("Entry")
        st.code(parts["entry"] or "—", language="")
        st.caption("Age")
        st.code(parts["age"] or "—", language="")
    with _e2:
        st.caption("Skill")
        st.code(parts["skill"] or "—", language="")
        st.caption("Weight")
        st.code(parts["weight"] or "—", language="")

    with st.expander("Full destination path (backup)", expanded=False):
        st.code(parts["full"] or "—", language="")

    st.caption("Public note — on the new registration")
    st.code(public_note or DEFAULT_PUBLIC_NOTE, language="")


def render_apply_to_smoothcomp(moves, *, expanded=True, key_prefix="apply"):
    """Render Apply Mode: workflow list + compact companion for Smoothcomp.

    Does not contact Smoothcomp — copy/paste helper only.
    Tuned for the director Copy workflow: keep original registration, set
    Entry/Skill/Age/Weight dropdowns, admin + public notes, then verify.
    """
    migrate_moves_applied_fields(moves)
    stats = apply_mode_stats(moves)
    if stats["planned"] == 0:
        return

    indexed = sorted_active_moves_with_index(moves)
    remaining = [(i, m) for i, m in indexed if not m.get("applied")]
    applied_list = [(i, m) for i, m in indexed if m.get("applied")]

    st.markdown('<div class="ez-apply-panel">', unsafe_allow_html=True)
    st.subheader("Apply to Smoothcomp")
    st.markdown(
        "EZ Brackets has **not** updated Smoothcomp. In Smoothcomp use **Copy** "
        "(not Move) so they stay in the original if someone else signs up.  \n"
        "Checklist: check athlete → **Copy** → admin note (original) → Entry / Skill / "
        "Age / Weight → **Copy registrations** → verify + public note → **Mark Applied** here."
    )

    _url_col, _open_col = st.columns([4, 1])
    with _url_col:
        st.text_input(
            "Smoothcomp event URL (optional)",
            key="smoothcomp_event_url",
            placeholder="https://smoothcomp.com/en/event/…",
            help="Opens your event in a new tab. EZ Brackets never logs into Smoothcomp.",
        )
    with _open_col:
        st.write("")
        st.write("")
        _event_url = normalize_smoothcomp_event_url(
            st.session_state.get("smoothcomp_event_url", "")
        )
        if _event_url:
            st.link_button("Open event", _event_url, type="primary")
        else:
            st.caption("Add URL to open")

    if "apply_public_note_template" not in st.session_state:
        st.session_state["apply_public_note_template"] = DEFAULT_PUBLIC_NOTE
    st.text_input(
        "Public note template",
        key="apply_public_note_template",
        help="Copied onto each new registration after Copy (athletes/parents can see this).",
    )
    _public_note = (
        str(st.session_state.get("apply_public_note_template", "") or "").strip()
        or DEFAULT_PUBLIC_NOTE
    )

    _p1, _p2, _p3 = st.columns(3)
    with _p1:
        st.markdown(
            f'<div class="ez-sticky-progress"><span class="ez-pill ez-pill-amber">'
            f'Planned <b>{stats["planned"]}</b></span></div>',
            unsafe_allow_html=True,
        )
    with _p2:
        st.markdown(
            f'<div class="ez-sticky-progress"><span class="ez-pill ez-pill-green">'
            f'Applied <b>{stats["applied"]}</b></span></div>',
            unsafe_allow_html=True,
        )
    with _p3:
        _rem_cls = "ez-pill-red" if stats["remaining"] else "ez-pill-green"
        st.markdown(
            f'<div class="ez-sticky-progress"><span class="ez-pill {_rem_cls}">'
            f'Remaining <b>{stats["remaining"]}</b></span></div>',
            unsafe_allow_html=True,
        )

    if "apply_compact_companion" not in st.session_state:
        st.session_state["apply_compact_companion"] = True
    st.checkbox(
        "Compact companion (side-by-side with Smoothcomp)",
        key="apply_compact_companion",
        help="Shows the next unapplied copy large — put EZ Brackets beside Smoothcomp.",
    )
    _compact = bool(st.session_state.get("apply_compact_companion", True))

    if not remaining:
        st.success("All planned copies are marked Applied. Double-check Smoothcomp, then publish.")
    else:
        if _compact:
            _idx, _next = remaining[0]
            st.markdown("#### Next copy")
            st.markdown(
                f'<div class="ez-apply-next">'
                f'<div class="ez-apply-athlete">{_next["athlete_name"]}</div>'
                f'<p class="ez-apply-path">KEEP / FROM: {_next["original_division"]}</p>'
                f'<p class="ez-apply-to">COPY INTO: {_next["new_division"]}</p>'
                f'<p class="ez-apply-why">{format_apply_why(_next)}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )
            render_smoothcomp_copy_kit(
                _next,
                key_prefix=f"{key_prefix}_next_{_idx}",
                public_note=_public_note,
            )
            if st.button(
                "✅ Mark Applied",
                key=f"{key_prefix}_mark_next_{_idx}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["moves"][_idx]["applied"] = True
                st.session_state["moves"][_idx]["applied_at"] = (
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                )
                st.rerun()
            st.caption(
                f"{len(remaining)} remaining · order: Kids/Teens Gi → Kids/Teens No-Gi → Adult Gi → …"
            )

        _list_expanded = (not _compact) or expanded
        with st.expander(
            f"Full apply list — {len(remaining)} remaining",
            expanded=_list_expanded and not _compact,
        ):
            st.caption(
                "Order: Kids/Teens Gi → Kids/Teens No-Gi → Adult Gi → Adult No-Gi "
                "(finish one entry type before switching)."
            )
            for _mi, (_idx, _m) in enumerate(remaining):
                _parts = smoothcomp_copy_fields(_m.get("new_division", ""))
                st.markdown(
                    f"**{_mi + 1}. {_m['athlete_name']}**  \n"
                    f"KEEP: `{_m['original_division']}`  \n"
                    f"COPY INTO: `{_m['new_division']}`  \n"
                    f"Dropdowns: `{_parts['entry']}` · `{_parts['skill']}` · "
                    f"`{_parts['age']}` · `{_parts['weight']}`  \n"
                    f"{format_apply_why(_m)}"
                )
                with st.expander("Copy kit", expanded=False):
                    render_smoothcomp_copy_kit(
                        _m,
                        key_prefix=f"{key_prefix}_row_{_idx}",
                        public_note=_public_note,
                    )
                if st.button(
                    "Mark Applied",
                    key=f"{key_prefix}_mark_{_idx}",
                    use_container_width=True,
                ):
                    st.session_state["moves"][_idx]["applied"] = True
                    st.session_state["moves"][_idx]["applied_at"] = (
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    )
                    st.rerun()
                st.divider()

    if applied_list:
        with st.expander(f"Applied ({len(applied_list)})", expanded=False):
            for _idx, _m in applied_list:
                _when = _m.get("applied_at") or ""
                st.markdown(
                    f'<div class="ez-apply-done-row">'
                    f'✅ <b>{_m["athlete_name"]}</b> → {_m["new_division"]}'
                    f'{(" · " + _when) if _when else ""}'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Undo Applied",
                    key=f"{key_prefix}_unmark_{_idx}",
                ):
                    st.session_state["moves"][_idx]["applied"] = False
                    st.session_state["moves"][_idx]["applied_at"] = ""
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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
    elif wd <= 10:
        bullets.append("⚠️ 1 weight class apart")
    elif wd <= 20:
        bullets.append("⚠️ 2 weight classes apart")
    else:
        bullets.append(f"⛔ {wd:.0f} lbs gap — exceeds limit")

    if sd is None:
        bullets.append("⚠️ Unknown skill level")
    elif sd == 0:
        bullets.append("✅ Same skill/belt level")
    elif sd == 1:
        bullets.append("⚠️ 1 skill level apart")
    else:
        bullets.append(f"⛔ {sd} skill levels — exceeds limit")

    if ad is None:
        bullets.append("⚠️ Unknown age group")
    elif ad == 0:
        bullets.append("✅ Same age group")
    elif ad == 1:
        bullets.append("⚠️ 1 age group apart")
    else:
        bullets.append(f"⛔ {ad} age groups — exceeds limit")

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
            "title": "Not Safe",
            "lines": ["Blocked by current safety rules."] + clean_lines[:3],
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
        "title": "Looks Safe",
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


def planned_athlete_counts(summary_df, moves):
    """Project division sizes after Active moves (CSV unchanged).

    Each Active move removes one athlete from ``original_division`` and adds one
    to ``new_division``. Used so accepting A→B (two singles) clears both from
    the unresolved single queue without inventing a second Action Plan row.
    """
    counts = {}
    if summary_df is not None and not summary_df.empty:
        for _, row in summary_df.iterrows():
            counts[str(row["group"])] = int(row["athletes"])
    for m in active_moves_only(moves):
        src = str(m.get("original_division", "") or "").strip()
        dst = str(m.get("new_division", "") or "").strip()
        if src:
            counts[src] = max(0, int(counts.get(src, 0)) - 1)
        if dst:
            counts[dst] = int(counts.get(dst, 0)) + 1
    return counts


def filter_planned_singles(singles_df, planned_counts):
    """Keep only divisions that are still alone after planned moves."""
    if singles_df is None or singles_df.empty:
        return singles_df
    mask = singles_df["group"].astype(str).map(lambda g: int(planned_counts.get(g, 0)) == 1)
    return singles_df.loc[mask].copy()


def filter_planned_conflict_groups(conflict_df, planned_counts):
    """Drop academy-conflict groups that no longer have 2+ planned athletes."""
    if conflict_df is None or conflict_df.empty:
        return conflict_df
    mask = conflict_df["group"].astype(str).map(lambda g: int(planned_counts.get(g, 0)) >= 2)
    return conflict_df.loc[mask].copy()


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
        safe = bool(has_rec and str(best.get("Safety Flag", "")).strip() == "")
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
        safe = bool(has_rec and str(best.get("Safety Flag", "")).strip() == "")
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


def append_accepted_move(athlete_name, original_division, new_division, score, academy_warning=""):
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
    })


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
        "active_moves": len(active),
        "skipped_count": len(skipped),
        "manual_count": len(manual),
        "applied_count": sum(1 for m in active if m.get("applied")),
    }


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
    saved_preset = result.get("last_preset", "")
    if saved_preset in SCORING_PRESETS:
        st.session_state["rule_preset_select"] = saved_preset
        st.session_state["last_preset"] = saved_preset
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
                    Find athletes stuck alone in a division, suggest safer places to move them,
                    and export a clear move list for Smoothcomp.
                </div>
                <span class="ez-badge">Find alone athletes</span>
                <span class="ez-badge">Suggest safe moves</span>
                <span class="ez-badge">Flag academy-only brackets</span>
                <span class="ez-badge">Export a move list</span>
            </div>
        </div>
    </div>
    ''',
        unsafe_allow_html=True,
    )
    st.info(
        "**How EZ Brackets works:**  \n"
        "1. Load your event  \n"
        "2. Review each recommendation in Focus Mode  \n"
        "3. Download your Action Plan and apply the moves in Smoothcomp before publishing"
    )
    st.markdown('<div class="ez-save-panel">', unsafe_allow_html=True)
    st.markdown("#### Resume Progress")
    st.caption(
        "Coming back mid-event? Upload your saved `.json` session first, then load the same registration CSV."
    )
    _landing_resume = st.file_uploader(
        "Upload saved progress (.json)",
        type=["json"],
        key=f"landing_resume_{st.session_state.get('restore_key_counter', 0)}",
        help="Restores moves planned, skipped, manual review, and Focus position.",
    )
    if _landing_resume is not None:
        _err = try_restore_uploaded_session(_landing_resume)
        if _err:
            st.error(_err)
        else:
            st.rerun()
    if st.session_state.get("restore_notice"):
        st.success(st.session_state.get("restore_notice"))
        if st.session_state.get("restore_csv_hash") and not st.session_state.get("csv_hash"):
            st.info("Next: load the same registration CSV below so your divisions match.")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    _cs = st.session_state
    st.markdown(
        f'''<div class="ez-compact-header">
            <span class="ez-compact-logo">🥋 EZ Brackets</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_athlete_count", "—")}</b> athletes</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_singles_count", "—")}</b> alone</span>
            <span class="ez-compact-pill"><b>{_cs.get("last_conflicts_count", "—")}</b> academy issues</span>
            <span class="ez-compact-pill">Preset: <b>{_cs.get("last_preset", "—")}</b></span>
        </div>''',
        unsafe_allow_html=True,
    )

st.markdown("### Step 1 — Load your event")
load_choice = st.radio(
    "Choose one:",
    ["Try Sample Event", "Upload Smoothcomp CSV", "Other Registration Systems"],
    horizontal=True,
    key="load_choice_radio",
    help="Most directors should use Upload Smoothcomp CSV. Try Sample Event to practice first.",
)

uploaded = None
data_ready = False
df = None
hash_changed = False

if load_choice == "Try Sample Event":
    sample_kind = st.radio(
        "Sample type",
        ["Smoothcomp sample", "Universal sample"],
        horizontal=True,
        key="sample_kind_radio",
    )
    if sample_kind == "Smoothcomp sample":
        raw_df = demo_raw_dataframe()
        df = normalize_dataframe(raw_df)
        data_ready = True
        st.caption("Sample Smoothcomp-style data loaded. Practice the full workflow — Smoothcomp is not updated by this app.")
    else:
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
        st.caption("Sample universal data loaded. This shows mapped columns from a non-Smoothcomp file.")
    with st.expander("Need a CSV template?"):
        st.download_button(
            "📥 Download sample CSV template",
            data=sample_csv_bytes(),
            file_name="ez_brackets_sample_template.csv",
            mime="text/csv",
            key="sample_template_dl",
        )

elif load_choice == "Upload Smoothcomp CSV":
    uploaded = st.file_uploader("Upload your Smoothcomp registrations CSV", type=["csv"], key="smoothcomp_uploader")
    if uploaded:
        _file_bytes = uploaded.getvalue()
        _new_hash = hashlib.md5(_file_bytes).hexdigest()
        _prev_hash = st.session_state.get("csv_hash", "")
        if _new_hash != _prev_hash and _prev_hash != "":
            hash_changed = True
        st.session_state["csv_hash"] = _new_hash
        raw_df = pd.read_csv(BytesIO(_file_bytes))
        df = normalize_dataframe(raw_df)
        data_ready = True

else:
    st.caption("Use this only if your registration file is not a Smoothcomp export.")
    uploaded = st.file_uploader("Upload registrations CSV", type=["csv"], key="universal_uploader")
    if uploaded:
        _file_bytes = uploaded.getvalue()
        _new_hash = hashlib.md5(_file_bytes).hexdigest()
        _prev_hash = st.session_state.get("csv_hash", "")
        if _new_hash != _prev_hash and _prev_hash != "":
            hash_changed = True
        st.session_state["csv_hash"] = _new_hash
        raw_df = pd.read_csv(BytesIO(_file_bytes))
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
    migrate_moves_applied_fields(st.session_state.get("moves", []))
    if "smoothcomp_event_url" not in st.session_state:
        st.session_state["smoothcomp_event_url"] = ""
    if "move_back_alerts" not in st.session_state:
        st.session_state["move_back_alerts"] = []
    if "guided_skipped" not in st.session_state:
        st.session_state["guided_skipped"] = set()
    if "manual_review" not in st.session_state:
        st.session_state["manual_review"] = set()
    if "focus_index" not in st.session_state:
        st.session_state["focus_index"] = 0
    if "has_data" not in st.session_state:
        st.session_state["has_data"] = False
    if "restore_key_counter" not in st.session_state:
        st.session_state["restore_key_counter"] = 0
    # Migrate legacy view mode label once
    if st.session_state.get("view_mode_radio") == "📋 Table Mode":
        st.session_state["view_mode_radio"] = "📋 Advanced Table View"

    with st.sidebar:
        st.subheader("Session")
        st.caption("Save before closing. Restore later to continue. EZ Brackets never updates Smoothcomp for you.")
        if session_has_progress():
            _sj = build_session_payload()
            st.download_button(
                "💾 Save Progress",
                data=json.dumps(_sj, indent=2).encode("utf-8"),
                file_name=f"ez_brackets_session_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                key="sidebar_save_session",
                help="Save moves planned, skipped/manual items, Focus position, preset, and view mode.",
            )
        else:
            st.caption("No progress to save yet — accept, skip, or mark a decision first.")
        _restore_file = st.file_uploader(
            "Resume Progress (.json)",
            type=["json"],
            key=f"restore_session_{st.session_state['restore_key_counter']}",
            help="Upload a previously saved EZ Brackets session file.",
        )
        if _restore_file is not None:
            _err = try_restore_uploaded_session(_restore_file)
            if _err:
                st.error(_err)
            else:
                st.rerun()
        if st.session_state.get("restore_notice"):
            st.success(st.session_state.get("restore_notice"))

        st.divider()
        st.subheader("Rule Preset")
        _preset_keys = list(SCORING_PRESETS.keys())
        _default_preset_idx = 1 if len(_preset_keys) > 1 else 0
        if "rule_preset_select" not in st.session_state:
            st.session_state["rule_preset_select"] = _preset_keys[_default_preset_idx]
        rule_preset = st.selectbox(
            "Choose scoring preset",
            _preset_keys,
            key="rule_preset_select",
            help="Kids Conservative is safest for youth events. Adult Standard is the usual default.",
        )
        preset = SCORING_PRESETS[rule_preset]

        with st.expander("Safety settings (optional)", expanded=False):
            st.caption("Most directors can leave these on the preset defaults.")
            only_approved = st.checkbox("Only analyze approved athletes", value=True)
            min_target_size = st.selectbox(
                "Suggest moving alone athletes into groups with at least:",
                [1, 2, 3],
                index=0,
            )
            top_n = st.slider("Top suggestions per alone athlete", min_value=1, max_value=5, value=3)
            allow_entry_crossover = st.checkbox("Show Gi/No-Gi crossover emergency options", value=False)
            max_safe_weight_diff = st.slider(
                "Do Not Match if weight gap is over (lbs):",
                5, 60, preset["max_safe_weight_diff"], 5,
                help="Weight difference in pounds. Larger gaps are marked unsafe.",
            )
            max_safe_age_diff = st.slider(
                "Do Not Match if age gap is over (age groups):",
                0, 5, preset["max_safe_age_diff"],
                help="0 means only the same age group is allowed (best for kids).",
            )
            max_safe_skill_diff = st.slider(
                "Do Not Match if skill/belt gap is over:",
                0, 5, preset["max_safe_skill_diff"],
            )
            st.markdown("**Advanced scoring weights**")
            same_academy_penalty = st.slider("Same-academy penalty", 0, 60, preset["same_academy_penalty"], 5)
            entry_crossover_penalty = st.slider("Gi/No-Gi crossover penalty", 0, 60, preset["entry_crossover_penalty"], 5)

        # Defaults when expander values are first created — Streamlit still executes expander body
        # so variables above are always defined.

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

    # Original CSV-truth singles / conflicts (uploaded file never modified).
    csv_singles = summary[summary["athletes"] == 1].copy()
    csv_academy_conflict_groups = summary[(summary["athletes"] >= 2) & (summary["academy_count"] == 1)].copy()

    # Planned event state = CSV + Active accepted moves (revert drops them back out).
    _planned_counts = planned_athlete_counts(summary, st.session_state.get("moves", []))
    singles = filter_planned_singles(csv_singles, _planned_counts)
    academy_conflict_groups = filter_planned_conflict_groups(csv_academy_conflict_groups, _planned_counts)

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

    # Cache stats for compact header (planned unresolved alone count).
    st.session_state["has_data"] = True
    st.session_state["last_athlete_count"] = len(working_df)
    st.session_state["last_singles_count"] = len(singles)
    st.session_state["last_conflicts_count"] = len(academy_conflict_groups)
    st.session_state["last_preset"] = rule_preset

    # Pending impact for divisions that are still alone in planned state
    _pending_impacts = {
        row["group"]: get_pending_impact(row["group"], summary, full_summary)
        for _, row in singles.iterrows()
    }
    _may_resolve_count = sum(1 for v in _pending_impacts.values() if v["impact"] == "resolves")

    # Action Plan / exports: only Rank-1 for divisions still unresolved in planned state
    _planned_single_groups = set(singles["group"].astype(str).tolist()) if not singles.empty else set()
    if recommendations.empty:
        rank1_recommendations = recommendations.copy()
    else:
        rank1_recommendations = recommendations[
            (recommendations["Rank"] == 1)
            & (recommendations["Current Division"].astype(str).isin(_planned_single_groups))
        ].copy()
    _planned_conflict_groups = (
        set(academy_conflict_groups["group"].astype(str).tolist())
        if not academy_conflict_groups.empty
        else set()
    )
    if academy_conflict_recommendations.empty:
        rank1_conflicts = academy_conflict_recommendations.copy()
    else:
        rank1_conflicts = academy_conflict_recommendations[
            (academy_conflict_recommendations["Rank"] == 1)
            & (academy_conflict_recommendations["Problem Division"].astype(str).isin(_planned_conflict_groups))
        ].copy()
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
        metric_card("Athletes", len(working_df), "People currently being reviewed")
    with c2:
        metric_card("Divisions", len(summary), "Active brackets / groups in the file")
    with c3:
        metric_card(
            "Alone Athletes",
            len(singles),
            "Still alone after accepted moves (planned state) — need a partner or a move",
        )
    with c4:
        metric_card("Academy Issues", len(academy_conflict_groups), "Divisions where everyone is from the same academy")

    # ── Event Health Dashboard ────────────────────────────────────────────────
    _active_moves_count = sum(1 for m in st.session_state.get("moves", []) if m["status"] == "Active")
    _manual_ids = normalize_id_set(st.session_state.get("manual_review", set()))
    _queue = build_decision_queue(
        singles,
        academy_conflict_groups,
        recommendations,
        academy_conflict_recommendations,
        st.session_state.get("moves", []),
        st.session_state.get("guided_skipped", set()),
        st.session_state.get("manual_review", set()),
        _pending_impacts,
    )
    _decisions_remaining = len(_queue)
    # Baseline = original CSV problems; handled includes destination singles auto-resolved by a move.
    _total_problems = len(csv_singles) + len(csv_academy_conflict_groups)
    _current_problem_ids = (
        {decision_id("single", g) for g in singles["group"].tolist()}
        | {decision_id("conflict", g) for g in academy_conflict_groups["group"].tolist()}
    )
    _manual_count = len(_manual_ids & _current_problem_ids)
    _skipped_count = len([i for i in _queue if i.get("skipped")])
    # Baseline minus queue size: one move A→B can close two CSV singles at once.
    # Skipped items stay in the queue (still "remaining").
    _handled = max(0, _total_problems - _decisions_remaining)
    _progress_val = (_handled / _total_problems) if _total_problems > 0 else 0.0

    if _decisions_remaining == 0 and _total_problems > 0:
        _event_status = "✅ Review finished — ready to apply in Smoothcomp"
    elif _decisions_remaining <= max(1, _total_problems // 4):
        _event_status = "🟡 Almost done — continue Focus Mode below"
    else:
        _event_status = "🔴 Action needed — start Focus Mode below"

    st.markdown(
        f"""
        <div class="ez-sticky-progress">
            <span class="ez-pill ez-pill-red">Decisions left: <b>{_decisions_remaining}</b></span>
            <span class="ez-pill ez-pill-green">Moves planned: <b>{_active_moves_count}</b></span>
            <span class="ez-pill ez-pill-amber">Skipped: <b>{_skipped_count}</b></span>
            <span class="ez-pill">Manual review: <b>{_manual_count}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Save / Resume Progress (main workflow — easy to find mid-event) ───────
    if st.session_state.get("restore_notice"):
        st.success(st.session_state.pop("restore_notice"))
        _saved_hash = st.session_state.get("restore_csv_hash", "")
        _current_hash = st.session_state.get("csv_hash", "")
        if _saved_hash and _current_hash and _saved_hash != _current_hash:
            st.warning(
                "This registration file looks different from the one used when the session was saved. "
                "Double-check that your accepted moves still make sense."
            )

    st.markdown('<div class="ez-save-panel">', unsafe_allow_html=True)
    st.markdown("#### Save / Resume Progress")
    st.caption(
        "Save before you leave. Resume later with the same CSV + this file — "
        "picks up moves planned, skipped, manual review, and Focus position."
    )
    _sp1, _sp2 = st.columns(2)
    with _sp1:
        if session_has_progress():
            _main_sj = build_session_payload()
            st.download_button(
                "💾 Save Progress",
                data=json.dumps(_main_sj, indent=2).encode("utf-8"),
                file_name=f"ez_brackets_session_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                key="main_save_progress",
                type="primary",
                help="Download your mid-event progress as a .json file.",
            )
        else:
            st.caption("Accept, skip, or mark a decision to enable Save Progress.")
    with _sp2:
        _main_resume = st.file_uploader(
            "Resume Progress (.json)",
            type=["json"],
            key=f"main_resume_{st.session_state.get('restore_key_counter', 0)}",
            help="Upload a previously saved progress file.",
        )
        if _main_resume is not None:
            _err = try_restore_uploaded_session(_main_resume)
            if _err:
                st.error(_err)
            else:
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ez-health-panel">', unsafe_allow_html=True)
    st.subheader("Event Health")
    st.caption(
        "Your checklist for this file. **Alone** and **Decisions left** use planned state "
        "(CSV + accepted moves) — moving Single A into Single B clears both. "
        "**Moves planned** still need to be applied in Smoothcomp before publishing."
    )
    st.progress(
        _progress_val,
        text=f"{_handled} of {_total_problems} handled · {_active_moves_count} moves planned — {_event_status}",
    )
    _h1, _h2, _h3, _h4 = st.columns(4)
    with _h1:
        _c = "#ef4444" if len(singles) > 0 else "#22c55e"
        st.markdown(
            f'<div class="ez-health-number" style="color:{_c}">{len(singles)}</div>'
            f'<div class="ez-health-label">Alone</div>',
            unsafe_allow_html=True,
        )
    with _h2:
        _c = "#f97316" if len(academy_conflict_groups) > 0 else "#22c55e"
        st.markdown(
            f'<div class="ez-health-number" style="color:{_c}">{len(academy_conflict_groups)}</div>'
            f'<div class="ez-health-label">Academy Issues</div>',
            unsafe_allow_html=True,
        )
    with _h3:
        st.markdown(
            f'<div class="ez-health-number" style="color:#22c55e">{_active_moves_count}</div>'
            f'<div class="ez-health-label">Moves Planned</div>',
            unsafe_allow_html=True,
        )
    with _h4:
        _c = "#fbbf24" if _may_resolve_count > 0 else "#94a3b8"
        st.markdown(
            f'<div class="ez-health-number" style="color:{_c}">{_may_resolve_count}</div>'
            f'<div class="ez-health-label">May Fix Itself</div>',
            unsafe_allow_html=True,
        )
    if _may_resolve_count > 0:
        st.caption(
            f"{_may_resolve_count} alone division(s) have other athletes waiting on approval — "
            "those may get partners without you moving anyone."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Completion Cockpit ────────────────────────────────────────────────────
    _review_complete = _decisions_remaining == 0 and _total_problems > 0
    if _review_complete:
        _plan_text = format_action_plan_text(st.session_state.get("moves", []))
        _apply_stats = apply_mode_stats(st.session_state.get("moves", []))
        st.markdown('<div class="ez-complete-panel">', unsafe_allow_html=True)
        st.subheader("✅ Bracket Review Complete")
        st.markdown(
            f"**{_active_moves_count}** moves planned · **{_skipped_count}** skipped · "
            f"**{_manual_count}** manual review.  \n"
            "EZ Brackets has **not** updated Smoothcomp. Use **Apply to Smoothcomp** below "
            "to copy each move and mark it Applied, or download the Action Plan backup."
        )
        if _apply_stats["planned"]:
            st.caption(
                f"Apply progress: {_apply_stats['applied']} applied · "
                f"{_apply_stats['remaining']} remaining"
            )
        _nb1, _nb2 = st.columns(2)
        with _nb1:
            if _plan_text:
                st.download_button(
                    "📥 Download Action Plan (.txt)",
                    data=_plan_text.encode("utf-8"),
                    file_name=f"ez_brackets_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key="next_step_download_txt",
                )
            else:
                st.caption("No moves planned — nothing to download.")
        with _nb2:
            st.markdown("**Smoothcomp checklist**")
            st.markdown(
                "1. Open Smoothcomp (link in Apply Mode)  \n"
                "2. Check athlete → **Copy** (keep original)  \n"
                "3. Admin note = original division  \n"
                "4. Set Entry / Skill / Age / Weight  \n"
                "5. Copy registrations → verify + public note  \n"
                "6. Mark Applied when Remaining is 0"
            )
        if _plan_text:
            with st.expander("Copy full Action Plan (backup)", expanded=False):
                st.code(_plan_text, language="")

        _active_moves_list = [m for m in st.session_state.get("moves", []) if m.get("status") == "Active"]
        if _active_moves_list:
            with st.expander(f"Moves planned ({len(_active_moves_list)})", expanded=False):
                for m in _active_moves_list:
                    _done = " ✅" if m.get("applied") else ""
                    st.markdown(
                        f"- **{m['athlete_name']}**: {m['original_division']} → {m['new_division']}{_done}"
                    )
        if _manual_count:
            with st.expander(f"Manual review ({_manual_count})", expanded=False):
                for mid in sorted(_manual_ids & _current_problem_ids):
                    kind, group = parse_decision_id(mid)
                    st.markdown(f"- **{kind}**: {group}")
        if _skipped_count:
            with st.expander(f"Skipped ({_skipped_count})", expanded=False):
                for item in _queue:
                    if item.get("skipped"):
                        st.markdown(f"- **{item['name']}** · {item['group']}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Apply Mode — prominent when review is done; available collapsed mid-review
    if _active_moves_count > 0:
        if _review_complete:
            render_apply_to_smoothcomp(
                st.session_state.get("moves", []),
                expanded=True,
                key_prefix="apply_main",
            )
        else:
            _as_mid = apply_mode_stats(st.session_state.get("moves", []))
            with st.expander(
                f"Apply to Smoothcomp — {_as_mid['remaining']} remaining · "
                f"{_as_mid['applied']} applied",
                expanded=False,
            ):
                render_apply_to_smoothcomp(
                    st.session_state.get("moves", []),
                    expanded=False,
                    key_prefix="apply_mid",
                )

    # ── View Mode Toggle ──────────────────────────────────────────────────────
    st.markdown("### Step 2 — Review recommendations")
    if "view_mode_radio" not in st.session_state:
        st.session_state["view_mode_radio"] = "🃏 Guided Mode"
    _view_mode = st.radio(
        "How do you want to review?",
        ["🃏 Guided Mode", "📋 Advanced Table View"],
        horizontal=True,
        key="view_mode_radio",
        help=(
            "Guided Mode: Focus Mode walks you through one decision at a time. "
            "Advanced Table View: full spreadsheets and every export."
        ),
    )
    _guided_mode = _view_mode == "🃏 Guided Mode"

    # ── Guided Mode ───────────────────────────────────────────────────────────
    if _guided_mode:
        # Apply pending Queue→Focus navigation BEFORE the layout radio is instantiated.
        if st.session_state.pop("pending_focus_open", False):
            st.session_state["guided_layout_radio"] = "Focus Mode"
            st.session_state["focus_index"] = int(st.session_state.pop("pending_focus_index", 0))
        if "guided_layout_radio" not in st.session_state:
            st.session_state["guided_layout_radio"] = "Focus Mode"
        _layout = st.radio(
            "Guided layout",
            ["Focus Mode", "Queue View"],
            horizontal=True,
            key="guided_layout_radio",
            help="Focus Mode shows one decision at a time. Queue View lists remaining decisions.",
        )

        if _queue:
            if st.session_state["focus_index"] >= len(_queue):
                st.session_state["focus_index"] = max(0, len(_queue) - 1)
            if st.session_state["focus_index"] < 0:
                st.session_state["focus_index"] = 0
        else:
            st.session_state["focus_index"] = 0

        def _accept_item(item, rec_row):
            warning = str(
                rec_row.get("Academy Warning", "")
                or rec_row.get("Academy Mix After Merge", "")
            )
            append_accepted_move(
                item["name"],
                item["group"],
                str(rec_row["Suggested Division"]),
                int(rec_row["Match Score"]),
                warning,
            )
            st.session_state["guided_skipped"].discard(item["id"])
            st.session_state["manual_review"].discard(item["id"])
            st.rerun()

        def _render_decision_card(item, key_prefix, show_nav=False, position_label=""):
            best = item["best"]
            safe = item["safe"]
            has_rec = item["has_rec"]

            if show_nav:
                nav_l, nav_c, nav_r = st.columns([1, 2, 1])
                with nav_l:
                    if st.button(
                        "← Previous",
                        key=f"{key_prefix}_prev",
                        disabled=st.session_state["focus_index"] <= 0,
                    ):
                        st.session_state["focus_index"] = max(0, st.session_state["focus_index"] - 1)
                        st.rerun()
                with nav_c:
                    st.markdown(
                        f"<div style='text-align:center;color:#cbd5e1;font-weight:700;padding-top:8px;'>{position_label}</div>",
                        unsafe_allow_html=True,
                    )
                with nav_r:
                    if st.button(
                        "Next →",
                        key=f"{key_prefix}_next",
                        disabled=st.session_state["focus_index"] >= len(_queue) - 1,
                    ):
                        st.session_state["focus_index"] = min(
                            len(_queue) - 1, st.session_state["focus_index"] + 1
                        )
                        st.rerun()

            if not safe:
                st.markdown('<div class="ez-manual-banner">', unsafe_allow_html=True)
                kind_label = "Academy conflict" if item["kind"] == "conflict" else "Alone athlete"
                st.markdown(f"**⛔ No safe match** · {kind_label}: **{item['name']}**")
                st.caption(item["group"])
                if has_rec:
                    trust = trust_summary(best)
                    st.caption(f"{trust['title']}: {'; '.join(trust['lines'][:2])}")
                else:
                    st.caption("No recommendation could be generated for this division.")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Skip For Now", key=f"{key_prefix}_skip"):
                        # Keep focus index: skipped item moves to end, so same index becomes next.
                        st.session_state.setdefault("guided_skipped", set()).add(item["id"])
                        st.rerun()
                with b2:
                    if st.button("Mark for Manual Review", key=f"{key_prefix}_manual", type="primary"):
                        st.session_state.setdefault("manual_review", set()).add(item["id"])
                        st.session_state.get("guided_skipped", set()).discard(item["id"])
                        st.rerun()
                with st.expander("Details"):
                    if has_rec:
                        st.caption(str(best.get("Why", ""))[:240])
                        st.caption(f"Safety Flag: {best.get('Safety Flag', '')}")
                    st.caption("Try a different rule preset in Safety settings if you want more options.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            trust = trust_summary(best)
            state = trust["state"]
            st.markdown(f'<div class="ez-focus-card {state}">', unsafe_allow_html=True)
            top_l, top_r = st.columns([3, 1])
            with top_l:
                kind_bit = "Academy conflict" if item["kind"] == "conflict" else item.get("academy", "")
                st.markdown(
                    f'<div class="ez-focus-athlete">{item["name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ez-focus-meta">{kind_bit}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ez-focus-from">Current division<br/>'
                    f'<span style="color:#e2e8f0">{item["group"]}</span></div>',
                    unsafe_allow_html=True,
                )
                dest_label = "Suggested merge" if item["kind"] == "conflict" else "Suggested division"
                st.markdown(
                    f'<div class="ez-focus-from">{dest_label}</div>'
                    f'<div class="ez-focus-to">{best["Suggested Division"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ez-trust-title {state}">{trust["title"]}</div>',
                    unsafe_allow_html=True,
                )
                for line in trust["lines"]:
                    st.markdown(
                        f'<div class="ez-trust-line">• {line}</div>',
                        unsafe_allow_html=True,
                    )
            with top_r:
                q = str(best.get("Quality", ""))
                q_color = "#4ade80" if state == "safe" else ("#fbbf24" if state == "review" else "#f87171")
                st.markdown(
                    f'<div class="ez-score-box"><div class="ez-score-label" style="color:{q_color}">{q}</div>'
                    f'<div class="ez-score-value">{int(best["Match Score"])}</div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("Other Options / details"):
                if item["pending"].get("pending_count", 0) > 0:
                    st.caption(item["pending"].get("label", ""))
                src = recommendations if item["kind"] == "single" else academy_conflict_recommendations
                div_col = "Current Division" if item["kind"] == "single" else "Problem Division"
                if not src.empty:
                    alts = src[src[div_col] == item["group"]].sort_values("Rank")
                    for _, rr in alts.iterrows():
                        flag = str(rr.get("Safety Flag", "")).strip()
                        lbl = (
                            "⛔ Not safe"
                            if flag
                            else f"Option {int(rr['Rank'])} · {int(rr['Match Score'])} · {rr['Quality']}"
                        )
                        st.markdown(f"**{lbl}** → {rr['Suggested Division']}")
                        st.caption(str(rr.get("Why", ""))[:140])
                        if not flag and int(rr["Rank"]) != 1:
                            if st.button(
                                f"Accept option {int(rr['Rank'])}",
                                key=f"{key_prefix}_alt_{int(rr['Rank'])}",
                            ):
                                _accept_item(item, rr)

            a1, a2 = st.columns([1, 2])
            with a1:
                if st.button("Skip For Now", key=f"{key_prefix}_skip"):
                    # Keep focus index: skipped item moves to end, so same index becomes next.
                    st.session_state.setdefault("guided_skipped", set()).add(item["id"])
                    st.rerun()
            with a2:
                accept_label = "Accept This Move"
                if item["pending"].get("impact") == "resolves":
                    accept_label = "Accept Anyway"
                if st.button(accept_label, key=f"{key_prefix}_accept", type="primary"):
                    _accept_item(item, best)

        if not _queue and not _review_complete:
            st.markdown(
                '<div class="success-card">No open decisions right now. '
                "If this is a new file, check Event Health above.</div>",
                unsafe_allow_html=True,
            )
        elif _queue and not _review_complete:
            if _layout == "Focus Mode":
                _idx = st.session_state["focus_index"]
                _item = _queue[_idx]
                _render_decision_card(
                    _item,
                    key_prefix=f"focus_{widget_key_slug(_item['id'])}",
                    show_nav=True,
                    position_label=f"Decision {_idx + 1} of {len(_queue)}",
                )
            else:
                st.caption("Queue View — open a decision or switch back to Focus Mode.")
                for qi, item in enumerate(_queue):
                    label = "Looks Safe" if item["safe"] else "No Safe Match"
                    if item["skipped"]:
                        label = "Skipped · " + label
                    cols = st.columns([5, 1])
                    with cols[0]:
                        st.markdown(
                            f'<div class="ez-compact-row"><div><b>{item["name"]}</b><br/>'
                            f'<span style="color:#94a3b8;font-size:13px;">{item["group"]}</span></div>'
                            f'<div style="color:#cbd5e1;">{label}</div></div>',
                            unsafe_allow_html=True,
                        )
                    with cols[1]:
                        if st.button("Open", key=f"queue_open_{widget_key_slug(item['id'])}"):
                            st.session_state["pending_focus_open"] = True
                            st.session_state["pending_focus_index"] = qi
                            st.rerun()

        _planned = [m for m in st.session_state.get("moves", []) if m.get("status") == "Active"]
        if _planned:
            with st.expander(f"Moves planned this session — {len(_planned)}", expanded=False):
                for m in _planned:
                    full_idx = next(
                        (i for i, x in enumerate(st.session_state["moves"]) if x is m),
                        None,
                    )
                    r1, r2 = st.columns([5, 1])
                    with r1:
                        st.markdown(
                            f'<div class="ez-compact-row"><div><b>{m["athlete_name"]}</b> → {m["new_division"]}'
                            f'<br/><span style="color:#94a3b8;font-size:12px;">'
                            f'from {m["original_division"]} · score {m["score"]}</span></div></div>',
                            unsafe_allow_html=True,
                        )
                    with r2:
                        if full_idx is not None and st.button("↩ Revert", key=f"g_revert_{full_idx}"):
                            st.session_state["moves"][full_idx]["status"] = "Reverted"
                            st.rerun()
                    note = st.text_input(
                        "Note",
                        key=f"g_note_{full_idx}",
                        value=m.get("director_notes", ""),
                        placeholder="Optional note (e.g. coach approved)",
                        label_visibility="collapsed",
                    )
                    if full_idx is not None and note != m.get("director_notes", ""):
                        st.session_state["moves"][full_idx]["director_notes"] = note

        if _manual_count and not _review_complete:
            with st.expander(f"Manual review — {_manual_count}", expanded=False):
                for mid in sorted(_manual_ids & _current_problem_ids):
                    kind, group = parse_decision_id(mid)
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.caption(f"{kind}: {group}")
                    with c2:
                        if st.button("Restore", key=f"restore_manual_{widget_key_slug(mid)}"):
                            st.session_state["manual_review"].discard(mid)
                            st.rerun()

        if not _review_complete and _active_moves_count > 0:
            _as = apply_mode_stats(st.session_state.get("moves", []))
            st.info(
                f"{_active_moves_count} move(s) planned · {_as['remaining']} still to apply in Smoothcomp. "
                "Use **Apply to Smoothcomp** above anytime — you do not have to wait until review is done."
            )

    # ── Advanced Table View (only when selected) ──────────────────────────────
    if not _guided_mode:
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
            # Hide divisions already solved in planned state (incl. destination singles).
            if _planned_single_groups:
                filtered_recommendations = filtered_recommendations[
                    filtered_recommendations["Current Division"].astype(str).isin(_planned_single_groups)
                ]
            else:
                filtered_recommendations = filtered_recommendations.iloc[0:0].copy()

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
                if not filtered_recommendations.empty:
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
                    _safe_best = best_matches[
                        best_matches["Safety Flag"].astype(str).str.strip().eq("")
                        & ~best_matches["Quality"].astype(str).eq("Do Not Match")
                    ].copy()
                    _blocked_best = best_matches.loc[
                        ~best_matches.index.isin(_safe_best.index)
                    ]
                    if not _blocked_best.empty:
                        st.caption(
                            f"{len(_blocked_best)} recommendation(s) are marked Do Not Match / unsafe "
                            "and cannot be accepted here."
                        )
                    _accept_col1, _accept_col2 = st.columns([4, 1])
                    _accept_options = ["— select athlete —"] + sorted(
                        _safe_best["Athlete"].dropna().unique().tolist()
                    )
                    with _accept_col1:
                        _athlete_to_accept = st.selectbox(
                            "Accept a safe move:",
                            _accept_options,
                            key="accept_athlete_selectbox",
                            help="Only athletes with safe recommendations are listed.",
                        )
                    with _accept_col2:
                        st.write("")
                        _accept_clicked = st.button(
                            "\u2713 Accept Move",
                            disabled=(_athlete_to_accept == "— select athlete —"),
                            key="accept_move_btn",
                        )
                    if _accept_clicked and _athlete_to_accept != "— select athlete —":
                        _row = _safe_best[_safe_best["Athlete"] == _athlete_to_accept].iloc[0]
                        _flag = str(_row.get("Safety Flag", "")).strip()
                        _quality = str(_row.get("Quality", "")).strip()
                        if _flag or _quality == "Do Not Match":
                            st.error(
                                "This recommendation exceeds safety limits (Do Not Match) "
                                "and cannot be accepted."
                            )
                        else:
                            append_accepted_move(
                                _athlete_to_accept,
                                str(_row["Current Division"]),
                                str(_row["Suggested Division"]),
                                int(_row["Match Score"]),
                                str(_row.get("Academy Warning", "")),
                            )
                            st.rerun()

            with tab2:
                _disp_all = (
                    filtered_recommendations[[c for c in _BASIC_COLS if c in filtered_recommendations.columns]]
                    if _basic_view else filtered_recommendations
                )
                st.dataframe(style_quality_rows(_disp_all), use_container_width=True)

            with tab3:
                st.markdown("### Step 3 — Download your reports")
                st.write(
                    "These files help you (or your staff) apply moves in Smoothcomp. "
                    "The **Copy Action Plan** at the bottom is usually the easiest day-of checklist."
                )
                rank1_all = recommendations[recommendations["Rank"] == 1].copy()
                rank1_conflicts = academy_conflict_recommendations[
                    academy_conflict_recommendations["Rank"] == 1
                ].copy() if not academy_conflict_recommendations.empty else pd.DataFrame()
                export_action_plan = build_action_plan(rank1_all, rank1_conflicts)

                if not export_action_plan.empty:
                    st.download_button(
                        "📥 Download Action Plan CSV",
                        data=to_csv_bytes(export_action_plan),
                        file_name="ez_brackets_action_plan.csv",
                        mime="text/csv",
                        help="Top recommendation for each problem division.",
                    )

                st.download_button(
                    "📥 Download Rank #1 Excel Report",
                    data=to_excel_bytes(
                        rank1_all,
                        singles,
                        summary,
                        rank1_conflicts,
                    ),
                    file_name="ez_brackets_rank1_recommendations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Excel workbook with the best suggestion per alone athlete / conflict.",
                )

                st.download_button(
                    "📥 Download All Suggestions CSV",
                    data=to_csv_bytes(recommendations),
                    file_name="ez_brackets_all_single_suggestions.csv",
                    mime="text/csv",
                    help="Every ranked suggestion, not just the top pick.",
                )

                if not academy_conflict_recommendations.empty:
                    st.download_button(
                        "📥 Download Academy Conflict CSV",
                        data=to_csv_bytes(academy_conflict_recommendations),
                        file_name="ez_brackets_academy_conflicts.csv",
                        mime="text/csv",
                        help="Suggestions for same-academy brackets.",
                    )

                st.download_button(
                    "📥 Download Full Excel Report",
                    data=to_excel_bytes(recommendations, singles, summary, academy_conflict_recommendations),
                    file_name="ez_brackets_full_recommendations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Complete workbook with all recommendation sheets.",
                )

                _export_plan_text = format_action_plan_text(st.session_state.get("moves", []))
                if _export_plan_text:
                    st.divider()
                    st.markdown("**Copy Action Plan**")
                    st.caption(
                        "Copy this text and paste it into email, WhatsApp, Discord, or any messaging app. "
                        "Click the copy icon in the top-right corner of the box."
                    )
                    st.download_button(
                        "📥 Download Action Plan (.txt)",
                        data=_export_plan_text.encode("utf-8"),
                        file_name=f"ez_brackets_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="export_tab_download_txt",
                    )
                    st.code(_export_plan_text, language="")
                else:
                    st.divider()
                    st.caption("Accept moves in Guided Mode to generate a Copy Action Plan here.")

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
            if "applied" not in _move_df.columns:
                _move_df["applied"] = False
            _move_df["Applied"] = _move_df["applied"].map(lambda x: "Yes" if x else "No")
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
                    "Score", "Academy Warning", "Accepted", "Notes", "Status", "Applied",
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
                    "Score", "Academy Warning", "Accepted", "Notes", "Status", "Applied",
                ]]),
                file_name="ez_brackets_move_log.csv",
                mime="text/csv",
                key="download_move_log_btn",
            )

            st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown(
        '<div class="section-card">'
        '<b>Ready when you are.</b> Upload a Smoothcomp CSV, map columns from another '
        'registration system, or choose sample data above to begin.'
        '</div>',
        unsafe_allow_html=True,
    )
