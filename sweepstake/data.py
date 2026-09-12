"""Pulse Live (premierleague.com) API client, payload parsing and fallback data.

Everything here is plain Python: no Streamlit. The app wraps ``get_standings``
in ``st.cache_data`` so the network is hit at most once per cache window.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from . import config
from .scoring import points_for_position

API_BASE = "https://footballapi.pulselive.com/football"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/tables",
}
TIMEOUT_SECONDS = 10

TABLE_COLUMNS = [
    "Position",
    "StartingPosition",
    "Team",
    "ShortName",
    "Opta_ID",
    "Crest_URL",
    "Played",
    "Won",
    "Drawn",
    "Lost",
    "GF",
    "GA",
    "GD",
    "Points_League",
    "Form",
    "Next",
    "Zone",
    "Points_Value",
]

# Offline snapshot of the 2026/27 table after matchweek 3, used only when the
# data service cannot be reached. (position, team, opta, P, W, D, L, GD, Pts)
FALLBACK_SNAPSHOT_DATE = "12 Sep 2026"
FALLBACK_SNAPSHOT_LABEL = "2026/27"
_FALLBACK_ROWS = [
    (1, "Manchester City", "t43", 3, 3, 0, 0, 5, 9),
    (2, "Arsenal", "t3", 3, 3, 0, 0, 5, 9),
    (3, "Hull City", "t88", 3, 2, 1, 0, 3, 7),
    (4, "Chelsea", "t8", 3, 2, 0, 1, 1, 6),
    (5, "Brentford", "t94", 3, 1, 2, 0, 3, 5),
    (6, "Liverpool", "t14", 3, 1, 2, 0, 2, 5),
    (7, "Newcastle United", "t4", 3, 1, 2, 0, 2, 5),
    (8, "Everton", "t11", 3, 1, 2, 0, 2, 5),
    (9, "Leeds United", "t2", 3, 1, 2, 0, 1, 5),
    (10, "Brighton & Hove Albion", "t36", 3, 1, 1, 1, 3, 4),
    (11, "Manchester United", "t1", 3, 1, 1, 1, 1, 4),
    (12, "Sunderland", "t56", 3, 1, 1, 1, 0, 4),
    (13, "Crystal Palace", "t31", 3, 1, 0, 2, -4, 3),
    (14, "Ipswich Town", "t40", 3, 1, 0, 2, -4, 3),
    (15, "Bournemouth", "t91", 3, 0, 2, 1, -1, 2),
    (16, "Nottingham Forest", "t17", 3, 0, 2, 1, -1, 2),
    (17, "Aston Villa", "t7", 3, 0, 1, 2, -5, 1),
    (18, "Tottenham Hotspur", "t6", 3, 0, 1, 2, -5, 1),
    (19, "Fulham", "t54", 3, 0, 0, 3, -3, 0),
    (20, "Coventry City", "t9", 3, 0, 0, 3, -5, 0),
]


@dataclass
class StandingsResult:
    """A league table plus where it came from."""

    table: pd.DataFrame
    source: str  # "live" | "preseason" | "fallback"
    message: str = ""
    comp_season_id: int | None = None
    comp_season_label: str | None = None
    fetched_at: datetime = field(default_factory=datetime.now)

    @property
    def is_live(self) -> bool:
        return self.source == "live"

    @property
    def matchweek(self) -> int:
        if self.table is None or self.table.empty or "Played" not in self.table:
            return 0
        played = pd.to_numeric(self.table["Played"], errors="coerce").fillna(0)
        return int(played.max())


# --------------------------------------------------------------------------- #
# Season label helpers
# --------------------------------------------------------------------------- #
_SEASON_RE = re.compile(r"(\d{4})\s*[/\-–]\s*(\d{2,4})")


def parse_season_years(label: Any) -> tuple[int, int] | None:
    """'2026/27' -> (2026, 2027); 'English Premier League Season 2026/2027' -> (2026, 2027)."""
    match = _SEASON_RE.search(str(label or ""))
    if not match:
        return None
    start = int(match.group(1))
    end_raw = match.group(2)
    end = int(end_raw) if len(end_raw) == 4 else (start // 100) * 100 + int(end_raw)
    if end < start:  # e.g. 1999/00
        end += 100
    return start, end


def season_matches(api_label: Any, requested_label: Any) -> bool:
    """True when two season labels describe the same season, whatever their format."""
    parsed = parse_season_years(api_label)
    return parsed is not None and parsed == parse_season_years(requested_label)


def season_start_year_from_label(label: Any) -> int | None:
    years = parse_season_years(label)
    return years[0] if years else None


def _normalize_comp_id(value: Any) -> Any:
    """Coerce ints, floats (777.0) and numeric strings ('777.0') to int.

    Returns the original value if it cannot be interpreted as a number.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    try:
        return int(round(float(str(value).strip())))
    except (TypeError, ValueError):
        return value


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def _get_json(url: str) -> Any | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            return None
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def list_comp_seasons() -> list[dict]:
    """All Premier League competition seasons known to the data service."""
    sources = [
        f"{API_BASE}/competitions/1/compseasons?page=0&pageSize=120",
        f"{API_BASE}/compseasons?comps=1&page=0&pageSize=120",
        f"{API_BASE}/competitions/1/compseasons",
    ]
    seasons: dict[Any, dict] = {}
    for url in sources:
        payload = _get_json(url)
        if not payload:
            continue
        if isinstance(payload, dict):
            items = payload.get("content") or payload.get("compSeasons") or payload.get("seasons") or []
        else:
            items = payload
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            sid = _normalize_comp_id(item.get("id"))
            if sid is None:
                continue
            seasons.setdefault(sid, {"id": sid, "label": item.get("label")})
        if seasons:
            break
    return list(seasons.values())


