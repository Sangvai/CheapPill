# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "cheappill.db"

st.set_page_config(page_title="CheapPill.in", page_icon="\U0001F48A", layout="centered")

st.markdown(
    """
    <style>
        .stApp { background: #eef1ec; }
        [data-testid="stAppViewContainer"] * { color: #15231d; }
        .salt-badge {
            display: inline-block;
            background: #dbeee2;
            color: #0b6e4f;
            padding: 8px 14px;
            border-radius: 8px;
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            font-size: 14px;
            margin: 4px 0 10px 0;
        }
        .tagline { color: #4c5d55; font-size: 14px; margin-top: -8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.text_factory = str
    return conn


conn = get_conn()


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


st.markdown("## \U0001F48A CheapPill.in")
st.markdown('<div class="tagline">Same salt. Different price tag.</div>', unsafe_allow_html=True)
st.write(
    "Type the exact brand name printed on the strip. We match it against "
    "237,000+ real pack listings by salt composition and show every other "
    "brand selling the identical formula — cheapest first."
)

query = st.text_input("Search a brand name", placeholder="e.g. Augmentin 625 Duo Tablet")

if query:
    hit = find_brand(query)
    if not hit:
        st.error(f"No exact match for “{query}”.")
        st.caption("Brand names must match exactly (spelling is checked, not fuzzy).")
        sugg = suggestions(query)
        if sugg:
            st.write("Did you mean one of these?")
            for s in sugg:
                st.write(f"- {s}")
    else:
        salt_key, salt_display = hit
        rows = alternatives(salt_key)

        you_unit = None
        for b, m, p, pack, u in rows:
            if b.strip().lower() == query.strip().lower():
                you_unit = u
                break
        if you_unit is None:
            you_unit = rows[0][4]

        st.markdown(f"**Searched brand:** {query}")
        st.markdown(f'<div class="salt-badge">{salt_display}</div>', unsafe_allow_html=True)
        st.caption(f"{len(rows)} brand(s) on record with this exact composition.")

        TOP_N = 25
        table_rows = []
        for b, m, p, pack, u in rows[:TOP_N]:
            is_you = b.strip().lower() == query.strip().lower()
            pct = (you_unit - u) / you_unit * 100 if you_unit else 0
            if is_you:
                savings = "Searched brand"
            elif pct > 0.5:
                savings = f"Save {pct:.0f}%"
            elif pct < -0.5:
                savings = f"{abs(pct):.0f}% pricier"
            else:
                savings = "Same price"
            table_rows.append(
                {
                    "Brand": b + (" ⭐" if is_you else ""),
                    "Manufacturer": m,
                    "Price": f"₹{p:,.2f}",
                    "Pack": pack,
                    "Vs. you": savings,
                }
            )

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if len(rows) > TOP_N:
            st.caption(f"+{len(rows) - TOP_N} more brand(s) with this composition not shown.")

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Salt groups", "6,235", help="Groups with 2+ competing brands")
c2.metric("Median price gap", "184%", help="Cheapest vs. priciest brand of the same formula")
c3.metric("Sun Pharma", "171×", help="Times it was the single priciest brand for a given salt")

st.caption(
    "Built on the public Indian Medicine Dataset (junioralive/Indian-Medicine-Dataset), "
    "~254k pack listings. Always confirm composition and dosage with a pharmacist before switching."
)
