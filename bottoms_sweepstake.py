import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import requests
from bs4 import BeautifulSoup
import re
import time

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

# Function to get current Premier League standings
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_premier_league_standings():
    try:
        # Current Premier League standings data
        # In a production app, this would be scraped or fetched from an API
        standings_data = {
            "Position": list(range(1, 21)),
            "Team": [
                "Liverpool", "Arsenal", "Nottingham Forest", "Chelsea", 
                "Manchester City", "Newcastle United", "Brighton & Hove Albion", "Fulham", 
                "Aston Villa", "Bournemouth", "Brentford", "Crystal Palace", 
                "Manchester United", "Tottenham Hotspur", "Everton", "West Ham United", 
                "Wolverhampton Wanderers", "Ipswich Town", "Leicester City", "Southampton"
            ],
            "Points_League": [70, 58, 54, 49, 48, 47, 47, 45, 45, 44, 41, 39, 37, 34, 34, 34, 26, 17, 17, 9]
        }
        
        # Add points based on position (reverse order: 1st = 20pts, 20th = 1pt)
        standings_data["Points_Value"] = [21 - pos for pos in standings_data["Position"]]
        
        return pd.DataFrame(standings_data)
    except Exception as e:
        st.error(f"Error retrieving Premier League data: {e}")
        # Fallback data
        return pd.DataFrame({
            "Position": list(range(1, 21)),
            "Team": [
                "Liverpool", "Arsenal", "Nottingham Forest", "Chelsea", 
                "Manchester City", "Newcastle United", "Brighton & Hove Albion", "Fulham", 
                "Aston Villa", "Bournemouth", "Brentford", "Crystal Palace", 
                "Manchester United", "Tottenham Hotspur", "Everton", "West Ham United", 
                "Wolverhampton Wanderers", "Ipswich Town", "Leicester City", "Southampton"
            ],
            "Points_League": [70, 58, 54, 49, 48, 47, 47, 45, 45, 44, 41, 39, 37, 34, 34, 34, 26, 17, 17, 9],
            "Points_Value": list(range(20, 0, -1))  # 20 points for 1st, 1 point for 20th
        })

# Get standings data
standings_df = get_premier_league_standings()

# Create player picks data for the 24/25 season
player_picks = {
    "Player": ["Sean", "Sean", "Dom", "Dom", "Harry", "Harry", "Chris", "Chris", "Adam", "Adam"],
    "Team": ["Fulham", "Everton", "Bournemouth", "Ipswich Town", "Nottingham Forest", "Wolverhampton Wanderers", 
             "Brentford", "Leicester City", "Brighton & Hove Albion", "Southampton"]
}

picks_df = pd.DataFrame(player_picks)

# Merge with standings to get points
merged_df = pd.merge(picks_df, standings_df, on="Team", how="left")

# Calculate total points per player
player_totals = merged_df.groupby("Player")["Points_Value"].sum().reset_index()
player_totals = player_totals.sort_values("Points_Value", ascending=False)

# Display data source info
st.caption("Using Premier League 2024/25 positions for points calculation")

# Add a toggle for advanced details
with st.expander("Points Assignment Details"):
    st.write("""
    Each team's position in the Premier League table determines its points value:
    - 1st place: 20 points
    - 2nd place: 19 points
    - 3rd place: 18 points
    - ...and so on down to...
    - 20th place: 1 point
    
    Each player's total is the sum of points from their two team picks.
    """)
    
    # Show the current standings table
    st.subheader("Current Premier League Positions")
    display_standings = standings_df[["Position", "Team", "Points_Value"]].rename(
        columns={"Points_Value": "Position Points Worth"}
    )
    st.dataframe(
        display_standings,
        column_config={
            "Position": st.column_config.NumberColumn(format="%d"),
            "Team": "Team",
            "Position Points Worth": st.column_config.NumberColumn(format="%d points")
        },
        hide_index=True
    )

