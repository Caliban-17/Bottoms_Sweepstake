import json
import os
import random
import sys
import unittest

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sweepstake import banter, config, data, scoring, ui  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_gen3_roster(self):
        self.assertEqual(config.GENERATION, 3)
        self.assertEqual(config.SEASON_LABEL, "2026/27")
        self.assertEqual(
            config.players(), ["Sean", "Vosey", "Dom", "Adam", "Sam", "Wilson"]
        )
        self.assertNotIn("Chris", config.players())
        for teams in config.PLAYER_PICKS.values():
            self.assertEqual(len(teams), config.TEAMS_PER_PLAYER)

    def test_picked_teams_are_unique_and_have_crests(self):
        teams = config.picked_teams()
        self.assertEqual(len(teams), 12)
        self.assertEqual(len(set(teams)), 12)
        for team in teams:
            self.assertIn(team, config.OPTA_ID_MAP, team)
            self.assertTrue(config.crest_url(config.OPTA_ID_MAP[team]).endswith("@x2.png"))

    def test_promoted_club_crests(self):
        self.assertEqual(config.OPTA_ID_MAP["Hull City"], "t88")
        self.assertEqual(config.OPTA_ID_MAP["Coventry City"], "t9")
        self.assertEqual(config.OPTA_ID_MAP["Ipswich Town"], "t40")
        self.assertNotEqual(config.OPTA_ID_MAP["Ipswich Town"], config.OPTA_ID_MAP["Chelsea"])

    def test_team_owner_and_jackpot(self):
        owners = config.team_owner()
        self.assertEqual(owners["Coventry City"], "Dom")
        self.assertEqual(owners["Nottingham Forest"], "Wilson")
        self.assertEqual(config.jackpot_gbp(), 30)
        self.assertEqual(config.jackpot_gbp(5), 25)

    def test_crest_url(self):
        self.assertIsNone(config.crest_url(None))
        self.assertIsNone(config.crest_url("t0"))
        self.assertEqual(
            config.crest_url("t8", retina=False),
            "https://resources.premierleague.com/premierleague/badges/70/t8.png",
        )


class TestScoring(unittest.TestCase):
    def test_points_for_position(self):
        self.assertEqual(scoring.points_for_position(1), 20)
        self.assertEqual(scoring.points_for_position(20), 1)
        self.assertEqual(scoring.points_for_position(10), 11)
        for bad in (0, 21, None, "n/a", float("nan")):
            self.assertEqual(scoring.points_for_position(bad), 0, bad)

    def test_player_points(self):
        picks = {"A": ("X", "Y"), "B": ("Z", "Missing")}
        positions = {"X": 1, "Y": 20, "Z": 5}
        self.assertEqual(scoring.player_points(picks, positions), {"A": 21, "B": 16})

    def test_rank_players_with_ties(self):
        ranked = scoring.rank_players({"A": 10, "B": 12, "C": 10, "D": 3}, order=["A", "B", "C", "D"])
        self.assertEqual([r["player"] for r in ranked], ["B", "A", "C", "D"])
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 2, 4])
        self.assertEqual([r["tied"] for r in ranked], [False, True, True, False])
        self.assertEqual(scoring.leaders(ranked), ["B"])
        self.assertEqual(scoring.wooden_spoons(ranked), ["D"])

    def test_all_level_preseason(self):
        ranked = scoring.rank_players({"A": 0, "B": 0}, order=["A", "B"])
        self.assertEqual(scoring.leaders(ranked), ["A", "B"])
        self.assertEqual(scoring.wooden_spoons(ranked), ["A", "B"])

    def test_hall_of_fame_results(self):
        gen1, gen2 = config.PREVIOUS_GENERATIONS
        results1 = scoring.generation_results(gen1)
        self.assertEqual(results1[0]["player"], "Vosey")
        self.assertEqual(results1[0]["points"], 19)
        self.assertEqual(results1[1]["player"], "Sean")
        self.assertEqual(results1[1]["points"], 18)
        self.assertEqual({r["player"] for r in results1 if r["rank"] == 3}, {"Dom", "Chris", "Adam"})

        results2 = scoring.generation_results(gen2)
        self.assertEqual(results2[0]["player"], "Dom")
        self.assertEqual(results2[0]["points"], 26)
        self.assertEqual(results2[-1]["player"], "Sam")
        self.assertEqual(results2[-1]["points"], 6)
        self.assertEqual(results2[0]["teams"][0], ("Brentford", 9, 12))


