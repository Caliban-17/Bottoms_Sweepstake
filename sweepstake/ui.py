"""CSS and HTML building blocks for the Streamlit app.

Every builder is a pure function that returns an HTML string; the app hands the
result to ``st.html``. Class names are prefixed ``bs-`` to stay clear of
Streamlit's own styles. The look is deliberately plain: neutral dark surfaces,
hairline borders, one accent, tabular numerals, no decoration.
"""

from __future__ import annotations

import base64
import html
import os
from functools import lru_cache
from urllib.parse import quote

from . import config

# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def ordinal(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "–"
    if n < 1:
        return "–"
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def rank_label(rank: int, tied: bool) -> str:
    return f"{rank}=" if tied else str(rank)


@lru_cache(maxsize=64)
def _image_data_uri_cached(path: str, mtime: float) -> str:
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode()
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    return f"data:{mime};base64,{encoded}"


def image_data_uri(path: str) -> str | None:
    """Base64 data URI for a local image (cached by path + mtime)."""
    if not path or not os.path.exists(path):
        return None
    return _image_data_uri_cached(path, os.path.getmtime(path))


def avatar_data_uri(name: str) -> str:
    """Flat initial-letter SVG avatar for players without a headshot."""
    initial = (name or "?").strip()[:1].upper() or "?"
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'>"
        "<rect width='120' height='120' fill='#2A2F3A'/>"
        "<text x='60' y='78' font-family='Inter, Helvetica, Arial, sans-serif' font-size='52' "
        f"font-weight='600' fill='#E6E8EC' text-anchor='middle'>{esc(initial)}</text></svg>"
    )
    return "data:image/svg+xml;utf8," + quote(svg)


HEADSHOT_DIR = os.path.join("assets", "headshots")


def player_image(name: str, directory: str = HEADSHOT_DIR) -> str:
    """Headshot data URI if one exists on disk, otherwise a generated avatar."""
    for ext in (".png", ".jpg", ".jpeg"):
        uri = image_data_uri(os.path.join(directory, f"{name}{ext}"))
        if uri:
            return uri
    return avatar_data_uri(name)


# --------------------------------------------------------------------------- #
# Stylesheet
# --------------------------------------------------------------------------- #
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{
  --c-surface:#161920;--c-surface-2:#1C2029;--c-line:#262B36;--c-line-2:#363C4A;
  --c-text:#E6E8EC;--c-muted:#8A919F;--c-dim:#5C6370;
  --c-accent:#8B7CF6;--c-accent-soft:rgba(139,124,246,.13);
  --c-pos:#3DDC84;--c-neg:#FF6B6B;--c-draw:#6B7280;--c-gold:#E2B84C;
  --r:8px;
  --font:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
}
/* Streamlit gives st.html blocks a fixed pixel width measured at first render; let them fill their container. */
div.stHtml,[data-testid="stHtml"]{width:100% !important}
div.stMainBlockContainer{padding-top:4.75rem;padding-bottom:3rem}
.bs{font-family:var(--font);color:var(--c-text);font-size:14px;line-height:1.45;font-feature-settings:"tnum" 1,"cv11" 1}
.bs *{box-sizing:border-box}
.bs img{max-width:100%}

/* top bar */
.bs-top{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;padding:0 0 14px;border-bottom:1px solid var(--c-line);flex-wrap:wrap}
.bs-wordmark{font-size:22px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.bs-sub{color:var(--c-muted);font-size:13px;margin-top:5px}
.bs-status{display:flex;align-items:center;gap:14px;color:var(--c-muted);font-size:12.5px;white-space:nowrap;padding-bottom:2px}
.bs-status i{width:7px;height:7px;border-radius:50%;background:var(--c-dim);display:inline-block;margin-right:7px;vertical-align:1px}
.bs-status i.live{background:var(--c-pos)}
.bs-status i.stale{background:var(--c-neg)}
.bs-status i.pre{background:var(--c-accent)}
.bs-status b{color:var(--c-text);font-weight:600}

/* summary strip */
.bs-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--c-line);border-radius:var(--r);background:var(--c-surface);margin:16px 0 12px}
.bs-cell{padding:14px 18px;border-right:1px solid var(--c-line);min-width:0}
.bs-cell:last-child{border-right:0}
.bs-label{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--c-muted);margin-bottom:8px}
.bs-value{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:700;letter-spacing:-.01em;line-height:1.1;min-width:0}
.bs-value span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bs-sub2{font-size:12.5px;color:var(--c-muted);margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (max-width:900px){
  .bs-strip{grid-template-columns:repeat(2,minmax(0,1fr))}
  .bs-cell:nth-child(2){border-right:0}
  .bs-cell:nth-child(-n+2){border-bottom:1px solid var(--c-line)}
}
@media (max-width:480px){
  .bs-strip{grid-template-columns:1fr}
  .bs-cell{border-right:0;border-bottom:1px solid var(--c-line)}
  .bs-cell:last-child{border-bottom:0}
}

/* banter */
.bs-quote{display:flex;gap:16px;align-items:baseline;padding:12px 16px;border-left:2px solid var(--c-accent);background:var(--c-surface);border-radius:0 var(--r) var(--r) 0;margin:0 0 4px}
.bs-quote .who{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--c-accent);white-space:nowrap}
.bs-quote .msg{font-size:15px;font-style:italic}

