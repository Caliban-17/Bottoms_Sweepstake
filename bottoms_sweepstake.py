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

# Function to scrape Premier League table (simplified - using default data)
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_premier_league_standings():
    # For now, we'll use default data since web scraping is proving challenging
    # In a production app, you'd implement proper scraping or use an API
    standings_data = {
        "Position": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "Team": ["Brighton", "Bournemouth", "Fulham", "Wolves", "Everton", "Brentford", "Forest", "Southampton", "Leicester", "Ipswich"],
        "Points_Value": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    }
    return pd.DataFrame(standings_data)

# Get standings data
standings_df = get_premier_league_standings()

# Create player picks data
player_picks = {
    "Player": ["Sean", "Sean", "Dom", "Dom", "Harry", "Harry", "Chris", "Chris", "Adam", "Adam"],
    "Team": ["Fulham", "Everton", "Bournemouth", "Ipswich", "Forest", "Wolves", "Brentford", "Leicester", "Brighton", "Southampton"]
}

picks_df = pd.DataFrame(player_picks)

# Standardize team names if needed
def standardize_team_names(df):
    name_mapping = {
        "Nottingham Forest": "Forest",
        "Wolverhampton Wanderers": "Wolves"
    }
    
    if "Team" in df.columns:
        df["Team"] = df["Team"].apply(lambda x: name_mapping.get(x, x))
    
    return df

standings_df = standardize_team_names(standings_df)

# Merge with standings to get points
merged_df = pd.merge(picks_df, standings_df, on="Team", how="left")

# Calculate total points per player
player_totals = merged_df.groupby("Player")["Points_Value"].sum().reset_index()
player_totals = player_totals.sort_values("Points_Value", ascending=False)

# Display data source info
st.caption("Using Premier League 2024/25 bottom 10 positions for points calculation")

# Add a toggle for advanced details
with st.expander("Team Points Assignment Details"):
    st.write("""
    Each team's position in the Premier League table determines its points value:
    - 11th place: 10 points
    - 12th place: 9 points
    - 13th place: 8 points
    - ...and so on down to...
    - 20th place: 1 point
    
    Each player's total is the sum of points from their two team picks.
    """)
    
    # Show the current standings table
    st.subheader("Current Premier League Positions (11-20)")
    st.dataframe(
        standings_df,
        column_config={
            "Position": st.column_config.NumberColumn(format="%d"),
            "Team": "Team",
            "Points_Value": st.column_config.NumberColumn("Points Worth", format="%d points")
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
        for _, row in player_data.iterrows():
            team = row["Team"]
            position = row["Position"]
            points = row["Points_Value"]
            
            # Calculate background color based on points
            # Higher points get deeper green
            bg_color = f"rgba(0, {min(200, 100 + points * 10)}, 0, 0.2)"
            
            st.markdown(
                f"""
                <div style="padding: 10px; margin-bottom: 10px; background-color: {bg_color}; border-radius: 5px;">
                    <b>{team}</b><br>
                    Position: {position}th<br>
                    Points: {points}
                </div>
                """, 
                unsafe_allow_html=True
            )

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
st.subheader("Final Standings")
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

# Create columns for the teams
col1, col2 = st.columns(2)

# Store modified positions
modified_positions = {}

# First column of teams (11-15)
with col1:
    st.subheader("Teams 11-15")
    for pos in range(11, 16):
        team = standings_df[standings_df["Position"] == pos]["Team"].values[0]
        modified_positions[team] = st.selectbox(
            f"{team} position:", 
            options=list(range(11, 21)),
            index=pos - 11,
            key=f"pos_{team}"
        )

# Second column of teams (16-20)
with col2:
    st.subheader("Teams 16-20")
    for pos in range(16, 21):
        team = standings_df[standings_df["Position"] == pos]["Team"].values[0]
        modified_positions[team] = st.selectbox(
            f"{team} position:", 
            options=list(range(11, 21)),
            index=pos - 11,
            key=f"pos_{team}"
        )

# Calculate button
if st.button("Calculate New Standings"):
    # Validate positions (each position should be used exactly once)
    position_counts = {}
    for pos in modified_positions.values():
        position_counts[pos] = position_counts.get(pos, 0) + 1
    
    if any(count > 1 for count in position_counts.values()):
        st.error("⚠️ Each position must be unique. Please ensure no position is used more than once.")
    else:
        # Create a new dataframe with modified positions
        new_standings = []
        for team, position in modified_positions.items():
            new_standings.append({
                "Team": team,
                "Position": position,
                "Points_Value": 21 - position  # Calculate points value
            })
        
        new_standings_df = pd.DataFrame(new_standings)
        
        # Merge with player picks
        new_merged_df = pd.merge(picks_df, new_standings_df, on="Team", how="left")
        
        # Calculate new totals
        new_player_totals = new_merged_df.groupby("Player")["Points_Value"].sum().reset_index()
        new_player_totals = new_player_totals.sort_values("Points_Value", ascending=False)
        
        # Display results
        st.subheader("New League Table")
        new_standings_df = new_standings_df.sort_values("Position")
        st.dataframe(
            new_standings_df,
            column_config={
                "Position": st.column_config.NumberColumn(format="%d"),
                "Team": "Team",
                "Points_Value": st.column_config.NumberColumn("Points Worth", format="%d points")
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