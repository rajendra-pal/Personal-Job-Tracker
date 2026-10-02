import unittest
import pandas as pd

from scripts.generate_report import build_summary


class ReportTestCase(unittest.TestCase):
    def test_summary_counts_and_response_rate(self):
        df = pd.DataFrame({
            "status": ["applied", "interview", "rejected", "applied"],
            "applied_on": pd.to_datetime(["2026-09-01", "2026-09-02", "2026-09-10", "2026-09-11"]),
        })
        summary = build_summary(df)
        self.assertEqual(summary["response_rate"], 50.0)
        applied = summary["by_status"].set_index("status").loc["applied", "count"]
        self.assertEqual(applied, 2)

    def test_empty_dataframe(self):
        summary = build_summary(pd.DataFrame(columns=["status", "applied_on"]))
        self.assertEqual(summary["response_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
