import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from src.Database.database import Base
from src.Database.models import ScanRun
from src.Database.crud import get_last_scan_for_domain
from src.Core.diffing import compute_diff

# Direct SQLAlchemy to compile PostgreSQL JSONB as JSON when running tests on SQLite
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

class TestDiffingAndCrud(unittest.TestCase):
    def test_compute_diff_basic(self):
        old_output = {
            "subdomains": ["a.com", "b.com"],
            "endpoints": ["/api/v1", "/login"],
            "risk_level": "low",
            "malicious_votes": 2
        }
        new_output = {
            "subdomains": ["b.com", "c.com"],
            "endpoints": ["/login", "/auth"],
            "risk_level": "medium",
            "malicious_votes": 5
        }

        diff = compute_diff(old_output, new_output)

        self.assertEqual(diff["added_subdomains"], ["c.com"])
        self.assertEqual(diff["removed_subdomains"], ["a.com"])
        self.assertEqual(diff["added_endpoints"], ["/auth"])
        self.assertEqual(diff["removed_endpoints"], ["/api/v1"])
        self.assertTrue(diff["risk_changed"])
        self.assertEqual(diff["previous_risk_level"], "low")
        self.assertEqual(diff["current_risk_level"], "medium")
        self.assertEqual(diff["malicious_votes_delta"], 3)

    def test_compute_diff_missing_keys(self):
        old_output = {}
        new_output = {
            "subdomains": ["a.com"],
            "endpoints": ["/api"],
            "risk_level": "high",
            "malicious_votes": None
        }

        diff = compute_diff(old_output, new_output)

        self.assertEqual(diff["added_subdomains"], ["a.com"])
        self.assertEqual(diff["removed_subdomains"], [])
        self.assertEqual(diff["added_endpoints"], ["/api"])
        self.assertEqual(diff["removed_endpoints"], [])
        self.assertTrue(diff["risk_changed"])
        self.assertIsNone(diff["previous_risk_level"])
        self.assertEqual(diff["current_risk_level"], "high")
        self.assertEqual(diff["malicious_votes_delta"], 0)

    def test_compute_diff_exception_safety(self):
        # Passing invalid arguments should not raise an exception, should return {}
        diff = compute_diff(None, None)
        self.assertEqual(diff, {})

    def test_get_last_scan_for_domain(self):
        # Create an in-memory SQLite database for testing the CRUD operation
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        # Insert test runs
        run1 = ScanRun(run_id="run-1", input="google.com", output={"subdomains": ["a"]})
        run2 = ScanRun(run_id="run-2", input="GOOGLE.COM", output={"subdomains": ["b"]})
        run3 = ScanRun(run_id="run-3", input="yahoo.com", output={"subdomains": ["c"]})

        db.add_all([run1, run2, run3])
        db.commit()

        # 1. Exact case-insensitive matching
        last_scan = get_last_scan_for_domain(db, "google.com")
        self.assertIsNotNone(last_scan)
        self.assertIn(last_scan.run_id, ["run-1", "run-2"])

        # 2. Exclude current run
        last_scan_exclude = get_last_scan_for_domain(db, "google.com", exclude_run_id="run-2")
        self.assertEqual(last_scan_exclude.run_id, "run-1")

        # 3. None returned for non-existent domain
        non_existent = get_last_scan_for_domain(db, "bing.com")
        self.assertIsNone(non_existent)

        db.close()

if __name__ == "__main__":
    unittest.main()
