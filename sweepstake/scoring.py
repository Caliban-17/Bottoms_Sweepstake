"""Pure scoring and ranking helpers (no Streamlit, no network)."""

from __future__ import annotations

from typing import Iterable, Mapping

from . import config


def points_for_position(position) -> int:
    """Sweepstake value of a league position: 1st = 20 ... 20th = 1.

    Anything that is not a valid 1..20 position (pre-season ``0``, ``None``,
    NaN, a missing team) is worth 0.
    """
    try:
        pos = int(position)
    except (TypeError, ValueError):
        return 0
    if pos < 1 or pos > config.LEAGUE_SIZE:
        return 0
    return config.LEAGUE_SIZE + 1 - pos


def player_points(
    picks: Mapping[str, Iterable[str]], positions: Mapping[str, int]
) -> dict[str, int]:
    """Total sweepstake points per player for the given team positions."""
    return {
        player: sum(points_for_position(positions.get(team)) for team in teams)
        for player, teams in picks.items()
    }


def rank_players(
    totals: Mapping[str, int], order: Iterable[str] | None = None
) -> list[dict]:
    """Rank players by points (desc). Ties share a rank ("1=" style).

    ``order`` is the tie-break display order (defaults to roster order).
    Returns ``[{"player", "points", "rank", "tied"}, ...]`` sorted best-first.
    """
    order_list = list(order) if order is not None else list(totals)
    order_index = {p: i for i, p in enumerate(order_list)}
    players_sorted = sorted(
        totals, key=lambda p: (-int(totals[p]), order_index.get(p, len(order_index)))
    )
    ranked: list[dict] = []
    for i, player in enumerate(players_sorted):
        pts = int(totals[player])
        rank = 1 + sum(1 for other in totals if int(totals[other]) > pts)
        tied = sum(1 for other in totals if int(totals[other]) == pts) > 1
        ranked.append({"player": player, "points": pts, "rank": rank, "tied": tied})
    return ranked


def leaders(ranked: list[dict]) -> list[str]:
    return [r["player"] for r in ranked if r["rank"] == 1]


def wooden_spoons(ranked: list[dict]) -> list[str]:
    if not ranked:
        return []
    worst = max(r["rank"] for r in ranked)
    return [r["player"] for r in ranked if r["rank"] == worst]


def generation_results(generation: dict) -> list[dict]:
    """Final standings for a past generation (see ``config.PREVIOUS_GENERATIONS``)."""
    picks = generation["picks"]
    totals = {
        player: sum(points_for_position(pos) for _, pos in teams)
        for player, teams in picks.items()
    }
    ranked = rank_players(totals, order=list(picks))
    for row in ranked:
        row["teams"] = [
            (team, pos, points_for_position(pos)) for team, pos in picks[row["player"]]
        ]
    return ranked
