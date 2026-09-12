"""Bottoms Sweepstake — Streamlit app.

Gen 3 · Premier League 2026/27. Run with ``streamlit run bottoms_sweepstake.py``.
All logic lives in the ``sweepstake`` package; this file is the page.
"""

from __future__ import annotations

import os

import altair as alt
import pandas as pd
import streamlit as st

from sweepstake import banter, config, scoring, ui
from sweepstake.data import StandingsResult, get_standings

TOTAL_MATCHWEEKS = 38
BANTER_MEMORY = 12  # templates to avoid repeating within a session

# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title=f"Bottoms Sweepstake · Gen {config.GENERATION} · {config.SEASON_LABEL}",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            f"Bottoms Sweepstake · Generation {config.GENERATION} · Premier League {config.SEASON_LABEL}. "
            "Table data from premierleague.com."
        )
    },
)
st.html(ui.CSS)


@st.cache_data(ttl=30 * 60, show_spinner="Fetching the Premier League table…")
def load_standings(season_label: str) -> StandingsResult:
    return get_standings(season_label)


def refresh_data() -> None:
    st.cache_data.clear()
    st.session_state.pop("banter", None)
    st.rerun()


def leaderboard_chart(ranked: list[dict]) -> alt.Chart:
    frame = pd.DataFrame(
        [{"Player": r["player"], "Points": r["points"], "Rank": r["rank"]} for r in ranked]
    )
    base = alt.Chart(frame).encode(
        y=alt.Y(
            "Player:N",
            sort=alt.EncodingSortField(field="Points", order="descending"),
            title=None,
            axis=alt.Axis(
                labelFontSize=13,
                labelColor="#E6E8EC",
                labelFont="Inter, sans-serif",
                ticks=False,
                domain=False,
                labelPadding=12,
            ),
        )
    )
    bars = base.mark_bar(cornerRadiusEnd=3, size=22, color="#8B7CF6").encode(
        x=alt.X(
            "Points:Q",
            title=None,
            scale=alt.Scale(domain=[0, config.MAX_PLAYER_POINTS]),
            axis=alt.Axis(
                grid=True,
                gridColor="#262B36",
                labelColor="#8A919F",
                labelFont="Inter, sans-serif",
                tickCount=4,
                domain=False,
                ticks=False,
            ),
        ),
        tooltip=[
            alt.Tooltip("Player:N", title="Player"),
            alt.Tooltip("Points:Q", title="Points"),
            alt.Tooltip("Rank:Q", title="Rank"),
        ],
    )
    labels = base.mark_text(
        align="left", dx=8, color="#E6E8EC", fontSize=12.5, font="Inter, sans-serif", fontWeight=600
    ).encode(x="Points:Q", text="Points:Q")
    return (
        (bars + labels)
        .properties(height=alt.Step(38), padding={"left": 0, "right": 28, "top": 6, "bottom": 6})
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
result = load_standings(config.SEASON_LABEL)
table = result.table
if table is None or table.empty:
    st.error("Could not load any league table at all. Try again in a minute.")
    st.stop()

team_rows: dict[str, dict] = {row["Team"]: row for row in table.to_dict("records")}
owners = config.team_owner()
players = config.players()
picked = config.picked_teams()
missing_teams = [team for team in picked if team not in team_rows]

positions = {
    team: int(team_rows[team]["Position"]) if team in team_rows else 0 for team in picked
}
totals = scoring.player_points(config.PLAYER_PICKS, positions)
ranked = scoring.rank_players(totals, order=players)
rank_by_player = {row["player"]: row for row in ranked}
leaders = scoring.leaders(ranked)
spoons = scoring.wooden_spoons(ranked)
pot = config.jackpot_gbp()
season_started = result.matchweek > 0

images = {player: ui.player_image(player) for player in players}
for generation in config.PREVIOUS_GENERATIONS:
    for player in generation["picks"]:
        images.setdefault(player, ui.player_image(player))

SOURCE_LABELS = {
    "live": "Live table",
    "preseason": "Pre-season",
    "fallback": "Offline snapshot",
}
SOURCE_DETAILS = {
    "live": "Live from premierleague.com",
    "preseason": "Pre-season team list from premierleague.com",
    "fallback": "Offline snapshot (data service unreachable)",
}


def team_summary(team: str) -> dict:
    row = team_rows.get(team)
    return {
        "name": team,
        "short": config.short_name(team),
        "crest": row["Crest_URL"] if row else config.crest_url(config.OPTA_ID_MAP.get(team)),
        "position": positions[team],
        "starting_position": int(row["StartingPosition"]) if row else 0,
        "league_points": int(row["Points_League"]) if row else 0,
        "points": scoring.points_for_position(positions[team]),
        "form": (row["Form"] if row else "") or "",
        "next": (row["Next"] if row else "") or "",
        "zone": (row["Zone"] if row else "") or "",
        "missing": row is None,
    }


player_views = [
    {
        "player": row["player"],
        "image": images[row["player"]],
        "rank": row["rank"],
        "tied": row["tied"],
        "points": row["points"],
        "is_leader": row["player"] in leaders and season_started,
        "is_spoon": row["player"] in spoons and season_started and row["player"] not in leaders,
        "teams": [team_summary(team) for team in config.PLAYER_PICKS[row["player"]]],
    }
    for row in ranked
]

# ---- BanterBot -------------------------------------------------------------
banter_ctx = banter.build_context(
    ranked,
    config.PLAYER_PICKS,
    {view["name"]: view for card in player_views for view in card["teams"]},
    matchweek=result.matchweek,
    previous=config.PREVIOUS_GENERATIONS,
    pot=pot,
    stake=config.STAKE_GBP,
)


def new_banter() -> None:
    history = st.session_state.setdefault("banter_history", [])
    line = banter.pick_line(banter_ctx, avoid=history)
    if line is None:
        st.session_state["banter"] = banter.get_banter(banter_ctx)
        return
    history.append(line.text)
    del history[:-BANTER_MEMORY]
    st.session_state["banter"] = banter.render(line, banter_ctx)


if "banter" not in st.session_state:
    new_banter()

# --------------------------------------------------------------------------- #
# Sidebar: data status + headshots
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### Controls")
    if st.button("Refresh table", use_container_width=True, help="Clear the cache and refetch"):
        refresh_data()
    st.caption(
        f"**Source:** {SOURCE_DETAILS[result.source]}  \n"
        f"**Season:** {result.comp_season_label or config.SEASON_LABEL}  \n"
        f"**Fetched:** {result.fetched_at:%a %d %b, %H:%M}  \n"
        "Cached for 30 minutes."
    )
    st.divider()
    st.markdown("### Headshots")
    st.caption("Pick a player and upload an image. It replaces their current headshot.")
    with st.form("headshot_form", clear_on_submit=True):
        selected_player = st.selectbox("Player", players)
        uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Save headshot", use_container_width=True)
    if submitted:
        if uploaded is None:
            st.warning("Choose an image first.")
        else:
            ext = os.path.splitext(uploaded.name)[1].lower() or ".png"
            os.makedirs(ui.HEADSHOT_DIR, exist_ok=True)
            for old_ext in (".png", ".jpg", ".jpeg"):
                old_path = os.path.join(ui.HEADSHOT_DIR, f"{selected_player}{old_ext}")
                if old_ext != ext and os.path.exists(old_path):
                    os.remove(old_path)
            with open(os.path.join(ui.HEADSHOT_DIR, f"{selected_player}{ext}"), "wb") as handle:
                handle.write(uploaded.getbuffer())
            st.toast(f"Headshot updated for {selected_player}.")
            st.rerun()

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.html(
    ui.topbar_html(
        generation=config.GENERATION,
        season=config.SEASON_LABEL,
        status=result.source,
        status_label=SOURCE_LABELS[result.source],
        matchweek=result.matchweek,
        fetched=f"{result.fetched_at:%H:%M}",
    )
)

action_refresh, action_banter, action_party, _ = st.columns([1, 1, 1, 2.5])
with action_refresh:
    if st.button("Refresh", use_container_width=True, help="Refetch the league table"):
        refresh_data()
with action_banter:
    if st.button("New banter", use_container_width=True, help="Roll a fresh line"):
        new_banter()
with action_party:
    if st.button("Celebrate", use_container_width=True, help="Balloons for the leader"):
        st.balloons()

if result.message:
    (st.info if result.source == "preseason" else st.warning)(result.message)
if missing_teams:
    st.warning("These picks aren't in the loaded table and score 0 for now: " + ", ".join(missing_teams))

# --------------------------------------------------------------------------- #
# Summary + BanterBot
# --------------------------------------------------------------------------- #
leader_row = rank_by_player[leaders[0]]
spoon_row = rank_by_player[spoons[0]]
runner_up = next((row for row in ranked if row["rank"] > 1), None)
margin = leader_row["points"] - runner_up["points"] if runner_up else 0
gap = leader_row["points"] - spoon_row["points"]

if not season_started:
    leader_sub = "Nothing to separate anyone yet"
elif len(leaders) > 1:
    leader_sub = f"{leader_row['points']} pts, level at the top"
elif runner_up:
    leader_sub = f"{leader_row['points']} pts, {margin} clear of {runner_up['player']}"
else:
    leader_sub = f"{leader_row['points']} pts"

cells = [
    {
        "label": "Leader" if len(leaders) == 1 else "Leaders",
        "value": " & ".join(leaders),
        "sub": leader_sub,
        "image": images[leaders[0]],
    },
    {
        "label": "Wooden spoon",
        "value": " & ".join(spoons),
        "sub": f"{spoon_row['points']} pts, {gap} behind" if season_started else "Awaiting the first slip",
        "image": images[spoons[0]],
    },
    {
        "label": "Matchweek",
        "value": f"{result.matchweek} of {TOTAL_MATCHWEEKS}" if season_started else "Pre-season",
        "sub": f"{TOTAL_MATCHWEEKS - result.matchweek} rounds still to play",
    },
    {
        "label": "Prize pot",
        "value": f"£{pot}",
        "sub": f"{len(players)} players × £{config.STAKE_GBP}, winner takes all",
    },
]
st.html(ui.summary_html(cells))
st.html(ui.banter_html(st.session_state["banter"]))

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
tab_board, tab_squads, tab_table, tab_rules = st.tabs(
    ["Leaderboard", "Squads", "League table", "Rules & history"]
)

with tab_board:
    col_list, col_chart = st.columns([3, 2], gap="large")
    with col_list:
        st.html(ui.head_html("Standings", f"sweepstake points, max {config.MAX_PLAYER_POINTS}"))
        st.html(ui.leaderboard_html(player_views))
    with col_chart:
        st.html(ui.head_html("Points"))
        st.altair_chart(leaderboard_chart(ranked), use_container_width=True, theme=None)

with tab_squads:
    st.html(ui.head_html("Squads", "position, league points, form and next fixture for each club"))
    st.html(ui.cards_html(player_views))

with tab_table:
    st.html(
        ui.head_html(
            "Premier League table",
            f"{result.comp_season_label or config.SEASON_LABEL}, owned clubs highlighted",
        )
    )
    only_owned = st.toggle("Only show owned clubs", value=False)
    table_rows = table.to_dict("records")
    if only_owned:
        table_rows = [row for row in table_rows if row["Team"] in owners]
    st.html(ui.table_html(table_rows, owners, images))

with tab_rules:
    st.html(ui.head_html("How it works"))
    st.html(ui.rules_html(config.STAKE_GBP, pot, len(players)))
    st.html(ui.head_html("Previous generations", "final tables"))
    history = [
        {
            "generation": generation["generation"],
            "season": generation["season"],
            "pot": generation["stake_gbp"] * len(generation["picks"]),
            "results": scoring.generation_results(generation),
        }
        for generation in config.PREVIOUS_GENERATIONS
    ]
    st.html(ui.history_html(history, images))

# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
st.html(
    ui.footer_html(
        config.GENERATION,
        config.SEASON_LABEL,
        f"{result.fetched_at:%d %b %Y %H:%M}",
        SOURCE_LABELS[result.source],
    )
)
