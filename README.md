# Premier League Bottoms Sweepstake

A Streamlit application for tracking a Premier League "Bottoms Sweepstake" for the 24/25 season.

## About the Sweepstake

A friendly competition with the following rules:
- 6 Participants: Vosey, Dom, Chris, Sam, Adam, Sean.
- Each player is assigned two teams (see below).
- **Scoring:** Points are awarded based on the *inverse* of the final Premier League position. The team finishing 1st gets 20 points, 2nd gets 19 points, ..., down to 20th place getting 1 point.
- Each player's score is the sum of the points from their two assigned teams.
- The player with the **most points** at the end of the season wins the £25 jackpot! 🤑

## Features

- **Live Standings Tracker**: Fetches current Premier League standings from the Pulse Live API (used by premierleague.com) and calculates player scores based on the inverse position points system. Includes fallback static data if fetching fails.
- **Visual Leaderboard**: Interactive bar chart showing player rankings based on their current total points.
- **Team Selection Cards**: Visual display of each player's team picks with current league position, league points, and calculated sweepstake points.
- **What-If Scenario Builder**: Simulate how changing the positions of the selected teams would affect the *sweepstake points* and the overall leaderboard (note: this only recalculates points for the selected teams, it doesn't simulate the full league table).
- **Responsive Design**: Works on desktop and mobile devices.

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/yourusername/bottoms-sweepstake.git # Replace with your actual repo URL
    cd bottoms-sweepstake
    ```

2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    streamlit run bottoms_sweepstake.py
    ```

4.  Open your web browser and navigate to the local URL provided by Streamlit (usually http://localhost:8501).

## Current Player Selections

| Player | Team Picks                      |
| :----- | :------------------------------ |
| Vosey  | Bournemouth, Leeds United       |
| Dom    | Brentford, Sunderland           |
| Chris  | Wolverhampton Wanderers, Fulham |
| Sam    | Burnley, Tottenham Hotspur      |
| Adam   | West Ham United, Manchester United |
| Sean   | Everton, Crystal Palace         |

*Note: Team names must match the official long names used by the data source for correct data merging.*

## Data Source

The application attempts to fetch live league standings from the Pulse Live API (`footballapi.pulselive.com`), which powers the official Premier League website.

**Disclaimer:** This relies on public API endpoints. If the API structure changes, the fetching function may break. The application includes fallback static data, but for live updates, the API connection must be working.

## Customization

### Modifying Player Picks

Edit the `get_player_picks()` function in `bottoms_sweepstake.py`. **Ensure team names exactly match the long names found on premierleague.com.**

```python
def get_player_picks():
    return pd.DataFrame({
        "Player": ["Vosey", "Vosey", "Dom", "Dom", ...],
        "Team": ["Bournemouth", "Leeds United", "Brentford", "Sunderland", ...]
    })
```