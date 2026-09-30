"""Import, portable backups, and projected event state for the director workflow."""

import copy
import csv
import hashlib
import json
from io import StringIO

import pandas as pd


EVENT_COLUMNS = (
    "athlete_name", "approved_clean", "academy_clean", "group_clean",
    "entry_clean", "skill_clean", "age_clean", "weight_clean", "gender_clean",
)
MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_BACKUP_BYTES = 100 * 1024 * 1024
MAX_REGISTRATIONS = 25000
RULE_LIMITS = {
    "set_min_target_size": (1, 3, 1), "set_top_n": (1, 5, 1),
    "set_max_safe_weight_diff": (5, 60, 5), "set_max_safe_age_diff": (0, 5, 1),
    "set_max_safe_skill_diff": (0, 5, 1), "set_same_academy_penalty": (0, 60, 5),
    "set_entry_crossover_penalty": (0, 60, 5),
}
BOOL_RULES = {"set_only_approved", "set_allow_entry_crossover", "set_juvenile_adult_step_up"}


def smoothcomp_column_names(header):
    """Keep the first normalized heading; suffix repeats without stealing names.

    Reserve every source heading before generating suffixes so, for example,
    an existing 'Weight [2]' column is never overwritten by a second Weight.
    """
    reserved = {name.strip().casefold() for name in header}
    used, names = set(), []
    for original in header:
        base = original.strip()
        name = base
        suffix = 2
        if name.casefold() in used:
            name = f"{base} [{suffix}]"
            while name.casefold() in reserved or name.casefold() in used:
                suffix += 1
                name = f"{base} [{suffix}]"
        used.add(name.casefold())
        names.append(name)
    return names


