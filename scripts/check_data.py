"""Verify published aggregate consistency and attribution before deployment."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check() -> None:
    """Require unique matches, valid references, reconciled runs and source notices."""
    data = json.loads((ROOT / "site/data.json").read_text())
    ids = {row["id"] for row in data["matches"]}
    if (
        len(ids) != len(data["matches"])
        or len(ids) != data["manifest"]["selected_matches"]
    ):
        raise ValueError("Match totals do not reconcile")
    runs = {key: 0 for key in ids}
    for row in data["players"]:
        if row["match_id"] not in ids or not 2008 <= row["season"] <= 2020:
            raise ValueError("Invalid player reference or period")
        if (
            min(
                row[key]
                for key in [
                    "runs",
                    "balls_faced",
                    "wickets",
                    "legal_balls",
                    "runs_conceded",
                ]
            )
            < 0
        ):
            raise ValueError("Negative aggregate")
        runs[row["match_id"]] += row["runs"]
    for row in data["matches"]:
        if (
            not 2008 <= row["season"] <= 2020
            or runs[row["id"]] + row["extras"] != row["runs"]
        ):
            raise ValueError("Period or batting/extras reconciliation failed")
    if "ODC-By" not in (ROOT / "data/source-notices/LICENSE.txt").read_text():
        raise ValueError("Original data license notice is missing")
    print("Data checks passed:", len(ids), "matches")


if __name__ == "__main__":
    check()
