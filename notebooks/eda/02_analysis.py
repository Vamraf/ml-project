"""Stage 1 numeric EDA: completeness, distributions, relationships and sensitivity.

Keep 01_audit.py in the same folder as this file.
Dependencies: python -m pip install pandas numpy matplotlib seaborn scipy
Run: python 02_analysis.py
Options: --input PATH --output DIRECTORY --figures DIRECTORY --zero-price-as-missing
Zero prices are retained by default: they are not automatically assumed invalid.
No source file is overwritten; analyses and their scopes are exported separately.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Reuse the audit implementation without executing its command-line entry point.
spec = importlib.util.spec_from_file_location('numeric_audit', Path(__file__).with_name('01_audit.py'))
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)
MIN_REVIEWS = 10  # A sensitivity threshold, not a guarantee of rating reliability.


def save(fig, folder, name):
    fig.tight_layout()
    fig.savefig(folder / name, dpi=180, bbox_inches='tight')
    plt.close(fig)


def fences(series):
    q1, q3 = series.quantile([.25, .75])
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


def correlation_tables(frame, output, label):
    columns = ['price_usd', 'average_rating', 'rating_number']
    raw = frame[columns]
    logs = raw.rename(columns={'price_usd': 'log1p_price_usd', 'rating_number': 'log1p_rating_number'}).copy()
    logs['log1p_price_usd'] = np.log1p(logs['log1p_price_usd'])
    logs['log1p_rating_number'] = np.log1p(logs['log1p_rating_number'])
    matrices = [raw.corr(), logs.corr(), raw.corr(method='spearman')]
    for matrix, method in zip(matrices, ['pearson_raw', 'pearson_log1p', 'spearman']):
        matrix.to_csv(output / f'{label}_{method}.csv')
    # Record pairwise observation counts because price is missing for many products.
    valid = raw.notna().astype('int64')
    valid.T.dot(valid).to_csv(output / f'{label}_pairwise_counts.csv')
    return matrices


def rating_groups(frame, output, figures, exact=False):
    values = frame.dropna(subset=['average_rating', 'rating_number']).copy()
    if exact:
        values['group'] = values.average_rating.round(1)
        title = 'Exact recorded rating (0.1-star precision)'
        filename = 'exact_rating_groups'
    else:
        # Use explicit intervals rather than rounding 4.8/4.9 into a group called 5.0.
        edges = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5.0001]
        labels = ['1.0–<1.5', '1.5–<2.0', '2.0–<2.5', '2.5–<3.0', '3.0–<3.5', '3.5–<4.0', '4.0–<4.5', '4.5–5.0']
        values['group'] = pd.cut(values.average_rating, bins=edges, labels=labels, right=False)
        title = 'Explicit rating intervals (final interval includes 5.0)'
        filename = 'rating_intervals'
    summary = values.groupby('group', observed=True).agg(n=('rating_number', 'size'),
                     median_reviews=('rating_number', 'median'), share_le3=('rating_number', lambda s: s.le(3).mean()))
    summary.to_csv(output / f'{filename}.csv')
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    axes[0].bar(np.arange(len(summary)), summary.median_reviews, color='darkorange')
    if summary.median_reviews.gt(0).all():
        axes[0].set_yscale('log')
    axes[0].set_ylabel('Median rating count')
    axes[1].bar(np.arange(len(summary)), summary.share_le3 * 100, color='seagreen')
    axes[1].set_ylabel('Products with at most 3 ratings (%)')
    for ax in axes:
        ax.set_xticks(np.arange(len(summary)), summary.index.astype(str), rotation=90)
        ax.set_xlabel(title)
    fig.suptitle(f'All products with valid rating/count: n={len(values):,}; price not required')
    save(fig, figures, f'{filename}.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--figures', type=Path)
    parser.add_argument('--zero-price-as-missing', action='store_true')
    args = parser.parse_args()
    path = audit_module.resolve_input(args.input)
    output = (args.output or audit_module.default_output(path)).resolve()
    # Keep published figures separate from generated report tables in the repository.
    if args.figures is not None:
        figures = args.figures.resolve()
    elif path.parent.name == 'numeric' and path.parent.parent.name == 'data':
        figures = path.parents[2] / 'reports/figures/numeric_eda'
    else:
        figures = output / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    frame, coercions = audit_module.load_products(path)
    source_summary = audit_module.write_audit(frame, coercions, path, output)

    # Fail explicitly for malformed data instead of truncating counts or hiding errors.
    checks = source_summary['checks']
    fatal = {key: value for key, value in checks.items() if value and
             (key in ['missing_parent_asin', 'negative_price', 'rating_outside_1_5', 'negative_rating_count', 'noninteger_rating_count'] or key.startswith('nonfinite_'))}
    if fatal or any(coercions.values()):
        raise ValueError(f'Correct malformed source values before analysis: {fatal}; conversion failures: {coercions}')
    before = len(frame)
    frame = frame.drop_duplicates().copy()
    if frame.parent_asin.duplicated().any():
        raise ValueError('Conflicting duplicate parent_asin values need manual resolution')
    zeros = int(frame.price_usd.eq(0).sum())
    if args.zero_price_as_missing:
        frame.loc[frame.price_usd.eq(0), 'price_usd'] = np.nan
    # The full prepared table preserves products whose price is unknown.
    frame.to_csv(output / 'products_prepared_all.csv', index=False)
    work = frame.dropna(subset=['price_usd', 'average_rating', 'rating_number']).copy()
    if len(work) < 20 or work.price_usd.nunique() < 2:
        raise ValueError('Insufficient complete cases or price variation for this analysis')
    work.to_csv(output / 'products_price_complete_cases.csv', index=False)
    sns.set_theme(style='whitegrid')

    # Group comparisons describe associations with missingness, not MAR/MNAR proof.
    differences = []
    has_price = frame.price_usd.notna()
    for col in ['average_rating', 'rating_number']:
        a = frame.loc[has_price, col].dropna()
        b = frame.loc[~has_price, col].dropna()
        if len(a) and len(b):
            u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
            # U/(n1*n2) is P(A>B) + 0.5*P(A=B), including ties.
            effect = u / (len(a) * len(b))
            differences.append(dict(metric=col, n_with_price=len(a), n_without_price=len(b),
                                    median_with_price=a.median(), median_without_price=b.median(),
                                    probability_superiority_half_ties=effect, p_value=p))
    pd.DataFrame(differences).to_csv(output / 'price_missingness_associations.csv', index=False)

    # Flag outliers on both scales; retain extremes in the primary analysis.
    outlier_rows = []
    filtered = pd.Series(True, index=work.index)
    winsorized = work.copy()
    for col in ['price_usd', 'rating_number']:
        for scale in ['raw', 'log1p']:
            series = work[col] if scale == 'raw' else np.log1p(work[col])
            lo, hi = fences(series)
            outside = ~series.between(lo, hi)
            outlier_rows.append(dict(column=col, scale=scale, lower=lo if scale == 'raw' else np.expm1(lo),
                                     upper=hi if scale == 'raw' else np.expm1(hi), n_outliers=int(outside.sum()),
                                     percent=outside.mean() * 100))
            if scale == 'log1p':
                filtered &= ~outside
                winsorized[col] = np.expm1(series.clip(lo, hi))
    pd.DataFrame(outlier_rows).to_csv(output / 'outlier_flags_iqr.csv', index=False)

    positive = work.loc[work.price_usd.gt(0)]
    p99 = work.price_usd.quantile(.99)
    hidden = int(work.price_usd.gt(p99).sum())
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    # Filter for display only; do not pile expensive products into the last bin.
    axes[0, 0].hist(work.loc[work.price_usd.le(p99), 'price_usd'], bins=60)
    axes[0, 0].set(title=f'Known prices <= p99 (${p99:.2f}); {hidden:,} higher prices hidden', xlabel='Price (USD)')
    if len(positive):
        edges = np.geomspace(positive.price_usd.min(), positive.price_usd.max(), 51)
        axes[0, 1].hist(positive.price_usd, bins=edges)
        axes[0, 1].set_xscale('log')
    axes[0, 1].set(title=f'Positive prices only: n={len(positive):,}', xlabel='Price (USD, log axis)')
    axes[1, 0].hist(frame.average_rating.dropna(), bins=np.arange(.95, 5.051, .1))
    axes[1, 0].set(title=f'Ratings: all available values, n={frame.average_rating.notna().sum():,}', xlabel='Average rating')
    counts = frame.loc[frame.rating_number.gt(0), 'rating_number']
    if len(counts):
        axes[1, 1].hist(counts, bins=np.geomspace(.5, counts.max() + 1, 40))
        axes[1, 1].set_xscale('log')
    axes[1, 1].set(title=f'Positive rating counts: n={len(counts):,}; zeros excluded from log display', xlabel='Rating count (log axis)')
    for ax in axes.flat:
        ax.set_ylabel('Products')
    save(fig, figures, '01_distributions.png')

    # Export all-product pairwise correlations AND common complete-case comparisons.
    correlation_tables(frame, output, 'all_products_pairwise')
    matrices = correlation_tables(work, output, 'price_complete_cases')
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, matrix, title in zip(axes, matrices, ['Pearson: original values', 'Pearson: log1p price/count', 'Spearman']):
        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, ax=ax)
        ax.set_title(title)
    fig.suptitle(f'Common complete-case subset: n={len(work):,} ({len(work)/len(frame):.2%} of products)')
    save(fig, figures, '02_correlations.png')

    # Compare sensitivity choices without calling every extreme value an error.
    sensitivity = []
    for label, subset in [('primary', work), ('log_iqr_filter', work.loc[filtered]),
                          ('log_iqr_winsorized', winsorized), ('at_least_10_ratings', work.loc[work.rating_number.ge(MIN_REVIEWS)])]:
        for a, b in [('price_usd', 'average_rating'), ('price_usd', 'rating_number'), ('average_rating', 'rating_number')]:
            rho, p = stats.spearmanr(subset[a], subset[b]) if len(subset) > 2 else (np.nan, np.nan)
            sensitivity.append(dict(variant=label, n=len(subset), pair=f'{a} / {b}', spearman=rho, p_value=p))
    pd.DataFrame(sensitivity).to_csv(output / 'correlation_sensitivity.csv', index=False)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    specs = [(np.log1p(work.price_usd), work.average_rating, 'log1p(price USD)', 'Average rating'),
             (np.log1p(work.price_usd), np.log1p(work.rating_number), 'log1p(price USD)', 'log1p(rating count)'),
             (work.average_rating, np.log1p(work.rating_number), 'Average rating', 'log1p(rating count)')]
    for i, (ax, (x, y, xl, yl)) in enumerate(zip(axes, specs)):
        hb = ax.hexbin(x, y, gridsize=45, bins='log', mincnt=1, cmap='Blues')
        fig.colorbar(hb, ax=ax, label='Products per hexagon (log color scale)')
        groups = pd.DataFrame({'x': x, 'y': y}).groupby(pd.cut(x, bins=25), observed=True)
        summary = groups.agg(x=('x', 'median'), n=('y', 'count'), med=('y', 'median'),
                             q25=('y', lambda s: s.quantile(.25)), q75=('y', lambda s: s.quantile(.75)))
        summary = summary.loc[summary.n.ge(200)]
        summary.to_csv(output / f'hexbin_trend_{i+1}.csv')
        ax.plot(summary.x, summary.med, color='red', label='Median; bins with n >= 200')
        ax.plot(summary.x, summary.q25, '--', color='red', linewidth=1, label='25th/75th percentiles')
        ax.plot(summary.x, summary.q75, '--', color='red', linewidth=1)
        ax.set(xlabel=xl, ylabel=yl)
        ax.legend(fontsize=8)
    fig.suptitle(f'Price-complete subset, n={len(work):,}; associations do not establish causality')
    save(fig, figures, '03_relationships.png')

    # Price quantile groups may differ in size when many prices are tied.
    work['price_bucket'] = pd.qcut(work.price_usd, q=10, duplicates='drop')
    groups = work.groupby('price_bucket', observed=True)
    summary = groups.agg(n=('average_rating', 'size'), mean_rating=('average_rating', 'mean'),
                         median_rating=('average_rating', 'median'), sem=('average_rating', 'sem'), median_reviews=('rating_number', 'median'))
    summary['ci95_halfwidth'] = 1.96 * summary['sem']
    summary['mean_rating_ge10'] = work.loc[work.rating_number.ge(10)].groupby('price_bucket', observed=True).average_rating.mean()
    summary['n_ge10'] = work.loc[work.rating_number.ge(10)].groupby('price_bucket', observed=True).size()
    summary.to_csv(output / 'price_quantile_groups.csv')
    labels = [f'({bucket.left:.2f}, {bucket.right:.2f}]' for bucket in summary.index]
    x = np.arange(len(summary))
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    axes[0].errorbar(x, summary.mean_rating, yerr=summary.ci95_halfwidth, fmt='o-', capsize=3, label='Mean +/- approximate 95% normal interval')
    axes[0].plot(x, summary.median_rating, '^:', label='Median')
    axes[0].plot(x, summary.mean_rating_ge10, 's--', label='Mean: products with >=10 ratings')
    axes[0].set_ylabel('Average rating')
    axes[0].legend(fontsize=8)
    axes[1].bar(x, summary.median_reviews, color='darkorange')
    axes[1].set_ylabel('Median rating count')
    for ax in axes:
        ax.set_xticks(x, labels, rotation=60, ha='right')
        ax.set_xlabel('Price quantile interval (USD); exact boundaries in CSV')
    fig.suptitle(f'Price-complete subset, n={len(work):,}; intervals assume independent product observations')
    save(fig, figures, '04_price_groups.png')

    rating_groups(frame, output, figures, exact=False)
    rating_groups(frame, output, figures, exact=True)
    exact5 = frame.loc[frame.average_rating.eq(5), 'rating_number'].dropna()
    middle = frame.loc[frame.average_rating.between(4.3, 4.7), 'rating_number'].dropna()
    test = {'exact_5_n': len(exact5), 'exact_5_median_count': float(exact5.median()),
            'rating_4_3_to_4_7_n': len(middle), 'rating_4_3_to_4_7_median_count': float(middle.median())}
    if len(exact5) and len(middle):
        u, p = stats.mannwhitneyu(exact5, middle, alternative='less')
        test.update(u=float(u), p_value=float(p), probability_superiority_half_ties=float(u / (len(exact5) * len(middle))))
    (output / 'exact_rating_comparison.json').write_text(json.dumps(test, indent=2), encoding='utf-8')
    overview = {'source_rows': before, 'exact_duplicates_removed': before-len(frame), 'retained_all_products': len(frame),
                'price_complete_cases': len(work), 'price_complete_percent': len(work)/len(frame)*100,
                'source_zero_prices': zeros, 'zero_price_policy': 'replace with missing by explicit option' if args.zero_price_as_missing else 'retain; no evidence that zero is always invalid',
                'price_p99': float(p99), 'prices_hidden_above_p99_in_plot_only': hidden,
                'primary_outlier_policy': 'retain; compare log-IQR filtering and winsorization separately',
                'python': sys.version.split()[0], 'pandas': pd.__version__, 'numpy': np.__version__}
    (output / 'analysis_summary.json').write_text(json.dumps(overview, indent=2), encoding='utf-8')
    notes = f'''# Numeric EDA: findings and interpretation

- Source: {path.name}, complete supplied product table ({before:,} rows). See audit_summary.json for the source checksum and quality checks.
- Missing source prices: {frame.price_usd.isna().sum():,} under the selected zero-price policy. Zero prices in source: {zeros}; policy: {overview['zero_price_policy']}.
- Overall rating/count analysis retains all {len(frame):,} products. Price relationships use {len(work):,} complete cases ({len(work)/len(frame):.2%}); findings about these rows do not automatically generalize to products with unknown prices.
- Pairwise full-table correlations include different row counts; consult all_products_pairwise_pairwise_counts.csv. The three plotted correlation matrices share the same complete-case rows.
- Missingness group comparisons describe differences in observed variables. They do not identify MAR versus MNAR or prove why prices are missing. The Mann-Whitney effect equals P(A>B) + half of P(A=B), not strict P(A>B).
- The primary analysis retains extreme valid values. outlier_flags_iqr.csv contains heuristic flags, not confirmed errors; correlation_sensitivity.csv compares alternative treatments and the >=10-rating subset.
- Distribution plots use all available ratings/counts. Zero prices are excluded only from the logarithmic price display. The first price histogram hides {hidden:,} values above p99=${p99:.2f}; those values were not changed or removed from the tables.
- Rating intervals and exact recorded ratings are exported separately. The exact 5.0 group contains {len(exact5):,} products, with median rating count {exact5.median():.1f}; the 4.3–4.7 group has median {middle.median():.1f}. This association does not establish its cause.
- Confidence intervals are approximate normal intervals under independent-product assumptions. The data are a fixed collected category, not a designed random sample; these intervals are not a guarantee of population representativeness.
- Interpret correlation magnitudes rather than p-values alone. A numerical p-value of 0 means floating-point underflow for an extremely small value, not a mathematically zero probability.
- Research questions: How are price, mean rating and rating count associated? Does the relationship persist after restricting low-count products or treating outliers differently? How do products with unknown prices differ?
- Use the exported tables to write the team's final conclusions. This EDA does not train the later numeric models or replace the Stage 1 PDF.
'''
    (output / 'findings.md').write_text(notes, encoding='utf-8')
    print(json.dumps(overview, indent=2), flush=True)
    print(f'Completed. Tables, findings and figures: {output}', flush=True)


if __name__ == '__main__':
    main()
