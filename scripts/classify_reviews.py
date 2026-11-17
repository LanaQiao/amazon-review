#!/usr/bin/env python3
"""Classify cleaned reviews with an OpenAI-compatible structured-output endpoint."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from review_mining.prompting import build_messages
from review_mining.taxonomy import CAUSES, LABEL_SCHEMA


def load_workspace_env():
    """Load simple KEY=VALUE settings from a gitignored workspace .env file."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'") )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--model", default=os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "qwen3.7-flash"))
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv(
            "LLM_BASE_URL",
            os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        ),
    )
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-retries", type=int, default=4)
    return parser.parse_args()


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_items(items, expected_ids):
    by_id = {item.get("review_id"): item for item in items}
    if set(by_id) != set(expected_ids):
        raise ValueError("Model response IDs do not match this batch")
    for item in items:
        if item["primary_cause"] not in CAUSES:
            raise ValueError("Unexpected cause")
        if item["primary_cause"] in item["secondary_causes"]:
            raise ValueError("Primary cause repeated as secondary")
        if not 1 <= item["severity"] <= 5 or not 0 <= item["confidence"] <= 1:
            raise ValueError("Invalid score range")
    return by_id


def request_labels(client, model, batch, max_retries):
    messages = build_messages(batch)
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "review_attribution", "strict": True, "schema": LABEL_SCHEMA},
                },
            )
            content = response.choices[0].message.content
            return validate_items(json.loads(content)["items"], [row["review_id"] for row in batch])
        except Exception as error:
            last_error = error
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


def main():
    load_workspace_env()
    args = parse_args()
    all_rows = read_jsonl(args.input)
    if args.limit:
        all_rows = all_rows[:args.limit]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if output_path.exists():
        completed = {row["review_id"] for row in read_jsonl(output_path)}
    pending = [row for row in all_rows if row["review_id"] not in completed]
    api_key = os.getenv(
        "LLM_API_KEY", os.getenv("DASHSCOPE_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    )
    if not api_key:
        raise SystemExit("Set LLM_API_KEY in the environment or in the workspace .env file.")
    client = OpenAI(base_url=args.base_url, api_key=api_key)

    with output_path.open("a", encoding="utf-8") as output:
        for offset in range(0, len(pending), args.batch_size):
            batch = pending[offset: offset + args.batch_size]
            labels = request_labels(client, args.model, batch, args.max_retries)
            for source in batch:
                output_row = {**source, **labels[source["review_id"]]}
                output.write(json.dumps(output_row, ensure_ascii=False) + "\n")
            output.flush()
            print(f"Completed {offset + len(batch)}/{len(pending)} pending reviews")


if __name__ == "__main__":
    main()
