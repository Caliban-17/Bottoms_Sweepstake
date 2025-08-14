import streamlit as st
import pandas as pd
import altair as alt
import time
from datetime import datetime
import requests

from bs4 import BeautifulSoup

SEASON_LABEL = "2025/26"

# Set page config
st.set_page_config(
    page_title=f"Bottoms Sweepstake {SEASON_LABEL} Season",
    page_icon="⚽",
    layout="wide"
)

# Title and description
st.title("⚽ Bottoms Sweepstake")
st.subheader(f"Premier League {SEASON_LABEL} Season")

# Stake and jackpot info
col1, col2 = st.columns(2)
with col1:
    st.info("**Stake:** £5 each")
with col2:
    st.success("**Jackpot:** £25 🤑")

# --- Fallback Data ---
# Used if scraping fails
def get_fallback_standings():
    st.warning(f"⚠️ Using placeholder fallback data (24/25 snapshot). Could not fetch {SEASON_LABEL} live standings yet.")
    standings_data = {
        "Position": list(range(1, 21)),
        "Team": [
            "Liverpool", "Arsenal", "Nottingham Forest", "Chelsea",
            "Manchester City", "Newcastle United", "Brighton and Hove Albion", "Fulham",
            "Aston Villa", "Bournemouth", "Brentford", "Crystal Palace",
            "Manchester United", "Tottenham Hotspur", "Everton", "West Ham United",
            "Wolverhampton Wanderers", "Ipswich Town", "Leicester City", "Southampton"
        ],
        "Points_League": [70, 58, 54, 49, 48, 47, 47, 45, 45, 44, 41, 39, 37, 34, 34, 34, 26, 17, 17, 9]
    }
    df = pd.DataFrame(standings_data)
    # Add points based on position (reverse order: 1st = 20pts, 20th = 1pt)
    df["Points_Value"] = 21 - df["Position"]
    return df

