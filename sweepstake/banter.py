"""BanterBot: data-aware dressing-room abuse for the current standings.

Lines are templates over a context built from the live table: who leads and by
how much, who holds the spoon, which clubs are on a losing run, who dropped
this week, who is in the bottom three, who won last season. Each line declares
the context keys it needs and an optional predicate, so only lines that fit
the actual situation are eligible. Everyone gets it, the leader included.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from . import config
from .scoring import generation_results

TOTAL_MATCHWEEKS = 38


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _trailing(form: str, letter: str) -> int:
    count = 0
    for result in reversed(form):
        if result != letter:
            break
        count += 1
    return count


@dataclass(frozen=True)
class Line:
    text: str
    category: str
    needs: tuple[str, ...] = ()
    when: Callable[[Mapping], bool] | None = None

    def fits(self, ctx: Mapping) -> bool:
        if any(key not in ctx for key in self.needs):
            return False
        if self.when is None:
            return True
        try:
            return bool(self.when(ctx))
        except (KeyError, TypeError, ValueError):
            return False


# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #
def build_context(
    ranked: Sequence[Mapping],
    picks: Mapping[str, Iterable[str]],
    teams: Mapping[str, Mapping],
    *,
    matchweek: int = 0,
    previous: Sequence[dict] = (),
    pot: int = 0,
    stake: int = 0,
) -> dict:
    """Everything a line might want to mention.

    ``ranked`` is best-first (see ``scoring.rank_players``); ``teams`` maps a
    club to ``{position, starting_position, form, short, zone}``.
    """
    matchweek = int(matchweek or 0)
    ctx: dict = {
        "matchweek": matchweek,
        "remaining": max(0, TOTAL_MATCHWEEKS - matchweek),
        "pot": pot,
        "stake": stake,
        "n_players": len(ranked),
    }
    if not ranked:
        return ctx

    leader, loser = ranked[0], ranked[-1]
    runner_up = ranked[1] if len(ranked) > 1 else leader
    second_bottom = ranked[-2] if len(ranked) > 1 else loser
    ranks = {row["player"]: int(row["rank"]) for row in ranked}
    ctx.update(
        {
            "leader": leader["player"],
            "leader_pts": int(leader["points"]),
            "leader_tied": bool(leader.get("tied")),
            "runner_up": runner_up["player"],
            "runner_up_pts": int(runner_up["points"]),
            "loser": loser["player"],
            "loser_pts": int(loser["points"]),
            "second_bottom": second_bottom["player"],
            "second_bottom_pts": int(second_bottom["points"]),
            "margin": int(leader["points"]) - int(runner_up["points"]),
            "gap": int(leader["points"]) - int(loser["points"]),
            "loser_gap_to_next": int(second_bottom["points"]) - int(loser["points"]),
            "ranks": ranks,
        }
    )

    owners = {team: player for player, owned in picks.items() for team in owned}
    clubs = []
    for team, owner in owners.items():
        info = teams.get(team) or {}
        position = int(info.get("position") or 0)
        starting = int(info.get("starting_position") or 0)
        form = str(info.get("form") or "")
        clubs.append(
            {
                "name": team,
                "short": info.get("short") or config.short_name(team),
                "owner": owner,
                "pos": position,
                "start": starting,
                "form": form,
                "zone": info.get("zone") or "",
                "losing": _trailing(form, "L"),
                "winning": _trailing(form, "W"),
                "drop": (position - starting) if position and starting else 0,
            }
        )
    placed = [club for club in clubs if club["pos"] >= 1]

    ctx["leader_clubs"] = " and ".join(c["short"] for c in clubs if c["owner"] == ctx["leader"])
    ctx["loser_clubs"] = " and ".join(c["short"] for c in clubs if c["owner"] == ctx["loser"])

    def best(group):
        return min(group, key=lambda c: c["pos"]) if group else None

    def worst(group):
        return max(group, key=lambda c: c["pos"]) if group else None

    def put(prefix: str, club: dict | None) -> None:
        if club:
            ctx[f"{prefix}_club"] = club["short"]
            ctx[f"{prefix}_owner"] = club["owner"]
            ctx[f"{prefix}_pos"] = _ordinal(club["pos"])
            ctx[f"{prefix}_pos_n"] = club["pos"]

    put("leader_best", best([c for c in placed if c["owner"] == ctx["leader"]]))
    put("loser_worst", worst([c for c in placed if c["owner"] == ctx["loser"]]))
    put("best", best(placed))
    put("worst", worst(placed))
    put("rel", worst([c for c in placed if c["zone"] == "rel" or c["pos"] >= 18]))

    streak = max(placed, key=lambda c: c["losing"], default=None)
    if streak and streak["losing"] >= 2:
        put("streak", streak)
        ctx["streak_n"] = streak["losing"]
        ctx["streak_form"] = " ".join(streak["form"][-5:])

    hot = max(placed, key=lambda c: c["winning"], default=None)
    if hot and hot["winning"] >= 2:
        put("hot", hot)
        ctx["hot_n"] = hot["winning"]

    drop = max(placed, key=lambda c: c["drop"], default=None)
    if drop and drop["drop"] >= 2:
        put("drop", drop)
        ctx["drop_n"] = drop["drop"]

    rise = min(placed, key=lambda c: c["drop"], default=None)
    if rise and rise["drop"] <= -2:
        put("rise", rise)
        ctx["rise_n"] = -rise["drop"]

    if previous:
        last = previous[-1]
        results = generation_results(last)
        if results:
            ctx["last_season"] = last.get("season", "last season")
            ctx["champ"] = results[0]["player"]
            ctx["last_spoon"] = results[-1]["player"]
            if ctx["champ"] in ranks:
                ctx["champ_rank"] = ranks[ctx["champ"]]
                ctx["champ_rank_ordinal"] = _ordinal(ranks[ctx["champ"]])
            if ctx["last_spoon"] in ranks:
                ctx["last_spoon_rank"] = ranks[ctx["last_spoon"]]
                ctx["last_spoon_rank_ordinal"] = _ordinal(ranks[ctx["last_spoon"]])
    return ctx


# --------------------------------------------------------------------------- #
# Lines
# --------------------------------------------------------------------------- #
def _started(ctx: Mapping) -> bool:
    return int(ctx.get("matchweek", 0)) > 0 and int(ctx.get("gap", 0)) > 0


LINES: list[Line] = [
    # ---- the spoon ---------------------------------------------------------
    Line("{loser}. {loser_pts} points. {gap} behind {leader}. That's not a gap, that's a different postcode.", "loser", when=_started),
    Line("{loser} drew {loser_clubs} and said 'yeah, go on then'. Should have said no.", "loser", ("loser_clubs",), when=lambda c: bool(c["loser_clubs"])),
    Line("{loser_worst_club} are {loser_worst_pos} and {loser} still checks the table every morning. That's not optimism, that's a condition.", "loser", ("loser_worst_club",), when=lambda c: c["loser_worst_pos_n"] >= 12),
    Line("If {loser}'s two clubs merged they'd still be bottom half. Of the Championship.", "loser", when=_started),
    Line("Somebody put {loser}'s £{stake} on the fire. At least it would warm the room.", "loser", when=lambda c: c["stake"] > 0 and _started(c)),
    Line("{loser} is {loser_gap_to_next} behind {second_bottom}, and {second_bottom} is shite. Let that sink in.", "loser", when=lambda c: c["loser_gap_to_next"] >= 2),
    Line("MW{matchweek} and {loser} is already playing for pride. There is no pride. There is a spoon.", "loser", when=_started),
    Line("It's the hope that kills you, {loser}. Luckily you never had any.", "loser", when=_started),
    Line("Enjoy Millwall away, {loser}. Pack a coat and a personality.", "loser", when=_started),
    Line("{loser} couldn't hit a barn door with a banjo, and now there are {matchweek} matchweeks of evidence.", "loser", when=_started),
    Line("Taxi for {loser}. Actually, cancel it. Let him walk.", "loser", when=_started),
    Line("The spoon's already engraved. {loser} had it done twice to be safe.", "loser", when=_started),
    Line("{loser}'s season is a hostage situation and nobody is paying the ransom.", "loser", when=_started),
    Line("{loser} is gripping the wooden spoon so hard the handle's bent.", "loser", when=_started),
    Line("Bald fraud, beard fraud, whatever {loser} is, the word fraud is in there somewhere.", "loser", when=_started),
    Line("{loser}, your nan rang. She's disappointed as well.", "loser", when=_started),
    Line("Championship scouts have been seen parked outside {loser}'s house.", "loser", when=_started),
    Line("{loser} bottom with {loser_pts}. A dropped bacon sandwich has more points than that.", "loser", when=lambda c: _started(c) and c["loser_pts"] <= 12),
    Line("{rel_club} are {rel_pos} and {loser} owns them. That's not a pick, that's a cry for help.", "loser", ("rel_club",), when=lambda c: c["rel_owner"] == c["loser"]),
    Line("{loser}'s {streak_club} have gone {streak_form}. That's not form, that's a ransom note.", "loser", ("streak_club",), when=lambda c: c["streak_owner"] == c["loser"]),
    # ---- the leader --------------------------------------------------------
    Line("{leader} is {margin} clear and hasn't had to try. The rest of you are furniture.", "leader", when=lambda c: c["margin"] >= 3),
    Line("{leader} top on {leader_pts}, and only because {runner_up} keeps tripping over his own laces.", "leader", when=lambda c: c["margin"] >= 1),
    Line("{leader}: 'I'd like to thank the draw.' Enjoy it. The draw giveth and the draw taketh away.", "leader", when=_started),
    Line("MW{matchweek} form and a pub quiz trophy have the same resale value. Sit down, {leader}.", "leader", when=lambda c: _started(c) and c["matchweek"] <= 12),
    Line("{leader_best_club} are {leader_best_pos} and {leader} is walking round like he scouted them personally.", "leader", ("leader_best_club",), when=lambda c: c["leader_best_pos_n"] <= 6),
    Line("{leader} is cooking. Someone watch the hob, it's usually {leader} who burns the house down by March.", "leader", when=_started),
    Line("Statues for {leader}. Small ones. Easy to take down.", "leader", when=_started),
    Line("{leader} top, {loser} bottom, {gap} points between them. One of them is insufferable and it isn't {loser}.", "leader", when=lambda c: c["gap"] >= 5),
    Line("Champagne on ice for {leader}. Then back in the cupboard, it's matchweek {matchweek}.", "leader", when=lambda c: _started(c) and c["matchweek"] <= 20),
    Line("{leader} has more points than {loser} has had hot dinners, and {loser} eats like a bin.", "leader", when=lambda c: c["gap"] >= 10),
    Line("{leader} and {runner_up} level at the top. Two mugs, one trophy, no plan.", "leader", when=lambda c: c["leader_tied"] and _started(c)),
    Line("{leader} is {margin} clear. {runner_up} says he's 'still in it'. {runner_up} is not still in it.", "leader", when=lambda c: c["margin"] >= 6),
    Line("Fraudiola himself has rung {leader} for tips. That's how bad the rest of you are.", "leader", when=lambda c: c["margin"] >= 4),
    # ---- what's happening on the pitch -------------------------------------
    Line("{streak_club} have lost {streak_n} on the bounce. {streak_owner} has stopped checking the scores. Wise.", "situation", ("streak_club",), when=lambda c: c["streak_n"] >= 2),
    Line("{streak_form}. That's {streak_owner}'s {streak_club}. Read it out loud at his funeral.", "situation", ("streak_club",), when=lambda c: c["streak_n"] >= 3),
    Line("{hot_club} have won {hot_n} in a row and {hot_owner} is unbearable about it. Correctly.", "situation", ("hot_club",), when=lambda c: c["hot_n"] >= 2),
    Line("{drop_club} fell {drop_n} places this week. {drop_owner} felt every single one.", "situation", ("drop_club",), when=lambda c: c["drop_n"] >= 2),
    Line("{rise_club} up {rise_n} this week. {rise_owner} is pretending it was the plan all along.", "situation", ("rise_club",), when=lambda c: c["rise_n"] >= 2),
    Line("{rel_club} are {rel_pos}. {rel_owner} keeps saying 'long season'. It is. That's the problem.", "situation", ("rel_club",)),
    Line("{worst_club} are {worst_pos}. {worst_owner} describes them as 'a project'. So is a landfill.", "situation", ("worst_club",), when=lambda c: c["worst_pos_n"] >= 17),
    Line("{best_club} sitting {best_pos}. {best_owner} didn't earn that, but he'll take it and he'll mention it.", "situation", ("best_club",), when=lambda c: c["best_pos_n"] <= 4),
    Line("Can {loser} do it on a cold rainy night in Stoke? {loser} can't do it on a sunny afternoon in September.", "situation", when=_started),
    # ---- history -----------------------------------------------------------
    Line("{champ} won {last_season} and is currently {champ_rank_ordinal}. Defending champion. Defending nothing.", "history", ("champ_rank",), when=lambda c: c["champ_rank"] > 1 and _started(c)),
    Line("{champ} won it {last_season}, top again now. Someone check the draw for fingerprints.", "history", ("champ_rank",), when=lambda c: c["champ"] == c["leader"] and _started(c)),
    Line("{last_spoon} took the spoon {last_season} and sits {last_spoon_rank_ordinal} now. Growth. Sort of.", "history", ("last_spoon_rank",), when=lambda c: c["last_spoon"] != c["loser"] and _started(c)),
    Line("{last_spoon}: bottom {last_season}, bottom again. Consistency. Awful, awful consistency.", "history", ("last_spoon_rank",), when=lambda c: c["last_spoon"] == c["loser"] and _started(c)),
    Line("Two generations, two different winners. {leader} wants a third name on the trophy. {loser} wants a lift home.", "history", ("champ",), when=_started),
    Line("{champ} won {last_season} and now sits below {loser}. Let that one breathe for a minute.", "history", ("champ_rank",), when=lambda c: c["champ_rank"] >= c["ranks"][c["loser"]] and c["champ"] != c["loser"]),
    # ---- general abuse -----------------------------------------------------
    Line("{n_players} mugs, one spoon. {loser} has already put it in the dishwasher.", "generic", when=_started),
    Line("The pot is £{pot}. {leader} has mentally spent it. {loser} has mentally spent it on a new hobby.", "generic", when=lambda c: c["pot"] > 0 and _started(c)),
    Line("MW{matchweek} of 38. {second_bottom} is one bad weekend from the spoon. Sleep well.", "generic", when=lambda c: _started(c) and c["loser_gap_to_next"] <= 3),
    Line("{remaining} rounds to go. Plenty of time for {leader} to bottle it. History says he will.", "generic", when=lambda c: _started(c) and c["remaining"] >= 10),
    Line("Someone check {runner_up} is still breathing. {leader} keeps pulling away and nobody's said anything.", "generic", when=lambda c: c["margin"] >= 4),
    Line("VAR is checking whether {loser}'s picks were made under duress.", "generic", when=_started),
    Line("Game's gone. Not for {leader}, obviously. For {loser} it went weeks ago.", "generic", when=_started),
    Line("Nothing to separate anyone yet. Give it a fortnight and {loser} will find a way.", "generic", when=lambda c: not _started(c)),
    Line("Pre-season. Everyone's a contender. Enjoy it, {loser}, it's the last time you'll hear that.", "generic", when=lambda c: not _started(c)),
    Line("Six clubs each side of the table and a pot of £{pot}. Nobody's talking to {loser} already.", "generic", when=lambda c: c["pot"] > 0 and _started(c)),
    # ---- the classics, sharpened -------------------------------------------
    Line("Whichever team scores more goals usually wins. Michael Owen. Still smarter than {loser}'s picks.", "classic", when=_started),
    Line("Unbelievable, Jeff. {loser} has done it again.", "classic", when=_started),
    Line("I threw an apple core in the bin from distance. It went in. That's still more than {loser} has managed this season.", "classic", when=_started),
    Line("{leader}, Ballon d'Or! Ballon d'Or! Ballon d'Or!", "classic", when=_started),
    Line("Prawn sandwich brigade out in force. {leader} brought the prawns.", "classic", when=_started),
    Line("Sometimes maybe good, sometimes maybe shit. Mostly the second one, {loser}.", "classic", when=_started),
    Line("Chat shit, get banged. {loser} chatted. {loser} got banged.", "classic", when=_started),
    Line("Meat pie, sausage roll, come on {loser}, give us a goal. Any goal. One.", "classic", when=_started),
    Line("No era penal. Was, though, {loser}.", "classic", when=_started),
]

CATEGORY_WEIGHTS = {
    "loser": 4,
    "leader": 3,
    "situation": 4,
    "history": 2,
    "generic": 2,
    "classic": 1,
}


def eligible(ctx: Mapping) -> list[Line]:
    return [line for line in LINES if line.fits(ctx)]


def pick_line(ctx: Mapping, rng: random.Random | None = None, avoid: Iterable[str] = ()) -> Line | None:
    """Choose a line that fits ``ctx``; ``avoid`` holds recently used templates."""
    rng = rng or random
    lines = eligible(ctx)
    if not lines:
        return None
    avoided = set(avoid)
    fresh = [line for line in lines if line.text not in avoided] or lines
    by_category: dict[str, list[Line]] = {}
    for line in fresh:
        by_category.setdefault(line.category, []).append(line)
    categories = list(by_category)
    weights = [CATEGORY_WEIGHTS.get(category, 1) for category in categories]
    category = rng.choices(categories, weights=weights, k=1)[0]
    return rng.choice(by_category[category])


def render(line: Line, ctx: Mapping) -> str:
    try:
        return line.text.format(**ctx)
    except (KeyError, IndexError):
        return "BanterBot has been sent to VAR. Back in a minute."


def get_banter(ctx: Mapping, rng: random.Random | None = None, avoid: Iterable[str] = ()) -> str:
    if not ctx or not ctx.get("leader"):
        return "No table, no banter. Even BanterBot needs something to work with."
    line = pick_line(ctx, rng, avoid)
    if line is None:
        return "BanterBot is speechless. It won't last."
    return render(line, ctx)
