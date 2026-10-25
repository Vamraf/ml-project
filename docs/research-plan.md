# Proposed research plan

This is a starting proposal, not a completed experiment or an additional assignment requirement. Confirm the final questions and methods with the team and the course material.

The team and task owners are listed in `team.md`. Stage 1 is due on October 30, 2026, at 23:59 (Europe/Warsaw).

## Research questions

1. How well can review text predict a review's rating or sentiment compared with non-text review and product features?
2. Does combining text and numeric features improve predictive performance over either representation alone?
3. Which review or product groups emerge from unsupervised analysis, and how do their ratings and text differ?

## Stage 1 exploration

- Describe the text and numeric tables, their provenance, row counts, columns, types, and join keys.
- Examine missing values, rating imbalance, review lengths, duplicates, timestamps, product popularity, and numeric distributions.
- Explore the relationship between text and numeric features, without treating observations as causal evidence.
- State which rows and columns are used. Keep full-data statistics distinct from any reproducible sample used for expensive analyses.

## Experimental design

- Join review views using `review_row`; join product features using `parent_asin`.
- Define the prediction target before selecting features. If predicting rating, exclude `rating` from inputs; if predicting sentiment derived from rating, exclude both the original rating and its label transformation.
- Consider product-level or chronological splits to reduce leakage. Fit vectorizers, preprocessing, and models only on training data.
- Check whether product-level aggregate ratings or counts reveal information unavailable at prediction time before using them as features.
- Use appropriate baselines and metrics; account for the strongly imbalanced rating distribution.
- Daniil will implement two text classifiers; Andrei will develop and interpret models using numeric features. Final supervised model choices remain to be agreed.
- Mykola will apply K-means to products and Latent Dirichlet Allocation (LDA) to text topics as the two planned unsupervised methods.
- Artur will implement a transformer-based text model and compare it with the baseline NLP models. Valentyn will integrate the models and implement the results interface.
- Save configurations, seeds, splits, metrics, and figures so results can be reproduced and displayed in the planned interface.

## Repository locations

- `notebooks/eda/`: first-stage exploratory analyses.
- `experiments/supervised/`, `experiments/unsupervised/`, `experiments/nlp/`, `experiments/transformers/`: later experiments.
- `reports/stage-1/`: report sources and final PDF.
- `reports/figures/`: plots referenced by reports.
- `app/`: the future results interface.