class TestSeasonHelpers(unittest.TestCase):
    def test_parse_season_years(self):
        self.assertEqual(data.parse_season_years("2025/26"), (2025, 2026))
        self.assertEqual(
            data.parse_season_years("English Premier League Season 2026/2027"), (2026, 2027)
        )
        self.assertEqual(data.parse_season_years("1999/00"), (1999, 2000))
        self.assertIsNone(data.parse_season_years("random_string"))
        self.assertIsNone(data.parse_season_years(None))

    def test_season_matches_across_label_formats(self):
        self.assertTrue(data.season_matches("English Premier League Season 2026/2027", "2026/27"))
        self.assertTrue(data.season_matches("2025/26", "2025/26"))
        self.assertFalse(data.season_matches("2025/26", "2026/27"))
        self.assertFalse(data.season_matches(None, "2026/27"))

    def test_season_start_year(self):
        self.assertEqual(data.season_start_year_from_label("2025/26"), 2025)
        self.assertIsNone(data.season_start_year_from_label("nope"))

    def test_normalize_comp_id(self):
        self.assertEqual(data._normalize_comp_id(123), 123)
        self.assertEqual(data._normalize_comp_id(123.0), 123)
        self.assertEqual(data._normalize_comp_id("123"), 123)
        self.assertEqual(data._normalize_comp_id("123.0"), 123)
        self.assertEqual(data._normalize_comp_id("  123  "), 123)
        self.assertEqual(data._normalize_comp_id("abc"), "abc")

    def test_resolve_comp_season(self):
        seasons = [
            {"id": 841.0, "label": "English Premier League Season 2026/2027"},
            {"id": 777.0, "label": "2025/26"},
            {"id": 719, "label": "2024/25"},
        ]
        self.assertEqual(
            data.resolve_comp_season(seasons, "2026/27"),
            (841, "English Premier League Season 2026/2027"),
        )
        self.assertEqual(data.resolve_comp_season(seasons, "2025/26"), (777, "2025/26"))
        # Unknown season falls back to the most recent one on record.
        self.assertEqual(data.resolve_comp_season(seasons, "2030/31")[0], 841)
        self.assertEqual(data.resolve_comp_season([], "2026/27"), (None, None))


def _entry(name, position, opta, played=3, points=5, starting=None, form=None, nxt=None, annotations=None):
    return {
        "team": {"name": name, "shortName": name, "altIds": {"opta": opta}},
        "position": position,
        "startingPosition": starting if starting is not None else position,
        "overall": {
            "played": played,
            "won": 1,
            "drawn": 2,
            "lost": 0,
            "goalsFor": 4,
            "goalsAgainst": 2,
            "goalsDifference": 2,
            "points": points,
        },
        "form": form or [],
        "next": nxt,
        "annotations": annotations,
    }


def _match(gameweek, home, home_score, away, away_score):
    return {
        "gameweek": {"gameweek": gameweek},
        "kickoff": {"millis": gameweek * 1000, "label": f"Sat {gameweek} Sep 2026, 15:00 BST"},
        "teams": [
            {"team": {"name": home, "shortName": home}, "score": home_score},
            {"team": {"name": away, "shortName": away}, "score": away_score},
        ],
        "status": "C",
    }