def resolve_comp_season(seasons: list[dict], requested_label: str) -> tuple[int | None, str | None]:
    """Pick the compSeason id for ``requested_label``.

    Prefers an exact season match; otherwise the most recent season on record.
    """
    for season in seasons:
        if season_matches(season.get("label"), requested_label):
            return _normalize_comp_id(season.get("id")), season.get("label")
    dated = [(parse_season_years(s.get("label")), s) for s in seasons]
    dated = [(years, s) for years, s in dated if years]
    if dated:
        _, latest = max(dated, key=lambda pair: pair[0])
        return _normalize_comp_id(latest.get("id")), latest.get("label")
    return None, None


# --------------------------------------------------------------------------- #
# Payload parsing
# --------------------------------------------------------------------------- #
def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _team_result(team_name: str, match: dict) -> str | None:
    """W / D / L from ``team_name``'s point of view, or None if not involved."""
    teams = match.get("teams") or []
    if len(teams) != 2:
        return None
    home, away = teams
    home_name = (home.get("team") or {}).get("name")
    away_name = (away.get("team") or {}).get("name")
    home_score, away_score = home.get("score"), away.get("score")
    if home_score is None or away_score is None:
        return None
    if team_name == home_name:
        mine, theirs = home_score, away_score
    elif team_name == away_name:
        mine, theirs = away_score, home_score
    else:
        return None
    if mine > theirs:
        return "W"
    if mine < theirs:
        return "L"
    return "D"


def form_string(team_name: str, form_matches: Any, last_n: int = 5) -> str:
    """Recent results oldest -> newest, e.g. ``'WWDLW'``."""
    matches = [m for m in (form_matches or []) if isinstance(m, dict)]
    matches.sort(
        key=lambda m: (
            _as_int((m.get("gameweek") or {}).get("gameweek")),
            _as_int((m.get("kickoff") or {}).get("millis")),
        )
    )
    results = [r for r in (_team_result(team_name, m) for m in matches) if r]
    return "".join(results[-last_n:])


_KICKOFF_RE = re.compile(r"^(\w{3} \d{1,2} \w{3}) \d{4}, (\d{2}:\d{2})")


