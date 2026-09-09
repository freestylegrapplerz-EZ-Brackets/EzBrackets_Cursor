import ast
import copy
import json
from io import BytesIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from contextlib import nullcontext

import pandas as pd
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from workflow_support import (
    action_evidence, event_fingerprint, event_frame, import_problems,
    project_registrations, read_registration_csv, validate_saved_session,
)

ROOT = Path(__file__).resolve().parents[1]


def load_engine():
    """Exercise the real monolithic app functions without rendering its UI."""
    source = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    nodes = []
    for node in source.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            nodes.append(node)
        elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
            nodes.append(node)
    module = ModuleType("engine_under_test")
    module.__file__ = str(ROOT / "app.py")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), module.__file__, "exec"), module.__dict__)
    module.st = SimpleNamespace(session_state={}, spinner=lambda *a, **k: nullcontext())
    return module


def make_roster(engine, rows=None):
    rows = rows or [
        ("Alex", "A", "Men Gi / White / Adult / 150 - 159 lbs"),
        ("Blair", "B", "Men Gi / White / Adult / 160 - 169 lbs"),
        ("Casey", "C", "Men Gi / White / Adult / 160 - 169 lbs"),
    ]
    raw = pd.DataFrame(rows, columns=["Name", "Academy", "Group"])
    raw["Status"] = "Approved"
    return event_frame(engine.normalize_dataframe(raw))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.e = load_engine()
        self.frame = make_roster(self.e)
        self.e.st.session_state = {"moves": [], "apply_method": "copy", "guided_skipped": set(), "manual_review": set()}
        self.e.append_accepted_move("Alex", self.frame.iloc[0]["group_clean"], self.frame.iloc[1]["group_clean"], 90)
        self.move = self.e.st.session_state["moves"][0]

    def test_blank_and_header_only_csv_have_actionable_error(self):
        for content in (b"", b"  ", b"Name,Group\n"):
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_registration_csv(content)

    def test_delimiter_and_encoding_support(self):
        text = "Name;Group\nJos\u00e9;Adult\n"
        for content in (text.encode("utf-8-sig"), text.encode("utf-16"), text.encode("cp1252")):
            with self.subTest(content=content[:4]):
                self.assertEqual(read_registration_csv(content).iloc[0]["Name"], "Jos\u00e9")

    def test_duplicate_headers_and_malformed_rows_rejected(self):
        for content in (b"Name,Name\nA,B\n", b'Name,Group\n"Alex,Adult\n', b"Name,Group\nAlex,Adult,extra\n"):
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_registration_csv(content)

    def test_blank_names_are_not_fabricated(self):
        frame = self.e.normalize_dataframe(pd.DataFrame({"Name": [None], "Group": ["Gi / White / Adult / 150 lbs"]}))
        self.assertEqual(frame.iloc[0]["athlete_name"], "")
        self.assertTrue(import_problems(frame)[0])

    def test_duplicate_registration_is_blocked_but_multiple_divisions_are_valid(self):
        repeated = pd.concat([self.frame, self.frame.iloc[[0]]], ignore_index=True)
        self.assertTrue(import_problems(repeated)[0])
        other = self.frame.iloc[[0]].copy()
        other["group_clean"] = "Men No-Gi / Beginner / Adult / 150 - 159 lbs"
        self.assertFalse(import_problems(pd.concat([self.frame, other], ignore_index=True))[0])

    def test_mapping_changes_affect_identity(self):
        changed = self.frame.copy()
        changed.loc[0, "approved_clean"] = "Pending"
        self.assertNotEqual(event_fingerprint(self.frame), event_fingerprint(changed))

    def test_conflicting_fields_within_one_division_are_blocked(self):
        changed = self.frame.copy()
        changed.loc[2, "weight_clean"] = "90 kg"
        self.assertTrue(any("conflicting" in e for e in import_problems(changed)[0]))

    def test_projection_retains_explicit_destination_mapping(self):
        frame = self.frame.copy()
        frame.loc[1:, "weight_clean"] = "70 - 75 kg"
        result, issues = project_registrations(frame, [self.move], self.e.parse_group)
        self.assertFalse(issues)
        copied = result[result["athlete_name"].eq("Alex") & result["group_clean"].eq(self.move["new_division"])]
        self.assertEqual(copied.iloc[0]["weight_clean"], "70 - 75 kg")

    def test_copy_projection_keeps_original(self):
        result, issues = project_registrations(self.frame, [self.move], self.e.parse_group)
        self.assertFalse(issues)
        self.assertEqual(len(result), 4)
        self.assertEqual(int(result["athlete_name"].eq("Alex").sum()), 2)

    def test_copy_projection_is_idempotent_after_export_refresh(self):
        result, _ = project_registrations(self.frame, [self.move], self.e.parse_group)
        rerun, issues = project_registrations(result, [self.move], self.e.parse_group)
        pd.testing.assert_frame_equal(result, rerun)
        self.assertFalse(issues)
        self.assertEqual(action_evidence(self.move, rerun), "Verified in export")

    def test_move_projection_is_idempotent_and_removes_original(self):
        self.move["apply_method"] = "move"
        result, issues = project_registrations(self.frame, [self.move], self.e.parse_group)
        self.assertEqual(len(result), 3)
        self.assertFalse(issues)
        self.assertEqual(int(result["group_clean"].eq(self.move["original_division"]).sum()), 0)
        rerun, issues = project_registrations(result, [self.move], self.e.parse_group)
        pd.testing.assert_frame_equal(result, rerun)
        self.assertEqual(action_evidence(self.move, result), "Verified in export")

    def test_applied_checkbox_alone_does_not_verify_export(self):
        self.move["applied"] = True
        self.assertEqual(action_evidence(self.move, self.frame), "Still to apply")

    def test_copy_without_original_does_not_verify(self):
        result, _ = project_registrations(self.frame, [self.move], self.e.parse_group)
        result = result[result["group_clean"].ne(self.move["original_division"])]
        self.assertNotEqual(action_evidence(self.move, result), "Verified in export")
        _, issues = project_registrations(result, [self.move], self.e.parse_group)
        self.assertEqual(len(issues), 1)

    def test_wrong_registration_is_not_matched_by_division_alone(self):
        changed = self.frame.copy()
        changed.loc[0, "athlete_name"] = "Someone else"
        _, issues = project_registrations(changed, [self.move], self.e.parse_group)
        self.assertEqual(len(issues), 1)
        self.assertIn("not found", action_evidence(self.move, changed))

    def test_group_accept_and_revert_are_per_athlete(self):
        self.e.st.session_state["moves"] = []
        self.e.append_group_move(["Blair", "Casey"], self.move["new_division"], self.move["original_division"], 90)
        moves = self.e.st.session_state["moves"]
        self.assertEqual(len(moves), 2)
        result, issues = project_registrations(self.frame, moves, self.e.parse_group)
        self.assertEqual(len(result), 5)
        self.assertFalse(issues)
        self.assertEqual(self.e.revert_move(moves, 0), 2)
        self.assertFalse(self.e.active_moves_only(moves))

    def test_self_opponent_is_excluded(self):
        frame = make_roster(self.e, [("Alex", "A", self.move["original_division"]), ("Alex", "A", self.move["new_division"])])
        self.assertTrue(self.e.make_recommendations(frame).empty)

    def test_unapproved_athletes_do_not_become_opponents(self):
        self.frame.loc[1:, "approved_clean"] = "Pending"
        self.assertTrue(self.e.make_recommendations(self.frame, only_approved=True).empty)

    def test_group_summary_handles_empty_filter(self):
        summary = self.e.group_summary(self.frame.iloc[:0])
        self.assertTrue(summary.empty)
        self.assertIn("group", summary.columns)

    def test_kg_and_belt_ladders_preserved(self):
        self.assertAlmostEqual(self.e.weight_mid("60 - 65 kg"), 62.5 * 2.2046226218, delta=0.05)
        self.assertEqual(self.e.skill_step_difference("White", "Blue", "Adult", "Adult")[0], 1)
        self.assertEqual(self.e.age_step_difference("Master 2", "Master 3"), 1)

    def test_unknown_weight_and_gender_never_look_safe(self):
        frame = make_roster(self.e, [("Alex", "A", "Gi / White / Adult / unknown"), ("Blair", "B", "Gi / White / Adult / 150 lbs")])
        recs = self.e.make_recommendations(frame)
        self.assertFalse(recs.empty)
        self.assertTrue(recs["Data Gaps"].str.contains("weight").all())
        self.assertTrue(recs["Data Gaps"].str.contains("gender").all())
        self.assertFalse(any(self.e.recommendation_is_safe(r) for _, r in recs.iterrows()))

    def test_opposite_genders_and_entry_types_are_excluded(self):
        for target in ("Women Gi / White / Adult / 150 - 159 lbs", "Men No-Gi / White / Adult / 150 - 159 lbs"):
            with self.subTest(target=target):
                frame = make_roster(self.e, [("Alex", "A", self.move["original_division"]), ("Blair", "B", target)])
                self.assertTrue(self.e.make_recommendations(frame).empty)

    def test_actual_gap_labels_do_not_invent_class_counts(self):
        row = {"Weight Difference": 30, "Skill Difference": 2, "Age Difference": 2, "Academy Warning": ""}
        bullets = " ".join(self.e.build_safety_bullets(row))
        self.assertIn("30 lbs", bullets)
        self.assertNotIn("exceeds limit", bullets)
        self.assertNotIn("weight classes apart", bullets)

    def test_backups_include_event_rules_and_apply_method(self):
        state = self.e.st.session_state
        state.update(event_df=self.frame, event_name="Test event", practice=False, last_preset="Adult Standard", set_max_safe_weight_diff=25, set_only_approved=False)
        payload = json.loads(self.e.workflow_backup())
        validated = validate_saved_session(payload, self.e.SCORING_PRESETS)
        self.assertEqual(len(validated["event"]["registrations"]), 3)
        self.assertEqual(validated["rules"]["set_max_safe_weight_diff"], 25)
        self.assertFalse(validated["rules"]["set_only_approved"])
        self.assertEqual(validated["apply_method"], "copy")

    def test_corrupt_backup_is_rejected_before_state_change(self):
        state = self.e.st.session_state
        original = copy.deepcopy(state)
        payload = self.e.build_session_payload()
        for field, value in (("moves", [None]), ("manual_review", [{}]), ("rules", {"set_top_n": 99}), ("focus_index", "bad"), ("apply_method", "delete")):
            bad = copy.deepcopy(payload)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_saved_session(bad, self.e.SCORING_PRESETS)
        self.assertEqual(state, original)

    def test_legacy_backup_remains_supported(self):
        payload = self.e.session_to_json([self.move], [], "Adult Standard", "🃏 Guided Mode")
        validated = validate_saved_session(payload, self.e.SCORING_PRESETS)
        self.assertNotIn("event", validated)
        self.assertEqual(validated["moves"][0]["athlete_name"], "Alex")

    def test_spreadsheet_exports_keep_uploaded_text_literal(self):
        data = pd.DataFrame({"Name": ['=HYPERLINK("bad")', "+formula", "Alex"]})
        csv_text = self.e.to_csv_bytes(data).decode("utf-8-sig")
        self.assertIn("'=HYPERLINK", csv_text)
        book = load_workbook(BytesIO(self.e.to_excel_bytes(pd.DataFrame(), pd.DataFrame(), data)))
        self.assertEqual(book["All Groups"]["A2"].data_type, "s")


