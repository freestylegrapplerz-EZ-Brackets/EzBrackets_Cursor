import csv
from io import BytesIO, StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from test_workflow import ROOT, load_engine
from workflow_support import read_registration_csv


FIXTURE = Path(__file__).parent / "fixtures" / "smoothcomp_duplicate_headers.csv"


class SmoothcompImportTests(unittest.TestCase):
    def test_real_header_pattern_preserves_every_cell_and_original_heading(self):
        payload = FIXTURE.read_bytes()
        source = list(csv.reader(StringIO(payload.decode())))
        raw = read_registration_csv(payload, smoothcomp=True)
        self.assertEqual(raw.attrs["original_csv_headers"], source[0])
        self.assertEqual(raw.values.tolist(), source[1:])
        self.assertEqual(list(raw.columns)[7:13],
                         ["Weight", "Belt", "Weight [2]", "SKILL [2]", "AGE [2]", "WEIGHT [3]"])
        self.assertEqual(list(raw.columns), list(read_registration_csv(payload, smoothcomp=True).columns))
        engine = load_engine()
        frame = engine.normalize_dataframe(raw)
        self.assertEqual(frame[list(raw.columns)].values.tolist(), source[1:])
        self.assertEqual(frame["group_clean"].tolist(), raw["Group"].tolist())
        self.assertEqual(frame["entry_clean"].tolist(), ["Men No-Gi", "Men Gi"])
        self.assertEqual(frame["skill_clean"].tolist(), ["Beginner", "White"])
        self.assertEqual(frame["age_clean"].tolist(), ["Adult", "Adult"])
        self.assertEqual(frame["weight_clean"].tolist(), ["170 - 179.9 lbs."] * 2)

    def test_suffix_collisions_exact_duplicates_and_casefold_are_lossless(self):
        raw = read_registration_csv(
            b"Weight,Weight,WEIGHT [2],weight [3],Weight ,Group,GROUP\n1,2,3,4,5,correct,wrong\n",
            smoothcomp=True,
        )
        self.assertEqual(list(raw.columns),
                         ["Weight", "Weight [4]", "WEIGHT [2]", "weight [3]", "Weight [5]", "Group", "GROUP [2]"])
        self.assertEqual(raw.iloc[0].tolist(), ["1", "2", "3", "4", "5", "correct", "wrong"])
        self.assertEqual(load_engine().find_col(raw, ["group"]), "Group")

    def test_universal_mapping_remains_strict(self):
        for payload in (FIXTURE.read_bytes(), b"Name,Name\nA,B\n", b"Age, AGE \nA,B\n"):
            for options in ({}, {"smoothcomp": False}):
                with self.subTest(payload=payload[:30], options=options):
                    with self.assertRaisesRegex(ValueError, "different, nonempty"):
                        read_registration_csv(payload, **options)

    def test_smoothcomp_still_rejects_blank_headings_and_bad_rows(self):
        for payload in (b"Name, \nA,B\n", b"Name,Name\nA,B,C\n", b'Name,Name\n"A,B\n', b"Name,Name\n"):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                read_registration_csv(payload, smoothcomp=True)

    def test_duplicate_import_keeps_encoding_and_delimiter_support(self):
        for delimiter in (",", ";", "\t"):
            text = delimiter.join(["Name", "Weight", "WEIGHT"]) + "\n" + delimiter.join(["Jos\u00e9", "001", "002"]) + "\n"
            for encoding in ("utf-8-sig", "utf-16", "cp1252"):
                with self.subTest(delimiter=delimiter, encoding=encoding):
                    raw = read_registration_csv(text.encode(encoding), smoothcomp=True)
                    self.assertEqual(raw.iloc[0].tolist(), ["Jos\u00e9", "001", "002"])

    def test_ui_enables_disambiguation_only_for_smoothcomp(self):
        uploaded = BytesIO(FIXTURE.read_bytes())
        uploaded.name = "regression.csv"

        def uploader(label, *args, **kwargs):
            return uploaded if kwargs.get("key") == "event_csv_upload" else None

        with patch("streamlit.file_uploader", side_effect=uploader):
            at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            self.assertFalse(at.exception)
            self.assertFalse(at.error)
            self.assertFalse(at.button(key="start_uploaded").disabled)
            at.radio(key="import_source").set_value("Another registration system").run()
            self.assertFalse(at.exception)
            self.assertTrue(any("different, nonempty" in error.value for error in at.error))
            at.radio(key="import_source").set_value("Smoothcomp CSV").run()
            at.button(key="start_uploaded").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["event_df"]["skill_clean"].tolist(), ["Beginner", "White"])


if __name__ == "__main__":
    unittest.main()
