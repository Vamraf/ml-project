# ml-project

Analysis of Amazon Reviews 2023, Video Games category.
The complete category contains **4,624,615 reviews** and **137,269 products**.

This machine learning project combines natural-language and numeric data from a public, real-world dataset. The instructor's requirements (ML_proj_1.pdf) are stored in `docs/requirements/project-requirements.pdf`; an English checklist is in `docs/project-checklist.md`. Team members, student IDs, and responsibilities are recorded in [docs/team.md](docs/team.md).

**Stage 1 submission deadline: October 30, 2026, at 23:59 (Europe/Warsaw).**

Stage 1 requires two datasets, exploratory data analysis, research questions, and one PDF report. Later work includes two supervised methods, two unsupervised methods, NLP, transformer models, and a simple interface for exploring results. These analyses, models, and the interface are not implemented yet.

## Project structure

| Directory | Purpose |
| --- | --- |
| `data/raw/` | Original JSONL files, compressed with gzip without data loss |
| `data/numeric/` | Numeric review and product features, retaining identifiers and titles for joins |
| `data/text/` | Review text and its original accompanying fields |
| `data/combined/` | Combined text and numeric review features |
| `data/manifests/` | Data provenance, row counts, and original SHA-256 checksums |
| `scripts/` | Data preparation, restoration, and joining |
| `notebooks/eda/` | Exploratory data analysis |
| `src/ml_project/` | Project source code |
| `models/` | Local model artifacts |
| `reports/figures/` | Report figures |
| `docs/` | Documentation |
| `tests/` | Code tests |
| `experiments/` | Supervised, unsupervised, NLP, and transformer experiments |
| `reports/stage-1/` | First-stage report and supporting material |
| `app/` | Planned interface for exploring results |

Large files are stored using **Git LFS**. A regular repository ZIP may contain only LFS pointers. To clone the repository:

```powershell
git lfs install
git clone https://github.com/Vamraf/ml-project.git
cd ml-project
git lfs pull
```

## Data

Files were copied from the source directory; the originals were preserved. The original CSV and compressed CSV files are unchanged. The names `numeric` and `text` describe the tables' main purpose: the original tables also contain join keys, product titles, and accompanying fields.

Restore the original JSONL files and verify their SHA-256 checksums using Python 3.11+:

```powershell
python scripts/restore_raw.py
```

Download the complete source files again and regenerate the tables using Python 3.11+ and the standard library:

```powershell
python scripts/download_and_prepare.py
```

Join reviews by `review_row`, validating shared fields:

```powershell
python scripts/combine_reviews.py
```

This creates `data/combined/reviews_combined.csv.gz` locally. Generated combined data is not added to Git automatically.

Original tables: `products_numeric.csv`, `reviews_numeric.csv.gz`, and `reviews_text.csv.gz`. Product features can be joined to reviews separately using `parent_asin`.

Source: [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/). URLs pinned to a source revision and checksums are recorded in `data/manifests/download_manifest.json`. Check the source terms before further distribution or use.

## Project plan

See `docs/project-checklist.md` for the required deliverables, `docs/research-plan.md` for a proposed use of the two datasets, and `docs/team.md` for task ownership. The team lead confirmed October 30, 2026, at 23:59 as the Stage 1 deadline, resolving the conflicting dates in the assignment PDF.

## Branches

`main` contains the project structure and dataset.
