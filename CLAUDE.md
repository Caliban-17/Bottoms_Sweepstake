# CLAUDE.md - Bottoms Sweepstake Codebase Guide

## Project Overview

**Premier League Bottoms Sweepstake** is a Streamlit web application that tracks a friendly competition based on Premier League team standings. The scoring system is inverse - teams finishing lower in the league table earn more sweepstake points (1st place = 20 points, 20th place = 1 point).

- **Primary File**: `bottoms_sweepstake.py` (690 lines)
- **Framework**: Streamlit
- **Current Season**: 2025/26 (configured via `SEASON_LABEL` constant)
- **Live Deployment**: Runs locally via `streamlit run bottoms_sweepstake.py`

## Codebase Structure

```
Bottoms_Sweepstake/
├── bottoms_sweepstake.py    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # User-facing documentation
└── CLAUDE.md                 # This file - AI assistant guide
```

## Core Dependencies

```
streamlit>=1.21.0           # Web application framework
pandas>=1.3.0               # Data manipulation
altair>=4.2.0               # Visualization library
requests>=2.27.0            # HTTP requests
beautifulsoup4>=4.10.0      # HTML parsing (legacy, minimal use)
```

## Architecture Overview

### Data Flow

```
Premier League API → get_premier_league_standings() → standings_df
                          ↓ (on failure)
                   get_fallback_standings()
                          ↓
Player Picks (get_player_picks()) → merged_df
                          ↓
              Leaderboard Calculations
                          ↓
              Streamlit UI Rendering
```

### Key Components

1. **Data Fetching Layer** (lines 38-356)
   - Primary: `get_premier_league_standings()` - Fetches live data from footballapi.pulselive.com
   - Fallback: `get_fallback_standings()` - Static snapshot data
   - Helper: `get_comp_season_teams()` - Retrieves team list for pre-season
   - Helper: `_normalize_comp_id()` - Normalizes compSeason IDs to integers

2. **Configuration Layer** (lines 358-368)
   - `get_player_picks()` - Defines player-to-team assignments
   - `SEASON_LABEL` - Global constant for current season

3. **UI Layer** (lines 370-690)
   - Leaderboard display
   - Player team cards
   - What-if scenario builder
   - Charts and visualizations

## Critical Constants & Configuration

### Season Configuration
```python
SEASON_LABEL = "2025/26"  # Line 11 - UPDATE THIS FOR NEW SEASONS
```

### Current Player Assignments (lines 360-368)
```python
def get_player_picks():
    return pd.DataFrame({
        "Player": ["Vosey", "Vosey", "Dom", "Dom", "Chris", "Chris",
                   "Sam", "Sam", "Adam", "Adam", "Sean", "Sean"],
        "Team": ["Bournemouth", "Leeds United",
                 "Brentford", "Sunderland",
                 "Wolverhampton Wanderers", "Fulham",
                 "Burnley", "Tottenham Hotspur",
                 "West Ham United", "Manchester United",
                 "Everton", "Crystal Palace"]
    })
```

**CRITICAL**: Team names MUST match the official Premier League API names exactly. Common variations that cause issues:
- "Brighton" vs "Brighton and Hove Albion"
- "Wolves" vs "Wolverhampton Wanderers"
- "Spurs" vs "Tottenham Hotspur"

### Scoring System
- **Inverse Position**: `Points_Value = 21 - Position`
- 1st place = 20 points
- 2nd place = 19 points
- ...
- 20th place = 1 point

### Caching Strategy
```python
@st.cache_data(ttl=1800)  # 30-minute cache
```
- Reduces API calls
- Can be manually cleared via "Refresh live data" button

## API Integration

### Premier League Data API

**Base URL**: `https://footballapi.pulselive.com/football/`

**Key Endpoints**:
1. **Competitions/Seasons**:
   - `/competitions/1/compseasons`
   - Returns list of Premier League seasons with IDs

2. **Standings**:
   - `/standings?compSeasons={comp_id}&altIds=true&detail=2`
   - Returns current league table

3. **Teams**:
   - `/competitions/1/compseasons/{comp_id}/teams`
   - Returns team list (useful pre-season)

**Headers Required**:
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Accept": "application/json",
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/tables",
}
```

### Season ID Resolution Logic (lines 176-251)

The function attempts multiple strategies to resolve the correct `compSeason` ID:
1. **Exact label match**: Matches `SEASON_LABEL` to API response `label` field
2. **Start year match**: Parses year from label (e.g., "2025" from "2025/26") and matches `startDate`
3. **Current season**: Falls back to season marked `isCurrent: true`
4. **Latest season**: Falls back to most recent `startDate`

**Why this matters**: Pre-season, the API may not have labeled the upcoming season yet, so start-year matching is essential.

### Data Validation & Error Handling

The application has robust error handling:

```python
# Handle missing teams after merge (lines 386-393)
missing_teams = merged_df[merged_df['Position'].isna()]
if not missing_teams.empty:
    st.warning("Could not find standings data for the following teams:")
    merged_df['Points_Value'].fillna(0, inplace=True)

