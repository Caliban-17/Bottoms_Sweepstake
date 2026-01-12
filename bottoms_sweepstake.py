import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import requests
import numpy as np

import random

SEASON_LABEL = "2025/26"

# --- Funky Assets ---
BANTER_PHRASES = {
    "leader": [
        "{0} is absolutely flying! Liquid football. 🌊",
        "Put the champagne on ice. {0} is doing a madness.",
        "Top bins from {0}. Pure class.",
        "{0}: 'I would love it if we beat them! Love it!' 😤",
        "Statues will be built. Streets will be named after {0}.",
        "{0} is drinking it in. Long. Hard. Deep.",
        "Gary Neville is currently groaning at how good {0} is. 😩",
        "Prime Barcelona vibes from {0}. Tiki-taka merchants.",
    ],
    "loser": [
        "{0} mate, you've absolutely bottled it. 🍾",
        "Proper Sunday League stuff from {0}. Get in the bin.",
        "{0} couldn't hit a barn door with a banjo. 📉",
        "Enjoy Millwall away you mug. {0} is down.",
        "{0} is holding the Wooden Spoon. Cheers Geoff. 🥄",
        "Even Big Sam couldn't save {5} from this wreck.",
        "{2} is currently in the mud. Absolute shambles.",
        "Fraudiola has nothing on the fraudulence of {2}.",
        "I prefer not to speak about {3}. If I speak, I am in big trouble.",
    ],
    "generic": [
        "Game's gone. Soft penalties everywhere.",
        "Can they do it on a cold rainy night in Stoke?",
        "Ref needs Specsavers. 👓",
        "VAR checking... still checking... Good ebening. 🖥️",
        "Unbelievable Jeff!",
        "Chat sh*t, get banged. 🦊",
        "Prawn sandwich brigade out in force today. 🍤",
        "Meat pie, sausage roll, come on {5}, give us a goal!",
        "Back in my day you could tackle. Game's gone soft.",
        "Bald fraud detected.",
        "Farmers league performance.",
    ]
}

# --- Authoritative Opta IDs (for Crests) ---
# The badge URL uses 't{id}' where id is the OPTA id, not Pulse ID.
OPTA_ID_MAP = {
    "Arsenal": "t3",
    "Aston Villa": "t7",
    "Bournemouth": "t91",
    "Brentford": "t94",
    "Brighton & Hove Albion": "t36",
    "Brighton and Hove Albion": "t36",
    "Burnley": "t90",
    "Chelsea": "t8",
    "Crystal Palace": "t31",
    "Everton": "t11",
    "Fulham": "t54",
    "Ipswich Town": "t8", # Verify if needed, keeping placeholder
    "Leeds United": "t2",
    "Leicester City": "t13",
    "Liverpool": "t14",
    "Luton Town": "t102",
    "Manchester City": "t43",
    "Manchester United": "t1",
    "Newcastle United": "t4",
    "Nottingham Forest": "t17",
    "Sheffield United": "t49",
    "Southampton": "t20",
    "Sunderland": "t56",
    "Tottenham Hotspur": "t6",
    "Watford": "t57",
    "West Ham United": "t21",
    "Wolverhampton Wanderers": "t39",
}


def get_banter(sorted_players):
    """Generate a random bit of 'banter' based on game state.
    Args:
        sorted_players: List of player names sorted by score (0=First, -1=Last).
    """
    if not sorted_players:
        return "Not enough players for banter yet."

    r = random.random()
    try:
        if r < 0.4:
            # Leader banter
            return random.choice(BANTER_PHRASES["leader"]).format(*sorted_players)
        elif r < 0.8:
            # Loser banter
            return random.choice(BANTER_PHRASES["loser"]).format(*sorted_players)
        else:
            # Generic/Mid-table banter
            phrase = random.choice(BANTER_PHRASES["generic"])
            
            # If the phrase has no placeholders, just return it
            if "{" not in phrase:
                return phrase
                
            # If it has placeholders like {3} (specific rank), format with all players
            return phrase.format(*sorted_players)
    except IndexError:
        # Fallback if a phrase references {5} but there are fewer players
        return "The banter generator is confused. Just like VAR."


