# Stage 1: text EDA (Daniil Khasanov, 72295)

The analysis code is `03_text_eda.py`. Published figures are in `reports/figures/text_eda/`.

## Reproduce the analysis

Use Python 3.10+ and run these commands from the repository root after cloning and authenticating to the private repository:

```powershell
git lfs install
git lfs pull
python -m pip install -r notebooks/eda/requirements-text-eda.txt
python notebooks/eda/03_text_eda.py
```

The script locates the repository from its own location. It can read the compressed `data/raw/Video_Games.jsonl.gz` directly; restoring the uncompressed JSONL is optional. No personal machine paths or new downloads are required. If using a separate input file, pass `--input PATH`.

Generated tables, the cleaned sample, provenance, and findings go to `reports/stage-1/text_eda/`. Figures go to `reports/figures/text_eda/`. Override these locations with `--output PATH` and `--figures PATH`.

## Published run

- First 500,000 source reviews were audited; this prefix is not a random sample of the full category.
- There were 144 missing/blank review texts and 1,594 duplicate source identities under `(user_id, asin, timestamp, text)`.
- Keeping the first duplicate identity left 498,406 rows. Repeated texts with different identities were retained.
- Text exploration used 100,000 retained rows with seed 42; 30 texts in that sample were empty after cleaning.
- The rating plot describes the 498,406 retained prefix rows. Vocabulary and length plots describe the 100,000-row text sample.
- Word counts are normalized per 10,000 content tokens to compare unequal rating groups. Negation is retained; the groups shown are exactly one-star and five-star reviews.
- The length plots hide 2,492 reviews with at least 2,000 characters and 2,092 with at least 400 whitespace-separated words. Those rows remain in the dataset.
- Word clouds are illustrations, not trained sentiment models or statistical significance tests.

The run was checked with Python 3.14.3, pandas 3.0.1, NumPy 2.4.2, and Matplotlib 3.10.8. Source revision and original dataset checksums are in `data/manifests/download_manifest.json`.

Published figures: `rating_distribution.png`, `review_lengths.png`, `top_words_by_rating.png`, and `wordclouds.png`.
