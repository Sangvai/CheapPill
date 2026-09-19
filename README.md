# CheapPill.in

Find the cheaper generic alternative for any branded Indian medicine, by matching exact salt composition.

A patient (or their doctor) types the exact brand name printed on a strip. The tool identifies its salt + strength, then lists every other brand selling the identical formula, cheapest first, with manufacturer and % savings clearly shown.

## Why

India's branded-generics market means the same molecule, at the same strength, is sold under dozens (sometimes thousands) of different brand names at wildly different prices - with no easy way for a patient or prescriber to see that at the point of purchase. This tool makes that price gap visible.

## Data

[junioralive/Indian-Medicine-Dataset](https://github.com/junioralive/Indian-Medicine-Dataset) - `DATA/indian_medicine_data.csv`, ~254,000 real Indian medicine pack listings (name, price, manufacturer, pack size, and composition split across two salt+strength fields).

## Pipeline (`pipeline/build_pipeline.py`)

1. Drop discontinued medicines and rows missing price or composition.
2. Normalize the two raw composition fields into one clean **salt key** (e.g. `Amoxycillin 500mg + Clavulanic Acid 125mg`), so the same formula groups together regardless of brand-name spacing/formatting differences in the source data.
3. Group by salt key, keep only groups with **2+ different brands** - a single-brand salt has nothing to compare against.
4. Compute a **unit price** for fair comparison across differing pack sizes:
   - Syrups/drops (strength expressed per volume, e.g. `125mg/5ml`) - normalized per ml, since bottle size varies independently of concentration.
   - Tablets/capsules (flat dose, e.g. `500mg`) - normalized per tablet/capsule when the pack label states a count.
   - Vials/ampoules/injections - compared as whole packs. A "vial of 20 ml" injection's ml figure is diluent volume, not more drug, so dividing by it would produce a nonsense unit price; the labeled dose is delivered per vial regardless of dilution.
5. Load into SQLite (`cheappill.db`) for querying.

## Insights (`pipeline/insights.py`)

Real SQL over the cleaned data turned up:

- **The price gap isn't a tail risk, it's the median.** Across all 6,235 comparable salt groups, the *median* gap between the cheapest and priciest brand of the identical formula is **184%**.
- **Chronic-disease drugs are exactly where this hurts most.** Telmisartan 40mg (a daily hypertension drug, 911 competing brands, both compared strip-of-10 to strip-of-10): ₹0.65/tablet (Telmisoft, Innovexia Life Sciences) vs ₹36.56/tablet (Micartel, Indchemie) - a **56x** difference for a pill taken daily for years.
- **"Priciest" isn't just multinational originators vs. generics - it's generic-vs-generic too.** Sun Pharmaceutical Industries was the single most expensive brand for the same salt combination in **171 different drug groups**, more than any other manufacturer.

## App (`app.py`)

Streamlit app querying `cheappill.db` directly with SQL - exact, case-insensitive brand search, cheapest-first alternatives, % savings vs. the searched brand, prefix suggestions on a miss.

Run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Caveats

- Brand/salt matching is exact by design (no fuzzy matching) - always confirm composition and dosage with a pharmacist before switching brands.
- The source dataset only tracks two composition fields; a small number of brands with 3+ active ingredients may be grouped by their first two, which can occasionally merge formulations that differ in a third component.