# Set page config
st.set_page_config(
    page_title=f"Bottoms Sweepstake {SEASON_LABEL} Season",
    page_icon="⚽",
    layout="wide",
)

# Title and description
st.title("⚽ Bottoms Sweepstake")
st.subheader(f"Premier League {SEASON_LABEL} Season")

# --- CSS Injection for Funky Animations ---
st.markdown(
    """
    <style>
    /* Spin Effect on Hover for Headshots */
    .headshot-img:hover {
        animation: spin 1s infinite linear;
        cursor: pointer;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* Pulsating Border for Leader */
    .leader-card {
        border: 2px solid #FFD700 !important;
        box-shadow: 0 0 10px #FFD700;
        animation: pulse-gold 2s infinite;
    }
    
    @keyframes pulse-gold {
        0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
    }

    /* Shake Effect for Loser */
    .loser-card {
        border: 2px solid #ff4b4b !important;
        background-color: rgba(255, 75, 75, 0.1) !important;
    }
    
    .loser-card:hover {
        animation: shake 0.5s;
        animation-iteration-count: infinite;
    }

    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        10% { transform: translate(-1px, -2px) rotate(-1deg); }
        20% { transform: translate(-3px, 0px) rotate(1deg); }
        30% { transform: translate(3px, 2px) rotate(0deg); }
        40% { transform: translate(1px, -1px) rotate(1deg); }
        50% { transform: translate(-1px, 2px) rotate(-1deg); }
        60% { transform: translate(-3px, 1px) rotate(0deg); }
        70% { transform: translate(3px, 1px) rotate(-1deg); }
        80% { transform: translate(-1px, -1px) rotate(1deg); }
        90% { transform: translate(1px, 2px) rotate(0deg); }
        100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Controls
col_ctrl1, col_ctrl2 = st.columns([1, 4])
with col_ctrl1:
    if st.button("🔄 Refresh", help="Clear cache and refetch standings"):
        st.cache_data.clear()
        st.rerun()
with col_ctrl2:
    if st.button("🎉 Celebrate Leader"):
        st.balloons()

# Stake and jackpot info
col1, col2 = st.columns(2)
with col1:
    st.info("**Stake:** £5 each")
with col2:
    st.success("**Jackpot:** £25 🤑")


import base64
import os

# --- Helper: image to base64 for dataframe display ---
def get_image_base64(path):
    """Convert a local image file to a base64 data URI."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    # Assume png for simplicity, browser often handles mixed mime types in data uris gracefully enough
    # or detect extension. Let's assume PNG/JPG.
    mime = "image/png"
    if path.lower().endswith(".jpg") or path.lower().endswith(".jpeg"):
        mime = "image/jpeg"
    return f"data:{mime};base64,{encoded}"

# --- Fallback Data ---
# Used if scraping fails
def get_fallback_standings():
    st.warning(
        f"⚠️ Using placeholder fallback data (previous season snapshot). Could not fetch {SEASON_LABEL} live standings yet."
    )
    standings_data = {
        "Position": list(range(1, 21)),
        "Team": [
            "Liverpool", "Arsenal", "Nottingham Forest", "Chelsea",
            "Manchester City", "Newcastle United", "Brighton and Hove Albion", "Fulham",
            "Aston Villa", "Bournemouth", "Brentford", "Crystal Palace",
            "Manchester United", "Tottenham Hotspur", "Everton", "West Ham United",
            "Wolverhampton Wanderers", "Ipswich Town", "Leicester City", "Southampton",
        ],
        "Team_ID": [
            OPTA_ID_MAP.get("Liverpool", "t14"), OPTA_ID_MAP.get("Arsenal", "t3"), OPTA_ID_MAP.get("Nottingham Forest", "t17"), OPTA_ID_MAP.get("Chelsea", "t8"),
            OPTA_ID_MAP.get("Manchester City", "t43"), OPTA_ID_MAP.get("Newcastle United", "t4"), OPTA_ID_MAP.get("Brighton and Hove Albion", "t36"), OPTA_ID_MAP.get("Fulham", "t54"),
            OPTA_ID_MAP.get("Aston Villa", "t7"), OPTA_ID_MAP.get("Bournemouth", "t91"), OPTA_ID_MAP.get("Brentford", "t94"), OPTA_ID_MAP.get("Crystal Palace", "t31"),
            OPTA_ID_MAP.get("Manchester United", "t1"), OPTA_ID_MAP.get("Tottenham Hotspur", "t6"), OPTA_ID_MAP.get("Everton", "t11"), OPTA_ID_MAP.get("West Ham United", "t21"),
            OPTA_ID_MAP.get("Wolverhampton Wanderers", "t39"), "t8", "t13", "t20" # Manual fallback for promoted teams if missing in map
        ], 
        "Points_League": [
            70, 58, 54, 49, 48, 47, 47, 45, 45, 44,
            41, 39, 37, 34, 34, 34, 26, 17, 17, 9
        ],
    }
    df = pd.DataFrame(standings_data)
    # Add points based on position (reverse order: 1st = 20pts, 20th = 1pt)
    df["Points_Value"] = 21 - df["Position"]
    # Generate Crest URLs using the verified IDs
    df["Crest_URL"] = df["Team_ID"].apply(
        lambda x: f"https://resources.premierleague.com/premierleague/badges/50/{x}.png" if x else None
    )
    return df


# --- Helper: get_comp_season_teams ---
@st.cache_data(ttl=1800)
def get_comp_season_teams(comp_id: int) -> list[str]:
    """Return a list of team names registered to a given compSeason id.

    Tries multiple Pulse Live endpoints because structures can vary pre‑season.
    Returns an empty list on failure.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://www.premierleague.com",
        "Referer": "https://www.premierleague.com/tables",
    }

    candidates = [
        f"https://footballapi.pulselive.com/football/competitions/1/compseasons/{comp_id}/teams",
        f"https://footballapi.pulselive.com/football/teams?comps=1&compSeasons={comp_id}",
    ]

    names: set[str] = set()
    for url in candidates:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            js = r.json()

            # Flexible extraction across likely shapes
            items = (
                js.get("teams")
                or js.get("clubs")
                or js.get("content")
                or (js if isinstance(js, list) else [])
            )
            for it in items:
                n = (
                    it.get("name")
                    or (it.get("team") or {}).get("name")
                    or (it.get("club") or {}).get("name")
                    or it.get("displayName")
                )
                if n:
                    names.add(str(n).strip())
        except Exception:
            continue

    return sorted(names)


# --- Helper: normalize compSeason id to an int ---
def _normalize_comp_id(value):
    """Return a clean integer compSeason id from various input types.

    Handles ints, floats (e.g., 777.0), and numeric strings ('777' or '777.0').
    Falls back to the original value if conversion is impossible.
    """
    try:
        # Fast path if already int
        if isinstance(value, int):
            return value
        # Handle floats and numpy types
        if isinstance(value, float):
            return int(round(value))
        # Handle strings like '777.0' or ' 777 '
        s = str(value).strip()
        try:
            # If it parses as float, coerce to int
            f = float(s)
            return int(round(f))
        except Exception:
            return int(s)
    except Exception:
        return value


def season_start_year_from_label(label: str) -> int | None:
    """Parse a season label like '2025/26' into its start year (e.g., 2025)."""
    try:
        return int(str(label).strip().split("/")[0])
    except Exception:
        return None


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
    # --- Insert: try to parse the requested start year for special matching ---
    requested_start_year = season_start_year_from_label(season_label)

    seasons_url = (
        "https://footballapi.pulselive.com/football/competitions/1/compseasons"
    )
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
        # Use multiple endpoints and explicit pagination; some responses are paginated or use 'content'
        season_sources = [
            "https://footballapi.pulselive.com/football/competitions/1/compseasons?page=0&pageSize=120",
            "https://footballapi.pulselive.com/football/compseasons?comps=1&page=0&pageSize=120",
            seasons_url,  # fallback (may be unpaginated)
        ]

        seasons_list = []
        for url in season_sources:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200:
                    continue
                js = r.json()
                items = (
                    js.get("compSeasons")
                    or js.get("seasons")
                    or js.get("content")
                    or (js if isinstance(js, list) else [])
                )
                # Ensure list
                if isinstance(items, dict):
                    items = [items]
                seasons_list.extend(items)
            except Exception:
                continue

        comp_id = None
        fallback_current = None
        latest_id = None
        latest_start = None
        # --- Insert: track compSeason id matching the requested start year ---
        comp_id_start_year = None

        for s in seasons_list:
            label = s.get("label") or s.get("competition", {}).get("label")
            sid_raw = s.get("id") or (s.get("compSeason") or {}).get("id")
            sid = _normalize_comp_id(sid_raw)
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

            # Prefer explicit start-year match if label match is unavailable
            if requested_start_year and start:
                try:
                    ts2 = start.replace("Z", "").replace("T", " ")
                    dt2 = datetime.fromisoformat(ts2)
                    if dt2.year == requested_start_year and comp_id_start_year is None:
                        comp_id_start_year = sid
                except Exception:
                    pass

        if not comp_id:
            # Try the start-year match for upcoming seasons
            comp_id = comp_id_start_year or fallback_current or latest_id

        # Normalize comp_id to an integer (avoid '777.0' which causes 400s)
        comp_id = _normalize_comp_id(comp_id)

        if not comp_id:
            st.error("Could not resolve a Premier League compSeason id.")
            return get_fallback_standings()

        # Fetch standings for the resolved compSeason id
        comp_id_str = str(_normalize_comp_id(comp_id))
        standings_url = (
            f"https://footballapi.pulselive.com/football/standings?compSeasons={comp_id_str}"
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
        ids: list[str] = []  # Store team IDs (Opta Strings)
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

            # Map correct ID from hardcoded map first, falling back to API response (looking for 'opta' id)
            clean_name = str(team_name).strip()
            # Try exact match or match stripping 'FC' etc if needed (usually exact works with Pulse Live names)
            mapped_id = OPTA_ID_MAP.get(clean_name)
            
            if mapped_id:
                ids.append(mapped_id)
            else:
                 # Extract Opta ID from API response if not in map
                opta_id = (e.get("team") or {}).get("altIds", {}).get("opta")
                # Fallback to hardcoded generic or Pulse ID extraction if absolutely necessary, but Opta usually exists
                if not opta_id:
                     # Try finding 'club'
                     opta_id = (e.get("club") or {}).get("altIds", {}).get("opta")
                
                ids.append(str(opta_id) if opta_id else "t0")

            # Extract points (usually in 'overall' -> 'points')
            points = 0
            if "overall" in e and "points" in e["overall"]:
                points = e["overall"]["points"]
            elif "points" in e:
                points = e["points"]
            
            try:
                points_league.append(int(points))
            except Exception:
                # Early-season/empty table case: default to zero
                points_league.append(0)

        if not positions:
            # Pre‑season: standings can be empty even though the compSeason exists.
            team_names = get_comp_season_teams(comp_id)
            if team_names:
                df = pd.DataFrame(
                    {
                        "Position": [0] * len(team_names),
                        "Team": team_names,
                        "Points_League": [0] * len(team_names),
                    }
                )
                df["Points_Value"] = 0
                st.info(
                    f"📅 {season_label} pre‑season: teams loaded; league table will populate once matches are played."
                )
                return df

            st.warning(
                f"No league entries returned for {season_label}, and no team list available; showing fallback."
            )
            return get_fallback_standings()

        df = pd.DataFrame(
            {"Position": positions, "Team": teams, "Team_ID": ids, "Points_League": points_league}
        )
        # Generate Crest URLs
        df["Crest_URL"] = df["Team_ID"].apply(
            lambda x: f"https://resources.premierleague.com/premierleague/badges/50/{x}.png" if x and x != "t0" else None
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
def get_player_picks():
    return pd.DataFrame(
        {
            "Player": [
                "Vosey",
                "Vosey",
                "Dom",
                "Dom",
                "Chris",
                "Chris",
                "Sam",
                "Sam",
                "Adam",
                "Adam",
                "Sean",
                "Sean",
            ],
            "Team": [
                "Bournemouth",
                "Leeds United",
                "Brentford",
                "Sunderland",
                "Wolverhampton Wanderers",
                "Fulham",
                "Burnley",
                "Tottenham Hotspur",
                "West Ham United",
                "Manchester United",
                "Everton",
                "Crystal Palace",
            ],
        }
    )


# Get standings data (tries scraping, falls back to static)
standings_df = get_premier_league_standings()

picks_df = get_player_picks()

if standings_df is None or standings_df.empty:
    st.error("🚨 Critical Error: Could not load league standings data. Aborting.")
    st.stop()

# --- Data Processing and Display (largely unchanged from original) ---

# Merge with standings to get points
# Add validation to handle cases where a picked team might not be in the scraped standings (e.g., mid-season)
merged_df = pd.merge(picks_df, standings_df, on="Team", how="left")

# Handle potential missing teams after merge (if scraping failed partially or team names mismatch)
missing_teams = merged_df[merged_df["Position"].isna()]
if not missing_teams.empty:
    st.warning("Could not find standings data for the following teams:")
    st.dataframe(missing_teams[["Player", "Team"]], hide_index=True)
    # Decide how to handle points for missing teams: assign 0 or handle differently
    merged_df["Points_Value"] = merged_df["Points_Value"].fillna(
        0
    )  # Assign 0 points if team not found
    merged_df["Position"] = merged_df["Position"].fillna(0)  # Assign 0 position
    merged_df["Points_League"] = merged_df["Points_League"].fillna(
        0
    )  # Assign 0 league points

# --- Ensure numeric, finite values to keep charts happy ---
for col in ["Points_Value", "Points_League", "Position"]:
    merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")
merged_df.replace([np.inf, -np.inf], np.nan, inplace=True)
merged_df[["Points_Value", "Points_League", "Position"]] = merged_df[
    ["Points_Value", "Points_League", "Position"]
].fillna(0)


# Calculate total points per player
player_totals = merged_df.groupby("Player")["Points_Value"].sum().reset_index()
player_totals = player_totals.sort_values("Points_Value", ascending=False)

# Display last update time
current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
st.caption(f"Last updated: {current_time}")

# Add a toggle for advanced details
with st.expander("Points Assignment & Current Standings"):
    st.write(
        """
    Each team's position in the Premier League table determines its sweepstake points value:
    - 1st place: 20 points
    - 2nd place: 19 points
    - 3rd place: 18 points
    - ...and so on down to...
    - 20th place: 1 point
    
    Each player's total is the sum of sweepstake points from their two team picks. Higher sweepstake points are better.
    """
    )

    # Show the current standings table based on fetched/fallback data
    st.subheader("Current Premier League Standings")
    display_standings = standings_df[
        ["Position", "Crest_URL", "Team", "Points_League", "Points_Value"]
    ].rename(
        columns={
            "Crest_URL": "",
            "Points_Value": "Sweepstake Points Worth",
            "Points_League": "League Points",
        }
    )
    st.dataframe(
        display_standings.sort_values("Position"),  # Ensure sorted by position
        column_config={
            "Position": st.column_config.NumberColumn(format="%d"),
            "": st.column_config.ImageColumn(width="small"),
            "Team": "Team",
            "League Points": st.column_config.NumberColumn(format="%d pts"),
            "Sweepstake Points Worth": st.column_config.NumberColumn(format="%d pts"),
        },
        hide_index=True,
        use_container_width=True,
    )

# --- Player Profile / Headshot Upload ---
with st.sidebar:
    st.header("👤 Player Profile")
    players_list = sorted(picks_df["Player"].unique())
    selected_player = st.selectbox("Select Player to Edit", players_list)
    
    st.caption("Upload a new headshot:")
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])
    
    headshot_dir = "assets/headshots"
    os.makedirs(headshot_dir, exist_ok=True)
    
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1]
        if not file_ext:
            file_ext = ".png" # default
            
        # Sanitize filename: use player name
        # e.g. "assets/headshots/Adam.png"
        target_filename = f"{selected_player}{file_ext}"
        target_path = os.path.join(headshot_dir, target_filename)
        
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Headshot updated for {selected_player}!")
        st.cache_data.clear() # Clear cache to potentially reload visuals if they depended on cached data
        # time.sleep(1) # requires import time; skip or just rerun
        st.rerun()

# --- Helper to get headshot URL/Base64 for a player ---
def get_player_headshot(player_name):
    # Check for png/jpg/jpeg
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join("assets/headshots", f"{player_name}{ext}")
        if os.path.exists(path):
            return get_image_base64(path)
    # Return a default placeholder (online or local?)
    # Using a generic placeholder URL
    return "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"


# Display player picks and points
st.header("Player Team Selections")

# Determine Leader and Loser first for styling
temp_totals = merged_df.groupby("Player")["Points_Value"].sum().sort_values(ascending=False)
if not temp_totals.empty:
    current_leader = temp_totals.index[0]
    current_loser = temp_totals.index[-1]
    
    # Display Banter Message
    # Pass the entire sorted list of player names to the banter generator
    banter_msg = get_banter(temp_totals.index.tolist())
    st.info(f"📢 **BanterBot:** {banter_msg}")
else:
    current_leader = None
    current_loser = None

cols = st.columns(len(picks_df["Player"].unique()))  # Dynamically create columns
players = sorted(picks_df["Player"].unique())

for i, player in enumerate(players):
    with cols[i]:
        # Header with Headshot
        headshot_src = get_player_headshot(player)
        
        # Styles for Headshot
        img_class = "headshot-img"
        extra_badges = ""
        
        if player == current_leader:
            extra_badges = "👑"
        elif player == current_loser:
            extra_badges = "🥄"

        # Use HTML for the circular headshot + name combo
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="{headshot_src}" class="{img_class}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd;">
                <h3>{player} {extra_badges}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        player_data = merged_df[merged_df["Player"] == player]
        # Recalculate total points here to ensure consistency after potential fillna
        total_points = player_data["Points_Value"].sum()

        # Styles for the Card Container
        card_class = ""
        if player == current_leader:
            card_class = "leader-card"
        elif player == current_loser:
            card_class = "loser-card"

        for _, row in player_data.iterrows():
            team = row["Team"]
            position = row["Position"]
            points = row["Points_Value"]
            league_points = row["Points_League"]
            crest = row.get("Crest_URL")

            # Format position nicely, handle potential 0 from fillna
            pos_display = f"{int(position)}" if position > 0 else "N/A"

            # Calculate background color based on points (higher = better)
            # Handle potential 0 points from fillna
            intensity = int(min(255, 100 + (points / 20) * 155)) if points > 0 else 100
            bg_color = (
                f"rgba(0, {intensity}, 0, 0.2)"
                if points > 0
                else "rgba(128, 128, 128, 0.1)"
            )  # Grey if N/A
            
            # Crest image tag
            crest_html = f'<img src="{crest}" width="24" style="vertical-align: middle; margin-right: 5px;">' if crest else ''

            st.markdown(
                f"""
                <div class="{card_class}" style="padding: 10px; margin-bottom: 10px; background-color: {bg_color}; border-radius: 5px;">
                    <div style="font-weight: bold; font-size: 1.1em;">{crest_html}{team}</div>
                    Position: {pos_display}<br>
                    Sweepstake Points: {int(points)}<br>
                    League Points: {int(league_points)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(f"<div style='text-align: center; font-weight: bold;'>Total: {int(total_points)} points</div>", unsafe_allow_html=True)


# Display leaderboard
st.header("Sweepstake Leaderboard")

# Clean and guard data for chart rendering
player_totals["Points_Value"] = pd.to_numeric(
    player_totals["Points_Value"], errors="coerce"
)
player_totals.replace([np.inf, -np.inf], np.nan, inplace=True)
player_totals["Points_Value"] = player_totals["Points_Value"].fillna(0)

# Skip chart if there's nothing to plot (prevents Vega-Lite Infinity warnings)
if player_totals.empty or player_totals["Points_Value"].isna().all():
    st.info("No leaderboard data to plot yet.")
else:
    # Create horizontal bar chart with Altair
    chart = (
        alt.Chart(player_totals)
        .mark_bar()
        .encode(
            x=alt.X("Points_Value:Q", title="Total Sweepstake Points"),
            y=alt.Y("Player:N", title="Player", sort="-x"),
            color=alt.Color(
                "Points_Value:Q", scale=alt.Scale(scheme="blues"), legend=None
            ),
            tooltip=["Player", alt.Tooltip("Points_Value:Q", title="Points")],
        )
        .properties(
            title="Player Rankings",
            height=alt.Step(40),  # Adjust height based on number of players
        )
    )

    # Force a domain if all zeros to avoid Vega "Infinite extent" warnings
    if player_totals["Points_Value"].max() == 0:
        chart = chart.encode(
            x=alt.X(
                "Points_Value:Q",
                title="Total Sweepstake Points",
                scale=alt.Scale(domain=[0, 1]),
            )
        )

    st.altair_chart(chart, use_container_width=True)

# Create a leaderboard table
st.subheader("Current Standings")
leaderboard_df = player_totals.copy()

# Add Headshots
leaderboard_df["Headshot"] = leaderboard_df["Player"].apply(get_player_headshot)

# Handle ties in rank
leaderboard_df["Rank"] = (
    leaderboard_df["Points_Value"].rank(method="min", ascending=False).astype(int)
)
leaderboard_df = leaderboard_df.sort_values("Rank")
leaderboard_df = leaderboard_df[["Rank", "Headshot", "Player", "Points_Value"]]
leaderboard_df.rename(columns={"Points_Value": "Total Points", "Headshot": ""}, inplace=True)

st.dataframe(
    leaderboard_df,
    column_config={
        "Rank": st.column_config.NumberColumn(format="%d"),
        "": st.column_config.ImageColumn(width="small"),
        "Player": "Player",
        "Total Points": st.column_config.NumberColumn(format="%d"),
    },
    hide_index=True,
    use_container_width=True,
)

# Highlight leaders
if not player_totals.empty:
    max_points = player_totals["Points_Value"].max()
    leaders = player_totals[player_totals["Points_Value"] == max_points][
        "Player"
    ].tolist()
    leaders_text = " and ".join(leaders)
    st.write(
        f"### 🏆 Current Leader{'s' if len(leaders) > 1 else ''}: {leaders_text} ({int(max_points)} points)"
    )
else:
    st.write("Leaderboard data is currently unavailable.")


# Add what-if scenario option
st.header("What-If Scenario Builder")
st.write(
    "See how the standings would change if teams moved positions (based on currently loaded standings)"
)

# Create columns for team movement
team_columns = st.columns(2)

# Get player teams from the picks dataframe
player_teams = sorted(picks_df["Team"].unique())

# Store modified positions
modified_positions = {}
current_positions_map = pd.Series(
    standings_df.Position.values, index=standings_df.Team
).to_dict()

# Chunk teams for columns
num_teams = len(player_teams)
mid_point = (num_teams + 1) // 2  # Split roughly in half

# First column of teams
with team_columns[0]:
    st.subheader("Teams (Part 1)")
    for i, team in enumerate(player_teams[:mid_point]):
        # Get current position from the *loaded* standings_df, default to 20 if not found (minimal points)
        current_pos = current_positions_map.get(team, 20)
        modified_positions[team] = st.number_input(
            f"{team} new position:",
            min_value=1,
            max_value=20,
            value=int(current_pos),  # Ensure value is int
            key=f"pos_{team}",
            step=1,
        )

# Second column of teams
with team_columns[1]:
    st.subheader("Teams (Part 2)")
    for i, team in enumerate(player_teams[mid_point:]):
        current_pos = current_positions_map.get(team, 20)
        modified_positions[team] = st.number_input(
            f"{team} new position:",
            min_value=1,
            max_value=20,
            value=int(current_pos),  # Ensure value is int
            key=f"pos_{team}",
            step=1,
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
            conflict_messages.append(
                f"Position {pos} assigned to {count} teams: {', '.join(teams_at_pos)}"
            )

        st.error(f"⚠️ Position conflicts detected:\n" + "\n".join(conflict_messages))
        st.warning(
            "Please ensure each position is assigned to only one selected team in the builder."
        )
    else:
        # Create a new dataframe based on the *currently loaded* standings
        new_standings = standings_df.copy()

        # Update positions only for the teams included in the builder
        for team, new_pos in modified_positions.items():
            if team in new_standings["Team"].values:
                new_standings.loc[new_standings["Team"] == team, "Position"] = new_pos
            else:
                st.warning(
                    f"Team '{team}' selected in 'What-If' not found in current standings, ignoring."
                )

        st.subheader("Hypothetical Player Scores (What-If)")
        st.caption(
            "Calculated based ONLY on the new positions entered above. Other teams' positions are assumed unchanged for this calculation."
        )

        # Recalculate points values based on *hypothetical* positions
        hypothetical_points = {
            team: 21 - pos for team, pos in modified_positions.items()
        }

        # Calculate new player totals based on these hypothetical points
        new_player_totals_list = []
        for player in picks_df["Player"].unique():
            player_teams_list = picks_df[picks_df["Player"] == player]["Team"].tolist()
            new_total = 0
            for team in player_teams_list:
                # Use the hypothetical point value if the team was modified
                if team in hypothetical_points:
                    new_total += hypothetical_points[team]
                # Otherwise, use the original point value from the loaded standings
                elif team in merged_df["Team"].values:
                    # Get original points value for teams not in the what-if builder
                    original_points = merged_df.loc[
                        merged_df["Team"] == team, "Points_Value"
                    ].iloc[0]
                    new_total += original_points
                else:
                    new_total += 0  # Team not found in original merge either

            new_player_totals_list.append({"Player": player, "Points_Value": new_total})

        new_player_totals = pd.DataFrame(new_player_totals_list)
        new_player_totals = new_player_totals.sort_values(
            "Points_Value", ascending=False
        )

        # Add Headshots to Hypothetical Leaderboard
        new_player_totals["Headshot"] = new_player_totals["Player"].apply(get_player_headshot)
        
        # Clean and guard data for chart rendering
        new_player_totals["Points_Value"] = pd.to_numeric(
            new_player_totals["Points_Value"], errors="coerce"
        )
        new_player_totals.replace([np.inf, -np.inf], np.nan, inplace=True)
        new_player_totals["Points_Value"] = new_player_totals["Points_Value"].fillna(0)

        if new_player_totals.empty or new_player_totals["Points_Value"].isna().all():
            st.info("No hypothetical data to plot.")
        else:
            # Display new leaderboard chart
            new_chart = (
                alt.Chart(new_player_totals)
                .mark_bar()
                .encode(
                    x=alt.X("Points_Value:Q", title="Total Points (Hypothetical)"),
                    y=alt.Y("Player:N", title="Player", sort="-x"),
                    color=alt.Color(
                        "Points_Value:Q", scale=alt.Scale(scheme="greens"), legend=None
                    ),
                    tooltip=["Player", alt.Tooltip("Points_Value:Q", title="Points")],
                )
                .properties(title="Hypothetical Player Rankings", height=alt.Step(40))
            )

            # Force a domain if all zeros to avoid Vega "Infinite extent" warnings
            if new_player_totals["Points_Value"].max() == 0:
                new_chart = new_chart.encode(
                    x=alt.X(
                        "Points_Value:Q",
                        title="Total Points (Hypothetical)",
                        scale=alt.Scale(domain=[0, 1]),
                    )
                )

            st.altair_chart(new_chart, use_container_width=True)

        # Display new leaderboard table
        new_leaderboard_df = new_player_totals.copy()
        new_leaderboard_df["Rank"] = (
            new_leaderboard_df["Points_Value"]
            .rank(method="min", ascending=False)
            .astype(int)
        )
        new_leaderboard_df = new_leaderboard_df.sort_values("Rank")
        new_leaderboard_df = new_leaderboard_df[["Rank", "Headshot", "Player", "Points_Value"]]
        new_leaderboard_df.rename(
            columns={"Points_Value": "Total Points", "Headshot": ""}, inplace=True
        )

        st.dataframe(
            new_leaderboard_df,
            column_config={
                "Rank": st.column_config.NumberColumn(format="%d"),
                "": st.column_config.ImageColumn(width="small"),
                "Player": "Player",
                "Total Points": st.column_config.NumberColumn(format="%d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Highlight new leaders
        if not new_player_totals.empty:
            new_max_points = new_player_totals["Points_Value"].max()
            new_leaders = new_player_totals[
                new_player_totals["Points_Value"] == new_max_points
            ]["Player"].tolist()
            new_leaders_text = " and ".join(new_leaders)
            st.write(
                f"### 🏆 Hypothetical Leader{'s' if len(new_leaders) > 1 else ''}: {new_leaders_text} ({int(new_max_points)} points)"
            )
        else:
            st.write("Hypothetical leaderboard data is currently unavailable.")


# Add a footer
st.markdown("---")
st.caption(
    f"Bottoms Sweepstake {SEASON_LABEL} Season | Made with Streamlit | Data via premierleague.com | Last updated: {current_time}"
)
