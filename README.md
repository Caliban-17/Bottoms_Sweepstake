# Premier League Bottoms Sweepstake

A Streamlit application for tracking a Premier League "Bottoms Sweepstake" for the 24/25 season.

## About the Sweepstake

A friendly competition with the following rules:
- 5 Participants: Sean, Dom, Harry, Chris, Adam.
- Each player is assigned two teams (see below).
- **Scoring:** Points are awarded based on the *inverse* of the final Premier League position. The team finishing 1st gets 20 points, 2nd gets 19 points, ..., down to 20th place getting 1 point.
- Each player's score is the sum of the points from their two assigned teams.
- The player with the **most points** at the end of the season wins the £25 jackpot! 🤑

## Features

- **Live Standings Tracker**: Fetches current Premier League standings from premierleague.com (with a 30-minute cache) and calculates player scores based on the inverse position points system. Includes fallback static data if scraping fails.
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
| Sean   | Fulham, Everton                 |
| Dom    | Bournemouth, Ipswich Town       |
| Harry  | Nottingham Forest, Wolverhampton Wanderers |
| Chris  | Brentford, Leicester City         |
| Adam   | Brighton & Hove Albion, Southampton |

*Note: Team names must match the official long names used on premierleague.com for correct data merging.*

## Data Source

The application attempts to scrape live league standings from `https://www.premierleague.com/tables`.

**Disclaimer:** Web scraping relies on the structure of the source website. If the Premier League website changes its HTML layout, the scraping function may break. The application includes fallback static data from April 2025, but for truly live data, the scraping function needs to work.

## Customization

### Modifying Player Picks

Edit the `get_player_picks()` function in `bottoms_sweepstake.py`. **Ensure team names exactly match the long names found on premierleague.com.**

```python
def get_player_picks():
    return pd.DataFrame({
        "Player": ["Sean", "Sean", "Dom", "Dom", "Harry", "Harry", "Chris", "Chris", "Adam", "Adam"],
        "Team": ["Fulham", "Everton", "Bournemouth", "Ipswich Town",
                 "Nottingham Forest", "Wolverhampton Wanderers",
                 "Brentford", "Leicester City",
                 "Brighton & Hove Albion", "Southampton"]
    })