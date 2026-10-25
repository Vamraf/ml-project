"""Join aligned text/numeric reviews without loading the dataset into memory."""
import csv
import gzip
import itertools
import json
import os
from pathlib import Path

# Resolve data paths independently of the current working directory.
DATA = Path(__file__).resolve().parents[1] / 'data'


def combine(text_path, numeric_path, target, expected_rows):
    # Keep an existing result intact until the replacement passes every check.
    stage = target.with_name(target.name + '.staging')
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    # Stream compressed CSV files instead of loading millions of rows into memory.
    with gzip.open(text_path, 'rt', encoding='utf-8', newline='') as text_file, gzip.open(numeric_path, 'rt', encoding='utf-8', newline='') as numeric_file, gzip.open(stage, 'wt', encoding='utf-8', newline='') as out:
        texts, numbers = csv.DictReader(text_file), csv.DictReader(numeric_file)
        # Keep shared columns once, followed by numeric-only columns.
        fields = list(texts.fieldnames) + [name for name in numbers.fieldnames if name not in texts.fieldnames]
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        shared = set(texts.fieldnames) & set(numbers.fieldnames)
        # zip_longest exposes unequal lengths instead of silently truncating a table.
        for text, numeric in itertools.zip_longest(texts, numbers):
            # This is an aligned join: row IDs and every other shared field must match.
            if text is None or numeric is None or any(text[key] != numeric[key] for key in shared):
                raise ValueError(f'Tables are misaligned at row {count}')
            if text['review_row'] != str(count):
                raise ValueError(f'Unexpected review_row at row {count}')
            writer.writerow({**text, **numeric})
            count += 1
            if count % 500000 == 0:
                print(f'Combined {count:,} reviews', flush=True)
    # Publish the joined table only if its row count matches the source manifest.
    if count != expected_rows:
        raise ValueError(f'Expected {expected_rows} reviews, found {count}')
    os.replace(stage, target)
    print(f'Created {target}: {count:,} reviews', flush=True)


if __name__ == '__main__':
    # Use the recorded full-dataset row count as an independent completeness check.
    manifest = json.loads((DATA / 'manifests/download_manifest.json').read_text(encoding='utf-8'))
    combine(DATA / 'text/reviews_text.csv.gz', DATA / 'numeric/reviews_numeric.csv.gz', DATA / 'combined/reviews_combined.csv.gz', manifest['review_rows'])