def next_fixture_label(team_name: str, next_match: Any) -> str:
    """Compact label such as ``'Newcastle (A) · Sat 19 Sep, 15:00'``."""
    if not isinstance(next_match, dict):
        return ""
    teams = next_match.get("teams") or []
    if len(teams) != 2:
        return ""
    home = teams[0].get("team") or {}
    away = teams[1].get("team") or {}
    if home.get("name") == team_name:
        opponent, venue = away, "H"
    elif away.get("name") == team_name:
        opponent, venue = home, "A"
    else:
        return ""
    opponent_name = opponent.get("shortName") or config.short_name(opponent.get("name", ""))
    kickoff = (next_match.get("kickoff") or {}).get("label") or ""
    match = _KICKOFF_RE.match(kickoff)
    when = f"{match.group(1)}, {match.group(2)}" if match else kickoff
    label = f"{opponent_name} ({venue})"
    return f"{label} · {when}" if when else label


_ZONE_BY_DESTINATION = {"EU_CL": "cl", "EU_EL": "el", "EU_ECL": "ecl"}


def zone_from_annotations(annotations: Any) -> str:
    """'cl' / 'el' / 'ecl' / 'rel' / '' from the API's table annotations."""
    for annotation in annotations or []:
        if not isinstance(annotation, dict):
            continue
        if annotation.get("type") == "R":
            return "rel"
        zone = _ZONE_BY_DESTINATION.get(annotation.get("destination"))
        if zone:
            return zone
    return ""


def parse_standings_payload(payload: Any) -> pd.DataFrame:
    """Turn a ``/standings`` payload into a table (see ``TABLE_COLUMNS``)."""
    tables = (payload or {}).get("tables") or (payload or {}).get("standings") or []
    table = None
    for candidate in tables:
        table_type = str(candidate.get("type") or "").upper()
        if table_type in ("TOTAL", "LEAGUE"):
            table = candidate
            break
    if table is None and tables:
        table = tables[0]

    rows: list[dict] = []
    for entry in (table or {}).get("entries") or []:
        team = entry.get("team") or {}
        club = team.get("club") or {}
        name = team.get("name") or club.get("name")
        position = entry.get("position", entry.get("rank"))
        if not name or position is None:
            continue
        position = _as_int(position, default=-1)
        if position < 0:
            continue
        name = str(name).strip()
        opta = (
            (team.get("altIds") or {}).get("opta")
            or (club.get("altIds") or {}).get("opta")
            or config.OPTA_ID_MAP.get(name)
        )
        overall = entry.get("overall") or {}
        starting = _as_int(entry.get("startingPosition"))
        rows.append(
            {
                "Position": position,
                "StartingPosition": starting if starting >= 1 else position,
                "Team": name,
                "ShortName": team.get("shortName") or config.short_name(name),
                "Opta_ID": opta or "t0",
                "Crest_URL": config.crest_url(opta),
                "Played": _as_int(overall.get("played")),
                "Won": _as_int(overall.get("won")),
                "Drawn": _as_int(overall.get("drawn")),
                "Lost": _as_int(overall.get("lost")),
                "GF": _as_int(overall.get("goalsFor")),
                "GA": _as_int(overall.get("goalsAgainst")),
                "GD": _as_int(overall.get("goalsDifference")),
                "Points_League": _as_int(overall.get("points", entry.get("points"))),
                "Form": form_string(name, entry.get("form")),
                "Next": next_fixture_label(name, entry.get("next")),
                "Zone": zone_from_annotations(entry.get("annotations")),
            }
        )

    df = pd.DataFrame(rows, columns=TABLE_COLUMNS[:-1])
    df = df.sort_values("Position").reset_index(drop=True)
    df["Points_Value"] = df["Position"].apply(points_for_position)
    return df


