# Team and responsibilities

**Stage 1 submission deadline: October 30, 2026, at 23:59 (Europe/Warsaw).**
This date was confirmed by the team lead and resolves the conflicting dates in the assignment PDF.

The Stage 1 contributions below reflect the team's confirmed account of completed work. Later-stage responsibilities remain planned work.

| Team member | Student ID | Main responsibility |
| --- | --- | --- |
| Valentyn Kovbasovskyi | 71540 | Team lead, repository, data collection, development support, review, integration, and interface |
| Daniil Khasanov | 72295 | Text data analysis, cleaning, NLP, and two text classification models |
| Andrei Kudrytski | 71527 | Numeric data cleaning, analysis, modeling, and interpretation |
| Mykola Zhuchok | 71899 | Combined analysis, shared figures, product clustering, and topic modeling |
| Artur Reznychenko | 71615 | Data provenance, reproducibility, report, research questions, and transformers |

## Stage 1 contributions

### Valentyn Kovbasovskyi — 71540 · Team leader

Organized and maintained the GitHub repository, collected and prepared the datasets, coordinated the team's work, and reviewed the submitted contributions. Assisted team members with development, debugging, and theoretical and practical questions.

### Daniil Khasanov — 72295 · Text analysis

Prepared the text EDA, including checks for missing and empty reviews, text cleaning, rating distributions, review-length distributions, and vocabulary comparisons between one-star and five-star reviews. Delivered the analysis script and four figures. A direct comparison of review lengths between rating groups remains a follow-up.

Artifacts: [analysis script](../notebooks/eda/03_text_eda.py), [figures](../reports/figures/text_eda/), and [analysis instructions](../notebooks/eda/README-text-eda.md).

### Andrei Kudrytski — 71527 · Numeric analysis

Prepared the numeric data audit and EDA. Examined missing values, duplicate product identifiers, extreme values, and the distributions of prices, average ratings, and rating counts. Analyzed relationships between these variables and checked sensitivity to preprocessing choices. Delivered two scripts and six figures.

Artifacts: [audit script](../notebooks/eda/01_audit.py), [analysis script](../notebooks/eda/02_analysis.py), [figures](../reports/figures/numeric_eda/).
### Mykola Zhuchok — 71899 · Combined analysis

Aggregated review data by product and joined the results with product metadata. Analyzed relationships between review length, the share of negative ratings, and product characteristics. Checked how the findings changed with the number of reviews available per product. Delivered the combined analysis script and five figures.

Artifacts: [analysis script](../notebooks/eda/04_combined_eda.py), [figures](../reports/figures/combined_eda/).

### Artur Reznychenko — 71615 · Documentation and reproducibility

Prepared the Stage 1 report, bringing together the team's methods, findings, and limitations. Documented the data sources, dataset structure, and subset selection procedures. Checked that the analysis scripts could be reproduced and helped formulate the research questions.

Artifact: [published Stage 1 report](../reports/stage-1/Raport_etap_1_Amazon_Video_Games.pdf).

## Later stages

| Owner | Planned work |
| --- | --- |
| Valentyn Kovbasovskyi | Integrate models, review the final PDF, implement the results interface, and prepare a presentation if needed; continue coordination and theoretical/practical support. |
| Daniil Khasanov | Implement and evaluate two text classification models. |
| Andrei Kudrytski | Implement models using numeric features and interpret their results. |
| Mykola Zhuchok | Apply two unsupervised methods: K-means for products and Latent Dirichlet Allocation (LDA) for text topics. |
| Artur Reznychenko | Implement a transformer-based text model and compare it with the baseline NLP models. |

## Contribution handoff

For later submissions, each member should provide reproducible code or notebooks, cleaning and sampling decisions, figures, findings, and limitations for their assigned work. Keep the team roster and contribution descriptions current in future reports. The [research plan](research-plan.md) and [project checklist](project-checklist.md) distinguish published Stage 1 results, the remaining analysis follow-up, and planned later work.