class BrowserWorkflowTests(unittest.TestCase):
    def start(self):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertNotIn("event_df", at.session_state.filtered_state)
        at.button(key="start_practice").click().run()
        self.assertFalse(at.exception)
        return at

    def accept(self, at):
        checks = [c for c in at.checkbox if c.key and c.key.startswith("decision_")]
        if checks:
            checks[0].check().run()
        [b for b in at.button if b.key and b.key.endswith("_accept")][0].click().run()
        self.assertFalse(at.exception)

    def test_practice_accept_apply_and_backup_restore(self):
        at = self.start()
        self.accept(at)
        self.assertEqual(len(at.session_state["moves"]), 1)
        at.radio(key="workflow_page").set_value("3 · Apply").run()
        self.assertTrue(at.button(key="mark_applied").disabled)
        at.checkbox(key="apply_check_0").check().run()
        at.button(key="mark_applied").click().run()
        self.assertTrue(at.session_state["moves"][0]["applied"])
        at.text_input(key="plan_note_0").set_value("Coach checked").run()
        engine = load_engine()
        engine.st.session_state = at.session_state.filtered_state
        payload = json.loads(engine.workflow_backup())
        self.assertEqual(payload["moves"][0]["director_notes"], "Coach checked")
        at.session_state["pending_restore"] = validate_saved_session(payload, engine.SCORING_PRESETS)
        at.run()
        at.button(key="confirm_restore").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["moves"][0]["director_notes"], "Coach checked")
        self.assertEqual(len(at.session_state["event_df"]), len(payload["event"]["registrations"]))

    def test_manual_items_can_be_reopened_after_queue_is_empty(self):
        at = self.start()
        ids = [b.key.removeprefix("open_decision_") for b in at.button if b.key and b.key.startswith("open_decision_")]
        self.assertTrue(ids)
        engine = load_engine()
        engine.st.session_state = at.session_state.filtered_state
        settings = {key: engine.st.session_state["set_" + key] for key in engine.SCORING_PRESETS[engine.st.session_state["last_preset"]]}
        context = engine.current_review_data(settings)
        at.session_state["manual_review"] = {item["id"] for item in context["queue"]}
        at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any("not finished" in w.value for w in at.warning))
        at.radio(key="workflow_page").set_value("4 · Finish").run()
        [b for b in at.button if b.key and b.key.startswith("manual_return_")][0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.radio(key="workflow_page").value, "2 · Review")

    def test_event_settings_survive_load_cancel_and_page_changes(self):
        at = self.start()
        at.slider(key="set_max_safe_weight_diff").set_value(25).run()
        at.button(key="change_event").click().run()
        at.button(key="cancel_load").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.slider(key="set_max_safe_weight_diff").value, 25)
        at.radio(key="workflow_page").set_value("3 · Apply").run()
        at.text_input(key="smoothcomp_event_url").set_value("https://smoothcomp.com/en/event/123").run()
        at.radio(key="workflow_page").set_value("2 · Review").run()
        at.radio(key="workflow_page").set_value("3 · Apply").run()
        self.assertEqual(at.text_input(key="smoothcomp_event_url").value, "https://smoothcomp.com/en/event/123")

    def test_practice_to_real_requires_fresh_plan(self):
        at = self.start()
        self.accept(at)
        frame = at.session_state["event_df"]
        at.session_state["pending_event"] = {"frame": frame, "name": "Real event", "practice": False, "csv_hash": "real"}
        at.run()
        self.assertTrue(at.button(key="keep_event").disabled)
        self.assertEqual(len(at.session_state["moves"]), 1)
        at.button(key="new_event").click().run()
        self.assertFalse(at.exception)
        self.assertFalse(at.session_state["moves"])
        self.assertFalse(at.session_state["practice"])

    def test_zero_approved_does_not_report_finished(self):
        at = self.start()
        frame = at.session_state["event_df"].copy()
        frame["approved_clean"] = "Pending"
        at.session_state["event_df"] = frame
        at.radio(key="workflow_page").set_value("4 · Finish").run()
        self.assertFalse(at.exception)
        self.assertTrue(any("No registrations match" in w.value for w in at.warning))
        self.assertFalse(any("Check your work" in h.value for h in at.header))

    def test_updated_export_verifies_without_double_counting(self):
        at = self.start()
        self.accept(at)
        engine = load_engine()
        updated, _ = project_registrations(at.session_state["event_df"], at.session_state["moves"], engine.parse_group)
        at.session_state["pending_event"] = {"frame": updated, "name": "Updated practice", "practice": True, "csv_hash": "updated"}
        at.run()
        at.button(key="keep_event").click().run()
        self.assertFalse(at.exception)
        self.assertTrue(at.session_state["moves"][0]["applied"])
        self.assertEqual(len(at.session_state["event_df"]), len(updated))
        at.radio(key="workflow_page").set_value("4 · Finish").run()
        self.assertFalse(at.exception)
        self.assertTrue(any("1 of 1 actions confirmed" in m.value for m in at.markdown))


if __name__ == "__main__":
    unittest.main()
