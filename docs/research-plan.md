# Research plan and Stage 1 findings

Stage 1 exploratory analyses and the [final PDF report](../reports/stage-1/Raport_etap_1_Amazon_Video_Games.pdf) are published. The questions below correspond to P1-P3 on report page 4. Later modeling questions and methods remain proposals until experiments are implemented and evaluated.

The team and task owners are listed in [team.md](team.md). The confirmed Stage 1 deadline is October 30, 2026, at 23:59 (Europe/Warsaw). Deliverables and remaining work are tracked in the [project checklist](project-checklist.md).

## Stage 1 research questions and current evidence

### P1: price, rating, and rating count

Is product price associated with average rating and rating count, and do these relationships persist under different treatments of extreme observations?

The [numeric EDA](../notebooks/eda/README-numeric-eda.md) audits all 137,269 products and compares distributions, raw and log-transformed Pearson correlations, Spearman correlations, and sensitivity analyses. Price-complete analyses use 61,972 products; zero prices are retained by default. The observed price associations are weak. Missing prices and the treatment of extreme values limit how broadly the findings can be generalized.

### P2: review length, vocabulary, and rating distribution

How do review lengths and vocabulary differ between high- and low-rated reviews, and what is the rating distribution?

The [text EDA](../notebooks/eda/README-text-eda.md) examines a 500,000-row source prefix, removes 1,594 duplicate source identities, and uses a reproducible 100,000-row sample with seed 42 for lexical exploration. It documents rating imbalance, pooled review-length distributions, and vocabulary differences between 1-star and 5-star reviews. The prefix is not a random sample of the complete category.

**Remaining analysis:** a direct length comparison between rating groups is not yet implemented. Complete that comparison or narrow P2 before claiming that its length-comparison component has been answered. Vocabulary comparisons and pooled length statistics do not establish between-group length differences.

### P3: text features and product characteristics

Are mean review length and the share of negative ratings associated with product characteristics, and how do the results depend on the number of observed reviews per product?

The [combined EDA](../notebooks/eda/README-combined-eda.md) aggregates all 4,624,615 reviews into 137,249 observed products, all matched to product metadata. Twenty metadata products have no observed reviews. Negative share means the fraction of observed ratings equal to 1 or 2; it is a rating-derived measure rather than a text-model prediction.

The full-data Spearman association between mean review length and metadata rating count is approximately +0.125, but becomes negative when analysis is restricted to products with at least five observed reviews. The negative-share/price association is weak (approximately -0.062). Support thresholds of 1, 5, 10, and 30 reviews, missing-value counts, and pairwise versus complete-case scope are documented. These descriptive associations do not demonstrate causality.

## Proposed questions for later modeling

1. How well can review text predict a review's rating or sentiment compared with non-text review and product features?
2. Does combining text and numeric features improve predictive performance over either representation alone?
3. Which review or product groups emerge from unsupervised analysis, and how do their ratings and text differ?

## Completed Stage 1 exploration

- Documented the public Amazon Reviews 2023 Video Games source, prepared text/numeric views, identifiers, and checksums in the [download manifest](../data/manifests/download_manifest.json) and report.
- Published numeric quality checks, missing-value and outlier analyses, distributions, and relationships between price, rating, and rating count.
- Published text cleaning and sampling rules, rating distributions, pooled review lengths, and vocabulary comparisons.
- Published product-level text/numeric relationships and sensitivity checks using all source reviews.
- Included the team, sources, subset rules, research questions, EDA, limitations, and repository link in the final PDF. The P2 length-comparison follow-up remains open as described above.

## Experimental design for later stages

The following work is planned; supervised models, K-means, LDA, transformers, and the results interface are not implemented yet.

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

- `notebooks/eda/`: four runnable Stage 1 scripts, analysis instructions, and dependency files.
- `experiments/supervised/`, `experiments/unsupervised/`, `experiments/nlp/`, `experiments/transformers/`: later experiments.
- `reports/stage-1/`: published final PDF and destination for generated analysis tables; generated working tables are not currently committed.
- `reports/figures/`: plots referenced by reports.
- `app/`: the future results interface.