# Clean infinite/NaN values (lines 395-401)
for col in ["Points_Value", "Points_League", "Position"]:
    merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")
merged_df.replace([np.inf, -np.inf], np.nan, inplace=True)
merged_df[["Points_Value", "Points_League", "Position"]] = (
    merged_df[["Points_Value", "Points_League", "Position"]].fillna(0)
)
```

## Common Development Tasks

### 1. Starting a New Season

**Steps**:
1. Update `SEASON_LABEL` (line 11)
2. Update player picks in `get_player_picks()` (lines 359-368)
3. Verify team names match Premier League API
4. Test data fetching
5. Update fallback data in `get_fallback_standings()` (lines 38-54) once season starts

**Example**:
```python
SEASON_LABEL = "2026/27"  # Line 11

def get_player_picks():
    return pd.DataFrame({
        "Player": ["Player1", "Player1", "Player2", "Player2", ...],
        "Team": ["Team1", "Team2", "Team3", "Team4", ...]
    })
```

### 2. Adding a New Player

Simply add two rows to the DataFrame in `get_player_picks()`:
```python
"Player": [..., "NewPlayer", "NewPlayer"],
"Team": [..., "First Team", "Second Team"]
```

The UI will automatically create a new column for them.

### 3. Debugging Data Fetching Issues

**Check the following**:
1. API endpoint availability (test in browser/Postman)
2. Season ID resolution (look for season in `/compseasons` response)
3. Team name mismatches (compare API response to `get_player_picks()`)
4. Network errors (check Streamlit error messages)

**Debug mode**: Add print statements or use Streamlit's error display:
```python
st.write("Debug - comp_id:", comp_id)
st.write("Debug - standings response:", data)
```

### 4. Updating Fallback Data

When the season has progressed, update static data:
1. Run the app successfully with live data
2. Copy `standings_df` data from a working fetch
3. Update the dictionary in `get_fallback_standings()` (lines 40-49)

### 5. Modifying the Scoring System

Current system: `df["Points_Value"] = 21 - df["Position"]`

To change (e.g., exponential scoring):
```python
# Find all instances of scoring calculation:
# Line 53: df["Points_Value"] = 21 - df["Position"]
# Line 346: df["Points_Value"] = 21 - df["Position"]
# Line 617: hypothetical_points = {team: 21 - pos for team, pos in modified_positions.items()}

# Replace with your formula:
df["Points_Value"] = some_new_formula(df["Position"])
```

### 6. Styling and UI Changes

- **Colors**: Adjust in Altair charts (lines 496-506, 650-658) using `scale=alt.Scale(scheme='...')`
- **Layout**: Modify `st.columns()` calls (lines 30, 444, 543)
- **Cards**: Edit HTML in `st.markdown()` blocks (lines 468-478)

## What-If Scenario Builder (lines 538-686)

Allows users to simulate position changes and see hypothetical standings.

**How it works**:
1. Displays number inputs for each team's position
2. Validates no position conflicts among selected teams
3. Recalculates sweepstake points: `hypothetical_points = {team: 21 - pos for team, pos in modified_positions.items()}`
4. Merges with unchanged teams' original points
5. Displays new leaderboard

**Key logic** (lines 619-636):
```python
for player in picks_df['Player'].unique():
    player_teams_list = picks_df[picks_df['Player'] == player]['Team'].tolist()
    new_total = 0
    for team in player_teams_list:
        if team in hypothetical_points:
            new_total += hypothetical_points[team]  # Use modified position
        elif team in merged_df['Team'].values:
            original_points = merged_df.loc[merged_df['Team'] == team, 'Points_Value'].iloc[0]
            new_total += original_points  # Use original position
