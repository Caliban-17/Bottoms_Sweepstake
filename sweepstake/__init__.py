"""Bottoms Sweepstake — Premier League reverse-position sweepstake.

Package layout
--------------
- ``config``  : season, roster, crest IDs and past generations (static data)
- ``scoring`` : pure scoring / ranking helpers
- ``data``    : Pulse Live API client, payload parsing and fallback snapshot
- ``banter``  : BanterBot phrases
- ``ui``      : CSS and HTML component builders used by the Streamlit app
"""

from .config import GENERATION, SEASON_LABEL  # noqa: F401
