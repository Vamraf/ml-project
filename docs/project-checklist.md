# Machine learning project requirements

Source: [project-requirements.pdf](requirements/project-requirements.pdf) (ML_proj_1.pdf, the instructor's original Polish document). Checked items are supported by files in the repository. Later modeling and interface work remain separate from Stage 1.

## Organization and repository

- [x] Form a team of 4-5 people and record names, student IDs, and planned responsibilities in `team.md`.
- [x] Include the team roster, student IDs, and responsibility descriptions in the published report (pages 1 and 3).
- [x] Choose the Video Games topic and formulate research questions combining natural-language and numeric analyses (P1-P3 on report page 4).
- [x] Store source code, the prepared datasets, and data provenance on GitHub.
- [x] Store the completed Stage 1 PDF in `reports/stage-1/`.
- [x] Document dependencies, commands, dataset retrieval, and how to view published figures in the main README and contribution instructions.

## Stage 1

- [x] Describe public, real-world natural-language and numeric datasets from Amazon Reviews 2023 (report page 4).
- [x] Provide source URLs, a pinned revision, checksums, and reproducible subset selection rules (report pages 4-5, manifest, and EDA scripts).
- [x] Perform numeric EDA, text EDA, and combined product-level analysis using descriptive statistics, distributions, correlations, and sensitivity checks (report pages 6-11).
- [x] State research questions and connect them to the available data (P1-P3 on report page 4).
- [x] Publish one PDF containing the team, responsibilities, data sources, subset construction, EDA, research questions, and the GitHub link: [Stage 1 report](../reports/stage-1/Raport_etap_1_Amazon_Video_Games.pdf).

**Confirmed Stage 1 deadline: October 30, 2026, at 23:59 (Europe/Warsaw).** The team lead confirmed this date, resolving the conflicting dates in the assignment PDF. Task owners and responsibilities are listed in `team.md`.

## Full project

- [ ] Discuss suitable supervised methods and explain why they are useful; select and apply two, explain their results, and study the selected methods further.
- [ ] Discuss suitable unsupervised methods and explain why they are useful; select and apply two, explain their results, and study the selected methods further.
- [ ] Include supervised and unsupervised NLP models.
- [ ] Include transformer-based models.
- [ ] Interpret the analyses to answer the research questions and present the results.
- [ ] Implement a simple interface for exploring results and document how to run it.

## Analysis follow-up

- [ ] Complete the length-comparison part of P2: compare review lengths between rating groups, or narrow P2 to match the current pooled length analysis. The vocabulary comparison by rating is already available. This follow-up is distinct from the Stage 1 requirement to state research questions and provide EDA.

## Current dataset mapping

- Natural-language dataset: `data/text/reviews_text.csv.gz` (review text and accompanying identifiers/fields).
- Numeric datasets: `data/numeric/reviews_numeric.csv.gz` and `data/numeric/products_numeric.csv` (numeric features with identifiers and product titles retained).
- Shared provenance: Amazon Reviews 2023, Video Games category. These are complementary views of the same public source, not independent collections; the report explains this relationship.
- The complete category was retained during preparation. The text analysis documents its 500,000-row prefix, duplicate policy, and seeded 100,000-row sample. The combined analysis uses all source reviews.
- Original row counts, source URLs, pinned revision, missing-value counts, and checksums: `data/manifests/download_manifest.json`.
