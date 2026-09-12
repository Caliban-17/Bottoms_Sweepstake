# Bottoms Sweepstake · Gen 3

A Streamlit dashboard for the Premier League "Bottoms Sweepstake", now in its third generation for the **2026/27** season.

## The sweepstake

- Six players, each drawn two Premier League clubs.
- At the end of the season every club is worth its finishing position in reverse: 1st = 20 points, 2nd = 19, … 20th = 1.
- A player's score is the sum of their two clubs. Highest score wins the pot; lowest gets the wooden spoon.
- Stake is £5 each, so the Gen 3 pot is **£30**.

### Gen 3 roster (2026/27)

| Player | Clubs                              |
| :----- | :--------------------------------- |
| Sean   | Hull City, Chelsea                 |
| Vosey  | Tottenham Hotspur, Ipswich Town    |
| Dom    | Newcastle United, Coventry City    |
| Adam   | Brentford, Everton                 |
| Sam    | Leeds United, Fulham               |
| Wilson | Crystal Palace, Nottingham Forest  |

### Hall of Fame

| Gen | Season  | Winner        | Wooden spoon           |
| :-- | :------ | :------------ | :--------------------- |
| 1   | 2024/25 | Harry (19)    | Dom, Chris, Adam (14=) |
| 2   | 2025/26 | Dom (26)      | Sam (6)                |

Results are computed in-app from each season's final table and the picks recorded in this repo's history.

## What the app shows

- **Header** with data status (live / pre-season / offline snapshot), matchweek and fetch time.
- **Summary strip**: current leader, wooden spoon, matchweek and prize pot.
- **BanterBot**: dressing-room abuse built from the live table. Lines know who leads and by how much, who holds the spoon, which clubs are on a losing run or in the bottom three, who dropped this week, and who won last season, so only lines that fit the situation get used.
- **Leaderboard**: ranked list with each player's clubs and current positions, plus a points chart.
- **Squads**: a card per player with each club's position, movement this matchweek, league points, sweepstake value, recent form and next fixture.
- **League table**: the full Premier League table with owners highlighted, qualification and relegation zones, form and sweepstake value.
- **Rules & history**: the points ladder and the final standings of previous generations.
- **Sidebar**: refresh the table and upload player headshots.

## Running it

```bash
pip install -r requirements.txt
streamlit run bottoms_sweepstake.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

Tests:

```bash
python -m unittest discover -s tests -v
```

## Data

Standings come from the Premier League's public data service (`footballapi.pulselive.com`), the same feed that powers premierleague.com. The table is cached for 30 minutes; use the refresh button to refetch.

If the service can't be reached the app shows an offline snapshot of the table and says so in the header. Crest images are served from premierleague.com using each club's Opta id, which the API supplies; a small map in `sweepstake/config.py` backs the offline snapshot.

## Project layout

```
bottoms_sweepstake.py   Streamlit page (layout and wiring only)
sweepstake/
  config.py             season, roster, crest ids, previous generations
  scoring.py            points, ranking, hall-of-fame results
  data.py               API client, payload parsing, offline snapshot
  banter.py             BanterBot context builder and lines
  ui.py                 CSS and HTML component builders
assets/headshots/       player images (<Player>.png / .jpg)
tests/                  unit tests plus a saved API payload fixture
.streamlit/config.toml  dark Premier League theme
```

## New season checklist

1. Update `SEASON_LABEL`, `GENERATION` and `PLAYER_PICKS` in `sweepstake/config.py`. Team names must match the long names used on premierleague.com (for example "Tottenham Hotspur", "Nottingham Forest").
2. Add the finished season to `PREVIOUS_GENERATIONS` with each club's final position.
3. Add crests for any newly promoted club to `OPTA_ID_MAP` (only needed for the offline snapshot; the live feed supplies ids).
4. Drop a headshot for any new player into `assets/headshots/`, or upload one from the sidebar.
