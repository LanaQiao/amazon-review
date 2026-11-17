#!/usr/bin/env python3
"""Stream a stratified negative-review sample from Amazon Reviews 2023."""

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path



def normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--categories",
        default="All_Beauty,Appliances,Home_and_Kitchen,Pet_Supplies",
        help="Comma-separated Amazon Reviews 2023 category file names",
    )
    parser.add_argument("--per-category", type=int, default=250)
    parser.add_argument("--negative-stars", default="1,2")
    parser.add_argument("--min-chars", type=int, default=20)
    parser.add_argument("--max-chars", type=int, default=1800)
    parser.add_argument("--scan-cap", type=int, default=30000)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir", default=None, help="Hugging Face cache directory")
    parser.add_argument(
        "--trust-remote-code", action="store_true",
        help="Allow the published dataset loader to execute",
    )
    return parser.parse_args()


def iter_records(category, trust_remote_code):
    from datasets import load_dataset

    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{category}",
        split="full",
        streaming=True,
        trust_remote_code=trust_remote_code,
    )
    for line_number, row in enumerate(dataset, start=1):
        yield line_number, row


def collect_category(category, args, negative_stars, seen):
    retained = []
    dropped = Counter()
    for line_number, row in iter_records(category, args.trust_remote_code):
        if line_number > args.scan_cap:
            break
        rating = int(row.get("rating", 0))
        if rating not in negative_stars:
            dropped["non_negative_star"] += 1
            continue
        body = normalize(row.get("text"))
        title = normalize(row.get("title"))
        if len(body) < args.min_chars:
            dropped["too_short"] += 1
            continue
        if len(body) > args.max_chars:
            body = body[:args.max_chars].rsplit(" ", 1)[0] or body[:args.max_chars]
            dropped["truncated"] += 1
        product_id = row.get("parent_asin") or row.get("asin") or "unknown"
        duplicate_key = (product_id, body.casefold())
        if duplicate_key in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(duplicate_key)
        retained.append({
            "review_id": f"amazon2023:{category}:{line_number}",
            "product_id": product_id,
            "stars": rating,
            "language": "en",
            "product_category": category,
            "review_title": title,
            "review_body": body,
            "review_timestamp": row.get("timestamp"),
            "verified_purchase": row.get("verified_purchase"),
        })
        if len(retained) >= args.per_category:
            break
    return retained, dropped


def main():
    args = parse_args()
    categories = [item.strip() for item in args.categories.split(",") if item.strip()]
    negative_stars = {int(value) for value in args.negative_stars.split(",")}
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else output_dir.parent / ".hf_cache"
    os.environ.setdefault("HF_HOME", str(cache_dir))
    all_rows = []
    all_dropped = Counter()
    category_summary = {}
    seen = set()

    for category in categories:
        rows, dropped = collect_category(category, args, negative_stars, seen)
        all_rows.extend(rows)
        all_dropped.update(dropped)
        category_summary[category] = {"retained": len(rows), "dropped": dict(dropped)}
        print(f"Collected {len(rows)} negative reviews from {category}")

    output_path = output_dir / "negative_reviews.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "source": "Amazon Reviews 2023 (McAuley Lab, UCSD)",
        "categories": categories,
        "negative_stars": sorted(negative_stars),
        "retained": len(all_rows),
        "star_distribution": dict(Counter(row["stars"] for row in all_rows)),
        "category_distribution": dict(Counter(row["product_category"] for row in all_rows)),
        "dropped": dict(all_dropped),
        "by_category": category_summary,
    }
    (output_dir / "processing_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(all_rows)} reviews to {output_path}")


if __name__ == "__main__":
    main()