def fetch_comp_season_teams(comp_id: int) -> list[str]:
    """Team names registered to a compSeason (used pre-season when the table is empty)."""
    sources = [
        f"{API_BASE}/competitions/1/compseasons/{comp_id}/teams",
        f"{API_BASE}/teams?comps=1&compSeasons={comp_id}&pageSize=40",
    ]
    names: set[str] = set()
    for url in sources:
        payload = _get_json(url)
        if not payload:
            continue
        if isinstance(payload, dict):
            items = payload.get("teams") or payload.get("clubs") or payload.get("content") or []
        else:
            items = payload
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            name = (
                item.get("name")
                or (item.get("team") or {}).get("name")
                or (item.get("club") or {}).get("name")
            )
            if name:
                names.add(str(name).strip())
        if names:
            break
    return sorted(names)


def preseason_table(team_names: list[str]) -> pd.DataFrame:
    rows = [
        {
            "Position": 0,
            "StartingPosition": 0,
            "Team": name,
            "ShortName": config.short_name(name),
            "Opta_ID": config.OPTA_ID_MAP.get(name, "t0"),
            "Crest_URL": config.crest_url(config.OPTA_ID_MAP.get(name)),
            "Played": 0,
            "Won": 0,
            "Drawn": 0,
            "Lost": 0,
            "GF": 0,
            "GA": 0,
            "GD": 0,
            "Points_League": 0,
            "Form": "",
            "Next": "",
            "Zone": "",
            "Points_Value": 0,
        }
        for name in team_names
    ]
    return pd.DataFrame(rows, columns=TABLE_COLUMNS)


def fallback_standings() -> pd.DataFrame:
    rows = [
        {
            "Position": pos,
            "StartingPosition": pos,
            "Team": team,
            "ShortName": config.short_name(team),
            "Opta_ID": opta,
            "Crest_URL": config.crest_url(opta),
            "Played": played,
            "Won": won,
            "Drawn": drawn,
            "Lost": lost,
            "GF": 0,
            "GA": 0,
            "GD": gd,
            "Points_League": pts,
            "Form": "",
            "Next": "",
            "Zone": "rel" if pos >= 18 else "",
            "Points_Value": points_for_position(pos),
        }
        for pos, team, opta, played, won, drawn, lost, gd, pts in _FALLBACK_ROWS
    ]
    return pd.DataFrame(rows, columns=TABLE_COLUMNS)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def get_standings(requested_label: str = config.SEASON_LABEL) -> StandingsResult:
    """Fetch the live table for ``requested_label``; fall back to the snapshot."""
    fetched_at = datetime.now()
    snapshot_note = (
        f"Showing the offline snapshot of the {FALLBACK_SNAPSHOT_LABEL} table "
        f"from {FALLBACK_SNAPSHOT_DATE}."
    )

    def fallback(reason: str) -> StandingsResult:
        return StandingsResult(
            fallback_standings(), "fallback", f"{reason} {snapshot_note}", fetched_at=fetched_at
        )

    seasons = list_comp_seasons()
    if not seasons:
        return fallback("Could not reach the Premier League data service.")

    comp_id, comp_label = resolve_comp_season(seasons, requested_label)
    if comp_id is None:
        return fallback(f"No competition season matched {requested_label}.")

    payload = _get_json(f"{API_BASE}/standings?compSeasons={comp_id}&altIds=true&detail=2")
    if not payload:
        return fallback(f"The standings request for {comp_label} failed.")

    table = parse_standings_payload(payload)
    if table.empty:
        team_names = fetch_comp_season_teams(comp_id)
        if team_names:
            return StandingsResult(
                preseason_table(team_names),
                "preseason",
                f"{comp_label} hasn't kicked off yet. The table fills in once matches are played.",
                comp_id,
                comp_label,
                fetched_at,
            )
        return fallback(f"The {comp_label} table is empty.")

    message = ""
    if not season_matches(comp_label, requested_label):
        message = f"{requested_label} isn't on the data service yet, so this is the {comp_label} table."
    return StandingsResult(table, "live", message, comp_id, comp_label, fetched_at)
