"""Audit numeric product data without changing the source file.

Dependencies: python -m pip install pandas numpy
Run beside products_numeric.csv or from notebooks/eda/: python 01_audit.py
Optional: --input PATH --output DIRECTORY
English comments explain each processing step; all tables are saved for the report.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

NUMERIC = ['price_usd', 'average_rating', 'rating_number', 'image_count',
           'video_count', 'feature_count', 'category_count', 'description_section_count']


def resolve_input(value=None):
    """Support the shared study folder and the repository layout."""
    if value is not None:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    base = Path(__file__).resolve().parent
    for folder in [base, *base.parents]:
        for path in [folder / 'products_numeric.csv', folder / 'data/numeric/products_numeric.csv']:
            if path.is_file():
                return path
    raise FileNotFoundError('Cannot locate products_numeric.csv. Supply --input PATH.')


def default_output(path):
    # Keep report artifacts together without changing any input table.
    if path.parent.name == 'numeric' and path.parent.parent.name == 'data':
        return path.parents[2] / 'reports/stage-1/numeric_eda'
    return path.parent / 'numeric_eda'


def load_products(path):
    # Preserve literal strings, then normalize empty/whitespace-only cells.
    frame = pd.read_csv(path, encoding='utf-8-sig', keep_default_na=False)
    required = {'parent_asin', 'price_usd', 'average_rating', 'rating_number'}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError(f'Empty dataset or missing required columns: {sorted(required - set(frame.columns))}')
    frame = frame.replace(r'^\s*$', np.nan, regex=True)
    coercions = {}
    for column in NUMERIC:
        if column in frame:
            values = pd.to_numeric(frame[column], errors='coerce')
            coercions[column] = int((frame[column].notna() & values.isna()).sum())
            frame[column] = values
    return frame, coercions


def audit(frame, coercions):
    """Check completeness, identifiers, numeric domains, and duplicate records."""
    counts = frame.isna().sum()
    quality = pd.DataFrame({'column': frame.columns, 'dtype': frame.dtypes.astype(str).values,
                            'missing_count': counts.values, 'missing_percent': counts.values / len(frame) * 100})
    quality['entire_column_missing'] = quality['missing_count'].eq(len(frame))
    invalid = {'missing_parent_asin': int(frame.parent_asin.isna().sum()),
               'negative_price': int(frame.price_usd.lt(0).sum()),
               'zero_price': int(frame.price_usd.eq(0).sum()),
               'positive_price_below_one': int((frame.price_usd.gt(0) & frame.price_usd.lt(1)).sum()),
               'rating_outside_1_5': int((frame.average_rating.notna() & ~frame.average_rating.between(1, 5)).sum()),
               'negative_rating_count': int(frame.rating_number.lt(0).sum()),
               'zero_rating_count': int(frame.rating_number.eq(0).sum()),
               'noninteger_rating_count': int((frame.rating_number.notna() & frame.rating_number.mod(1).ne(0)).sum())}
    for column in NUMERIC:
        if column in frame:
            invalid[f'nonfinite_{column}'] = int((frame[column].notna() & ~np.isfinite(frame[column])).sum())
    summary = {'rows': len(frame), 'columns': len(frame.columns),
               'exact_duplicate_rows': int(frame.duplicated().sum()),
               'duplicate_parent_asin': int(frame.parent_asin.duplicated().sum()),
               'numeric_conversion_failures': coercions, 'checks': invalid}
    return quality, summary


def write_audit(frame, coercions, path, output):
    output.mkdir(parents=True, exist_ok=True)
    quality, summary = audit(frame, coercions)
    quality.to_csv(output / 'source_data_quality.csv', index=False)
    frame.select_dtypes(include='number').describe(percentiles=[.01, .25, .5, .75, .95, .99]).to_csv(output / 'source_descriptive_statistics.csv')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    summary.update(input_file=str(path), input_sha256=digest,
                   subset='Complete supplied product table; no sampling in the audit')
    (output / 'audit_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(quality.to_string(index=False), flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    path = resolve_input(args.input)
    output = (args.output or default_output(path)).resolve()
    frame, coercions = load_products(path)
    write_audit(frame, coercions, path, output)
    print(f'Audit saved to {output}')


if __name__ == '__main__':
    main()