# Function to get current Premier League standings via public JSON API
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_premier_league_standings(season_label: str = SEASON_LABEL) -> pd.DataFrame:
    """Fetch Premier League standings for a given season label (e.g. "2025/26").

    This uses the Premier League's public data service (footballapi.pulselive.com)
    to resolve the compSeason ID for the requested season and then retrieves the
    table standings. If anything fails (e.g., network issues, season not yet
    populated), it falls back to static placeholder data.

    Parameters
    ----------
    season_label : str
        The season label to fetch (default: value of SEASON_LABEL constant).

    Returns
    -------
    pandas.DataFrame
        Columns: [Position, Team, Points_League, Points_Value]
    """
    seasons_url = "https://footballapi.pulselive.com/football/competitions/1/compseasons"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://www.premierleague.com",
        "Referer": "https://www.premierleague.com/tables",
    }

    try:
        # Resolve the compSeason ID for the requested season label
        resp = requests.get(seasons_url, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

        seasons_list = (
            payload.get("compSeasons")
            or payload.get("seasons")
            or (payload if isinstance(payload, list) else [])
        )

        comp_id = None
        fallback_current = None
        latest_id = None
        latest_start = None

        for s in seasons_list:
            label = s.get("label") or s.get("competition", {}).get("label")
            sid = s.get("id") or s.get("compSeason", {}).get("id")
            start = s.get("startDate") or s.get("start", {}).get("date")
            is_current = s.get("isCurrent") or s.get("current", False)

            if season_label and label == season_label:
                comp_id = sid

            if is_current and fallback_current is None:
                fallback_current = sid

            if start:
                try:
                    # Normalise ISO strings that may contain a 'T'
                    ts = start.replace("Z", "").replace("T", " ")
                    dt = datetime.fromisoformat(ts)
                    if latest_start is None or dt > latest_start:
                        latest_start = dt
                        latest_id = sid
                except Exception:
                    pass

        if not comp_id:
            comp_id = fallback_current or latest_id

        if not comp_id:
            st.error("Could not resolve a Premier League compSeason id.")
            return get_fallback_standings()

        # Fetch standings for the resolved compSeason id
        standings_url = (
            f"https://footballapi.pulselive.com/football/standings?compSeasons={comp_id}"
            "&altIds=true&detail=2"
        )
        resp2 = requests.get(standings_url, headers=headers, timeout=10)
        resp2.raise_for_status()
        data = resp2.json()

        tables = data.get("tables") or data.get("standings") or []

        # Prefer the TOTAL (league) table; otherwise, take the first available
        table_total = None
        for t in tables:
            t_type = (t.get("type") or t.get("stage", {}).get("type", "")).upper()
            if t_type in ("TOTAL", "LEAGUE"):
                table_total = t
                break
        if table_total is None and tables:
            table_total = tables[0]

        entries = table_total.get("entries", []) if table_total else []

        positions: list[int] = []
        teams: list[str] = []
        points_league: list[int] = []

        for e in entries:
            pos = e.get("position") or e.get("rank")

            # Team name can live under a few different keys—be defensive
            team_name = (
                (e.get("team") or {}).get("name")
                or (e.get("team", {}).get("club") or {}).get("name")
                or (e.get("club") or {}).get("name")
                or (e.get("team") or {}).get("displayName")
            )

            # Points can appear either directly or inside a stats collection
            points = e.get("points")
            if points is None:
                stats = e.get("stats", {})
                if isinstance(stats, dict) and "points" in stats:
                    points = stats.get("points")
                elif isinstance(stats, list):
                    for it in stats:
                        if it.get("name") in ("points", "pts", "Points"):
                            points = it.get("value") or it.get("displayValue")
                            break

            if pos is None or team_name is None:
                continue

            try:
                positions.append(int(pos))
            except Exception:
                continue

            teams.append(str(team_name).strip())

            try:
                points_league.append(int(points))
            except Exception:
                # Early-season/empty table case: default to zero
                points_league.append(0)

        if not positions:
            st.warning(
                f"No league entries returned for {season_label}. The season may not be populated yet; showing fallback."
            )
            return get_fallback_standings()

        df = pd.DataFrame(
            {"Position": positions, "Team": teams, "Points_League": points_league}
        )
        df.sort_values("Position", inplace=True)
        df["Points_Value"] = 21 - df["Position"]
        st.success("✅ Live standings fetched successfully!")
        return df

    except requests.exceptions.RequestException as exc:
        st.error(f"Network error fetching standings: {exc}")
        return get_fallback_standings()
    except Exception as exc:
        st.error(f"An unexpected error occurred while fetching standings: {exc}")
        return get_fallback_standings()


# Create player picks data for the 24/25 season
# *** IMPORTANT: Ensure these team names EXACTLY match the long names scraped from premierleague.com ***
def get_player_picks():
    return pd.DataFrame({
        "Player": ["Sean", "Sean", "Dom", "Dom", "Harry", "Harry", "Chris", "Chris", "Adam", "Adam"],
        "Team": ["Fulham", "Everton", "Bournemouth", "Ipswich Town",
                 "Nottingham Forest", "Wolverhampton Wanderers", # Corrected names
                 "Brentford", "Leicester City",                 # Corrected name
                 "Brighton and Hove Albion", "Southampton"]         # Corrected name
    })

# Get standings data (tries scraping, falls back to static)
standings_df = get_premier_league_standings()

st.dataframe(standings_df)

picks_df = get_player_picks()

if standings_df is None or standings_df.empty:
    st.error("🚨 Critical Error: Could not load league standings data. Aborting.")
    st.stop()

# Check if standings_df is valid before proceeding
if standings_df is None or standings_df.empty:
    st.error("🚨 Critical Error: Could not load league standings data. Aborting.")
    st.stop() # Stop execution if standings are missing

# --- Data Processing and Display (largely unchanged from original) ---

# Merge with standings to get points
# Add validation to handle cases where a picked team might not be in the scraped standings (e.g., mid-season)
merged_df = pd.merge(picks_df, standings_df, on="Team", how="left")

# Handle potential missing teams after merge (if scraping failed partially or team names mismatch)
missing_teams = merged_df[merged_df['Position'].isna()]
if not missing_teams.empty:
    st.warning("Could not find standings data for the following teams:")
    st.dataframe(missing_teams[['Player', 'Team']], hide_index=True)
    # Decide how to handle points for missing teams: assign 0 or handle differently
    merged_df['Points_Value'].fillna(0, inplace=True) # Assign 0 points if team not found
    merged_df['Position'].fillna(0, inplace=True) # Assign 0 position
    merged_df['Points_League'].fillna(0, inplace=True) # Assign 0 league points


# Calculate total points per player
player_totals = merged_df.groupby("Player")["Points_Value"].sum().reset_index()
player_totals = player_totals.sort_values("Points_Value", ascending=False)

# Display last update time
current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
st.caption(f"Last updated: {current_time}")

# Add a toggle for advanced details
with st.expander("Points Assignment & Current Standings"):
    st.write("""
    Each team's position in the Premier League table determines its sweepstake points value:
    - 1st place: 20 points
    - 2nd place: 19 points
    - 3rd place: 18 points
    - ...and so on down to...
    - 20th place: 1 point
    
    Each player's total is the sum of sweepstake points from their two team picks. Higher sweepstake points are better.
    """)
    
    # Show the current standings table based on fetched/fallback data
    st.subheader("Current Premier League Standings")
    display_standings = standings_df[["Position", "Team", "Points_League", "Points_Value"]].rename(
        columns={"Points_Value": "Sweepstake Points Worth", "Points_League": "League Points"}
    )
    st.dataframe(
        display_standings.sort_values("Position"), # Ensure sorted by position
        column_config={
            "Position": st.column_config.NumberColumn(format="%d"),
            "Team": "Team",
            "League Points": st.column_config.NumberColumn(format="%d pts"),
            "Sweepstake Points Worth": st.column_config.NumberColumn(format="%d pts")
        },
        hide_index=True,
        use_container_width=True
    )

# Display player picks and points
st.header("Player Team Selections")
cols = st.columns(len(picks_df['Player'].unique())) # Dynamically create columns
players = sorted(picks_df['Player'].unique())

for i, player in enumerate(players):
    with cols[i]:
        st.subheader(player)
        player_data = merged_df[merged_df["Player"] == player]
        # Recalculate total points here to ensure consistency after potential fillna
        total_points = player_data["Points_Value"].sum()

        for _, row in player_data.iterrows():
            team = row["Team"]
            position = row["Position"]
            points = row["Points_Value"]
            league_points = row["Points_League"]

            # Format position nicely, handle potential 0 from fillna
            pos_display = f"{int(position)}" if position > 0 else "N/A"
            
            # Calculate background color based on points (higher = better)
            # Handle potential 0 points from fillna
            intensity = int(min(255, 100 + (points / 20) * 155)) if points > 0 else 100
            bg_color = f"rgba(0, {intensity}, 0, 0.2)" if points > 0 else "rgba(128, 128, 128, 0.1)" # Grey if N/A

            st.markdown(
                f"""
                <div style="padding: 10px; margin-bottom: 10px; background-color: {bg_color}; border-radius: 5px;">
                    <b>{team}</b><br>
                    Position: {pos_display}<br>
                    Sweepstake Points: {int(points)}<br>
                    League Points: {int(league_points)}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(f"**Total: {int(total_points)} points**")


# Display leaderboard
st.header("Sweepstake Leaderboard")

# Create horizontal bar chart with Altair
chart = alt.Chart(player_totals).mark_bar().encode(
    x=alt.X('Points_Value:Q', title='Total Sweepstake Points'),
    y=alt.Y('Player:N', title='Player', sort='-x'),
    color=alt.Color('Points_Value:Q', scale=alt.Scale(scheme='blues'), legend=None),
    tooltip=['Player', alt.Tooltip('Points_Value:Q', title='Points')]
).properties(
    title='Player Rankings',
    height=alt.Step(40) # Adjust height based on number of players
)

st.altair_chart(chart, use_container_width=True)

# Create a leaderboard table
st.subheader("Current Standings")
leaderboard_df = player_totals.copy()
# Handle ties in rank
leaderboard_df['Rank'] = leaderboard_df['Points_Value'].rank(method='min', ascending=False).astype(int)
leaderboard_df = leaderboard_df.sort_values('Rank')
leaderboard_df = leaderboard_df[["Rank", "Player", "Points_Value"]]
leaderboard_df.rename(columns={"Points_Value": "Total Points"}, inplace=True)

st.dataframe(
    leaderboard_df,
    column_config={
        "Rank": st.column_config.NumberColumn(format="%d"),
        "Player": "Player",
        "Total Points": st.column_config.NumberColumn(format="%d")
    },
    hide_index=True,
    use_container_width=True
)

# Highlight leaders
if not player_totals.empty:
    max_points = player_totals['Points_Value'].max()
    leaders = player_totals[player_totals["Points_Value"] == max_points]["Player"].tolist()
    leaders_text = " and ".join(leaders)
    st.write(f"### 🏆 Current Leader{'s' if len(leaders) > 1 else ''}: {leaders_text} ({int(max_points)} points)")
else:
    st.write("Leaderboard data is currently unavailable.")


# Add what-if scenario option
st.header("What-If Scenario Builder")
st.write("See how the standings would change if teams moved positions (based on currently loaded standings)")

# Create columns for team movement
team_columns = st.columns(2)

# Get player teams from the picks dataframe
player_teams = sorted(picks_df["Team"].unique())

# Store modified positions
modified_positions = {}
current_positions_map = pd.Series(standings_df.Position.values, index=standings_df.Team).to_dict()

# Chunk teams for columns
num_teams = len(player_teams)
mid_point = (num_teams + 1) // 2 # Split roughly in half

# First column of teams
with team_columns[0]:
    st.subheader("Teams (Part 1)")
    for i, team in enumerate(player_teams[:mid_point]):
        # Get current position from the *loaded* standings_df, default to 1 if not found
        current_pos = current_positions_map.get(team, 1)
        modified_positions[team] = st.number_input(
            f"{team} new position:",
            min_value=1,
            max_value=20,
            value=int(current_pos), # Ensure value is int
            key=f"pos_{team}",
            step=1
        )

# Second column of teams
with team_columns[1]:
    st.subheader("Teams (Part 2)")
    for i, team in enumerate(player_teams[mid_point:]):
        current_pos = current_positions_map.get(team, 1)
        modified_positions[team] = st.number_input(
            f"{team} new position:",
            min_value=1,
            max_value=20,
            value=int(current_pos), # Ensure value is int
            key=f"pos_{team}",
            step=1
        )

# Calculate button
if st.button("Calculate New Standings"):
    # Check for position conflicts *among the teams being modified*
    pos_counts = {}
    for team, pos in modified_positions.items():
        pos_counts[pos] = pos_counts.get(pos, 0) + 1

    conflicts = {pos: count for pos, count in pos_counts.items() if count > 1}

    if conflicts:
        conflict_messages = []
        for pos, count in conflicts.items():
            teams_at_pos = [t for t, p in modified_positions.items() if p == pos]
            conflict_messages.append(f"Position {pos} assigned to {count} teams: {', '.join(teams_at_pos)}")

        st.error(f"⚠️ Position conflicts detected:\n" + "\n".join(conflict_messages))
        st.warning("Please ensure each position is assigned to only one selected team in the builder.")
    else:
        # Create a new dataframe based on the *currently loaded* standings
        new_standings = standings_df.copy()

        # Update positions only for the teams included in the builder
        for team, new_pos in modified_positions.items():
            if team in new_standings['Team'].values:
                 new_standings.loc[new_standings["Team"] == team, "Position"] = new_pos
            else:
                st.warning(f"Team '{team}' selected in 'What-If' not found in current standings, ignoring.")

        st.subheader("Hypothetical Player Scores (What-If)")
        st.caption("Calculated based ONLY on the new positions entered above. Other teams' positions are assumed unchanged for this calculation.")

        # Recalculate points values based on *hypothetical* positions
        hypothetical_points = {team: 21 - pos for team, pos in modified_positions.items()}

        # Calculate new player totals based on these hypothetical points
        new_player_totals_list = []
        for player in picks_df['Player'].unique():
            player_teams_list = picks_df[picks_df['Player'] == player]['Team'].tolist()
            new_total = 0
            for team in player_teams_list:
                # Use the hypothetical point value if the team was modified
                if team in hypothetical_points:
                    new_total += hypothetical_points[team]
                # Otherwise, use the original point value from the loaded standings
                elif team in merged_df['Team'].values:
                     # Get original points value for teams not in the what-if builder
                     original_points = merged_df.loc[merged_df['Team'] == team, 'Points_Value'].iloc[0]
                     new_total += original_points
                else:
                    new_total += 0 # Team not found in original merge either

            new_player_totals_list.append({"Player": player, "Points_Value": new_total})

        new_player_totals = pd.DataFrame(new_player_totals_list)
        new_player_totals = new_player_totals.sort_values("Points_Value", ascending=False)

        # Display new leaderboard chart
        new_chart = alt.Chart(new_player_totals).mark_bar().encode(
            x=alt.X('Points_Value:Q', title='Total Points (Hypothetical)'),
            y=alt.Y('Player:N', title='Player', sort='-x'),
            color=alt.Color('Points_Value:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['Player', alt.Tooltip('Points_Value:Q', title='Points')]
        ).properties(
            title='Hypothetical Player Rankings',
            height=alt.Step(40)
        )
        st.altair_chart(new_chart, use_container_width=True)

        # Display new leaderboard table
        new_leaderboard_df = new_player_totals.copy()
        new_leaderboard_df['Rank'] = new_leaderboard_df['Points_Value'].rank(method='min', ascending=False).astype(int)
        new_leaderboard_df = new_leaderboard_df.sort_values('Rank')
        new_leaderboard_df = new_leaderboard_df[["Rank", "Player", "Points_Value"]]
        new_leaderboard_df.rename(columns={"Points_Value": "Total Points"}, inplace=True)

        st.dataframe(
            new_leaderboard_df,
            column_config={
                "Rank": st.column_config.NumberColumn(format="%d"),
                "Player": "Player",
                "Total Points": st.column_config.NumberColumn(format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

        # Highlight new leaders
        if not new_player_totals.empty:
            new_max_points = new_player_totals['Points_Value'].max()
            new_leaders = new_player_totals[new_player_totals["Points_Value"] == new_max_points]["Player"].tolist()
            new_leaders_text = " and ".join(new_leaders)
            st.write(f"### 🏆 Hypothetical Leader{'s' if len(new_leaders) > 1 else ''}: {new_leaders_text} ({int(new_max_points)} points)")
        else:
            st.write("Hypothetical leaderboard data is currently unavailable.")


# Add a footer
st.markdown("---")
st.caption(f"Bottoms Sweepstake {SEASON_LABEL} Season | Made with Streamlit | Data via premierleague.com | Last updated: {current_time}")