class TestPayloadParsing(unittest.TestCase):
    def test_parse_standings_payload(self):
        form = [
            _match(2, "Coventry City", 0, "Hull City", 1),
            _match(1, "Hull City", 2, "Manchester United", 0),
            _match(3, "Hull City", 0, "Aston Villa", 0),
        ]
        nxt = {
            "kickoff": {"label": "Sat 19 Sep 2026, 15:00 BST"},
            "teams": [
                {"team": {"name": "Newcastle United", "shortName": "Newcastle"}},
                {"team": {"name": "Hull City", "shortName": "Hull"}},
            ],
        }
        payload = {
            "tables": [
                {
                    "entries": [
                        _entry("Hull City", 3, "t88", points=7, starting=5, form=form, nxt=nxt,
                               annotations=[{"type": "Q", "destination": "EU_CL"}]),
                        _entry("Coventry City", 20, "t9", points=0,
                               annotations=[{"type": "R", "destination": "EN_CH"}]),
                        # No Opta id from the API: fall back to the map.
                        {"team": {"name": "Chelsea"}, "position": 4, "overall": {"points": 6}},
                    ]
                }
            ]
        }
        df = data.parse_standings_payload(payload)
        self.assertEqual(list(df.columns), data.TABLE_COLUMNS)
        self.assertEqual(df["Team"].tolist(), ["Hull City", "Chelsea", "Coventry City"])
        hull = df.iloc[0]
        self.assertEqual(hull["Points_Value"], 18)
        self.assertEqual(hull["Points_League"], 7)
        self.assertEqual(hull["StartingPosition"], 5)
        self.assertEqual(hull["Form"], "WWD")
        self.assertEqual(hull["Next"], "Newcastle (A) · Sat 19 Sep, 15:00")
        self.assertEqual(hull["Zone"], "cl")
        self.assertTrue(hull["Crest_URL"].endswith("/t88@x2.png"))
        self.assertEqual(df.iloc[1]["Opta_ID"], "t8")
        self.assertEqual(df.iloc[2]["Zone"], "rel")
        self.assertEqual(df.iloc[2]["Points_Value"], 1)

    def test_parse_empty_payload(self):
        df = data.parse_standings_payload({"tables": []})
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), data.TABLE_COLUMNS)

    def test_form_string_perspective_and_order(self):
        form = [
            _match(3, "A", 1, "B", 1),
            _match(1, "B", 0, "A", 2),
            _match(2, "A", 0, "B", 3),
        ]
        self.assertEqual(data.form_string("A", form), "WLD")
        self.assertEqual(data.form_string("B", form), "LWD")
        self.assertEqual(data.form_string("C", form), "")
        self.assertEqual(data.form_string("A", None), "")

    def test_fallback_snapshot(self):
        df = data.fallback_standings()
        self.assertEqual(len(df), 20)
        self.assertEqual(df["Position"].tolist(), list(range(1, 21)))
        self.assertEqual(list(df.columns), data.TABLE_COLUMNS)
        for team in config.picked_teams():
            self.assertIn(team, df["Team"].tolist(), team)
        self.assertEqual(df.iloc[0]["Points_Value"], 20)
        self.assertEqual(df.iloc[-1]["Zone"], "rel")

    def test_standings_result_matchweek(self):
        result = data.StandingsResult(data.fallback_standings(), "fallback")
        self.assertEqual(result.matchweek, 3)
        self.assertFalse(result.is_live)
        empty = data.StandingsResult(pd.DataFrame(columns=data.TABLE_COLUMNS), "live")
        self.assertEqual(empty.matchweek, 0)


