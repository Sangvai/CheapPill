# -*- coding: utf-8 -*-
import html
import sqlite3
import textwrap
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).parent / "cheappill.db"


def md(s: str) -> None:
    # st.markdown's markdown pass re-flows raw <style>/<div> content as paragraphs
    # (and treats indented HTML as a code block); st.html renders it literally.
    st.html(textwrap.dedent(s))


def inject_css(css: str) -> None:
    st.html("<style>" + textwrap.dedent(css) + "</style>")


st.set_page_config(page_title="CheapPill.in", page_icon="\U0001F48A", layout="centered")

# ---------------------------------------------------------------------------
# Design system (mirrors the CheapPill.in artifact's token set)
# ---------------------------------------------------------------------------
md(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    """
)

inject_css(
    """
    :root {
        --bg: #eef1ec; --surface: #ffffff; --surface-2: #e4e9e2;
        --ink: #15231d; --ink-soft: #4c5d55; --ink-faint: #82938a;
        --accent: #0b6e4f; --accent-ink: #ffffff; --accent-soft: #dbeee2;
        --clay: #b3402f; --clay-soft: #f5ddd7;
        --gold: #a9761f; --gold-soft: #f3e6c9;
        --border: #cdd6c8; --border-strong: #a9b6a1;
        --shadow: 0 1px 2px rgba(21,35,29,.06), 0 8px 24px rgba(21,35,29,.07);
        --radius: 14px;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg: #0e1512; --surface: #172019; --surface-2: #1e2a22;
            --ink: #eaf2ec; --ink-soft: #a4b8ab; --ink-faint: #708078;
            --accent: #3bc98d; --accent-ink: #06170f; --accent-soft: #163427;
            --clay: #e2836f; --clay-soft: #3a201b;
            --gold: #e6b95c; --gold-soft: #3a2f14;
            --border: #2a362e; --border-strong: #3c4a41;
            --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 28px rgba(0,0,0,.35);
        }
    }

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
    .stApp { background: var(--bg); }
    .main .block-container { max-width: 720px; padding-top: 2.2rem; padding-bottom: 3rem; }
    #MainMenu, header[data-testid="stHeader"] { background: transparent; }

    .cp-header { display:flex; align-items:center; gap:12px; margin-bottom: 6px; }
    .cp-mark { flex:none; width:40px; height:40px; border-radius:10px; background:var(--accent);
               display:flex; align-items:center; justify-content:center; font-size:20px; }
    .cp-brand { font-size:21px; font-weight:700; letter-spacing:-0.01em; color: var(--ink); }
    .cp-brand .dot { color: var(--accent); }
    .cp-tagline { font-size:12.5px; color:var(--ink-faint); margin-top:1px; }

    .cp-h1 { font-size: clamp(22px,5vw,30px); line-height:1.18; letter-spacing:-0.015em;
              margin: 10px 0 6px; color: var(--ink); font-weight: 700; }
    .cp-sub { color:var(--ink-soft); font-size:14.5px; line-height:1.5; max-width:54ch; margin:0 0 18px; }

    /* Streamlit form -> search card look */
    div[data-testid="stForm"] {
        background: var(--surface); border:1px solid var(--border); border-radius: var(--radius);
        box-shadow: var(--shadow); padding: 10px 10px; border-bottom: none;
    }
    div[data-testid="stForm"] [data-testid="stTextInput"] input {
        border: none !important; background: transparent !important; box-shadow:none !important;
        font-family: 'IBM Plex Sans', sans-serif; font-size:16px; color:var(--ink);
        padding: 10px 6px 10px 34px !important;
        background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'%3E%3Ccircle cx='11' cy='11' r='7' stroke='%2382938a' stroke-width='1.8'/%3E%3Cpath d='M20 20L16.2 16.2' stroke='%2382938a' stroke-width='1.8' stroke-linecap='round'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important; background-position: 8px center !important;
    }
    div[data-testid="stForm"] [data-testid="stTextInput"] > div {
        border: none !important; background: transparent !important;
    }
    div[data-testid="stForm"] label { display:none; }
    div[data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important; color: var(--accent-ink) !important; border:none !important;
        font-weight:600 !important; border-radius:9px !important; padding: 10px 18px !important;
        font-family:'IBM Plex Sans', sans-serif !important;
    }
    div[data-testid="stFormSubmitButton"] { display:flex; justify-content:flex-end; margin-top:-6px; }

    .cp-status { font-size:12.5px; color:var(--ink-faint); margin: 6px 2px 18px; }

    .cp-salt-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
                    box-shadow:var(--shadow); padding:18px 20px; margin: 6px 0 14px; }
    .cp-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-faint); }
    .cp-searched-brand { font-size:17px; font-weight:600; color:var(--ink); margin:2px 0 10px; }
    .cp-salt-key { display:inline-block; font-family:'IBM Plex Mono', monospace; font-size:14px;
                   background:var(--accent-soft); color:var(--accent); border-radius:8px; padding:8px 12px;
                   margin: 4px 0 10px; }
    .cp-salt-meta { font-size:13px; color:var(--ink-soft); }

    .cp-table-wrap { overflow-x:auto; border-radius:var(--radius); border:1px solid var(--border);
                     box-shadow:var(--shadow); margin-bottom: 6px; }
    table.cp-table { width:100%; min-width:540px; border-collapse:collapse; font-size:14px; }
    table.cp-table thead th { text-align:left; font-size:10.5px; font-weight:600; text-transform:uppercase;
                               letter-spacing:.07em; color:var(--ink-faint); background:var(--surface-2);
                               padding:10px 14px; border-bottom:1px solid var(--border); }
    table.cp-table td { padding:11px 14px; border-bottom:1px solid var(--border); background:var(--surface);
                         vertical-align:top; }
    table.cp-table tbody tr:last-child td { border-bottom:none; }
    table.cp-table tbody tr.you td { background: var(--gold-soft); }
    .cp-rank { display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px;
               border-radius:6px; background:var(--surface-2); color:var(--ink-soft); font-size:11px; font-weight:600; }
    tr.cheapest .cp-rank { background:var(--accent); color:var(--accent-ink); }
    .cp-bname { font-weight:600; color:var(--ink); }
    .cp-bmanu { color:var(--ink-faint); font-size:12.5px; margin-top:1px; }
    .cp-pmain { font-weight:600; color: var(--ink); font-variant-numeric: tabular-nums; }
    .cp-ppack { color:var(--ink-faint); font-size:12px; margin-top:1px; }
    .cp-pill { display:inline-block; padding:3px 9px; border-radius:999px; font-size:12.5px; font-weight:600; white-space:nowrap; }
    .cp-pill.good { background:var(--accent-soft); color:var(--accent); }
    .cp-pill.bad { background:var(--clay-soft); color:var(--clay); }
    .cp-pill.flat { background:var(--surface-2); color:var(--ink-faint); }
    .cp-more { font-size:12.5px; color:var(--ink-faint); text-align:center; padding:8px 4px 2px; }

    .cp-notfound { background:var(--surface); border:1px dashed var(--border-strong); border-radius:var(--radius);
                   padding:22px 20px; text-align:center; margin: 6px 0; }
    .cp-notfound .t { font-weight:600; font-size:15.5px; color:var(--ink); margin-bottom:4px; }
    .cp-notfound .s { color:var(--ink-soft); font-size:13.5px; }
    .cp-sugg { margin-top:10px; font-size:13.5px; color:var(--ink-soft); }
    .cp-sugg b { color: var(--accent); }

    .cp-insights { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin: 22px 0 10px; }
    .cp-tile { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 16px; }
    .cp-tile .num { font-family:'IBM Plex Mono', monospace; font-size:20px; font-weight:600; color:var(--accent); }
    .cp-tile .cap { font-size:11.5px; color:var(--ink-soft); line-height:1.4; margin-top:2px; }

    .cp-footer { font-size:12px; color:var(--ink-faint); line-height:1.6; text-align:center; padding-top:10px; }
    """
)


@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.text_factory = str
    return conn


conn = get_conn()


@st.cache_data
def brand_and_salt_count():
    row = conn.execute("SELECT COUNT(DISTINCT brand), COUNT(DISTINCT salt_key) FROM meds").fetchone()
    return row


def find_brand(brand: str):
    cur = conn.execute(
        "SELECT salt_key, salt_display FROM meds WHERE LOWER(brand) = LOWER(?) LIMIT 1",
        (brand.strip(),),
    )
    return cur.fetchone()


def suggestions(prefix: str, limit: int = 6):
    cur = conn.execute(
        "SELECT DISTINCT brand FROM meds WHERE LOWER(brand) LIKE LOWER(?) ORDER BY brand LIMIT ?",
        (prefix.strip() + "%", limit),
    )
    return [r[0] for r in cur.fetchall()]


def alternatives(salt_key: str):
    cur = conn.execute(
        """SELECT brand, manufacturer, price, pack_label, unit_price
           FROM meds WHERE salt_key = ? ORDER BY unit_price ASC""",
        (salt_key,),
    )
    return cur.fetchall()


def money(v: float) -> str:
    return "₹" + f"{v:,.2f}"


EMDASH = "—"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
md(
    """
    <div class="cp-header">
        <div class="cp-mark">\U0001F48A</div>
        <div>
            <div class="cp-brand">CheapPill<span class="dot">.in</span></div>
            <div class="cp-tagline">Same salt. Different price tag.</div>
        </div>
    </div>
    <div class="cp-h1">Find the cheaper generic for any branded medicine.</div>
    <div class="cp-sub">Type the exact brand name printed on the strip. We match it against
        237,000+ real pack listings by salt composition and show every other brand selling
        the identical formula &mdash; cheapest first.</div>
    """
)

with st.form("search_form", clear_on_submit=False):
    query = st.text_input("Search", placeholder="e.g. Augmentin 625 Duo Tablet", label_visibility="collapsed")
    submitted = st.form_submit_button("Compare")

n_brands, n_salts = brand_and_salt_count()
md(f'<div class="cp-status">{n_salts:,} salt groups &middot; {n_brands:,} brands ready to search</div>')

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if query.strip():
    hit = find_brand(query)
    if not hit:
        sugg = suggestions(query)
        sugg_html = ""
        if sugg:
            qlen = len(query.strip())
            items = "".join(
                f"<div>&bull; <b>{html.escape(s[:qlen])}</b>{html.escape(s[qlen:])}</div>" for s in sugg
            )
            sugg_html = f'<div class="cp-sugg">Did you mean:<br>{items}</div>'
        md(
            f"""
            <div class="cp-notfound">
                <div class="t">No exact match for &ldquo;{html.escape(query)}&rdquo;</div>
                <div class="s">Brand names must match exactly (spelling is checked, not fuzzy).
                Check the strip for the exact printed name.</div>
                {sugg_html}
            </div>
            """
        )
    else:
        salt_key, salt_display = hit
        rows = alternatives(salt_key)

        you_idx = -1
        for i, (b, m, p, pack, u) in enumerate(rows):
            if b.strip().lower() == query.strip().lower():
                you_idx = i
                break
        you_unit = rows[you_idx][4] if you_idx >= 0 else rows[0][4]

        md(
            f"""
            <div class="cp-salt-card">
                <div class="cp-label">Searched brand</div>
                <div class="cp-searched-brand">{html.escape(query)}</div>
                <div class="cp-label">Identified composition</div>
                <div class="cp-salt-key">{html.escape(salt_display)}</div>
                <div class="cp-salt-meta">{len(rows)} brand{'s' if len(rows) != 1 else ''} on record with this exact composition.</div>
            </div>
            """
        )

        TOP_N = 15

        def pct(u):
            return ((you_unit - u) / you_unit * 100) if you_unit else 0

        def row_html(b, m, p, pack, u, rank, is_you):
            p_pct = pct(u)
            if is_you:
                cls, text = "flat", "Searched brand"
            elif p_pct > 0.5:
                cls, text = "good", f"Save {p_pct:.0f}%"
            elif p_pct < -0.5:
                cls, text = "bad", f"{abs(p_pct):.0f}% pricier"
            else:
                cls, text = "flat", "Same price"
            row_cls = ("you " if is_you else "") + ("cheapest" if rank == 1 else "")
            return (
                f'<tr class="{row_cls}">'
                f'<td><span class="cp-rank">{rank}</span></td>'
                f'<td><div class="cp-bname">{html.escape(b)}</div><div class="cp-bmanu">{html.escape(m)}</div></td>'
                f'<td><div class="cp-pmain">{money(p)}</div><div class="cp-ppack">{html.escape(pack or EMDASH)}</div></td>'
                f'<td><span class="cp-pill {cls}">{text}</span></td>'
                f'</tr>'
            )

        shown = rows[:TOP_N]
        body = "".join(row_html(b, m, p, pack, u, i + 1, i == you_idx) for i, (b, m, p, pack, u) in enumerate(shown))
        if you_idx >= TOP_N:
            gap = you_idx - TOP_N
            body += f'<tr><td colspan="4" style="text-align:center;color:var(--ink-faint);font-size:12px;padding:6px;background:var(--surface-2);">&ctdot; {gap} more brand{"s" if gap != 1 else ""} &ctdot;</td></tr>'
            b, m, p, pack, u = rows[you_idx]
            body += row_html(b, m, p, pack, u, you_idx + 1, True)

        md(
            f"""
            <div class="cp-table-wrap">
                <table class="cp-table">
                    <thead><tr><th>#</th><th>Brand</th><th>Price</th><th>Vs. you</th></tr></thead>
                    <tbody>{body}</tbody>
                </table>
            </div>
            """
        )

        shown_count = len(shown) + (1 if you_idx >= TOP_N else 0)
        remaining = len(rows) - shown_count
        if remaining > 0:
            md(f'<div class="cp-more">+{remaining} more brand{"s" if remaining != 1 else ""} with this composition not shown</div>')

# ---------------------------------------------------------------------------
# Insight strip + footer
# ---------------------------------------------------------------------------
md(
    """
    <div class="cp-insights">
        <div class="cp-tile"><div class="num">6,235</div>
            <div class="cap">generic salt groups in the dataset with 2 or more competing brands</div></div>
        <div class="cp-tile"><div class="num">184%</div>
            <div class="cap">median price gap between the cheapest and priciest brand of the same exact formula</div></div>
        <div class="cp-tile"><div class="num">171&times;</div>
            <div class="cap">Sun Pharma was the single priciest brand for a given salt &mdash; more than any other manufacturer</div></div>
    </div>
    <div class="cp-footer">
        Built on the public Indian Medicine Dataset (junioralive/Indian-Medicine-Dataset), ~254k pack listings.
        Brand and salt matching is exact &mdash; always confirm composition and dosage with a pharmacist before switching.
    </div>
    """
)
