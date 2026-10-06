"""
OIL-Track AI - Test Suite
Verifies data extraction, AI semantic matching, schedule variance calculations,
and audit trail persistence.
"""

import os
import unittest
from src.extraction.extractor import parse_text_diary, detect_status, detect_discipline
from src.matching.matcher import ActivityMatcher
from src.schedule.db_manager import (
    init_db,
    ingest_schedule_file,
    sync_actual_progress,
    log_audit_record,
    get_reviewed_events_map,
    clear_audit_trail
)

class TestOILTrackPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure test database and baseline schedule exist."""
        init_db()
        sample_schedule = os.path.join("data", "schedule", "project_schedule.xlsx")
        if os.path.exists(sample_schedule):
            ingest_schedule_file(sample_schedule)
        cls.matcher = ActivityMatcher()

    def test_01_discipline_detection(self):
        """Verify keyword discipline parser."""
        self.assertEqual(detect_discipline("1. Civil Discipline: Reinforcement work"), "Civil")
        self.assertEqual(detect_discipline("Piping line fit-up ongoing"), "Piping")
        self.assertEqual(detect_discipline("Random unstructured sentence"), "Unknown")

    def test_02_status_detection(self):
        """Verify lifecycle status detection."""
        self.assertEqual(detect_status("Rebar fixing completed today"), "COMPLETED")
        self.assertEqual(detect_status("Excavation started this morning"), "STARTED")
        self.assertEqual(detect_status("Curing in progress"), "IN_PROGRESS")

    def test_03_semantic_matcher_accuracy(self):
        """Verify that site phrasing resolves to expected schedule activity ID."""
        # Query: 'Rebar fixing completed for compressor foundation' should map to CIV-FND-003
        results = self.matcher.match_activity(
            "Rebar fixing completed for compressor foundation",
            extracted_discipline="Civil",
            top_k=1
        )
        self.assertTrue(len(results) > 0)
        top_match = results[0]
        self.assertEqual(top_match["activity_id"], "CIV-FND-003")
        self.assertGreaterEqual(top_match["confidence"], 80.0)

    def test_04_schedule_variance_calculation(self):
        """Verify variance math when actual completion exceeds planned finish."""
        # CIV-FND-003 planned finish is 2026-09-09
        # Actual finish reported as 2026-09-11 -> +2 days delay
        result = sync_actual_progress(
            activity_id="CIV-FND-003",
            report_date="2026-09-11",
            event_type="COMPLETED",
            progress_pct=100.0
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["finish_variance_days"], 2)

    def test_05_audit_deduplication(self):
        """Verify that logged events appear in reviewed events map to prevent duplicates."""
        clear_audit_trail()
        test_record = {
            "report_date": "2026-09-07",
            "discipline": "Civil",
            "raw_site_text": "Unit testing audit deduplication entry.",
            "matched_activity_id": "CIV-FND-003",
            "matched_description": "Reinforcement Work",
            "confidence": 88.5,
            "event_type": "COMPLETED",
            "reported_progress": 100.0,
            "decision": "APPROVED",
            "reviewer_comments": "Automated test."
        }
        log_audit_record(test_record)
        
        reviewed_map = get_reviewed_events_map()
        expected_key = "2026-09-07||Unit testing audit deduplication entry."
        self.assertIn(expected_key, reviewed_map)
        self.assertEqual(reviewed_map[expected_key]["decision"], "APPROVED")

if __name__ == "__main__":
    unittest.main()