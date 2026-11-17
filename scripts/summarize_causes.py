#!/usr/bin/env python3
"""Turn validated LLM labels into reproducible cause summaries."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def read_rows(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def summarize(rows, dimensions):
    buckets = defaultdict(list)
    for row in rows:
        key = tuple(row.get(dimension, "unknown") for dimension in dimensions)
        buckets[key].append(row)
    result = []
    for key, bucket in buckets.items():
        count = len(bucket)
        avg_severity = sum(row["severity"] for row in bucket) / count
        avg_confidence = sum(row["confidence"] for row in bucket) / count
        result.append({
            **dict(zip(dimensions, key)), "review_count": count,
            "share": round(count / len(rows), 4), "avg_severity": round(avg_severity, 3),
            "avg_confidence": round(avg_confidence, 3),
            "priority_score": round(count * avg_severity * avg_confidence, 3),
        })
    return sorted(result, key=lambda row: row["priority_score"], reverse=True)


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def build_category_table(categories, top_n=3):
    """Render the leading causes of each category as a markdown table."""
    by_category = defaultdict(list)
    for row in categories:
        by_category[row["product_category"]].append(row)
    lines = ["| 品类 | 差评数 | 首位原因 | 第二位原因 | 第三位原因 |", "| --- | --- | --- | --- | --- |"]
    for category in sorted(by_category):
        bucket = sorted(by_category[category], key=lambda row: row["review_count"], reverse=True)
        total = sum(row["review_count"] for row in bucket)
        cells = [
            f"{row['primary_cause']}（{row['review_count']}，{row['review_count'] / total:.1%}）"
            for row in bucket[:top_n]
        ]
        cells += ["-"] * (top_n - len(cells))
        lines.append(f"| {category} | {total} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    args = parse_args()
    rows = read_rows(args.labels)
    if not rows:
        raise SystemExit("No labels found.")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    causes = summarize(rows, ["primary_cause"])
    categories = summarize(rows, ["product_category", "primary_cause"])
    write_csv(output_dir / "cause_summary.csv", causes)
    write_csv(output_dir / "category_cause_summary.csv", categories)
    if len({row.get("language") for row in rows}) > 1:
        write_csv(output_dir / "language_cause_summary.csv", summarize(rows, ["language", "primary_cause"]))
    top_causes = "\n".join(
        f"{idx}. `{row['primary_cause']}`：{row['review_count']} 条（{row['share']:.1%}），"
        f"平均严重度 {row['avg_severity']}，平均置信度 {row['avg_confidence']}，优先级 {row['priority_score']}"
        for idx, row in enumerate(causes, start=1)
    )
    report = f"""# 差评归因报告

分析评论数：{len(rows)}。

## 全量归因分布（按优先级排序）

{top_causes}

## 品类 × 归因

{build_category_table(categories)}

## 解释边界

优先级 = 评论数 × 平均严重度 × 平均置信度。它用于安排人工复核和改进顺序，不能证明某个原因是客观产品缺陷。建议优先复核置信度低于 0.6 的记录，并从每个一级原因中抽样核对证据片段。
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"Wrote summaries for {len(rows)} labeled reviews to {output_dir}")


if __name__ == "__main__":
    main()
