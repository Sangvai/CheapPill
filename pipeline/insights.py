# Reference copy: the SQL analysis behind the 3 insight bullets in README.md.
# Run from inside a scripts/ folder with cheappill.db in a sibling data/ folder,
# or just point sqlite3.connect() at this repo's ../cheappill.db.
import sqlite3

conn = sqlite3.connect("../data/cheappill.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== 1. Widest ABSOLUTE price gap (unit price, cheapest vs priciest brand) ===")
for row in cur.execute(
    """
    SELECT salt_display,
           COUNT(DISTINCT brand) AS n_brands,
           MIN(unit_price) AS min_p,
           MAX(unit_price) AS max_p,
           MAX(unit_price) - MIN(unit_price) AS gap,
           ROUND((MAX(unit_price) - MIN(unit_price)) * 100.0 / MIN(unit_price), 1) AS pct_gap
    FROM meds
    GROUP BY salt_key
    HAVING n_brands >= 2
    ORDER BY gap DESC
    LIMIT 10
    """
):
    print(dict(row))

print()
print("=== 2. Widest RELATIVE (%) price gap among salts with a meaningful number of brands (>=5) ===")
for row in cur.execute(
    """
    SELECT salt_display,
           COUNT(DISTINCT brand) AS n_brands,
           MIN(unit_price) AS min_p,
           MAX(unit_price) AS max_p,
           ROUND((MAX(unit_price) - MIN(unit_price)) * 100.0 / MIN(unit_price), 1) AS pct_gap
    FROM meds
    GROUP BY salt_key
    HAVING n_brands >= 5
    ORDER BY pct_gap DESC
    LIMIT 10
    """
):
    print(dict(row))

print()
print("=== 3. Average / median savings opportunity across all comparable salts ===")
row = cur.execute(
    """
    WITH g AS (
        SELECT salt_key,
               MIN(unit_price) AS min_p,
               MAX(unit_price) AS max_p
        FROM meds
        GROUP BY salt_key
        HAVING COUNT(DISTINCT brand) >= 2
    )
    SELECT COUNT(*) AS n_salts,
           ROUND(AVG((max_p - min_p) * 100.0 / min_p), 1) AS avg_pct_savings,
           ROUND(AVG(max_p - min_p), 2) AS avg_abs_gap
    FROM g
    """
).fetchone()
print(dict(row))

# median via python since sqlite has no native median
vals = [r[0] for r in cur.execute(
    """
    WITH g AS (
        SELECT salt_key, MIN(unit_price) AS min_p, MAX(unit_price) AS max_p
        FROM meds GROUP BY salt_key HAVING COUNT(DISTINCT brand) >= 2
    )
    SELECT (max_p - min_p) * 100.0 / min_p FROM g
    """
)]
vals.sort()
median = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
print("median_pct_savings:", round(median, 1))

print()
print("=== 4. Manufacturers most consistently PRICIEST for the same salt (appear as max-price brand often) ===")
for row in cur.execute(
    """
    WITH g AS (
        SELECT salt_key, MAX(unit_price) AS max_p
        FROM meds GROUP BY salt_key HAVING COUNT(DISTINCT brand) >= 3
    ),
    top_hits AS (
        SELECT m.manufacturer, m.salt_key
        FROM meds m
        JOIN g ON g.salt_key = m.salt_key AND m.unit_price = g.max_p
    )
    SELECT manufacturer, COUNT(*) AS times_priciest
    FROM top_hits
    GROUP BY manufacturer
    HAVING times_priciest >= 5
    ORDER BY times_priciest DESC
    LIMIT 15
    """
):
    print(dict(row))

print()
print("=== 5. Manufacturers with highest AVERAGE price rank (normalized 0-1, 1=always priciest) across salts they compete in (min 5 salts) ===")
for row in cur.execute(
    """
    WITH ranked AS (
        SELECT m.salt_key, m.manufacturer, m.unit_price,
               (m.unit_price - mn.min_p) * 1.0 / NULLIF(mx.max_p - mn.min_p, 0) AS norm_rank
        FROM meds m
        JOIN (SELECT salt_key, MIN(unit_price) AS min_p FROM meds GROUP BY salt_key) mn ON mn.salt_key = m.salt_key
        JOIN (SELECT salt_key, MAX(unit_price) AS max_p FROM meds GROUP BY salt_key) mx ON mx.salt_key = m.salt_key
    )
    SELECT manufacturer,
           COUNT(DISTINCT salt_key) AS n_salts,
           ROUND(AVG(norm_rank), 2) AS avg_price_rank
    FROM ranked
    GROUP BY manufacturer
    HAVING n_salts >= 5
    ORDER BY avg_price_rank DESC
    LIMIT 15
    """
):
    print(dict(row))

conn.close()
