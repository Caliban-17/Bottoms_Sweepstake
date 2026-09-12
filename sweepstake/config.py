"""Static configuration: season, roster, crests and previous generations."""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Current generation
# --------------------------------------------------------------------------- #
GENERATION = 3
SEASON_LABEL = "2026/27"
STAKE_GBP = 5

TEAMS_PER_PLAYER = 2
LEAGUE_SIZE = 20
MAX_TEAM_POINTS = LEAGUE_SIZE  # finishing 1st is worth 20 points
MAX_PLAYER_POINTS = MAX_TEAM_POINTS * TEAMS_PER_PLAYER  # 40

# Gen 3 roster. Team names must match the "long" names used by premierleague.com
# so they merge cleanly with the live table. Dict order is the tie-break order.
PLAYER_PICKS: dict[str, tuple[str, ...]] = {
    "Sean": ("Hull City", "Chelsea"),
    "Vosey": ("Tottenham Hotspur", "Ipswich Town"),
    "Dom": ("Newcastle United", "Coventry City"),
    "Adam": ("Brentford", "Everton"),
    "Sam": ("Leeds United", "Fulham"),
    "Wilson": ("Crystal Palace", "Nottingham Forest"),
}


def players() -> list[str]:
    """Players in roster order."""
    return list(PLAYER_PICKS)


def picked_teams() -> list[str]:
    """Every team owned by a player, in roster order."""
    return [team for teams in PLAYER_PICKS.values() for team in teams]


def team_owner() -> dict[str, str]:
    """Map team -> owning player."""
    return {team: player for player, teams in PLAYER_PICKS.items() for team in teams}


def jackpot_gbp(n_players: int | None = None) -> int:
    """Total pot: every player stakes STAKE_GBP."""
    n = len(PLAYER_PICKS) if n_players is None else n_players
    return n * STAKE_GBP


# --------------------------------------------------------------------------- #
# Crests
# --------------------------------------------------------------------------- #
# premierleague.com serves crests keyed by the club's Opta id ("t8" == Chelsea).
# The live API reports the Opta id for every club (team.altIds.opta) and that is
# always preferred; this map only backs the offline fallback snapshot.
OPTA_ID_MAP: dict[str, str] = {
    "Arsenal": "t3",
    "Aston Villa": "t7",
    "Bournemouth": "t91",
    "Brentford": "t94",
    "Brighton & Hove Albion": "t36",
    "Brighton and Hove Albion": "t36",
    "Burnley": "t90",
    "Chelsea": "t8",
    "Coventry City": "t9",
    "Crystal Palace": "t31",
    "Everton": "t11",
    "Fulham": "t54",
    "Hull City": "t88",
    "Ipswich Town": "t40",
    "Leeds United": "t2",
    "Leicester City": "t13",
    "Liverpool": "t14",
    "Luton Town": "t102",
    "Manchester City": "t43",
    "Manchester United": "t1",
    "Middlesbrough": "t25",
    "Newcastle United": "t4",
    "Norwich City": "t45",
    "Nottingham Forest": "t17",
    "Sheffield United": "t49",
    "Southampton": "t20",
    "Sunderland": "t56",
    "Tottenham Hotspur": "t6",
    "Watford": "t57",
    "West Bromwich Albion": "t35",
    "West Ham United": "t21",
    "Wolverhampton Wanderers": "t39",
}

TEAM_SHORT_NAMES: dict[str, str] = {
    "Aston Villa": "Villa",
    "Brighton & Hove Albion": "Brighton",
    "Brighton and Hove Albion": "Brighton",
    "Coventry City": "Coventry",
    "Crystal Palace": "Palace",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Leicester City": "Leicester",
    "Luton Town": "Luton",
    "Manchester City": "Man City",
    "Manchester United": "Man Utd",
    "Newcastle United": "Newcastle",
    "Norwich City": "Norwich",
    "Nottingham Forest": "Forest",
    "Sheffield United": "Sheff Utd",
    "Tottenham Hotspur": "Spurs",
    "West Bromwich Albion": "West Brom",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
}


def short_name(team: str) -> str:
    return TEAM_SHORT_NAMES.get(team, team)


def crest_url(opta_id: str | None, size: int = 70, retina: bool = True) -> str | None:
    """Crest image URL for an Opta id such as ``t8``. Returns None when unknown."""
    if not opta_id or opta_id == "t0":
        return None
    suffix = "@x2" if retina else ""
    return f"https://resources.premierleague.com/premierleague/badges/{size}/{opta_id}{suffix}.png"


# --------------------------------------------------------------------------- #
# Hall of Fame
# --------------------------------------------------------------------------- #
# Final positions come from the premierleague.com tables for each season; the
# picks come from this repo's history for each generation.
PREVIOUS_GENERATIONS: list[dict] = [
    {
        "generation": 1,
        "season": "2024/25",
        "stake_gbp": 5,
        "picks": {
            "Sean": (("Fulham", 11), ("Everton", 13)),
            "Dom": (("Bournemouth", 9), ("Ipswich Town", 19)),
            "Harry": (("Nottingham Forest", 7), ("Wolverhampton Wanderers", 16)),
            "Chris": (("Brentford", 10), ("Leicester City", 18)),
            "Adam": (("Brighton & Hove Albion", 8), ("Southampton", 20)),
        },
    },
    {
        "generation": 2,
        "season": "2025/26",
        "stake_gbp": 5,
        "picks": {
            "Vosey": (("Bournemouth", 6), ("Leeds United", 14)),
            "Dom": (("Brentford", 9), ("Sunderland", 7)),
            "Chris": (("Wolverhampton Wanderers", 20), ("Fulham", 11)),
            "Sam": (("Burnley", 19), ("Tottenham Hotspur", 17)),
            "Adam": (("West Ham United", 18), ("Manchester United", 3)),
            "Sean": (("Everton", 13), ("Crystal Palace", 15)),
        },
    },
]