/* avatars */
.bs-avatar{width:36px;height:36px;border-radius:50%;object-fit:cover;object-position:top;border:1px solid var(--c-line-2);background:#0f1115;flex:none;display:inline-block;vertical-align:middle}
.bs-avatar.xs{width:18px;height:18px}
.bs-avatar.sm{width:26px;height:26px}
.bs-avatar.lg{width:44px;height:44px}

/* section head */
.bs-head{display:flex;align-items:baseline;gap:10px;padding:8px 0 10px;margin-bottom:10px;border-bottom:1px solid var(--c-line)}
.bs-head h3{font-size:15px;font-weight:600;margin:0;color:inherit;letter-spacing:-.01em;font-family:var(--font)}
.bs-head span{font-size:12.5px;color:var(--c-muted)}

/* leaderboard list */
.bs-list{border:1px solid var(--c-line);border-radius:var(--r);background:var(--c-surface);overflow:hidden}
.bs-row{display:grid;grid-template-columns:28px 36px minmax(0,1fr) auto;gap:14px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--c-line);position:relative}
.bs-row:last-child{border-bottom:0}
.bs-row.lead:before,.bs-row.spoon:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--c-gold)}
.bs-row.spoon:before{background:var(--c-neg)}
.bs-rank{font-size:13px;color:var(--c-muted);font-weight:600}
.bs-name{font-weight:600;font-size:14.5px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.bs-tag{font-size:10.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.bs-tag.gold{color:var(--c-gold)}
.bs-tag.red{color:var(--c-neg)}
.bs-clubs{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:4px;font-size:12.5px;color:var(--c-muted)}
.bs-clubs span{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.bs-clubs img{width:16px;height:16px;object-fit:contain}
.bs-clubs b{color:var(--c-text);font-weight:600}
.bs-pts{font-size:22px;font-weight:700;letter-spacing:-.02em;text-align:right;line-height:1}
.bs-pts small{display:block;font-size:10.5px;color:var(--c-muted);font-weight:500;letter-spacing:.06em;text-transform:uppercase;margin-top:4px}

/* squad cards */
.bs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.bs-card{border:1px solid var(--c-line);border-radius:var(--r);background:var(--c-surface);padding:14px 16px}
.bs-card.lead{border-color:rgba(226,184,76,.55)}
.bs-card.spoon{border-color:rgba(255,107,107,.5)}
.bs-card-head{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid var(--c-line);margin-bottom:4px;min-width:0}
.bs-card-head .who{min-width:0;flex:1}
.bs-card-head .meta{font-size:12.5px;color:var(--c-muted);margin-top:2px}
.bs-club{display:grid;grid-template-columns:32px minmax(0,1fr) auto;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--c-line)}
.bs-club:last-child{border-bottom:0}
.bs-crest{width:32px;height:32px;object-fit:contain}
.bs-crest.sm{width:20px;height:20px}
.bs-crest-blank{width:32px;height:32px;border-radius:50%;background:var(--c-surface-2)}
.bs-club .t{font-weight:600;font-size:14px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.bs-club .m{font-size:12.5px;color:var(--c-muted);margin-top:3px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.bs-club .n{font-size:12px;color:var(--c-dim);margin-top:3px}
.bs-club .v{font-size:18px;font-weight:700;letter-spacing:-.01em;text-align:right}
.bs-club .v small{display:block;font-size:10px;color:var(--c-muted);font-weight:500;text-transform:uppercase;letter-spacing:.06em;margin-top:2px}
.bs-move{font-size:11.5px;font-weight:600}
.bs-move.up{color:var(--c-pos)}
.bs-move.down{color:var(--c-neg)}
.bs-move.same{color:var(--c-dim)}
.bs-form{display:inline-flex;gap:3px;vertical-align:middle}
.bs-pip{width:14px;height:14px;border-radius:3px;display:grid;place-items:center;font-size:9px;font-weight:700;color:#0f1115}
.bs-pip.W{background:var(--c-pos)}
.bs-pip.D{background:var(--c-draw);color:#fff}
.bs-pip.L{background:var(--c-neg);color:#fff}

/* table */
.bs-tablewrap{border:1px solid var(--c-line);border-radius:var(--r);background:var(--c-surface);overflow-x:auto}
.bs-table{width:100%;border-collapse:collapse;font-size:13.5px}
.bs-table th{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--c-muted);text-align:left;padding:10px 12px;border-bottom:1px solid var(--c-line);white-space:nowrap}
.bs-table td{padding:9px 12px;border-bottom:1px solid var(--c-line);white-space:nowrap;vertical-align:middle}
.bs-table tr:last-child td{border-bottom:0}
.bs-table .num{text-align:right}
.bs-table .c{text-align:center}
.bs-table tr.owned td{background:var(--c-accent-soft)}
.bs-table tr.zone-cl td:first-child{box-shadow:inset 2px 0 0 var(--c-pos)}
.bs-table tr.zone-el td:first-child{box-shadow:inset 2px 0 0 #5AB0F0}
.bs-table tr.zone-ecl td:first-child{box-shadow:inset 2px 0 0 #B39DDB}
.bs-table tr.zone-rel td:first-child{box-shadow:inset 2px 0 0 var(--c-neg)}
.bs-team{display:flex;align-items:center;gap:9px;font-weight:600}
.bs-owner{display:inline-flex;align-items:center;gap:6px}
.bs-owner.none{color:var(--c-dim)}
.bs-legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;color:var(--c-muted);margin-top:8px}
.bs-legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px;vertical-align:middle}

/* history */
.bs-hof{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.bs-hof .title{font-weight:600;font-size:15px}
.bs-hrow{display:grid;grid-template-columns:24px 26px minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--c-line);font-size:13px}
.bs-hrow:last-child{border-bottom:0}
.bs-hrow .rk{color:var(--c-muted);font-weight:600;font-size:12.5px}
.bs-hrow .who{font-weight:600;white-space:nowrap}
.bs-hrow .teams{font-size:12px;color:var(--c-muted);white-space:normal}
.bs-hrow .pts{font-weight:700;font-size:15px}
.bs-hrow .who .bs-tag{margin-left:8px}

/* rules */
.bs-prose{max-width:72ch;font-size:14px}
.bs-prose p{margin:0 0 10px}
.bs-ladder{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));border:1px solid var(--c-line);border-radius:var(--r);overflow:hidden;background:var(--c-surface);margin:12px 0 12px;max-width:760px}
.bs-ladder div{padding:8px 4px;text-align:center;border-right:1px solid var(--c-line);border-bottom:1px solid var(--c-line);font-size:11.5px;color:var(--c-muted)}
.bs-ladder div b{display:block;font-size:15px;font-weight:700;color:var(--c-text)}
.bs-ladder div:nth-child(10n){border-right:0}
.bs-ladder div:nth-child(n+11){border-bottom:0}
.bs-note{font-size:13px;color:var(--c-muted);max-width:72ch}
.bs-foot{font-size:12px;color:var(--c-dim);padding:18px 0 4px;border-top:1px solid var(--c-line);margin-top:20px}
</style>"""


# --------------------------------------------------------------------------- #
# Fragments
# --------------------------------------------------------------------------- #


def avatar_html(src: str, name: str, size: str = "") -> str:
    classes = " ".join(c for c in ("bs-avatar", size) if c)
    return f'<img class="{classes}" src="{esc(src)}" alt="{esc(name)}">'


def crest_html(url: str | None, team: str, small: bool = False) -> str:
    if not url:
        return '<span class="bs-crest-blank"></span>'
    cls = "bs-crest sm" if small else "bs-crest"
    return f'<img class="{cls}" src="{esc(url)}" alt="{esc(team)} crest" loading="lazy">'


def form_html(form: str) -> str:
    if not form:
        return ""
    pips = "".join(f'<span class="bs-pip {esc(r)}">{esc(r)}</span>' for r in form if r in "WDL")
    return f'<span class="bs-form" title="Last {len(form)} results, oldest first">{pips}</span>'


def move_html(position, starting_position) -> str:
    try:
        pos, start = int(position), int(starting_position)
    except (TypeError, ValueError):
        return ""
    if pos < 1 or start < 1:
        return ""
    diff = start - pos
    if diff > 0:
        return f'<span class="bs-move up" title="Up {diff} since the start of the matchweek">▲{diff}</span>'
    if diff < 0:
        return f'<span class="bs-move down" title="Down {-diff} since the start of the matchweek">▼{-diff}</span>'
    return '<span class="bs-move same" title="No change this matchweek">–</span>'


def tag_html(row: dict) -> str:
    if row.get("is_leader"):
        return '<span class="bs-tag gold">Leader</span>'
    if row.get("is_spoon"):
        return '<span class="bs-tag red">Wooden spoon</span>'
    return ""


def head_html(title: str, sub: str = "") -> str:
    extra = f"<span>{esc(sub)}</span>" if sub else ""
    return f'<div class="bs"><div class="bs-head"><h3>{esc(title)}</h3>{extra}</div></div>'


# --------------------------------------------------------------------------- #
# Components
# --------------------------------------------------------------------------- #


def topbar_html(
    *,
    generation: int,
    season: str,
    status: str,
    status_label: str,
    matchweek: int,
    fetched: str,
) -> str:
    dot = {"live": "live", "preseason": "pre"}.get(status, "stale")
    mw = f"Matchweek <b>{matchweek}</b>" if matchweek else "<b>Pre-season</b>"
    return (
        '<div class="bs"><div class="bs-top">'
        "<div>"
        '<div class="bs-wordmark">Bottoms Sweepstake</div>'
        f'<div class="bs-sub">Generation {generation} · Premier League {esc(season)}</div>'
        "</div>"
        '<div class="bs-status">'
        f'<span><i class="{dot}"></i>{esc(status_label)}</span>'
        f"<span>{mw}</span>"
        f"<span>Updated {esc(fetched)}</span>"
        "</div></div></div>"
    )


def summary_html(cells: list[dict]) -> str:
    """Each cell: {label, value, sub?, image?}."""
    out = ['<div class="bs"><div class="bs-strip">']
    for cell in cells:
        avatar = avatar_html(cell["image"], cell.get("value", ""), "sm") if cell.get("image") else ""
        out.append(
            '<div class="bs-cell">'
            f'<div class="bs-label">{esc(cell.get("label", ""))}</div>'
            f'<div class="bs-value">{avatar}<span>{esc(cell.get("value", ""))}</span></div>'
            f'<div class="bs-sub2">{esc(cell.get("sub", ""))}</div>'
            "</div>"
        )
    out.append("</div></div>")
    return "".join(out)


def banter_html(message: str) -> str:
    return (
        '<div class="bs"><div class="bs-quote">'
        '<span class="who">BanterBot</span>'
        f'<span class="msg">{esc(message)}</span>'
        "</div></div>"
    )


def leaderboard_html(rows: list[dict]) -> str:
    """Each row: {player, image, rank, tied, points, is_leader, is_spoon, teams: [{crest, short, position}]}."""
    out = ['<div class="bs"><div class="bs-list">']
    for row in rows:
        classes = "bs-row"
        if row.get("is_leader"):
            classes += " lead"
        elif row.get("is_spoon"):
            classes += " spoon"
        clubs = "".join(
            f'<span>{crest_html(t.get("crest"), t.get("short", ""), small=True)}'
            f'{esc(t.get("short", ""))} <b>{esc(ordinal(t.get("position")))}</b></span>'
            for t in row.get("teams", [])
        )
        out.append(
            f'<div class="{classes}">'
            f'<div class="bs-rank">{esc(rank_label(row["rank"], row["tied"]))}</div>'
            f'{avatar_html(row["image"], row["player"])}'
            "<div>"
            f'<div class="bs-name">{esc(row["player"])}{tag_html(row)}</div>'
            f'<div class="bs-clubs">{clubs}</div>'
            "</div>"
            f'<div class="bs-pts">{row["points"]}<small>pts</small></div>'
            "</div>"
        )
    out.append("</div></div>")
    return "".join(out)


def cards_html(cards: list[dict]) -> str:
    """Each card: {player, image, rank, tied, points, is_leader, is_spoon, teams: [team dicts]}.

    Team dict: {name, crest, position, starting_position, league_points, points, form, next, missing}.
    """
    out = ['<div class="bs"><div class="bs-grid">']
    n = len(cards)
    for card in cards:
        classes = "bs-card"
        if card.get("is_leader"):
            classes += " lead"
        elif card.get("is_spoon"):
            classes += " spoon"
        clubs = []
        for team in card.get("teams", []):
            position = team.get("position")
            if team.get("missing"):
                meta = "<span>Not in the current table</span>"
            elif not position:
                meta = "<span>No position yet</span>"
            else:
                meta = (
                    f"<span>{esc(ordinal(position))}</span>"
                    f'<span>{team.get("league_points", 0)} league pts</span>'
                    f'{form_html(team.get("form", ""))}'
                )
            nxt = f'<div class="n">Next: {esc(team["next"])}</div>' if team.get("next") else ""
            clubs.append(
                '<div class="bs-club">'
                f'{crest_html(team.get("crest"), team.get("name", ""))}'
                "<div>"
                f'<div class="t">{esc(team.get("name", ""))}{move_html(position, team.get("starting_position"))}</div>'
                f'<div class="m">{meta}</div>'
                f"{nxt}"
                "</div>"
                f'<div class="v">{team.get("points", 0)}<small>worth</small></div>'
                "</div>"
            )
        meta_bits = [f"{esc(ordinal(card['rank']))} of {n}"]
        if card.get("is_leader"):
            meta_bits.append("Leader")
        elif card.get("is_spoon"):
            meta_bits.append("Wooden spoon")
        out.append(
            f'<div class="{classes}">'
            '<div class="bs-card-head">'
            f'{avatar_html(card["image"], card["player"], "lg")}'
            '<div class="who">'
            f'<div class="bs-name">{esc(card["player"])}</div>'
            f'<div class="meta">{" · ".join(meta_bits)}</div>'
            "</div>"
            f'<div class="bs-pts">{card["points"]}<small>pts</small></div>'
            "</div>"
            f'{"".join(clubs)}'
            "</div>"
        )
    out.append("</div></div>")
    return "".join(out)


def table_html(rows: list[dict], owners: dict[str, str], images: dict[str, str]) -> str:
    """Rows are dicts with the columns from ``data.TABLE_COLUMNS``."""
    head = (
        "<tr><th class='c'>#</th><th>Club</th><th>Owner</th>"
        "<th class='num'>P</th><th class='num'>W</th><th class='num'>D</th><th class='num'>L</th>"
        "<th class='num'>GD</th><th class='num'>Pts</th><th>Form</th><th class='num'>Worth</th></tr>"
    )
    body = []
    for row in rows:
        team = row.get("Team", "")
        owner = owners.get(team)
        classes = []
        if owner:
            classes.append("owned")
        if row.get("Zone"):
            classes.append(f"zone-{row['Zone']}")
        if owner:
            owner_html = f'<span class="bs-owner">{avatar_html(images.get(owner, ""), owner, "xs")}{esc(owner)}</span>'
        else:
            owner_html = '<span class="bs-owner none">–</span>'
        gd = int(row.get("GD", 0) or 0)
        gd_txt = f"+{gd}" if gd > 0 else str(gd)
        position = row.get("Position", 0)
        pos_txt = str(int(position)) if position else "–"
        body.append(
            f'<tr class="{" ".join(classes)}">'
            f'<td class="c">{esc(pos_txt)} {move_html(position, row.get("StartingPosition"))}</td>'
            f'<td><span class="bs-team">{crest_html(row.get("Crest_URL"), team, small=True)}{esc(team)}</span></td>'
            f"<td>{owner_html}</td>"
            f'<td class="num">{int(row.get("Played", 0) or 0)}</td>'
            f'<td class="num">{int(row.get("Won", 0) or 0)}</td>'
            f'<td class="num">{int(row.get("Drawn", 0) or 0)}</td>'
            f'<td class="num">{int(row.get("Lost", 0) or 0)}</td>'
            f'<td class="num">{esc(gd_txt)}</td>'
            f'<td class="num"><b>{int(row.get("Points_League", 0) or 0)}</b></td>'
            f'<td>{form_html(row.get("Form", "") or "")}</td>'
            f'<td class="num"><b>{int(row.get("Points_Value", 0) or 0)}</b></td>'
            "</tr>"
        )
    legend = (
        '<div class="bs-legend">'
        '<span><i style="background:var(--c-accent)"></i>Owned by a player</span>'
        '<span><i style="background:var(--c-pos)"></i>Champions League</span>'
        '<span><i style="background:#5AB0F0"></i>Europa League</span>'
        '<span><i style="background:var(--c-neg)"></i>Relegation</span>'
        "<span>Worth: sweepstake points for that position</span>"
        "</div>"
    )
    return (
        '<div class="bs"><div class="bs-tablewrap"><table class="bs-table">'
        f"<thead>{head}</thead><tbody>{''.join(body)}</tbody></table></div>{legend}</div>"
    )


def history_html(generations: list[dict], images: dict[str, str]) -> str:
    """Each generation: {generation, season, pot, results: [rank rows with teams]}."""
    out = ['<div class="bs"><div class="bs-hof">']
    for gen in generations:
        results = gen["results"]
        worst = max(r["rank"] for r in results) if results else 0
        rows = []
        for r in results:
            teams = " · ".join(f"{config.short_name(t)} {ordinal(p)} ({pts})" for t, p, pts in r["teams"])
            tag = ""
            if r["rank"] == 1:
                tag = '<span class="bs-tag gold">Winner</span>'
            elif r["rank"] == worst and len(results) > 1:
                tag = '<span class="bs-tag red">Spoon</span>'
            rows.append(
                '<div class="bs-hrow">'
                f'<span class="rk">{esc(rank_label(r["rank"], r["tied"]))}</span>'
                f'{avatar_html(images.get(r["player"], avatar_data_uri(r["player"])), r["player"], "sm")}'
                f'<span><span class="who">{esc(r["player"])}{tag}</span><div class="teams">{esc(teams)}</div></span>'
                f'<span class="pts">{r["points"]}</span>'
                "</div>"
            )
        out.append(
            '<div class="bs-card">'
            '<div class="bs-card-head"><div class="who">'
            f'<div class="title">Generation {gen["generation"]} · {esc(gen["season"])}</div>'
            f'<div class="meta">{len(results)} players · £{gen["pot"]} pot</div>'
            "</div></div>"
            f'{"".join(rows)}'
            "</div>"
        )
    out.append("</div></div>")
    return "".join(out)


def rules_html(stake: int, pot: int, n_players: int) -> str:
    ladder = "".join(
        f"<div>{ordinal(pos)}<b>{config.LEAGUE_SIZE + 1 - pos}</b></div>"
        for pos in range(1, config.LEAGUE_SIZE + 1)
    )
    return (
        '<div class="bs"><div class="bs-prose">'
        "<p>Each player is drawn two Premier League clubs for the season. At the end of the season every club "
        f"is worth its finishing position in reverse: 1st is worth {config.LEAGUE_SIZE}, 2nd is worth "
        f"{config.LEAGUE_SIZE - 1}, and so on down to 20th, worth 1. A player's score is the sum of their two clubs.</p>"
        "</div>"
        f'<div class="bs-ladder">{ladder}</div>'
        f'<p class="bs-note">Highest score in May takes the pot: {n_players} players × £{stake} = £{pot}. '
        "Lowest score takes the wooden spoon. The table here updates during the season, so the leaderboard shows "
        "where things stand now, not the final result.</p>"
        "</div>"
    )


def footer_html(generation: int, season: str, fetched: str, source_label: str) -> str:
    return (
        f'<div class="bs"><div class="bs-foot">Bottoms Sweepstake · Generation {generation} · Premier League '
        f"{esc(season)} · {esc(source_label)}, fetched {esc(fetched)} · data from premierleague.com</div></div>"
    )