def read_registration_csv(payload, *, smoothcomp=False):
    """Read registrations; only Smoothcomp imports may disambiguate headings."""
    if not payload or not payload.strip():
        raise ValueError("This file is empty. Export the registrations again and choose the new CSV.")
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("This file exceeds 15 MB. Export only the registrations for this event.")
    try:
        if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
            text = payload.decode("utf-16")
        else:
            try:
                text = payload.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = payload.decode("cp1252")
        if "\x00" in text:
            raise ValueError("Choose a CSV text file, not an Excel workbook renamed to .csv.")
        try:
            delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","
        header = next(csv.reader(StringIO(text), delimiter=delimiter))
        normalized = [s.strip().casefold() for s in header]
        if not all(normalized) or (not smoothcomp and len(set(normalized)) != len(normalized)):
            raise ValueError("Each CSV column needs a different, nonempty heading. Fix the headings and upload again.")
        # Pandas can otherwise reinterpret an extra field as an implicit index,
        # silently putting the wrong values under athlete/division headings.
        reader = csv.reader(StringIO(text), delimiter=delimiter, strict=True)
        next(reader)
        for row_number, row in enumerate(reader, start=2):
            if row and len(row) != len(header):
                raise ValueError(f"CSV row {row_number} has {len(row)} fields; the headings have {len(header)}. Export a fresh CSV or fix that row.")
        names = smoothcomp_column_names(header) if smoothcomp else [s.strip() for s in header]
        frame = pd.read_csv(StringIO(text), sep=delimiter, header=0, names=names, dtype=str, keep_default_na=False)
    except (UnicodeError, csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as exc:
        raise ValueError("The CSV could not be read. Export a fresh CSV with one registration per row.") from exc
    frame.columns = frame.columns.str.strip()
    frame = frame.loc[frame.apply(lambda r: r.astype(str).str.strip().ne("").any(), axis=1)].reset_index(drop=True)
    if frame.empty:
        raise ValueError("This CSV has headings but no registrations. Check the export filters and try again.")
    if len(frame) > MAX_REGISTRATIONS:
        raise ValueError("This version supports up to 25,000 registrations per file. Export a smaller event file.")
    # Positional provenance includes original case and whitespace, even repeats.
    frame.attrs["original_csv_headers"] = header
    return frame


def event_frame(frame):
    """Only keep fields used by matching; backups do not need unrelated CSV data."""
    return frame.reindex(columns=EVENT_COLUMNS, fill_value="").fillna("").astype(str).apply(lambda c: c.str.strip())


def import_problems(frame):
    errors, notices = [], []
    data = event_frame(frame)
    if data.empty:
        return ["There are no registrations to review."], notices
    for col, label in (("athlete_name", "athlete name"), ("group_clean", "division")):
        missing = data[col].str.casefold().isin(["", "nan", "none", "null", "/ / /"])
        if missing.any():
            rows = ", ".join(str(i + 2) for i in data.index[missing][:8])
            errors.append(f"Missing {label} on CSV row(s) {rows}. Fill these in before reviewing.")
    identities = data[["athlete_name", "group_clean"]].apply(lambda c: c.str.casefold())
    duplicates = identities.duplicated(keep=False)
    if duplicates.any():
        names = ", ".join(data.loc[duplicates, "athlete_name"].drop_duplicates().head(5))
        errors.append(f"Repeated names in the same division: {names}. Remove duplicate registrations or distinguish athletes with the same name; otherwise counts and actions are ambiguous.")
    division_fields = ["entry_clean", "skill_clean", "age_clean", "weight_clean", "gender_clean"]
    inconsistent = data.groupby("group_clean")[division_fields].nunique().gt(1).any(axis=1)
    if inconsistent.any():
        examples = "; ".join(inconsistent.index[inconsistent].tolist()[:3])
        errors.append(f"Registrations in the same division have conflicting age, weight, experience, or entry fields: {examples}. Check the CSV or column mapping before reviewing.")
    missing_fields = [label for col, label in (("skill_clean", "belt/experience"), ("age_clean", "age"), ("weight_clean", "weight")) if data[col].eq("").any()]
    if missing_fields:
        notices.append("Some registrations lack " + ", ".join(missing_fields) + ". Their suggestions will need a data check.")
    if data["academy_clean"].eq("").any():
        notices.append("Some team names are missing. Team-only checks may be incomplete.")
    return errors, notices


def event_fingerprint(frame):
    # Mapping changes and status updates count as event-data changes, too.
    records = event_frame(frame).to_dict("records")
    content = json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def action_evidence(move, frame):
    """Evidence in a registration export; marking Applied alone is not verification."""
    data = event_frame(frame)
    name = str(move.get("athlete_name", "")).strip()
    src = str(move.get("original_division", "")).strip()
    dst = str(move.get("new_division", "")).strip()
    person = data["athlete_name"].eq(name)
    src_count = int((person & data["group_clean"].eq(src)).sum())
    dst_count = int((person & data["group_clean"].eq(dst)).sum())
    if src_count > 1 or dst_count > 1:
        return "Ambiguous registration"
    method = move.get("apply_method", "move")
    if dst_count == 1 and ((method == "copy" and src_count == 1) or (method == "move" and src_count == 0)):
        return "Verified in export"
    if src_count == 1:
        return "Still to apply" if dst_count == 0 else "Original still present for Move"
    return "Athlete or original registration not found"


def project_registrations(frame, moves, parse_group):
    """Apply accepted actions once to the roster used for subsequent suggestions.

    A refreshed export can already contain the destination registration. Never
    add it twice, and never treat a merely matching division as a matching person.
    Unmatched actions are reported so the UI can stop further planning.
    """
    planned = event_frame(frame).copy()
    issues = []
    for move in moves:
        if move.get("status") != "Active":
            continue
        name, src, dst = (str(move.get(k, "")).strip() for k in ("athlete_name", "original_division", "new_division"))
        person = planned["athlete_name"].eq(name)
        source = planned[person & planned["group_clean"].eq(src)]
        target = planned[person & planned["group_clean"].eq(dst)]
        if src == dst or len(source) > 1 or len(target) > 1:
            issues.append(move)
            continue
        if source.empty:
            if target.empty or move.get("apply_method", "move") == "copy":
                issues.append(move)
            continue
        new_row = source.iloc[0].copy()
        if target.empty:
            new_row["group_clean"] = dst
            destination_rows = planned[planned["group_clean"].eq(dst)]
            fields = ("entry_clean", "skill_clean", "age_clean", "weight_clean", "gender_clean")
            if not destination_rows.empty:
                # Retain explicit mapped values instead of re-parsing a less
                # detailed division label (e.g. a unit-less label with kg data).
                for col in fields:
                    new_row[col] = destination_rows.iloc[0][col]
            else:
                for col, value in zip(fields, parse_group(dst)):
                    new_row[col] = value
            planned = pd.concat([planned, new_row.to_frame().T], ignore_index=True)
        if move.get("apply_method", "move") == "move":
            planned = planned.loc[~(planned["athlete_name"].eq(name) & planned["group_clean"].eq(src))].reset_index(drop=True)
    return planned, issues


def validate_saved_session(data, presets):
    """Validate the entire portable backup before mutating live session state."""
    if not isinstance(data, dict) or data.get("ez_brackets_version") != "1.0":
        raise ValueError("Choose an EZ Brackets progress file (.json). This file is not a supported backup.")
    result = copy.deepcopy(data)
    moves = result.get("moves")
    if not isinstance(moves, list) or len(moves) > MAX_REGISTRATIONS:
        raise ValueError("The progress file has an invalid action list.")
    fields = ("athlete_name", "original_division", "new_division", "academy_warning", "timestamp", "director_notes", "status")
    active_keys = set()
    for m in moves:
        if not isinstance(m, dict) or any(not isinstance(m.get(k), str) for k in fields):
            raise ValueError("The progress file contains an invalid action. Your current event has not been changed.")
        if not all(m[k].strip() for k in fields[:3]) or m["original_division"] == m["new_division"]:
            raise ValueError("An action is missing its athlete or distinct source/destination divisions.")
        if m["status"] not in ("Active", "Reverted") or type(m.get("score")) is not int or not 0 <= m["score"] <= 100:
            raise ValueError("An action has an invalid status or score.")
        if type(m.get("applied", False)) is not bool or m.get("apply_method", "move") not in ("copy", "move"):
            raise ValueError("An action has invalid Copy/Move or Applied settings.")
        for field in ("group_action_id", "applied_at"):
            if field in m and not isinstance(m[field], str):
                raise ValueError("An action contains an invalid tracking field.")
        identity = (m["athlete_name"], m["original_division"])
        if m["status"] == "Active" and identity in active_keys:
            raise ValueError("The progress file contains two active actions for the same registration.")
        if m["status"] == "Active":
            active_keys.add(identity)
    for field in ("guided_skipped", "manual_review"):
        values = result.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError("The saved review list is invalid.")
    rules = result.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError("The saved event rules are invalid.")
    for key, value in rules.items():
        if key in BOOL_RULES and type(value) is not bool:
            raise ValueError("The saved event rules contain an invalid switch.")
        if key in RULE_LIMITS:
            lo, hi, step = RULE_LIMITS[key]
            if type(value) is not int or not lo <= value <= hi or (value - lo) % step:
                raise ValueError("A saved rule is outside the supported range. Choose an unchanged progress file.")
    if result.get("last_preset", "") not in ("", *presets):
        raise ValueError("The saved rules profile is not supported by this version.")
    if result.get("apply_method", "copy") not in ("copy", "move"):
        raise ValueError("The saved Copy/Move setting is invalid.")
    if type(result.get("focus_index", 0)) is not int or result.get("focus_index", 0) < 0:
        raise ValueError("The saved review position is invalid.")
    event = result.get("event")
    if event is not None:
        if not isinstance(event, dict) or not isinstance(event.get("name"), str) or type(event.get("practice", False)) is not bool:
            raise ValueError("The saved event information is invalid.")
        records = event.get("registrations")
        if not isinstance(records, list) or not 0 < len(records) <= MAX_REGISTRATIONS:
            raise ValueError("The backup has no valid event registrations.")
        if any(not isinstance(row, dict) or any(not isinstance(row.get(c), str) for c in EVENT_COLUMNS) for row in records):
            raise ValueError("The backup contains invalid registration fields.")
        errors, _ = import_problems(pd.DataFrame(records))
        if errors:
            raise ValueError(errors[0])
    return result


def safe_export_frame(frame):
    """Keep uploaded text literal when a report is opened in a spreadsheet."""
    def literal(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    return frame.map(literal)
