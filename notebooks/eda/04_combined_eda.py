"""Stage 1 combined text/numeric EDA for Mykola Zhuchok (71899).

Python 3.11+. Install: python -m pip install pandas numpy matplotlib scipy
Run beside the original data: python 04_combined_eda.py
Default: process ALL original reviews in chunks, not an arbitrary CSV export.
Optional prefix: --rows 1000000; zero means the full file.
Other options: --reviews PATH --products PATH --output DIR --figures DIR
Source files remain unchanged. Do not substitute CSV files edited in Excel.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import matplotlib
# Use a noninteractive backend so plots can be generated on any PC or server.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Detect local and repository layouts without hardcoding a personal directory.
BASE = Path(__file__).resolve().parent
REPOSITORY = next((folder for folder in [BASE, *BASE.parents]
                   if (folder / 'data/manifests').is_dir() and (folder / 'data/raw').is_dir()), None)
# Features used in correlation tables; observed-review measures and metadata
# measures are deliberately kept under different names.
FEATURES = ['observed_review_count', 'avg_review_rating', 'avg_review_chars',
            'negative_share', 'price_usd', 'average_rating', 'rating_number']
# The three main research relationships shown in separate figures.
PAIRS = [('avg_review_chars', 'average_rating'),
         ('avg_review_chars', 'rating_number'), ('negative_share', 'price_usd')]


def locate(explicit, names, subfolder):
    """Locate data from the script position, not the current working directory."""
    # An explicit command-line input takes priority over automatic file discovery.
    if explicit:
        path = explicit.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    # Search beside this script and in ancestor project directories.
    for folder in [BASE, *BASE.parents]:
        for name in names:
            for path in [folder / name, folder / subfolder / name]:
                if path.is_file():
                    return path.resolve()
    raise FileNotFoundError(f'Cannot find {names}; specify the input file explicitly.')


def source_record(path, kind):
    """Hash inputs and validate original manifest checksums when available."""
    # Hash raw file bytes, including gzip bytes when the input is compressed.
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    # A source manifest records the expected file size, checksum, and row count.
    manifest = None
    for folder in [path.parent, BASE, *BASE.parents]:
        for candidate in [folder / 'download_manifest.json', folder / 'data/manifests/download_manifest.json']:
            if candidate.is_file():
                manifest = json.loads(candidate.read_text(encoding='utf-8'))
                break
        if manifest is not None:
            break
    # Reject changed exports when an original manifest entry is available.
    expected = manifest.get('derived_files', {}).get(path.name) if manifest else None
    if expected and (digest != expected['sha256'] or path.stat().st_size != expected['bytes']):
        raise ValueError(f'{kind} differs from the original manifest: {path.name}. Use the original data.')
    return {'file': str(path), 'bytes': path.stat().st_size, 'sha256': digest,
            'verified_against_manifest': bool(expected),
            'expected_rows': expected.get('rows') if expected else None}


def load_products(path):
    # Product IDs are strings: treating numeric-looking IDs as numbers loses zeros.
    # Literal text such as "NA" is preserved until truly blank cells are normalized.
    products = pd.read_csv(path, dtype={'parent_asin': 'string'}, keep_default_na=False)
    required = {'parent_asin', 'price_usd', 'average_rating', 'rating_number'}
    if products.empty or not required.issubset(products):
        raise ValueError(f'Product data must contain {sorted(required)}')
    products = products.replace(r'^\s*$', np.nan, regex=True)
    if products.parent_asin.isna().any() or not products.parent_asin.str.fullmatch(r'[A-Z0-9]{10}').all():
        raise ValueError('Invalid product IDs; use original string identifiers, preserving leading zeros.')
    # Exact repeated metadata rows may be removed safely; conflicting records
    # sharing one product ID must be resolved manually before the join.
    exact_duplicates = int(products.duplicated().sum())
    products = products.drop_duplicates().copy()
    if products.parent_asin.duplicated().any():
        raise ValueError('Conflicting duplicate product IDs require manual resolution.')
    # Validate numeric domains before computing logarithms or correlations.
    # Missing prices remain missing, and valid zero prices are retained.
    for col in ['price_usd', 'average_rating', 'rating_number']:
        products[col] = pd.to_numeric(products[col], errors='raise')
        present = products[col].dropna()
        if not np.isfinite(present).all():
            raise ValueError(f'Non-finite product values in {col}')
    if products.price_usd.dropna().lt(0).any() or not products.average_rating.dropna().between(1, 5).all():
        raise ValueError('Invalid price or product rating.')
    count = products.rating_number.dropna()
    if count.lt(0).any() or count.mod(1).ne(0).any():
        raise ValueError('Product rating counts must be nonnegative integers.')
    return products, exact_duplicates


def aggregate_reviews(path, limit, chunk_size, expected_rows):
    """Stream original reviews and combine additive per-product statistics."""
    required = ['review_row', 'parent_asin', 'rating', 'text', 'title']
    # Read only the header first, rejecting spreadsheet exports with broken columns.
    header = pd.read_csv(path, nrows=0).columns
    if not set(required).issubset(header):
        raise ValueError('Use original reviews_text.csv.gz with review_row and parent_asin columns; malformed exports are not supported.')
    # Store additive totals per product, not all individual reviews in memory.
    parts = None
    total = empty_text = empty_title = 0
    # Pandas reads gzip directly. A limit of zero processes the complete source.
    # Reading text as strings also prevents literal words from becoming NaN.
    for chunk in pd.read_csv(path, usecols=required, dtype='string', keep_default_na=False,
                             nrows=None if limit == 0 else limit, chunksize=chunk_size):
        # The original row IDs must remain consecutive. This catches reset indices,
        # missing/repeated source rows, and trailing spreadsheet control records.
        ids = pd.to_numeric(chunk.review_row, errors='coerce')
        if not np.array_equal(ids.to_numpy(), np.arange(total, total + len(chunk))):
            raise ValueError(f'Broken source row sequence near row {total}; use the original dataset.')
        if not chunk.parent_asin.str.fullmatch(r'[A-Z0-9]{10}').all():
            raise ValueError(f'Malformed parent_asin near row {total}; leading zeros may have been lost.')
        # Reject missing or invalid ratings instead of counting them as nonnegative.
        rating = pd.to_numeric(chunk.rating, errors='coerce')
        if not rating.isin([1, 2, 3, 4, 5]).all():
            raise ValueError(f'Missing or invalid review ratings near row {total}')
        has_text = chunk.text.str.strip().ne('')
        # Missing/blank text is not a zero-length observation in the length mean.
        # Its rating still contributes to rating summaries and negative share.
        char_length = chunk.text.str.len().where(has_text, 0).astype('int64')
        word_length = chunk.text.str.count(r'\S+').where(has_text, 0).astype('int64')
        # Accumulate counts and sums within this chunk. Only additive statistics
        # are combined across chunks; averaging chunk means would give wrong weights.
        batch = pd.DataFrame({'parent_asin': chunk.parent_asin,
                              'observed_review_count': 1, 'text_review_count': has_text.astype('int64'),
                              'rating_sum': rating, 'negative_count': rating.le(2).astype('int64'),
                              'char_sum': char_length, 'word_sum': word_length}).groupby('parent_asin', sort=False).sum()
        # Align by product ID, adding new product groups as later chunks arrive.
        parts = batch if parts is None else parts.add(batch, fill_value=0)
        total += len(chunk)
        empty_text += int((~has_text).sum())
        empty_title += int(chunk.title.str.strip().eq('').sum())
        print(f'Aggregated {total:,} reviews across {len(parts):,} product IDs', flush=True)
    if parts is None:
        raise ValueError('The review input is empty.')
    # A full run must match the manifest count; partial/truncated inputs must fail.
    if limit == 0 and expected_rows is not None and total != expected_rows:
        raise ValueError(f'Expected the full {expected_rows:,} rows, found {total:,}.')
    for col in ['observed_review_count', 'text_review_count', 'negative_count', 'char_sum', 'word_sum']:
        parts[col] = parts[col].astype('int64')
    # Compute means only after all chunks are combined. Rating summaries use all
    # valid reviews, while text lengths use only the number of nonblank texts.
    parts['avg_review_rating'] = parts.rating_sum / parts.observed_review_count
    parts['negative_share'] = parts.negative_count / parts.observed_review_count
    # Products without usable text get an unknown mean, not a misleading zero.
    denominator = parts.text_review_count.replace(0, np.nan)
    parts['avg_review_chars'] = parts.char_sum / denominator
    parts['avg_review_words'] = parts.word_sum / denominator
    return parts.reset_index(), {'reviews_processed': total, 'blank_text_reviews': empty_text,
                                 'blank_title_reviews': empty_title,
                                 'selection': 'entire original source file' if limit == 0 else f'first {total:,} original rows; not a random full-category sample',
                                 'review_row_validation': 'unique consecutive original IDs from zero',
                                 'review_duplicate_policy': 'preserve original rows; repeated visible text is not proof of duplicate reviewer identity'}


def save_plot(fig, folder, filename):
    # Export report-ready images and close figures to release plotting memory.
    fig.tight_layout()
    fig.savefig(folder / filename, dpi=180, bbox_inches='tight')
    plt.close(fig)


def correlations(frame, output, prefix):
    values = frame[FEATURES].astype(float)
    # Matrix multiplication counts products available for every variable pair.
    # Pairwise correlations can use different sample sizes because price is missing.
    valid = values.notna().astype('int64')
    valid.T.dot(valid).to_csv(output / f'{prefix}_pairwise_counts.csv')
    for method in ['pearson', 'spearman']:
        values.corr(method=method, min_periods=3).to_csv(output / f'{prefix}_{method}.csv')
    # Also export a common complete-case matrix for a like-for-like comparison.
    complete = values.dropna()
    complete.corr(method='spearman', min_periods=3).to_csv(output / f'{prefix}_complete_case_spearman.csv')
    return values.corr(method='spearman', min_periods=3), len(complete)


def main():
    # STEP 1: Parse reproducible input, row-limit, chunk-size, and output settings.
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--products', type=Path)
    parser.add_argument('--rows', type=int, default=0, help='0 = all reviews; positive number = original source prefix')
    parser.add_argument('--chunksize', type=int, default=100000)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--figures', type=Path)
    args = parser.parse_args()
    if args.rows < 0 or args.chunksize < 1:
        parser.error('--rows must be >=0 and --chunksize must be positive.')
    # STEP 2: Resolve paths and keep output files separate from source datasets.
    reviews_path = locate(args.reviews, ['reviews_text.csv.gz', 'reviews_text.csv'], 'data/text')
    products_path = locate(args.products, ['products_numeric.csv'], 'data/numeric')
    output = (args.output or (REPOSITORY / 'reports/stage-1/combined_eda' if REPOSITORY else BASE / 'combined_eda')).resolve()
    figures = (args.figures or (REPOSITORY / 'reports/figures/combined_eda' if REPOSITORY else output / 'figures')).resolve()
    for source in [reviews_path, products_path]:
        if source.is_relative_to(output) or source.is_relative_to(figures):
            parser.error('Input data must not be inside the output directories.')
    output.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    # STEP 3: Verify source integrity, validate metadata, and aggregate reviews.
    review_source = source_record(reviews_path, 'Review source')
    product_source = source_record(products_path, 'Product source')
    products, duplicate_products = load_products(products_path)
    aggregates, quality = aggregate_reviews(reviews_path, args.rows, args.chunksize, review_source['expected_rows'])

    # A left join retains observed product groups. The indicator checks key
    # matches directly; an empty product title does not imply an unmatched key.
    # STEP 4: Join one review-statistics row to one metadata row per product.
    merged = aggregates.merge(products, on='parent_asin', how='left', validate='one_to_one', indicator=True)
    # A left_only marker means no matching product key, even when titles are blank.
    unmatched = merged.loc[merged['_merge'].eq('left_only')]
    unmatched[['parent_asin', 'observed_review_count']].to_csv(output / 'unmatched_products.csv', index=False)
    matched = merged.loc[merged['_merge'].eq('both')].copy()
    if len(merged) != len(aggregates) or not merged.parent_asin.is_unique:
        raise ValueError('Join unexpectedly multiplied product rows.')
    if matched.empty:
        raise ValueError('No product IDs matched. Check the input files.')
    if len(unmatched):
        print(f'WARNING: {len(unmatched):,} unmatched product IDs; inspect unmatched_products.csv', flush=True)
    merged.to_csv(output / 'merged_product_statistics.csv', index=False)
    aggregates.to_csv(output / 'review_statistics_by_product.csv', index=False)
    # Save the numeric evidence alongside figures so the report can be checked.
    matrix, complete_count = correlations(matched, output, 'all_matched_products')

    # Product means/shares based on one review can be unstable. Compare multiple
    # support thresholds instead of interpreting them as equally reliable evidence.
    # STEP 5: Repeat the main correlations at several review-support thresholds.
    sensitivity = []
    for threshold in [1, 5, 10, 30]:
        subset = matched.loc[matched.observed_review_count.ge(threshold)]
        for a, b in PAIRS:
            # Drop missing values only for the current pair, not for every feature.
            data = subset[[a, b]].dropna()
            rho, p = (stats.spearmanr(data[a], data[b]) if len(data) >= 3 and data[a].nunique() > 1 and data[b].nunique() > 1 else (np.nan, np.nan))
            sensitivity.append({'min_observed_reviews': threshold, 'pair': f'{a} / {b}',
                                'n_products': len(data), 'spearman_rho': rho, 'p_value': p})
    sensitivity = pd.DataFrame(sensitivity)
    sensitivity.to_csv(output / 'support_threshold_sensitivity.csv', index=False)

    # Log1p axes show dense relationships without deleting expensive/popular items.
    # Each point/hexagon represents products, not individual review weights.
    # STEP 6: Plot dense product relationships using hexagonal count bins.
    plot_info = []
    labels = [('Average nonblank review length vs metadata rating', 'log1p(mean review characters)', 'Metadata average rating'),
              ('Average nonblank review length vs metadata rating count', 'log1p(mean review characters)', 'log1p(metadata rating count)'),
              ('Price vs share of 1–2-star reviews', 'log1p(price USD)', 'Observed negative reviews (%)')]
    for number, ((a, b), (title, xlabel, ylabel)) in enumerate(zip(PAIRS, labels), 1):
        data = matched[[a, b]].dropna()
        # Transform display coordinates only; rho is calculated on original values.
        # The third plot displays negative share as a percentage for readability.
        if number == 1:
            x, y = np.log1p(data[a]), data[b]
        elif number == 2:
            x, y = np.log1p(data[a]), np.log1p(data[b])
        else:
            x, y = np.log1p(data[b]), data[a] * 100
        fig, ax = plt.subplots(figsize=(10, 6))
        if len(data):
            hb = ax.hexbin(x, y, gridsize=55, mincnt=1, bins='log', cmap='Blues')
            fig.colorbar(hb, ax=ax, label='Products per hexagon (log color scale)')
        rho = sensitivity.loc[(sensitivity.min_observed_reviews.eq(1)) & sensitivity.pair.eq(f'{a} / {b}'), 'spearman_rho'].iloc[0]
        ax.set(title=f'{title}\nn={len(data):,} products; Spearman rho={rho:.3f}', xlabel=xlabel, ylabel=ylabel)
        save_plot(fig, figures, f'0{number}_combined_relationship.png')
        plot_info.append({'figure': f'0{number}_combined_relationship.png', 'n_products': len(data), 'spearman_rho': float(rho)})

    # STEP 7: Use a fixed -1 to +1 heatmap scale centered on zero correlation.
    fig, ax = plt.subplots(figsize=(12, 10))
    image = ax.imshow(matrix.to_numpy(), cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(image, ax=ax, label='Spearman correlation')
    ax.set_xticks(range(len(FEATURES)), FEATURES, rotation=55, ha='right')
    ax.set_yticks(range(len(FEATURES)), FEATURES)
    for i in range(len(FEATURES)):
        for j in range(len(FEATURES)):
            value = matrix.iloc[i, j]
            ax.text(j, i, 'NA' if pd.isna(value) else f'{value:.2f}', ha='center', va='center', color='white' if abs(value) > .6 else 'black')
    ax.set_title(f'Product-level Spearman correlations: {len(matched):,} matched products\nPairwise rows; observation counts saved separately')
    save_plot(fig, figures, '04_combined_correlations.png')

    # Visualize how association estimates change with supporting review counts.
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, (a, b) in zip(axes, PAIRS):
        part = sensitivity.loc[sensitivity.pair.eq(f'{a} / {b}')]
        ax.plot(part.min_observed_reviews, part.spearman_rho, 'o-')
        ax.axhline(0, color='gray', linewidth=.8)
        ax.set(title=f'{a}\nvs {b}', xlabel='Minimum observed reviews per product', ylabel='Spearman rho', xticks=[1, 5, 10, 30])
    save_plot(fig, figures, '05_support_sensitivity.png')

    # STEP 8: Record actual sample sizes, quality checks, versions, and provenance.
    overview = {**quality, 'reviews_source': review_source, 'products_source': product_source,
                'product_metadata_rows': len(products), 'exact_duplicate_product_rows_removed': duplicate_products,
                'products_observed_in_reviews': len(aggregates), 'merged_rows': len(merged),
                'matched_products': len(matched), 'unmatched_product_ids': len(unmatched),
                'missing_titles_among_matched': int(matched.product_title.fillna('').astype(str).str.strip().eq('').sum()) if 'product_title' in matched else None,
                'metadata_products_without_observed_reviews': int((~products.parent_asin.isin(aggregates.parent_asin)).sum()),
                'products_with_one_observed_review': int(matched.observed_review_count.eq(1).sum()),
                'products_with_less_than_five_observed_reviews': int(matched.observed_review_count.lt(5).sum()),
                'products_without_any_nonblank_text': int(matched.text_review_count.eq(0).sum()),
                'missing_prices_among_matched': int(matched.price_usd.isna().sum()),
                'zero_prices_retained': int(matched.price_usd.eq(0).sum()),
                'heatmap_complete_case_products': complete_count, 'plots': plot_info,
                'runtime_seconds': round(time.monotonic() - started, 2),
                'versions': {'python': sys.version.split()[0], 'pandas': pd.__version__, 'numpy': np.__version__}}
    (output / 'analysis_summary.json').write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding='utf-8')
    # STEP 9: Write findings and limitations for the team to use in the Stage 1 PDF.
    description = f'''# Combined text/numeric EDA: findings and limitations

## Scope and quality

- Selection: {quality['selection']}; {quality['reviews_processed']:,} source reviews processed in chunks. Original row IDs and input checksums are recorded in analysis_summary.json.
- Missing/blank text: {quality['blank_text_reviews']:,}. Length averages exclude these texts; their valid ratings remain in the rating summaries. All original source reviews are retained; repeated visible text is not sufficient evidence of duplicate reviewer identity.
- Per-product aggregation produced {len(aggregates):,} groups. A validated one-to-one join matched {len(matched):,}; unmatched IDs: {len(unmatched):,}. A missing product title is checked separately from a missing key match.
- Price is missing for {overview['missing_prices_among_matched']:,} matched products. Zero prices are retained. Every plot and correlation pair uses its own nonmissing rows; pairwise counts and a common complete-case matrix are exported separately.

## Interpretation

'''
    for info, (a, b) in zip(plot_info, PAIRS):
        description += f"- {a} vs {b}: Spearman rho={info['spearman_rho']:.4f}, n={info['n_products']:,} products.\n"
    description += f'''
- These associations are descriptive, not causal evidence. Study the effect sizes and support_threshold_sensitivity.csv before writing the team's final conclusions. Very small or numerically zero p-values do not imply large practical effects.
- {overview['products_with_one_observed_review']:,} matched products have only one observed review; {overview['products_with_less_than_five_observed_reviews']:,} have fewer than five. Means and shares for these products may be unstable. Results are compared at support thresholds 1, 5, 10, and 30.
- observed_review_count counts rows in the analyzed source, while rating_number is a metadata rating count. avg_review_rating and average_rating also describe different sources/scopes; do not equate them. Metadata may reflect another collection time or coverage.
- negative_share is the fraction of observed valid ratings equal to 1 or 2. Its correlation with avg_review_rating partly reflects a mathematical relationship because both are calculated from the same ratings; it is not independent confirmation of sentiment.
- Avg_review_chars measures original text characters, not cleaned text or sentiment. Each product has equal weight in product-level correlations, regardless of its review count.
- Log1p axes improve visibility only: no expensive products, popular products, or long reviews were removed from the primary analysis.
- For a prefix run, results describe that prefix, not a random sample of the category. A full run reduces this particular source-order limitation but does not remove collection or missing-price bias.
- Candidate research questions: Is review length associated with metadata rating or popularity? Is the observed negative-review share associated with price? How sensitive are conclusions to the number of reviews supporting each product estimate?
- This script provides the combined EDA section for the Stage 1 PDF. It does not train K-means, LDA, or prediction models required in later stages.
'''
    (output / 'findings.md').write_text(description, encoding='utf-8')
    print(json.dumps(overview, indent=2, ensure_ascii=False), flush=True)
    print(f'Completed. Tables and findings: {output}; figures: {figures}', flush=True)


# Run analysis only when executed directly; importing functions does not rerun it.
if __name__ == '__main__':
    main()