class TestBanter(unittest.TestCase):
    TEAMS = {
        "Hull City": {"position": 3, "starting_position": 5, "form": "WDWW", "zone": "cl"},
        "Chelsea": {"position": 4, "starting_position": 4, "form": "WWLW", "zone": "cl"},
        "Tottenham Hotspur": {"position": 19, "starting_position": 17, "form": "DLLL", "zone": "rel"},
        "Ipswich Town": {"position": 14, "starting_position": 14, "form": "LWLW", "zone": ""},
        "Newcastle United": {"position": 7, "starting_position": 7, "form": "DWDD", "zone": ""},
        "Coventry City": {"position": 20, "starting_position": 20, "form": "LLLL", "zone": "rel"},
        "Brentford": {"position": 6, "starting_position": 5, "form": "WDDW", "zone": "el"},
        "Everton": {"position": 8, "starting_position": 8, "form": "DWDL", "zone": ""},
        "Leeds United": {"position": 9, "starting_position": 9, "form": "WDDL", "zone": ""},
        "Fulham": {"position": 17, "starting_position": 19, "form": "LLLW", "zone": ""},
        "Crystal Palace": {"position": 13, "starting_position": 13, "form": "LLWD", "zone": ""},
        "Nottingham Forest": {"position": 16, "starting_position": 16, "form": "DLDL", "zone": ""},
    }

    def _ranked(self):
        positions = {team: info["position"] for team, info in self.TEAMS.items()}
        totals = scoring.player_points(config.PLAYER_PICKS, positions)
        return scoring.rank_players(totals, order=config.players())

    def _ctx(self):
        return banter.build_context(
            self._ranked(), config.PLAYER_PICKS, self.TEAMS,
            matchweek=4, previous=config.PREVIOUS_GENERATIONS, pot=30, stake=5,
        )

    def test_context_reads_the_table(self):
        ctx = self._ctx()
        self.assertEqual(ctx["leader"], "Sean")
        self.assertEqual(ctx["leader_pts"], 35)
        self.assertEqual(ctx["loser"], "Vosey")
        self.assertEqual(ctx["gap"], 35 - 9)
        self.assertEqual(ctx["leader_best_club"], "Hull")
        self.assertEqual(ctx["leader_best_pos"], "3rd")
        self.assertEqual(ctx["loser_worst_club"], "Spurs")
        self.assertEqual(ctx["loser_worst_pos_n"], 19)
        self.assertEqual(ctx["rel_club"], "Coventry")
        self.assertEqual(ctx["rel_owner"], "Dom")
        self.assertEqual(ctx["streak_club"], "Coventry")
        self.assertEqual(ctx["streak_n"], 4)
        self.assertEqual(ctx["hot_club"], "Hull")
        self.assertEqual(ctx["hot_n"], 2)
        self.assertEqual(ctx["drop_club"], "Spurs")
        self.assertEqual(ctx["drop_n"], 2)
        self.assertEqual(ctx["rise_club"], "Hull")
        self.assertEqual(ctx["rise_n"], 2)
        self.assertEqual(ctx["champ"], "Dom")
        self.assertEqual(ctx["last_spoon"], "Sam")
        self.assertEqual(ctx["last_season"], "2025/26")
        self.assertIn("champ_rank_ordinal", ctx)

    def test_every_eligible_line_renders(self):
        ctx = self._ctx()
        lines = banter.eligible(ctx)
        self.assertGreater(len(lines), 30)
        categories = {line.category for line in lines}
        self.assertTrue({"loser", "leader", "situation", "history", "generic", "classic"} <= categories)
        for line in lines:
            message = banter.render(line, ctx)
            self.assertNotIn("{", message, line.text)
            self.assertNotIn("VAR. Back in a minute", message, line.text)

    def test_lines_target_the_right_people(self):
        ctx = self._ctx()
        rendered = {banter.render(line, ctx) for line in banter.eligible(ctx)}
        self.assertTrue(any("Vosey" in m and "Spurs" in m for m in rendered))
        self.assertTrue(any("Coventry" in m and "Dom" in m for m in rendered))
        self.assertTrue(any("Dom won 2025/26" in m for m in rendered))
        # The leader gets it too.
        self.assertTrue(any(m.startswith("Sean") for m in rendered))

    def test_get_banter_avoids_recent_lines(self):
        ctx = self._ctx()
        seen = set()
        history = []
        for seed in range(60):
            line = banter.pick_line(ctx, rng=random.Random(seed), avoid=history)
            self.assertIsNotNone(line)
            self.assertNotIn(line.text, history[-10:])
            history.append(line.text)
            seen.add(banter.render(line, ctx))
        self.assertGreater(len(seen), 25)

    def test_preseason_and_empty_contexts(self):
        ranked = scoring.rank_players({p: 0 for p in config.players()}, order=config.players())
        teams = {team: {"position": 0, "starting_position": 0, "form": ""} for team in config.picked_teams()}
        ctx = banter.build_context(ranked, config.PLAYER_PICKS, teams, matchweek=0, pot=30, stake=5)
        message = banter.get_banter(ctx, rng=random.Random(1))
        self.assertIsInstance(message, str)
        self.assertNotIn("{", message)
        self.assertTrue(all("{" not in banter.render(l, ctx) for l in banter.eligible(ctx)))
        self.assertEqual(banter.get_banter({}), "No table, no banter. Even BanterBot needs something to work with.")


