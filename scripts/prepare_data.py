"""Transform licensed Cricsheet JSON into bounded, browser-ready IPL aggregates."""

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://cricsheet.org/downloads/ipl_json.zip"
NON_BOWLER_WICKETS = {"run out", "retired hurt", "obstructing the field", "retired out"}


def aggregate_match(match: dict, match_id: str) -> tuple[dict, list[dict], dict]:
    """Count regulation deliveries, separating batting, bowling and team extras."""
    info = match["info"]
    season = date.fromisoformat(info["dates"][0]).year
    teams = info["teams"]
    if len(teams) != 2:
        raise ValueError("Expected exactly two teams")
    registry = info.get("registry", {}).get("people", {})
    stats = {}

    def player(name, team):
        key = (name, team)
        if key not in stats:
            stats[key] = {
                "match_id": match_id,
                "season": season,
                "team": team,
                "player": name,
                "player_id": registry.get(name, "name:" + name),
                "runs": 0,
                "balls_faced": 0,
                "wickets": 0,
                "legal_balls": 0,
                "runs_conceded": 0,
            }
        return stats[key]

    for team, names in info.get("players", {}).items():
        for name in names:
            player(name, team)
    runs = 0
    extras_total = 0
    deliveries = 0
    excluded = 0
    for innings in match["innings"]:
        if innings.get("super_over", False):
            excluded += 1
            continue
        batting = innings["team"]
        bowling = next(team for team in teams if team != batting)
        for over in innings["overs"]:
            for delivery in over["deliveries"]:
                deliveries += 1
                extras = delivery.get("extras", {})
                batter = player(delivery["batter"], batting)
                bowler = player(delivery["bowler"], bowling)
                batter["runs"] += delivery["runs"]["batter"]
                batter["balls_faced"] += int(not extras.get("wides", 0))
                bowler["legal_balls"] += int(
                    not extras.get("wides", 0) and not extras.get("noballs", 0)
                )
                bowler["runs_conceded"] += (
                    delivery["runs"]["total"]
                    - extras.get("byes", 0)
                    - extras.get("legbyes", 0)
                    - extras.get("penalty", 0)
                )
                bowler["wickets"] += sum(
                    wicket["kind"] not in NON_BOWLER_WICKETS
                    for wicket in delivery.get("wickets", [])
                )
                runs += delivery["runs"]["total"]
                extras_total += delivery["runs"]["extras"]
    outcome = info["outcome"]
    winner = (
        outcome.get("winner") or outcome.get("eliminator") or outcome.get("bowl_out")
    )
    result = {
        "id": match_id,
        "season": season,
        "date": info["dates"][0],
        "teams": teams,
        "venue": info["venue"],
        "winner": winner,
        "toss_winner": info["toss"]["winner"],
        "toss_decision": info["toss"]["decision"],
        "runs": runs,
        "extras": extras_total,
    }
    if sum(row["runs"] for row in stats.values()) + extras_total != runs:
        raise ValueError("Batting runs plus extras do not reconcile with team totals")
    return (
        result,
        list(stats.values()),
        {"deliveries": deliveries, "super_over_innings_excluded": excluded},
    )


def prepare(archive: Path) -> None:
    """Read the archive without extracting untrusted paths; preserve source notices."""
    matches, players = [], []
    totals = defaultdict(int)
    versions = set()
    notices = ROOT / "data/source-notices"
    notices.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for filename in ["README.txt", "LICENSE.txt"]:
            content = source.read(filename)
            (notices / filename).write_bytes(content)
            public_name = (
                "data-license.txt" if filename == "LICENSE.txt" else "source-readme.txt"
            )
            (ROOT / "site" / public_name).write_bytes(content)
        names = [name for name in source.namelist() if name.endswith(".json")]
        for name in names:
            match = json.loads(source.read(name))
            year = date.fromisoformat(match["info"]["dates"][0]).year
            if not 2008 <= year <= 2020:
                continue
            result, stats, counts = aggregate_match(match, Path(name).stem)
            matches.append(result)
            players.extend(stats)
            versions.add(match["meta"]["data_version"])
            for key, value in counts.items():
                totals[key] += value
    matches.sort(key=lambda row: (row["date"], row["id"]))
    manifest = {
        "source": SOURCE,
        "source_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "license": "Open Data Commons Attribution License 1.0 (ODC-By)",
        "attribution": (
            "Data from Cricsheet, transformed and aggregated by " "Subhash Dixit."
        ),
        "scope": (
            "Available IPL matches with calendar years 2008 through "
            "2020; regulation innings statistics"
        ),
        "archive_json_files": len(names),
        "selected_matches": len(matches),
        "data_versions": sorted(versions),
        "first_date": matches[0]["date"],
        "last_date": matches[-1]["date"],
        **totals,
    }
    payload = {"manifest": manifest, "matches": matches, "players": players}
    (ROOT / "site/data.json").write_text(
        json.dumps(payload, separators=(",", ":")) + "\n"
    )
    (ROOT / "data/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--download",
        action="store_true",
        help="Fetch the current original Cricsheet archive first",
    )
    args = parser.parse_args()
    if args.download:
        urlretrieve(SOURCE, args.archive)
    prepare(args.archive)