```

## Development Workflow

### Local Development
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run application**: `streamlit run bottoms_sweepstake.py`
3. **Access UI**: http://localhost:8501
4. **Auto-reload**: Streamlit watches file changes automatically

### Testing Changes
1. Test with live data (if season active)
2. Test with fallback data (force failure or disable network)
3. Test What-If builder with various scenarios
4. Verify mobile responsiveness
5. Check edge cases (missing teams, ties, pre-season)

### Git Workflow
- **Main branch**: Default production branch
- **Feature branches**: Use `claude/claude-md-{hash}` naming pattern for AI-assisted development
- **Commit strategy**: Clear, descriptive commits
- **Push**: Always to feature branch first, then PR to main

## Troubleshooting Guide

### Issue: "Could not find standings data for the following teams"
**Cause**: Team name mismatch between `get_player_picks()` and API response
**Fix**:
1. Check API response for exact team names
2. Update team names in `get_player_picks()` to match exactly
3. Common errors: "Brighton" should be "Brighton and Hove Albion"

### Issue: "Using placeholder fallback data"
**Causes**:
1. API is down or rate-limiting
2. Season not yet started (no standings data)
3. Network issues
4. Invalid `compSeason` ID

**Fix**:
1. Check API endpoint manually
2. Verify `SEASON_LABEL` matches available seasons
3. For pre-season: Expect this message, app will show teams with 0 points
4. Check network connectivity

### Issue: "Position conflicts detected"
**Cause**: In What-If builder, multiple teams assigned to same position
**Fix**: User error - assign unique positions to each team

### Issue: Charts not rendering / Vega-Lite warnings
**Cause**: Infinite or NaN values in data
**Fix**: Already handled by validation code (lines 395-401, 487-489, 642-644)

### Issue: Cache not clearing
**Fix**: Use "Refresh live data" button or manually call `st.cache_data.clear()`

## Code Conventions

### Naming Conventions
- **DataFrames**: `_df` suffix (e.g., `standings_df`, `picks_df`, `merged_df`)
- **Functions**: snake_case (e.g., `get_player_picks`, `season_start_year_from_label`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `SEASON_LABEL`)
- **Streamlit columns**: `col1`, `col2` or descriptive names

### Data Column Names
- `Position`: League position (1-20)
- `Team`: Full official team name
- `Points_League`: Actual Premier League points
- `Points_Value`: Sweepstake points (inverse position)
- `Player`: Player name

### Function Organization
1. **Utility functions** (lines 58-141): API helpers, ID normalization
2. **Data fetching** (lines 143-356): Main data pipeline
3. **Configuration** (lines 358-368): Player picks
4. **UI rendering** (lines 370-690): Streamlit components

### Comments Style
- Docstrings for complex functions (see `get_premier_league_standings`, lines 144-161)
- Inline comments for non-obvious logic
- Section dividers with `# ---` (e.g., line 36, 379)

## Performance Considerations

1. **Caching**: 30-minute TTL reduces API calls significantly
2. **Data validation**: Upfront cleaning prevents rendering errors
3. **Fallback data**: Ensures app always renders even when API fails
4. **Lazy computation**: What-If scenarios only calculated on button click

## Security Considerations

- **No authentication**: App is public, no sensitive data
- **API calls**: Uses public Premier League API, no API keys needed
- **User input**: What-If builder validates position ranges (1-20)
- **No data persistence**: All data is ephemeral (session-based)

## Future Enhancement Ideas

- **Historical tracking**: Store results over time, show trends
- **Prediction model**: ML-based position predictions
- **Mobile app**: Native iOS/Android versions
- **Multi-league**: Support other leagues (Championship, La Liga, etc.)
- **Authentication**: Add user accounts, private leagues
- **Notifications**: Email/SMS updates when positions change
- **API integration**: Direct integration with betting APIs for odds

## Testing Strategy

Currently no automated tests. Recommended additions:
1. **Unit tests**: Test scoring calculations, ID normalization
2. **Integration tests**: Mock API responses, test data pipeline
3. **UI tests**: Selenium/Playwright for user interactions
4. **Data validation tests**: Edge cases (missing teams, ties, etc.)

## AI Assistant Guidelines

### When Making Changes

1. **Always read the full file first**: Don't assume structure from partial reads
2. **Preserve data validation**: Don't remove NaN/Inf handling code
3. **Test with both live and fallback data**: Ensure both paths work
4. **Match existing code style**: Follow snake_case, maintain spacing
5. **Update CLAUDE.md**: If you add major features, document them here

### Common Pitfalls to Avoid

1. **Don't break caching**: Maintain `@st.cache_data` decorators
2. **Don't hardcode season data**: Use `SEASON_LABEL` constant
3. **Don't assume API structure**: It can vary (see flexible extraction lines 88-103)
4. **Don't remove error handling**: Users expect app to work even when API fails
5. **Don't create empty commits**: Verify changes before committing

### When Helping Users

1. **Check SEASON_LABEL first**: Often the issue is wrong season
2. **Verify team names**: Most common error is name mismatches
3. **Test API manually**: Use browser/curl to verify endpoints work
4. **Read error messages**: Streamlit displays helpful errors
5. **Check Recent Commits**: See git log for context on recent changes

## Dependencies Deep Dive

### Streamlit
- **Purpose**: Web framework for data apps
- **Key features used**:
  - `st.cache_data`: Caching decorator
  - `st.columns`: Layout
  - `st.dataframe`: Table display
  - `st.altair_chart`: Chart rendering
  - `st.markdown`: HTML rendering

### Pandas
- **Purpose**: Data manipulation
- **Key operations**:
  - DataFrame creation, merging
  - Grouping, aggregation
  - Sorting, filtering

### Altair
- **Purpose**: Declarative visualization
- **Charts used**: Horizontal bar charts for leaderboard

### Requests
- **Purpose**: HTTP client
- **Usage**: Fetch from Premier League API

### BeautifulSoup4
- **Status**: Legacy dependency, minimal use
- **Note**: Could potentially be removed if not used elsewhere

## Contact & Support

For issues or questions:
- Check this CLAUDE.md first
- Review README.md for user-facing info
- Check git commit history for recent changes
- Test with fallback data to isolate API issues

---

**Last Updated**: 2025-11-17
**Maintainer**: AI-assisted development
**Version**: 2025/26 Season
