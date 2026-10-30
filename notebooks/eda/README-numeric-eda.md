# Stage 1: numeric EDA (Andrei Kudrytski, 71527)

The analysis consists of [01_audit.py](01_audit.py) and [02_analysis.py](02_analysis.py). Keep both files together: the second imports audit helpers from the first. The six published figures are in [reports/figures/numeric_eda/](../../reports/figures/numeric_eda/). The analysis addresses P1 in the [published Stage 1 PDF report](../../reports/stage-1/Raport_etap_1_Amazon_Video_Games.pdf) and the [research plan](../../docs/research-plan.md).

## Reproduce the analysis

Use Python 3.11+ and run from the repository root after cloning the public repository. Authentication is not required for public read access. See the [main README](../../README.md#get-the-project-and-data) for cloning instructions and Git LFS setup.

```powershell
git lfs install
git lfs pull
python -m pip install -r notebooks/eda/requirements-numeric-eda.txt
python notebooks/eda/01_audit.py
python notebooks/eda/02_analysis.py
```

Both scripts find `data/numeric/products_numeric.csv` relative to their location, independently of the current working directory. No personal machine paths are hardcoded. For another file, pass `--input PATH`.

Audit results, numeric tables, prepared data, and findings are generated in `reports/stage-1/numeric_eda/`. The analysis saves figures in `reports/figures/numeric_eda/`. Override table and figure destinations with `--output PATH` and `--figures PATH`, respectively (`--figures` applies to `02_analysis.py`).

The six published PNGs and final PDF are committed. Generated working tables, audit outputs, and prepared analysis data are not currently committed; run the scripts to reproduce them.

## Published run and interpretation

- The complete product table contains 137,269 rows. There are no duplicate product IDs or missing average ratings/rating counts. Nine product titles are missing.
- There are 75,297 missing prices (54.85%) and 32 zero prices. Zero prices are retained by default because zero is not automatically an error. The explicit `--zero-price-as-missing` option can test a different assumption.
- Overall rating and rating-count distributions use all available products. The common subset for price relationships contains 61,972 products (45.15%). Positive-price logarithmic plots use 61,940 products.
- The first price histogram hides 620 values above the 99th percentile (approximately USD 359.98). Those prices remain unchanged in the tables and primary correlation analysis.
- Extreme values are flagged using raw and log1p IQR fences; they are not automatically considered invalid. Separate sensitivity results compare filtering, winsorization, and restriction to products with at least 10 ratings.
- Full-table correlations export pairwise observation counts. The three displayed correlation matrices use one common complete-case subset. Log-transformed variables are labeled explicitly.
- Group comparisons examine associations with price availability; they do not identify MAR versus MNAR. The Mann-Whitney effect includes half the probability of ties.
- Explicit rating intervals and exact recorded ratings are shown separately. The exact 5.0 group in the full table contains 11,534 products and has a median of two ratings.
- Approximate confidence intervals assume independent product observations. This collected category is not a designed random sample; correlation and statistical significance do not establish causation or population representativeness.

The run was checked with Python 3.14.3, pandas 3.0.1, and NumPy 2.4.2. Data provenance and original checksums are recorded in `data/manifests/download_manifest.json`. The scripts also save an input-file checksum in the audit output.

Published figures: `01_distributions.png`, `02_correlations.png`, `03_relationships.png`, `04_price_groups.png`, `exact_rating_groups.png`, and `rating_intervals.png`.

These scripts implement Stage 1 EDA. Selected findings and their limitations are interpreted in the published PDF alongside the text and combined analyses. Numeric prediction models are planned for later stages and are not implemented here.
