# Reference copy: this is the script that produced cheappill.db (used by app.py).
# It expects the raw CSV from junioralive/Indian-Medicine-Dataset (DATA/indian_medicine_data.csv,
# ~30MB, not included here) in a sibling data/ folder, run from inside a scripts/ folder -
# see README.md for the full pipeline explanation.
import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict

csv.field_size_limit(sys.maxsize)

SRC = "../data/indian_medicine_data.csv"
DB = "../data/cheappill.db"
OUT_JSON = "../site/data.json"

COMP_RE = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")
NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")
VOLUME_STRENGTH_RE = re.compile(r"/\d*\.?\d*(ml|gm|g|l)\b")
COUNT_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(tablet|capsule|sachet|suppositor|chewable|lozenge|pill)", re.I
)
VOLUME_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|gm|g|l|litre)\b", re.I)


def norm_strength(raw):
    s = raw.strip().lower()
    s = re.sub(r"\s+", "", s)
    return s


def norm_name(raw):
    s = raw.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def parse_component(raw):
    raw = raw.strip()
    if not raw:
        return None
    m = COMP_RE.match(raw)
    if m:
        name_raw, strength_raw = m.group(1), m.group(2)
    else:
        name_raw, strength_raw = raw, ""
    name_disp = norm_name(name_raw)
    if not name_disp:
        return None
    strength_disp = norm_strength(strength_raw)
    name_key = name_disp.lower()
    return name_key, strength_disp, name_disp, strength_disp


def build_salt(comp1, comp2):
    parts = []
    for raw in (comp1, comp2):
        p = parse_component(raw)
        if p:
            parts.append(p)
    if not parts:
        return None, None, []
    parts.sort(key=lambda x: x[0])
    key = "+".join(f"{k}|{s}" for k, s, _, _ in parts)
    display = " + ".join(
        f"{nd} {sd}".strip() if sd else nd for _, _, nd, sd in parts
    )
    strengths = [s for _, s, _, _ in parts]
    return key, display, strengths


def extract_qty(pack_label, strengths):
    """
    Quantity to normalize price by, chosen based on how the strength is expressed:
    - strength given per volume (e.g. "125mg/5ml", a syrup/drop concentration) ->
      normalize by the pack's volume (ml/gm/l), since bottle size varies independently
      of the labeled concentration.
    - strength given as a flat dose (e.g. "500mg", a tablet/capsule/vial) ->
      normalize by discrete dose-unit count (tablets/capsules) when the pack says so.
      A vial/ampoule/injection pack's "20 ml" is diluent volume, not extra drug content,
      so it is NOT used to normalize a flat-dose strength - the whole vial is the unit.
    """
    if not pack_label:
        return None
    is_volume_strength = any(VOLUME_STRENGTH_RE.search(s) for s in strengths)
    if is_volume_strength:
        m = VOLUME_UNIT_RE.search(pack_label)
    else:
        m = COUNT_UNIT_RE.search(pack_label)
    if not m:
        return None
    try:
        v = float(m.group(1))
        return v if v > 0 else None
    except ValueError:
        return None


def main():
    rows = []
    total = 0
    kept = 0
    with open(SRC, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            total += 1
            if row.get("Is_discontinued", "").strip().upper() == "TRUE":
                continue
            price_raw = row.get("price(₹)", "").strip()
            if not price_raw:
                continue
            try:
                price = float(price_raw)
            except ValueError:
                continue
            if price <= 0:
                continue
            comp1 = row.get("short_composition1", "") or ""
            comp2 = row.get("short_composition2", "") or ""
            salt_key, salt_display, strengths = build_salt(comp1, comp2)
            if not salt_key:
                continue
            name = norm_name(row.get("name", ""))
            if not name:
                continue
            manufacturer = norm_name(row.get("manufacturer_name", ""))
            pack_label = norm_name(row.get("pack_size_label", ""))
            qty = extract_qty(pack_label, strengths)
            unit_price = price / qty if qty else price

            rows.append(
                {
                    "salt_key": salt_key,
                    "salt_display": salt_display,
                    "brand": name,
                    "brand_lower": name.lower(),
                    "manufacturer": manufacturer or "Unknown",
                    "price": price,
                    "pack_label": pack_label,
                    "unit_price": unit_price,
                    "has_unit_price": qty is not None,
                }
            )
            kept += 1

    print(f"total rows read: {total}, kept after clean: {kept}")

    # dedupe: for the same (salt_key, brand_lower) keep the cheapest unit_price entry
    best = {}
    for rec in rows:
        k = (rec["salt_key"], rec["brand_lower"])
        cur = best.get(k)
        if cur is None or rec["unit_price"] < cur["unit_price"]:
            best[k] = rec

    dedup_rows = list(best.values())
    print(f"deduped brand x salt rows: {len(dedup_rows)}")

    # group by salt_key, count distinct brands
    groups = defaultdict(list)
    for rec in dedup_rows:
        groups[rec["salt_key"]].append(rec)

    multi_brand_salts = {k: v for k, v in groups.items() if len(v) >= 2}
    print(f"salt groups total: {len(groups)}, with 2+ brands: {len(multi_brand_salts)}")

    final_rows = [rec for v in multi_brand_salts.values() for rec in v]

    # ---- SQLite load ----
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS meds")
    cur.execute(
        """
        CREATE TABLE meds (
            salt_key TEXT,
            salt_display TEXT,
            brand TEXT,
            manufacturer TEXT,
            price REAL,
            pack_label TEXT,
            unit_price REAL,
            has_unit_price INTEGER
        )
        """
    )
    cur.executemany(
        """INSERT INTO meds
           (salt_key, salt_display, brand, manufacturer, price, pack_label, unit_price, has_unit_price)
           VALUES (:salt_key, :salt_display, :brand, :manufacturer, :price, :pack_label, :unit_price, :has_unit_price)""",
        final_rows,
    )
    cur.execute("CREATE INDEX idx_salt ON meds(salt_key)")
    cur.execute("CREATE INDEX idx_brand ON meds(brand)")
    conn.commit()
    print(f"loaded {len(final_rows)} rows into sqlite")

    # ---- JSON export for frontend (compact: dedupe manufacturer/pack strings,
    # arrays instead of repeated object keys, no separate brand index --
    # the client builds that once at load time from the groups it already has) ----
    manu_ids = {}
    manu_list = []
    pack_ids = {}
    pack_list = []

    def manu_idx(m):
        if m not in manu_ids:
            manu_ids[m] = len(manu_list)
            manu_list.append(m)
        return manu_ids[m]

    def pack_idx(p):
        if p not in pack_ids:
            pack_ids[p] = len(pack_list)
            pack_list.append(p)
        return pack_ids[p]

    groups_out = []
    for salt_key, recs in multi_brand_salts.items():
        recs_sorted = sorted(recs, key=lambda r: r["unit_price"])
        groups_out.append(
            {
                "s": recs_sorted[0]["salt_display"],
                "b": [
                    [
                        r["brand"],
                        manu_idx(r["manufacturer"]),
                        round(r["price"], 2),
                        pack_idx(r["pack_label"]),
                        round(r["unit_price"], 2),
                    ]
                    for r in recs_sorted
                ],
            }
        )

    payload = {"m": manu_list, "p": pack_list, "g": groups_out}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    print(f"wrote {OUT_JSON}, {len(manu_list)} manufacturers, {len(pack_list)} pack labels, {len(groups_out)} groups")

    conn.close()


if __name__ == "__main__":
    main()
