"""
Automation script: pull applications from the database and build a Pandas report.

Usage: python scripts/generate_report.py --db tracker.db --out reports
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd


def load_applications(db_path):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM applications", conn, parse_dates=["applied_on"])


def build_summary(df):
    # Return a dict of summary tables from the applications DataFrame.
    if df.empty:
        return {"by_status": pd.DataFrame(columns=["status", "count"]),
                "by_week": pd.DataFrame(columns=["week", "count"]),
                "response_rate": 0.0}

    by_status = df.groupby("status").size().reset_index(name="count")
    by_week = (
        df.set_index("applied_on").resample("W").size().reset_index(name="count")
        .rename(columns={"applied_on": "week"})
    )
    responded = df["status"].isin(["interview", "offer", "rejected"]).sum()
    return {"by_status": by_status, "by_week": by_week,
            "response_rate": round(responded / len(df) * 100, 1)}


def main():
    parser = argparse.ArgumentParser(description="Generate job application reports")
    parser.add_argument("--db", default="tracker.db")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()

    df = load_applications(args.db)
    summary = build_summary(df)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "applications.csv", index=False)
    summary["by_status"].to_csv(out_dir / "summary_by_status.csv", index=False)
    summary["by_week"].to_csv(out_dir / "summary_by_week.csv", index=False)

    print(f"Total applications: {len(df)}")
    print(f"Response rate: {summary['response_rate']}%")
    print(summary["by_status"].to_string(index=False))
    print(f"Reports saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