# Display player picks and points
st.header("Player Team Selections")
cols = st.columns(5)
for i, player in enumerate(["Sean", "Dom", "Harry", "Chris", "Adam"]):
    with cols[i]:
        st.subheader(player)
        player_data = merged_df[merged_df["Player"] == player]
        total_points = player_data["Points_Value"].sum()
        
        for _, row in player_data.iterrows():
            team = row["Team"]
            position = row["Position"]
            points = row["Points_Value"]
            
            # Calculate background color based on points (higher = better)
            intensity = int(min(255, 100 + (points / 20) * 155))
            bg_color = f"rgba(0, {intensity}, 0, 0.2)"
            
            st.markdown(
                f"""
                <div style="padding: 10px; margin-bottom: 10px; background-color: {bg_color}; border-radius: 5px;">
                    <b>{team}</b><br>
                    Position: {int(position)}<br>
                    Points: {int(points)}
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        st.markdown(f"**Total: {total_points} points**")

# Display leaderboard
st.header("Sweepstake Leaderboard")

# Create horizontal bar chart with Altair
chart = alt.Chart(player_totals).mark_bar().encode(
    x=alt.X('Points_Value:Q', title='Total Points'),
    y=alt.Y('Player:N', title='Player', sort='-x'),
    color=alt.Color('Points_Value:Q', scale=alt.Scale(scheme='blues'), legend=None),
    tooltip=['Player', alt.Tooltip('Points_Value:Q', title='Points')]
).properties(
    title='Player Rankings',
    height=300
)

st.altair_chart(chart, use_container_width=True)

# Create a leaderboard table
st.subheader("Current Standings")
leaderboard_df = player_totals.copy()
leaderboard_df["Rank"] = range(1, len(leaderboard_df) + 1)
leaderboard_df = leaderboard_df[["Rank", "Player", "Points_Value"]]
leaderboard_df.rename(columns={"Points_Value": "Total Points"}, inplace=True)

# Style the leaderboard with background colors
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
leaders = player_totals[player_totals["Points_Value"] == player_totals["Points_Value"].max()]["Player"].tolist()
leaders_text = " and ".join(leaders)
st.write(f"### 🏆 Current Leader{'s' if len(leaders) > 1 else ''}: {leaders_text} ({player_totals['Points_Value'].max()} points)")

# Add what-if scenario option
st.header("What-If Scenario Builder")
st.write("See how the standings would change if teams moved positions")

# Create columns for team movement
team_columns = st.columns(2)

# Get player teams
player_teams = sorted(picks_df["Team"].unique())

# Store modified positions
modified_positions = {}

# First column of teams
with team_columns[0]:
    st.subheader("First 5 Teams")
    for i, team in enumerate(player_teams[:5]):
        current_pos = standings_df[standings_df["Team"] == team]["Position"].values[0]
        modified_positions[team] = st.selectbox(
            f"{team} position:", 
            options=list(range(1, 21)),
            index=int(current_pos) - 1,
            key=f"pos_{team}"
        )

# Second column of teams
with team_columns[1]:
    st.subheader("Next 5 Teams")
    for i, team in enumerate(player_teams[5:]):
        current_pos = standings_df[standings_df["Team"] == team]["Position"].values[0]
        modified_positions[team] = st.selectbox(
            f"{team} position:", 
            options=list(range(1, 21)),
            index=int(current_pos) - 1,
            key=f"pos_{team}"
        )

# Calculate button
if st.button("Calculate New Standings"):
    # Check for position conflicts
    position_counts = {}
    for pos in modified_positions.values():
        position_counts[pos] = position_counts.get(pos, 0) + 1
    
    position_conflicts = [pos for pos, count in position_counts.items() if count > 1]
    
    if position_conflicts:
        st.error(f"⚠️ Position conflict: Position {', '.join(map(str, position_conflicts))} used multiple times")
    else:
        # Create a new dataframe with modified positions
        new_standings = standings_df.copy()
        
        # Update positions for player teams
        for team, new_pos in modified_positions.items():
            new_standings.loc[new_standings["Team"] == team, "Position"] = new_pos
        
        # Recalculate points values based on new positions
        new_standings["Points_Value"] = 21 - new_standings["Position"]
        
        # Sort by position
        new_standings = new_standings.sort_values("Position")
        
        # Calculate new player totals
        new_merged_df = pd.merge(picks_df, new_standings[["Team", "Position", "Points_Value"]], on="Team", how="left")
        new_player_totals = new_merged_df.groupby("Player")["Points_Value"].sum().reset_index()
        new_player_totals = new_player_totals.sort_values("Points_Value", ascending=False)
        
        # Display results
        st.subheader("New League Table")
        display_new_standings = new_standings[["Position", "Team", "Points_Value"]].rename(
            columns={"Points_Value": "Position Points Worth"}
        )
        st.dataframe(
            display_new_standings,
            column_config={
                "Position": st.column_config.NumberColumn(format="%d"),
                "Team": "Team",
                "Position Points Worth": st.column_config.NumberColumn(format="%d points")
            },
            hide_index=True
        )
        
        # Display new leaderboard
        st.subheader("New Leaderboard")
        
        # Create new horizontal bar chart
        new_chart = alt.Chart(new_player_totals).mark_bar().encode(
            x=alt.X('Points_Value:Q', title='Total Points'),
            y=alt.Y('Player:N', title='Player', sort='-x'),
            color=alt.Color('Points_Value:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['Player', alt.Tooltip('Points_Value:Q', title='Points')]
        ).properties(
            title='New Player Rankings',
            height=300
        )
        
        st.altair_chart(new_chart, use_container_width=True)
        
        # Create a new leaderboard table
        new_leaderboard_df = new_player_totals.copy()
        new_leaderboard_df["Rank"] = range(1, len(new_leaderboard_df) + 1)
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
        new_leaders = new_player_totals[new_player_totals["Points_Value"] == new_player_totals["Points_Value"].max()]["Player"].tolist()
        new_leaders_text = " and ".join(new_leaders)
        st.write(f"### 🏆 New Leader{'s' if len(new_leaders) > 1 else ''}: {new_leaders_text} ({new_player_totals['Points_Value'].max()} points)")

# Add a footer
st.markdown("---")
st.caption("Bottoms Sweepstake 2024/25 Season | Made with Streamlit")