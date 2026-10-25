# Machine learning project requirements

Source: `requirements/project-requirements.pdf` (ML_proj_1.pdf, the instructor's original Polish document). This checklist describes required work, not completed analyses. It replaces the checklist for the previously supplied assignment.

## Organization and repository

- [ ] Form a team of 4-5 people and record names, student IDs, and responsibilities in the submitted report.
- [ ] Choose a topic and formulate research questions that combine insights from natural-language and numeric analyses.
- [x] Store source code, the prepared datasets, and data provenance on GitHub.
- [ ] Store all project reports in the repository.
- [ ] Provide complete instructions for reproducing results and viewing them through a simple interface (for example, Gradio).

## Stage 1

- [ ] Describe two public, real-world datasets: one containing natural-language data and one containing numeric data. Do not use simulated or synthetic data.
- [ ] Provide complete source information and, if subsets are used, exact instructions for reproducing their selection.
- [ ] Perform exploratory data analysis using methods from Statistics or Python for DS and AI.
- [ ] State research questions and connect them to the datasets.
- [ ] Prepare one PDF report containing team details and responsibilities, data sources, subset selection if applicable, EDA, research questions, and the GitHub repository link.
- [ ] Submit that single PDF to the project section on Platon.

**Deadline discrepancy:** the document header says Friday, October 30, 2026, at 23:59; the Stage 1 section says October 31, 2026, at 23:59. Confirm the correct date with the instructor; do not assume the later date.

## Full project

- [ ] Discuss suitable supervised methods and explain why they are useful; select and apply two, explain their results, and study the selected methods further.
- [ ] Discuss suitable unsupervised methods and explain why they are useful; select and apply two, explain their results, and study the selected methods further.
- [ ] Include supervised and unsupervised NLP models.
- [ ] Include transformer-based models.
- [ ] Interpret the analyses to answer the research questions and present the results.
- [ ] Implement a simple interface for exploring results and document how to run it.

## Current dataset mapping

- Natural-language dataset: `data/text/reviews_text.csv.gz` (review text and accompanying identifiers/fields).
- Numeric datasets: `data/numeric/reviews_numeric.csv.gz` and `data/numeric/products_numeric.csv` (numeric features with identifiers and product titles retained).
- Shared provenance: Amazon Reviews 2023, Video Games category. These are complementary views of the same public source, not independent collections. Describe this relationship explicitly and confirm with the instructor if independent sources are expected.
- The complete category was retained; no sampling was applied during preparation. Any later sampling or filtering must be documented separately.
- Original row counts, source URLs, pinned revision, missing-value counts, and checksums: `data/manifests/download_manifest.json`.
