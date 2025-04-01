# Premier League Bottoms Sweepstake

A Streamlit application for tracking a Premier League "Bottoms Sweepstake" - a friendly competition where participants are only assigned (randomly) teams who to finished in the bottom half of the table the previous season.

## About the Sweepstake

In this sweepstake:
- Each player is assigned two teams from the Premier League
- Points are awarded based on final league position (11th-20th)
- The player with the most points at the end of the season wins the £25 jackpot!

### Scoring System

Points are awarded as follows:
- 11th place: 10 points
- 12th place: 9 points
- 13th place: 8 points
- 14th place: 7 points 
- 15th place: 6 points
- 16th place: 5 points
- 17th place: 4 points
- 18th place: 3 points
- 19th place: 2 points
- 20th place: 1 point

## Features

- **Live Standings Tracker**: View current positions of all teams and calculated player scores
- **Visual Leaderboard**: Interactive bar chart showing player rankings
- **Team Selection Cards**: Visual display of each player's team picks with position and points
- **What-If Scenario Builder**: Simulate league position changes to see how they would affect the sweepstake standings
- **Responsive Design**: Works well on desktop and mobile devices

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/bottoms-sweepstake.git
   cd bottoms-sweepstake
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install them manually:
   ```bash
   pip install streamlit pandas matplotlib altair
   ```

3. Run the application:
   ```bash
   streamlit run bottoms_sweepstake.py
   ```

4. Open your web browser and go to http://localhost:8501

## Current Player Selections

| Player | Team Picks               |
|--------|--------------------------|
| Sean   | Fulham, Everton          |
| Dom    | Bournemouth, Ipswich     |
| Harry  | Forest, Wolves           |
| Chris  | Brentford, Leicester     |
| Adam   | Brighton, Southampton    |

## Customization

### Modifying Player Picks

Edit the `player_picks` dictionary in the `bottoms_sweepstake.py` file:

```python
player_picks = {
    "Player": ["Sean", "Sean", "Dom", "Dom", "Harry", "Harry", "Chris", "Chris", "Adam", "Adam"],
    "Team": ["Fulham", "Everton", "Bournemouth", "Ipswich", "Forest", "Wolves", "Brentford", "Leicester", "Brighton", "Southampton"]
}
```

### Updating League Standings

Edit the `standings_data` dictionary in the `get_premier_league_standings()` function:

```python
standings_data = {
    "Position": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "Team": ["Brighton", "Bournemouth", "Fulham", "Wolves", "Everton", "Brentford", "Forest", "Southampton", "Leicester", "Ipswich"],
    "Points_Value": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
}
```

## Future Enhancements

Potential improvements for future versions:
- Integration with a live football data API for real-time standings
- Historical tracking of position changes throughout the season
- Email notifications when standings change
- Support for multiple sweepstakes/leagues
- User authentication for personalized views

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Your Name - your.email@example.com
Project Link: https://github.com/yourusername/bottoms-sweepstake# Bottoms_Sweepstake
