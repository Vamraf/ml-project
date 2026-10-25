# Combined data

Run `python scripts/combine_reviews.py` from the repository root.
The script streams and joins the text and numeric review tables by `review_row`, validating all shared fields.
Product features can be joined separately using `parent_asin`.
