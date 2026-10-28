"""Reproducible Stage 1 text EDA by Daniil Khasanov, with review fixes.

Requirements: Python 3.10+; pip install pandas numpy matplotlib scikit-learn
Optional word clouds: pip install wordcloud

Run next to Video_Games.jsonl: python 03_text_eda.py
Or: python 03_text_eda.py --input reviews_text.csv.gz --rows 500000
In the repository, tables go to reports/stage-1/text_eda and figures to
reports/figures/text_eda. Outside the repository, outputs go to text_eda next
to this script. Override these locations with --output and --figures.
The default input is the first 500,000 source rows, NOT a random sample of the
full category. Text analysis samples up to 100,000 retained rows with seed 42.
No source files are modified and no downloads are performed.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import sys

try:
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # Save plots without requiring a GUI or Colab session.
    import matplotlib.pyplot as plt
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
except ImportError as error:
    raise SystemExit('Install dependencies first: python -m pip install pandas numpy matplotlib scikit-learn') from error

BASE = Path(__file__).resolve().parent
# Locate the dataset from the script position, independently of the working directory.
PROJECT_ROOT = next((folder for folder in [BASE, *BASE.parents]
                     if (folder / 'data/raw').is_dir() and (folder / 'data/manifests').is_dir()), None)
# Keep negation because it carries meaning in positive/negative review analysis.
STOP_WORDS = set(ENGLISH_STOP_WORDS) - {'no', 'not', 'nor', 'never', 'cannot'}
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)


def clean_text(value):
    """Remove markup and normalize whitespace while preserving sentiment cues."""
    if pd.isna(value):
        return ''
    text = re.sub(r'<[^>]*>', ' ', str(value))
    text = html.unescape(text).replace('\u2019', "'")
    # Preserve punctuation, digits, Unicode, and contractions in this text view.
    return re.sub(r'\s+', ' ', text).strip().lower()


def read_data(path, limit):
    """Load a reproducible source prefix and preserve original row identities."""
    name = path.name.lower()
    if name.endswith(('.jsonl', '.jsonl.gz')):
        opener = gzip.open if name.endswith('.gz') else open
        rows = []
        with opener(path, 'rt', encoding='utf-8') as stream:
            # Check the limit before decoding the next row; no random full-data claim.
            for index, line in enumerate(stream):
                if index >= limit:
                    break
                row = json.loads(line)
                fields = ['rating', 'title', 'text', 'asin', 'parent_asin', 'user_id', 'timestamp']
                rows.append({**{field: row.get(field) for field in fields}, 'review_row': index})
        frame = pd.DataFrame(rows)
    elif name.endswith(('.csv', '.csv.gz')):
        # Do not interpret literal strings such as 'NA' as missing review content.
        frame = pd.read_csv(path, nrows=limit, keep_default_na=False, encoding='utf-8-sig')
        if 'review_row' not in frame:
            frame['review_row'] = np.arange(len(frame))
    else:
        raise ValueError('Input must be .jsonl, .jsonl.gz, .csv, or .csv.gz')
    required = {'rating', 'title', 'text', 'parent_asin', 'review_row'}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError(f'Input is empty or missing required columns: {sorted(required - set(frame.columns))}')
    if frame['review_row'].isna().any() or frame['review_row'].duplicated().any():
        raise ValueError('review_row must contain unique, non-missing source IDs')
    frame['rating'] = pd.to_numeric(frame['rating'], errors='raise')
    if not frame['rating'].isin([1, 2, 3, 4, 5]).all():
        raise ValueError('Every rating must be an integer from 1 to 5')
    return frame


def save_plot(fig, path):
    """Export clean report figures instead of cropped notebook screenshots."""
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches='tight')
    plt.close(fig)


def rating_table(frame):
    counts = frame['rating'].value_counts().reindex(range(1, 6), fill_value=0)
    return pd.DataFrame({'rating': counts.index, 'count': counts.values,
                         'percent': counts.values / len(frame) * 100})


def vocabulary(texts):
    """Count words and genuine adjacent bigrams without a dense feature matrix."""
    words, documents, bigrams = Counter(), Counter(), Counter()
    for text in texts:
        tokens = [word for word in WORD.findall(text) if len(word) > 1]
        useful = [word for word in tokens if word not in STOP_WORDS]
        words.update(useful)
        documents.update(set(useful))
        # Filter pairs AFTER finding neighbors, avoiding artificial adjacency.
        bigrams.update(f'{a} {b}' for a, b in zip(tokens, tokens[1:])
                       if a not in STOP_WORDS and b not in STOP_WORDS)
    return words, documents, bigrams


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', type=Path, help='Local source data file')
    parser.add_argument('--output', type=Path, default=(PROJECT_ROOT / 'reports/stage-1/text_eda' if PROJECT_ROOT else BASE / 'text_eda'))
    parser.add_argument('--figures', type=Path, help='Separate directory for report figures')
    parser.add_argument('--rows', type=int, default=500000, help='Maximum source prefix size')
    parser.add_argument('--sample-size', type=int, default=100000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--keep-duplicates', action='store_true', help='Retain duplicate source identities')
    parser.add_argument('--skip-wordcloud', action='store_true')
    args = parser.parse_args()
    if args.rows < 1 or args.sample_size < 1:
        parser.error('--rows and --sample-size must be positive')
    if args.input is None:
        folders = [BASE]
        if PROJECT_ROOT:
            folders += [PROJECT_ROOT / 'data/raw', PROJECT_ROOT / 'data/text']
        candidates = [folder / name for folder in folders
                      for name in ['Video_Games.jsonl', 'Video_Games.jsonl.gz', 'reviews_text.csv.gz', 'reviews_text.csv']]
        args.input = next((path for path in candidates if path.is_file()), None)
    if args.input is None or not args.input.is_file():
        parser.error('No local dataset found. Pass --input with a valid source file.')
    out = args.output.resolve()
    if args.input.resolve().is_relative_to(out):
        parser.error('Choose an output directory that does not contain the source file')
    out.mkdir(parents=True, exist_ok=True)
    figures = (args.figures or (PROJECT_ROOT / 'reports/figures/text_eda' if PROJECT_ROOT else out)).resolve()
    figures.mkdir(parents=True, exist_ok=True)
    print(f'Loading up to {args.rows:,} source-prefix rows from {args.input}', flush=True)
    frame = read_data(args.input, args.rows)
    loaded = len(frame)

    # Audit nulls AND empty strings before cleaning; neither is silently discarded.
    quality = pd.DataFrame({'column': frame.columns,
                            'null_count': [int(frame[col].isna().sum()) for col in frame.columns],
                            'blank_string_count': [int(frame[col].map(lambda value: isinstance(value, str) and not value.strip()).sum()) for col in frame.columns]})
    quality['missing_or_blank_count'] = quality['null_count'] + quality['blank_string_count']
    quality['missing_or_blank_percent'] = quality['missing_or_blank_count'] / loaded * 100
    quality['entire_column_empty'] = quality['missing_or_blank_count'] == loaded
    quality.to_csv(out / 'data_quality.csv', index=False)
    before_ratings = rating_table(frame)
    before_ratings.to_csv(out / 'rating_distribution_source_prefix.csv', index=False)

    # Remove only duplicate source identities when all identity fields are usable.
    # Repeated text alone can be legitimate, so it is reported but never auto-removed.
    identity = ['user_id', 'asin', 'timestamp', 'text']
    duplicate_mask = pd.Series(False, index=frame.index)
    identity_available = all(column in frame for column in identity)
    if identity_available:
        eligible = frame[['user_id', 'asin', 'timestamp']].notna().all(axis=1)
        for column in ['user_id', 'asin', 'timestamp']:
            eligible &= frame[column].astype(str).str.strip().ne('')
        duplicate_mask.loc[eligible] = frame.loc[eligible].duplicated(subset=identity, keep='first')
    duplicate_count = int(duplicate_mask.sum())
    # Export row IDs only; raw user identifiers are not needed in the report.
    frame.loc[duplicate_mask, ['review_row', 'parent_asin']].to_csv(out / 'duplicate_rows.csv', index=False)
    nonempty = frame['text'].fillna('').astype(str).str.strip()
    repeated_text = int(nonempty[nonempty.ne('')].duplicated().sum())
    removed = 0 if args.keep_duplicates else duplicate_count
    if removed:
        frame = frame.loc[~duplicate_mask].copy()

    # Record exactly which retained source rows feed the more expensive text EDA.
    sample = frame.sample(n=min(args.sample_size, len(frame)), random_state=args.seed).copy()
    sample['text_original'] = sample['text']
    sample['text_cleaned'] = sample['text'].map(clean_text)
    sample['char_length'] = sample['text'].fillna('').astype(str).str.len()
    sample['word_count'] = sample['text'].fillna('').astype(str).str.split().str.len()
    sample[['review_row', 'parent_asin', 'rating']].to_csv(out / 'sample_rows.csv', index=False)
    # Keep cleaned texts and join keys together for later NLP and team integration.
    sample.to_csv(out / 'text_sample_cleaned.csv.gz', index=False, compression='gzip')
    sample[['review_row', 'text_original', 'text_cleaned']].head(10).to_csv(out / 'cleaning_examples.csv', index=False)
    sample[['char_length', 'word_count']].describe(percentiles=[.5, .9, .95, .99]).to_csv(out / 'length_statistics.csv')

    ratings = rating_table(frame)
    ratings.to_csv(out / 'rating_distribution_retained.csv', index=False)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, field, label in zip(axes, ['count', 'percent'], ['Review count', 'Percent of reviews']):
        ax.bar(ratings['rating'], ratings[field], color='#3478a8')
        ax.set(xlabel='Rating (stars)', ylabel=label, xticks=range(1, 6))
    fig.suptitle(f'Rating distribution: {len(frame):,} retained rows from the source prefix')
    save_plot(fig, figures / 'rating_distribution.png')

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    hidden = {}
    for ax, field, limit, label in zip(axes, ['char_length', 'word_count'], [2000, 400], ['Characters', 'Whitespace-separated words']):
        values = sample[field]
        hidden[field] = int((values >= limit).sum())
        ax.hist(values[values < limit], bins=50, color='#3478a8', edgecolor='white')
        ax.set(xlabel=label, ylabel='Review count', title=f'{len(sample):,}-row sample; {hidden[field]:,} rows >= {limit} hidden')
    # Axis cutoffs affect these plots only; longer reviews remain in saved data.
    save_plot(fig, figures / 'review_lengths.png')

    print('Counting words and adjacent bigrams...', flush=True)
    counters = {}
    class_sizes = {}
    for label, subset in [('all', sample), ('5_star', sample[sample['rating'].eq(5)]), ('1_star', sample[sample['rating'].eq(1)])]:
        words, documents, bigrams = vocabulary(subset['text_cleaned'])
        counters[label] = words
        class_sizes[label] = len(subset)
        total_tokens = sum(words.values())
        rows = [{'word': word, 'occurrences': count,
                 'per_10000_content_tokens': count / total_tokens * 10000,
                 'reviews_with_word': documents[word],
                 'percent_reviews_with_word': documents[word] / len(subset) * 100}
                for word, count in words.most_common(50)]
        pd.DataFrame(rows, columns=['word', 'occurrences', 'per_10000_content_tokens', 'reviews_with_word', 'percent_reviews_with_word']).to_csv(out / f'top_words_{label}.csv', index=False)
        pd.DataFrame(bigrams.most_common(50), columns=['bigram', 'occurrences']).to_csv(out / f'top_bigrams_{label}.csv', index=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, label, color in zip(axes, ['5_star', '1_star'], ['#247a4a', '#922f36']):
        top = counters[label].most_common(10)[::-1]
        total = sum(counters[label].values())
        if top:
            ax.barh([word for word, _ in top], [count / total * 10000 for _, count in top], color=color)
        else:
            ax.text(.5, .5, 'No usable words in this class', ha='center', transform=ax.transAxes)
        ax.set(title=f'{label.replace("_", " ")}: {class_sizes[label]:,} sampled reviews', xlabel='Occurrences per 10,000 content tokens')
    save_plot(fig, figures / 'top_words_by_rating.png')

    # Word clouds are optional illustrations; numeric frequency tables are primary.
    cloud_status = 'skipped by request'
    if not args.skip_wordcloud:
        try:
            from wordcloud import WordCloud
        except ImportError:
            cloud_status = 'not generated: optional wordcloud package is not installed'
        else:
            cloud_status = 'generated for classes with usable words'
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            for ax, label, cmap in zip(axes, ['5_star', '1_star'], ['Greens', 'Reds']):
                if counters[label]:
                    cloud = WordCloud(width=1000, height=500, background_color='white', colormap=cmap, random_state=args.seed, max_words=150).generate_from_frequencies(counters[label])
                    ax.imshow(cloud, interpolation='bilinear')
                ax.set_title(label.replace('_', ' '))
                ax.axis('off')
            save_plot(fig, figures / 'wordclouds.png')

    # Persist provenance, decisions, and actual row counts alongside the figures.
    sample_id_hash = hashlib.sha256(','.join(sample['review_row'].astype(str)).encode()).hexdigest()
    summary = {'input_file': str(args.input.resolve()), 'selection': 'first N source rows, then a seeded random sample of retained rows',
               'requested_prefix_rows': args.rows, 'loaded_rows': loaded, 'duplicate_identity_columns': identity if identity_available else None,
               'duplicate_identity_rows': duplicate_count if identity_available else None, 'duplicate_rows_removed': removed,
               'duplicate_policy': 'keep all' if args.keep_duplicates else 'keep first source identity; preserve repeated text with different identities',
               'repeated_nonempty_text_rows_before_deduplication': repeated_text,
               'retained_rows': len(frame), 'text_sample_rows': len(sample), 'seed': args.seed,
               'sample_review_row_sha256': sample_id_hash, 'empty_text_after_cleaning_in_sample': int(sample['text_cleaned'].eq('').sum()),
               'rows_hidden_in_length_plots': hidden, 'wordcloud_status': cloud_status,
               'versions': {'python': sys.version.split()[0], 'pandas': pd.__version__, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__}}
    (out / 'run_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    quality_total = int(quality.loc[quality['column'].eq('text'), 'missing_or_blank_count'].iloc[0])
    five_percent = float(ratings.loc[ratings['rating'].eq(5), 'percent'].iloc[0])
    notes = f'''# Text EDA: findings and limitations

- Source-prefix rows inspected: {loaded:,}; missing/blank review texts: {quality_total:,}.
- Duplicate source identities: {duplicate_count if identity_available else 'not measurable: identity fields absent'}; rows removed: {removed:,}.
- Retained rows: {len(frame):,}; five-star share: {five_percent:.2f}%. Class imbalance should inform later evaluation.
- Text analysis uses {len(sample):,} retained rows, randomly sampled with seed {args.seed}.
- Empty texts after cleaning in that sample: {summary['empty_text_after_cleaning_in_sample']:,}.
- Histogram cutoffs hide {hidden['char_length']:,} rows at/above 2,000 characters and {hidden['word_count']:,} rows at/above 400 words. These reviews were not removed from the data.
- Word-frequency plots compare normalized frequencies, not raw counts from unequal class sizes. Classes are specifically one-star and five-star reviews; intermediate ratings remain in the overall analysis.
- Raw text is preserved. Cleaning removes HTML, decodes entities, normalizes spaces and case, and preserves contractions, Unicode, numbers, punctuation, and emoji. Token frequencies use a separate word tokenizer and English stop words with negation retained.
- This prefix may reflect source ordering. Do not generalize its rating proportions to the whole category without checking full-data statistics. Reproduce the exact subset using run_summary.json and sample_rows.csv.
- Word clouds: {cloud_status}. They illustrate frequent words and are not a statistical test or a trained sentiment model.
- Candidate research questions: How does vocabulary differ between one-star and five-star reviews? Does review length vary by rating? Can text later predict rating better than a majority-class baseline?
- No classifier was trained in this Stage 1 script. No causal conclusions are established by these descriptive figures.

See data_quality.csv, both rating-distribution tables, length_statistics.csv, top_words_*.csv, and top_bigrams_*.csv for the numeric results. Combine these findings with the team's other analyses in the Stage 1 PDF.
'''
    (out / 'findings.md').write_text(notes, encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    print(f'Completed. Tables, cleaned sample and findings: {out}; figures: {figures}', flush=True)


if __name__ == '__main__':
    main()