class TestUi(unittest.TestCase):
    def test_ordinal_and_rank_label(self):
        self.assertEqual(ui.ordinal(1), "1st")
        self.assertEqual(ui.ordinal(2), "2nd")
        self.assertEqual(ui.ordinal(3), "3rd")
        self.assertEqual(ui.ordinal(11), "11th")
        self.assertEqual(ui.ordinal(20), "20th")
        self.assertEqual(ui.ordinal(0), "–")
        self.assertEqual(ui.rank_label(2, True), "2=")
        self.assertEqual(ui.rank_label(2, False), "2")

    def test_player_image_falls_back_to_avatar(self):
        self.assertTrue(ui.player_image("Nobody").startswith("data:image/svg+xml"))
        self.assertTrue(ui.player_image("Dom").startswith("data:image/png;base64,"))

    def test_components_escape_and_render(self):
        avatar = ui.avatar_data_uri("X")
        rows = [
            {
                "player": "<Dom>",
                "image": avatar,
                "rank": 1,
                "tied": False,
                "points": 19,
                "is_leader": True,
                "is_spoon": False,
                "teams": [
                    {"name": "Newcastle United", "short": "Newcastle", "crest": None, "position": 7,
                     "starting_position": 9, "league_points": 5, "points": 14, "form": "WDL",
                     "next": "Hull (H) · Sat 19 Sep, 15:00", "missing": False},
                    {"name": "Coventry City", "short": "Coventry", "crest": "https://x/t9.png", "position": 20,
                     "starting_position": 20, "league_points": 0, "points": 1, "form": "", "next": "",
                     "missing": False},
                ],
            }
        ]
        board = ui.leaderboard_html(rows)
        self.assertIn("&lt;Dom&gt;", board)
        self.assertNotIn("<Dom>", board)
        self.assertIn("Leader", board)
        cards = ui.cards_html(rows)
        self.assertIn("▲2", cards)
        self.assertIn('bs-pip W', cards)
        self.assertIn("Next: Hull (H)", cards)
        table = ui.table_html(data.fallback_standings().to_dict("records"), config.team_owner(), {})
        self.assertIn("zone-rel", table)
        self.assertIn("owned", table)
        self.assertEqual(table.count("<tr"), 21)  # header + 20 clubs
        top = ui.topbar_html(generation=3, season="2026/27", status="live", status_label="Live table",
                             matchweek=3, fetched="16:58")
        self.assertIn("Matchweek <b>3</b>", top)
        self.assertIn("Generation 3", top)
        summary = ui.summary_html([{"label": "Leader", "value": "Sean", "sub": "35 pts", "image": avatar}])
        self.assertIn("Sean", summary)
        gens = [{"generation": 2, "season": "2025/26", "pot": 30,
                 "results": scoring.generation_results(config.PREVIOUS_GENERATIONS[1])}]
        history = ui.history_html(gens, {})
        self.assertIn("Winner", history)
        self.assertIn("Spoon", history)
        self.assertIn("Dom", history)


class TestLivePayloadFixture(unittest.TestCase):
    """Parses a saved copy of the real API payload when one is available."""

    FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "standings_2026_27_mw3.json")

    def test_fixture_parses(self):
        if not os.path.exists(self.FIXTURE):
            self.skipTest("fixture not present")
        with open(self.FIXTURE) as handle:
            payload = json.load(handle)
        df = data.parse_standings_payload(payload)
        self.assertEqual(len(df), 20)
        self.assertEqual(df["Position"].tolist(), list(range(1, 21)))
        for team in config.picked_teams():
            self.assertIn(team, df["Team"].tolist(), team)
        self.assertEqual(df.set_index("Team").loc["Coventry City", "Opta_ID"], "t9")
        self.assertEqual(df.set_index("Team").loc["Hull City", "Form"], "WWD")


if __name__ == "__main__":
    unittest.main()
