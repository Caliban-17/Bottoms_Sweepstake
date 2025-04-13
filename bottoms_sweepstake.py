import streamlit as st
import pandas as pd
import altair as alt
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Set page config
st.set_page_config(
    page_title="Bottoms Sweepstake 24/25 Season",
    page_icon="⚽",
    layout="wide"
)

# Title and description
st.title("⚽ Bottoms Sweepstake")
st.subheader("Premier League 24/25 Season")

# Stake and jackpot info
col1, col2 = st.columns(2)
with col1:
    st.info("**Stake:** £5 each")
with col2:
    st.success("**Jackpot:** £25 🤑")

# --- Fallback Data ---
# Used if scraping fails
def get_fallback_standings():
    st.warning("⚠️ Using fallback static data from April 2025. Could not fetch live standings.")
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

# Function to get current Premier League standings via scraping
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_premier_league_standings():
    url = "https://www.premierleague.com/tables"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')
        
        table_body = soup.find('tbody', class_='league-table__tbody')

        if not table_body:
            st.error("Could not find the league table body on the page.")
            return get_fallback_standings()

        rows = table_body.find_all('tr', attrs={'data-position': True})

        if not rows:
            st.error("Could not find any team rows in the table.")
            return get_fallback_standings()

        positions = []
        teams = []
        points_league = []

        for row in rows:
            try:
                # Position
                pos_cell = row.find('td', class_='league-table__pos')
                pos_span = pos_cell.find('span', class_='league-table__value')
                position = int(pos_span.text.strip())
                
                # Team Name
                team_cell = row.find('td', class_='league-table__team')
                team_span_long = team_cell.find('span', class_='league-table__team-name--long')
                team_name = team_span_long.text.strip()
                # Handle known name variations if necessary (though scraping long name should be consistent)
                # e.g., if team_name == "Nott'm Forest": team_name = "Nottingham Forest"

                # Points
                points_cell = row.find('td', class_='league-table__points')
                points = int(points_cell.text.strip())

                positions.append(position)
                teams.append(team_name)
                points_league.append(points)

            except (AttributeError, ValueError, TypeError) as e:
                st.warning(f"Skipping a row due to parsing error: {e}")
                continue # Skip row if parsing fails

        if not positions: # Check if any data was successfully parsed
             st.error("Failed to parse any team data from the table.")
             return get_fallback_standings()

        standings_df = pd.DataFrame({
            "Position": positions,
            "Team": teams,
            "Points_League": points_league
        })
        
        # Add points based on position (reverse order: 1st = 20pts, 20th = 1pt)
        standings_df["Points_Value"] = 21 - standings_df["Position"]
        
        # Clean up team names just in case (e.g., removing extra spaces)
        standings_df['Team'] = standings_df['Team'].str.strip()

        # Ensure all 20 teams were found
        if len(standings_df) != 20:
            st.warning(f"Warning: Found {len(standings_df)} teams instead of 20. Data might be incomplete.")
            # Optional: Fallback if not 20 teams? Or proceed with caution?
            # return get_fallback_standings() # Stricter check
        
        st.success("✅ Live standings fetched successfully!")
        return standings_df

    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching standings: {e}")
        return get_fallback_standings()
    except Exception as e:
        st.error(f"An unexpected error occurred during scraping: {e}")
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


        # --- IMPORTANT: What-if logic adjustment ---
        # The simple update above doesn't handle displacing other teams.
        # A full simulation is complex. Let's focus *only* on the points impact
        # for the selected teams based on their hypothetical new positions.
        # We won't display a full "New League Table" as it's misleading without
        # adjusting all other teams.

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
st.caption(f"Bottoms Sweepstake 2024/25 Season | Made with Streamlit | Data scraped from premierleague.com | Last updated: {current_time}")