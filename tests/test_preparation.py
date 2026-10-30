"""Cricket edge cases that change meaningful batting/bowling statistics."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "prepare_data", Path(__file__).resolve().parents[1] / "scripts/prepare_data.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_wides_no_balls_and_run_out():
    """Wides, no-balls and run-outs follow distinct denominator/credit rules."""
    deliveries = [
        {
            "batter": "Batter",
            "bowler": "Bowler",
            "runs": {"batter": 0, "extras": 1, "total": 1},
            "extras": {"wides": 1},
        },
        {
            "batter": "Batter",
            "bowler": "Bowler",
            "runs": {"batter": 4, "extras": 1, "total": 5},
            "extras": {"noballs": 1},
        },
        {
            "batter": "Batter",
            "bowler": "Bowler",
            "runs": {"batter": 0, "extras": 0, "total": 0},
            "wickets": [{"kind": "run out"}],
        },
        {
            "batter": "Batter",
            "bowler": "Bowler",
            "runs": {"batter": 0, "extras": 2, "total": 2},
            "extras": {"byes": 2},
        },
    ]
    match = {
        "info": {
            "dates": ["2020-01-01"],
            "teams": ["A", "B"],
            "venue": "X",
            "outcome": {"winner": "A"},
            "toss": {"winner": "B", "decision": "field"},
        },
        "innings": [
            {"team": "A", "overs": [{"deliveries": deliveries}]},
            {"team": "A", "super_over": True, "overs": [{"deliveries": deliveries}]},
        ],
    }
    result, players, counts = MODULE.aggregate_match(match, "one")
    batter = next(row for row in players if row["player"] == "Batter")
    bowler = next(row for row in players if row["player"] == "Bowler")
    assert batter["runs"] == 4 and batter["balls_faced"] == 3
    assert bowler["legal_balls"] == 2 and bowler["wickets"] == 0
    assert bowler["runs_conceded"] == 6
    assert result["runs"] == 8 and result["extras"] == 4
    assert counts["super_over_innings_excluded"] == 1
