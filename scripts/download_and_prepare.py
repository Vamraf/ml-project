"""Download complete official category files and prepare faithful analysis tables."""
import concurrent.futures
import csv
import gzip
import hashlib
import io
import json
import math
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DEST / "raw"
NUMERIC_DIR = DEST / "numeric"
TEXT_DIR = DEST / "text"
MANIFEST_DIR = DEST / "manifests"
REVISION = "2b6d039ed471f2ba5fd2acb718bf33b0a7e5598e"
BASE = f"https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/{REVISION}/raw"
FILES = {
    "Video_Games.jsonl": (f"{BASE}/review_categories/Video_Games.jsonl", 2682948518,
                          "7bde9e0a039bdb321e993bfe78a6c7d438fb1504b1ad152c0cb6a33a8b7cb26a"),
    "meta_Video_Games.jsonl": (f"{BASE}/meta_categories/meta_Video_Games.jsonl", 437375785,
                               "3ad94dfaa8dfed23c5f420aa9ddec415d00f2b8ec9f2d796f487b4b2c4d256de"),
}


def download(item):
    name, (url, expected, expected_sha256) = item
    path = RAW_DIR / name
    if path.exists():
        if path.stat().st_size != expected:
            raise RuntimeError(f"Existing file has unexpected size; left untouched: {name}")
        print(f"Using complete existing file: {name}", flush=True)
    else:
        part_dir = RAW_DIR / (".download_parts_" + name)
        part_dir.mkdir(exist_ok=True)
        chunk_size = 32 * 1024 * 1024
        total_chunks = math.ceil(expected / chunk_size)

        def part(index):
            start = index * chunk_size
            end = min(expected, start + chunk_size) - 1
            target = part_dir / f"{index:04d}.part"
            size = end - start + 1
            if target.exists() and target.stat().st_size == size:
                return size
            for attempt in range(3):
                try:
                    req = urllib.request.Request(f"{url}?download=true&part={index}",
                        headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity",
                                 "User-Agent": "Academic-ML-project/1.0"})
                    with urllib.request.urlopen(req, timeout=120) as response:
                        if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{expected}":
                            raise RuntimeError("Unexpected byte range response")
                        with target.open("wb") as output:
                            while block := response.read(1024 * 1024):
                                output.write(block)
                    if target.stat().st_size != size:
                        raise RuntimeError("Incomplete byte range")
                    return size
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2 * (attempt + 1))

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(part, i) for i in range(total_chunks)]
            for future in concurrent.futures.as_completed(futures):
                completed += future.result()
                print(f"{name}: {completed / expected:.0%} ({completed / 1e6:.0f}/{expected / 1e6:.0f} MB)", flush=True)
        partial = path.with_suffix(path.suffix + ".part")
        combined_hash = hashlib.sha256()
        with partial.open("wb") as output:
            for index in range(total_chunks):
                with (part_dir / f"{index:04d}.part").open("rb") as stream:
                    while block := stream.read(4 * 1024 * 1024):
                        output.write(block)
                        combined_hash.update(block)
        if partial.stat().st_size != expected or combined_hash.hexdigest() != expected_sha256:
            raise RuntimeError(f"Size or SHA256 mismatch: {name}")
        os.replace(partial, path)
        for index in range(total_chunks):
            (part_dir / f"{index:04d}.part").unlink()
        part_dir.rmdir()
        print(f"Downloaded {name}: {expected:,} bytes", flush=True)
    with path.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    if checksum != expected_sha256:
        raise RuntimeError(f"SHA256 mismatch: {name}")
    return name, {"url": url, "bytes": expected, "sha256": checksum,
                  "expected_sha256": expected_sha256, "revision": REVISION}


def number(value):
    if value is None or isinstance(value, bool):
        return ""
    try:
        result = float(str(value).replace("$", "").replace(",", "").strip())
        return result if math.isfinite(result) else ""
    except (ValueError, TypeError):
        return ""


