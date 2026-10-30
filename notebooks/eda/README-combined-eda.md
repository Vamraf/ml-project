# Stage 1: combined EDA (Mykola Zhuchok, 71899)

The analysis code is [04_combined_eda.py](04_combined_eda.py). The five published figures are in [reports/figures/combined_eda/](../../reports/figures/combined_eda/). The analysis addresses P3 in the [published Stage 1 PDF report](../../reports/stage-1/Raport_etap_1_Amazon_Video_Games.pdf) and the [research plan](../../docs/research-plan.md).

## Reproduce the analysis

Use Python 3.11+ and run from the repository root after cloning the public repository. Authentication is not required for public read access. See the [main README](../../README.md#get-the-project-and-data) for cloning instructions and Git LFS setup.

```powershell
git lfs install
git lfs pull
python -m pip install -r notebooks/eda/requirements-combined-eda.txt
python notebooks/eda/04_combined_eda.py
```

The script finds the repository from its own location. It reads `data/text/reviews_text.csv.gz` directly and joins product aggregates to `data/numeric/products_numeric.csv`. It preserves string identifiers and validates original file checksums against the manifest. No personal machine paths or spreadsheet exports are required.

All reviews are processed by default in chunks of 100,000 rows. To use a smaller source prefix:

```powershell
python notebooks/eda/04_combined_eda.py --rows 1000000
```

This option selects the first million source rows, not a random sample. Record that limitation when interpreting a prefix run. Adjust the chunk size with `--chunksize` to control memory use.

Generated aggregates, joined tables, quality checks, correlation matrices, sensitivity results, and findings go to `reports/stage-1/combined_eda/`. Figures go to `reports/figures/combined_eda/`. Override paths using `--reviews`, `--products`, `--output`, and `--figures`.

The five published PNGs and final PDF are committed. Generated working tables and aggregates are not currently committed; run the script to reproduce them. These product-level aggregates are separate from the optional review-row export produced by `scripts/combine_reviews.py` in `data/combined/`.

## Published full-data run

- All 4,624,615 source reviews were processed; 3,618 texts and one title were blank. Blank text is excluded from length means while its valid rating remains in rating summaries.
- Aggregation produced 137,249 observed product IDs, all successfully matched to metadata. Nine matched products have missing titles; that is separate from an unmatched key. Twenty metadata products have no observed review rows.
- There are 37,839 matched products with only one observed review, and 74,069 with fewer than five. The analysis compares support thresholds of 1, 5, 10, and 30 reviews per product.
- The length/rating and length/rating-count plots use 137,196 products with nonblank review text. The negative-share/price plot uses 61,965 products with known prices. Zero prices remain valid observations.
- The heatmap uses pairwise nonmissing values. Pairwise row counts and a separate complete-case matrix (61,941 products) are exported for checking scope differences.
- The main Spearman correlations are approximately -0.133 for review length versus metadata rating, +0.125 for review length versus metadata rating count, and -0.062 for negative-review share versus price. Check the sensitivity figure before generalizing: the length/count association changes sign after restricting products to those with at least five observed reviews.
- `observed_review_count` counts reviews in the analyzed source; `rating_number` is a metadata count. Likewise, the mean observed review rating and metadata average rating need not be equal because collection scope or time may differ.
- The negative share is the fraction of observed ratings equal to 1 or 2. Its association with the observed mean rating partly reflects their shared mathematical definition, not independent confirmation of sentiment.
- Original review rows are retained. Consecutive source row IDs are validated; repeated visible review text is not sufficient evidence of duplicate reviewer identity.
- Log1p axes improve visibility without removing long reviews, expensive products, or popular products. Correlations are descriptive and do not establish causality; each product has equal weight.

The full-data run was checked with Python 3.14.3, pandas 3.0.1, and NumPy 2.4.2. Original dataset provenance and checksums are in `data/manifests/download_manifest.json`.

Published figures: `01_combined_relationship.png`, `02_combined_relationship.png`, `03_combined_relationship.png`, `04_combined_correlations.png`, and `05_support_sensitivity.png`.

This is the combined Stage 1 EDA contribution. The published PDF interprets these findings alongside the numeric and text analyses, including the sensitivity of results to review support. K-means, LDA, and later prediction models remain planned work and are not implemented here.
