# ml-project

Machine learning project using **Amazon Reviews 2023: Video Games**. The public, real-world data contains **4,624,615 reviews** and **137,269 product metadata records**. Text and numeric tables describe complementary views of the same category.

**Stage 1 deadline: October 30, 2026, at 23:59 (Europe/Warsaw).** The team lead confirmed this date to resolve conflicting dates in the assignment document.

## Stage 1 status

| Deliverable | Current status |
| --- | --- |
| Five-person team, student IDs, and responsibilities | Recorded in [docs/team.md](docs/team.md) |
| Source datasets, preparation code, and provenance | Available through Git LFS; checksums and source URLs recorded |
| Numeric EDA: Andrei | Published audit, analysis, instructions, and 6 figures |
| Text EDA: Daniil | Published analysis, instructions, and 4 figures |
| Combined text/numeric EDA: Mykola | Published full-data analysis, instructions, and 5 figures |
| Research questions | Proposed in [docs/research-plan.md](docs/research-plan.md); finalize and include in the report |
| Final Stage 1 PDF report | Not yet published in `reports/stage-1/` |
| Submission to Platon | Requires the final PDF; submission is not tracked by this repository |

Stage 1 requires a single PDF covering the team and contributions, data sources and subset construction, EDA, research questions, and the GitHub link. The instructor's original document is [project-requirements.pdf](docs/requirements/project-requirements.pdf). The [project checklist](docs/project-checklist.md) describes required work; its unchecked items are not an up-to-date completion dashboard.

Supervised models, unsupervised models, transformers, and the results interface belong to later project work and are not implemented yet. The placeholder folders for that work do not indicate completed features.

## Get the project and data

Install Git, Git LFS, and Python 3.11+ before running the analyses. From a terminal:

```powershell
git lfs install
git clone https://github.com/Vamraf/ml-project.git
cd ml-project
git lfs pull
```

Large dataset files use **Git LFS**. A GitHub file preview may show a pointer, and a regular repository ZIP may contain pointers rather than the actual data. Use the commands above to obtain the dataset files.

To update an existing clone:

```powershell
git pull --ff-only
git lfs pull
```

## Reproduce Stage 1 analyses

Run from the repository root. Each script also resolves its data paths from the script location, so no personal computer directory is hardcoded.

```powershell
python -m pip install -r notebooks/eda/requirements-numeric-eda.txt -r notebooks/eda/requirements-text-eda.txt -r notebooks/eda/requirements-combined-eda.txt

python notebooks/eda/01_audit.py
python notebooks/eda/02_analysis.py
python notebooks/eda/03_text_eda.py
python notebooks/eda/04_combined_eda.py
```

Keep `01_audit.py` and `02_analysis.py` together: the numeric analysis imports audit helpers from the first file. The text analysis can read the compressed original JSONL directly, and the combined analysis streams the compressed review CSV. Manually extracting the source archives is not required for these analyses.

| Contribution | Code | Instructions | Published figures |
| --- | --- | --- | --- |
| Numeric: Andrei | [01_audit.py](notebooks/eda/01_audit.py), [02_analysis.py](notebooks/eda/02_analysis.py) | [Numeric EDA](notebooks/eda/README-numeric-eda.md) | [numeric_eda](reports/figures/numeric_eda/) |
| Text: Daniil | [03_text_eda.py](notebooks/eda/03_text_eda.py) | [Text EDA](notebooks/eda/README-text-eda.md) | [text_eda](reports/figures/text_eda/) |
| Combined: Mykola | [04_combined_eda.py](notebooks/eda/04_combined_eda.py) | [Combined EDA](notebooks/eda/README-combined-eda.md) | [combined_eda](reports/figures/combined_eda/) |

Generated tables, quality checks, sampling details, and findings go to `reports/stage-1/numeric_eda/`, `reports/stage-1/text_eda/`, and `reports/stage-1/combined_eda/`. Published PNGs are already available under `reports/figures/`; open them directly on GitHub. The generated working tables are not currently committed, and these outputs do not replace the required final PDF report.

### Analysis scope and interpretation

- **Numeric:** all 137,269 products are audited. Price-complete analyses use 61,972 products; zero prices are retained by default. Missing-price and outlier sensitivity analyses are exported separately.
- **Text:** the source prefix contains 500,000 reviews. Removing 1,594 duplicate source identities leaves 498,406 rows; lexical exploration uses a reproducible 100,000-row sample with seed 42. This prefix is not a random sample of the complete category.
- **Combined:** all 4,624,615 source reviews are aggregated in chunks into 137,249 observed products, with zero unmatched metadata keys. Twenty metadata products have no observed reviews. Products with little review support are examined separately in sensitivity comparisons.
- Correlation sample sizes depend on missing values and analysis scope. `observed_review_count` and metadata `rating_number` are different measures. Associations and small p-values do not establish causality.

For a shorter combined-analysis run:

```powershell
python notebooks/eda/04_combined_eda.py --rows 1000000
```

This selects the first million original rows. Omitting `--rows`, or using `--rows 0`, processes all reviews. See the contribution instructions for supported output paths and other options.

## Datasets and provenance

| Location | Contents |
| --- | --- |
| `data/raw/Video_Games.jsonl.gz` | Original review JSONL, compressed without data loss |
| `data/raw/meta_Video_Games.jsonl.gz` | Original product metadata JSONL, compressed without data loss |
| `data/text/reviews_text.csv.gz` | 4,624,615 review rows with text, ratings, and join keys |
| `data/numeric/reviews_numeric.csv.gz` | Numeric review features and accompanying join fields |
| `data/numeric/products_numeric.csv` | 137,269 product records with numeric features, IDs, and titles |
| `data/manifests/download_manifest.json` | Source URLs, pinned revision, row counts, checksums, and preparation statistics |

The names `text` and `numeric` describe each table's main purpose; the original tables also retain identifiers, titles, and supporting fields. Review views can be joined by `review_row`, and review/product data by `parent_asin`. No rows were sampled during the original dataset preparation; later analysis subsets and cleaning are documented separately.

Source: [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/), category Video Games. Exact pinned download URLs are in [download_manifest.json](data/manifests/download_manifest.json).

Optional preparation commands:

```powershell
python scripts/restore_raw.py
python scripts/download_and_prepare.py
python scripts/combine_reviews.py
```

`restore_raw.py` restores and verifies the original JSONL files. `download_and_prepare.py` can download the sources and regenerate the prepared tables. `combine_reviews.py` joins the text/numeric review views into `data/combined/reviews_combined.csv.gz`; this optional row-level export is separate from Mykola's product-level combined EDA.

## Repository structure

```text
data/
  raw/                 Original compressed JSONL
  text/                Prepared text review table
  numeric/             Prepared numeric review/product tables
  manifests/           Provenance and checksums
  combined/            Optional generated review-view join
notebooks/eda/         Four runnable EDA scripts, instructions, and dependencies
reports/
  figures/
    text_eda/          Daniil: 4 published PNGs
    numeric_eda/       Andrei: 6 published PNGs
    combined_eda/      Mykola: 5 published PNGs
  stage-1/             Destination for generated tables and final report
scripts/               Source download, restoration, and preparation
docs/                  Team, research plan, checklist, and original assignment
app/                   Placeholder for the future results interface
experiments/           Placeholders for later modeling experiments
models/                Local model artifacts
src/ml_project/        Placeholder for reusable project code
tests/                 Placeholder for future automated tests
```

## Access and collaboration

The repository is **public**: anyone with [the project link](https://github.com/Vamraf/ml-project) can view and clone it. Direct write access is limited to the owner and collaborators granted write permission. `main` contains the current shared project state.