def main():
    for folder in (RAW_DIR, NUMERIC_DIR, TEXT_DIR, MANIFEST_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        manifest = dict(pool.map(download, FILES.items()))
    product_ids = set()
    product_titles = {}
    numeric_path = NUMERIC_DIR / "products_numeric.csv.staging"
    fields = ["parent_asin", "product_title", "price_usd", "average_rating", "rating_number",
              "image_count", "video_count", "feature_count", "category_count", "description_section_count"]
    missing = {name: 0 for name in fields[2:]}
    products = 0
    with (RAW_DIR / "meta_Video_Games.jsonl").open("r", encoding="utf-8") as source, numeric_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for line in source:
            item = json.loads(line)
            product_ids.add(item["parent_asin"])
            product_title = item.get("title") or ""
            product_titles[item["parent_asin"]] = product_title
            row = {"parent_asin": item["parent_asin"], "product_title": product_title, "price_usd": number(item.get("price")),
                   "average_rating": number(item.get("average_rating")), "rating_number": number(item.get("rating_number"))}
            for out, key in [("image_count", "images"), ("video_count", "videos"), ("feature_count", "features"),
                             ("category_count", "categories"), ("description_section_count", "description")]:
                value = item.get(key)
                row[out] = len(value) if isinstance(value, list) else ""
            for key in missing:
                missing[key] += row[key] == ""
            writer.writerow(row)
            products += 1
    print(f"Numeric product table: {products:,} rows", flush=True)
    text_path = TEXT_DIR / "reviews_text.csv.gz.staging"
    review_numeric_path = NUMERIC_DIR / "reviews_numeric.csv.gz.staging"
    text_fields = ["review_row", "parent_asin", "product_title", "asin", "rating", "title", "text"]
    numeric_fields = ["review_row", "parent_asin", "product_title", "rating", "helpful_vote", "timestamp_ms", "verified_purchase"]
    reviews = empty_text = matched = 0
    rating_counts = {}
    with (RAW_DIR / "Video_Games.jsonl").open("r", encoding="utf-8") as source, \
         text_path.open("wb") as text_raw_out, \
         review_numeric_path.open("wb") as numeric_raw_out, \
         gzip.GzipFile(filename="reviews_text.csv", mode="wb", fileobj=text_raw_out, compresslevel=3, mtime=0) as text_gzip, \
         gzip.GzipFile(filename="reviews_numeric.csv", mode="wb", fileobj=numeric_raw_out, compresslevel=3, mtime=0) as numeric_gzip, \
         io.TextIOWrapper(text_gzip, encoding="utf-8", newline="") as text_out, \
         io.TextIOWrapper(numeric_gzip, encoding="utf-8", newline="") as numeric_out:
        tw = csv.DictWriter(text_out, fieldnames=text_fields)
        nw = csv.DictWriter(numeric_out, fieldnames=numeric_fields)
        tw.writeheader()
        nw.writeheader()
        for review_row, line in enumerate(source):
            item = json.loads(line)
            rating = number(item.get("rating"))
            product_title = product_titles.get(item.get("parent_asin"), "")
            tw.writerow({"review_row": review_row, "parent_asin": item.get("parent_asin", ""),
                         "product_title": product_title,
                         "asin": item.get("asin", ""), "rating": rating,
                         "title": item.get("title", ""), "text": item.get("text", "")})
            verified = item.get("verified_purchase")
            nw.writerow({"review_row": review_row, "parent_asin": item.get("parent_asin", ""),
                         "product_title": product_title,
                         "rating": rating, "helpful_vote": number(item.get("helpful_vote", item.get("helpful_votes"))),
                         "timestamp_ms": item.get("timestamp", item.get("sort_timestamp", "")),
                         "verified_purchase": int(verified) if isinstance(verified, bool) else ""})
            empty_text += not str(item.get("text") or "").strip()
            matched += item.get("parent_asin") in product_ids
            rating_counts[str(rating)] = rating_counts.get(str(rating), 0) + 1
            reviews += 1
            if reviews % 500000 == 0:
                print(f"Prepared {reviews:,} reviews", flush=True)
    previous_manifest = MANIFEST_DIR / "download_manifest.json"
    if previous_manifest.exists():
        previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
        if products != previous["product_rows"] or reviews != previous["review_rows"]:
            raise RuntimeError("Unexpected row count change; existing CSVs left untouched.")
    derived = {}
    for path in [numeric_path, text_path, review_numeric_path]:
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        derived[path.name.removesuffix(".staging")] = {"bytes": path.stat().st_size, "sha256": checksum,
                              "rows": products if path == numeric_path else reviews}
    result = {"category": "Video_Games", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_page": "https://amazon-reviews-2023.github.io/", "raw_files": manifest,
              "derived_files": derived, "product_rows": products, "unique_metadata_parent_asin": len(product_ids),
              "review_rows": reviews, "reviews_with_empty_text": empty_text,
              "reviews_matching_metadata": matched, "product_numeric_missing": missing,
              "rating_counts": rating_counts, "sampling": "None: full category retained; no rows dropped.",
              "product_title_source": "meta_Video_Games.jsonl:title, joined by parent_asin",
              "products_with_empty_title": sum(not title for title in product_titles.values())}
    manifest_stage = MANIFEST_DIR / "download_manifest.json.staging"
    manifest_stage.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for path in [numeric_path, text_path, review_numeric_path]:
        os.replace(path, path.with_name(path.name.removesuffix(".staging")))
    os.replace(manifest_stage, MANIFEST_DIR / "download_manifest.json")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
