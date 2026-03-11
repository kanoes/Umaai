#!/usr/bin/env python3
"""
Generate body metrics dataset from existing Uma info files.

Output:
  data/body_metrics.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

THREESIZE_PATTERN = re.compile(r"B\s*(\d+)\D+W\s*(\d+)\D+H\s*(\d+)", re.IGNORECASE)
HEIGHT_PATTERN = re.compile(r"(\d+)\s*cm", re.IGNORECASE)


def parse_threesize(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    matched = THREESIZE_PATTERN.search(value)
    if not matched:
        return None
    return int(matched.group(1)), int(matched.group(2)), int(matched.group(3))


def parse_height_cm(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None
    matched = HEIGHT_PATTERN.search(value)
    if not matched:
        return None
    return int(matched.group(1))


def safe_ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(float(numerator) / float(denominator), 4)


def load_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(payload, dict) and isinstance(payload.get("uma_list"), list):
        return [x for x in payload["uma_list"] if isinstance(x, dict)]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


def build_index_lookup(index_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in index_items:
        slug = item.get("slug")
        if isinstance(slug, str) and slug:
            out[slug] = item
    return out


def build_entry(info_path: Path, index_by_slug: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    try:
        payload = json.loads(info_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    slug = payload.get("slug")
    if not isinstance(slug, str) or not slug:
        return None

    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    profile = data.get("characterProfile")
    if not isinstance(profile, dict):
        return None

    threesize_text = profile.get("threesize")
    parsed = parse_threesize(threesize_text)
    if not parsed:
        return None
    bust, waist, hip = parsed

    height_cm = parse_height_cm(profile.get("height"))
    index_item = index_by_slug.get(slug, {})

    entry: dict[str, Any] = {
        "slug": slug,
        "name_zh": payload.get("name_zh"),
        "name_ja": payload.get("name_ja"),
        "name_en": data.get("alphabetName"),
        "folder_name": payload.get("folder_name"),
        "info_path": info_path.as_posix(),
        "chara_img": index_item.get("chara_img", "No"),
        "threesize_text": threesize_text,
        "bust_cm": bust,
        "waist_cm": waist,
        "hip_cm": hip,
        "height_cm": height_cm,
        "waist_to_hip": safe_ratio(waist, hip),
        "waist_to_bust": safe_ratio(waist, bust),
        "bust_to_hip": safe_ratio(bust, hip),
    }
    return entry


def build_ranking(items: list[dict[str, Any]], key: str, descending: bool = False) -> list[dict[str, Any]]:
    filtered = [item for item in items if isinstance(item.get(key), (int, float))]
    sorted_items = sorted(filtered, key=lambda x: float(x[key]), reverse=descending)
    ranking: list[dict[str, Any]] = []
    for idx, item in enumerate(sorted_items, start=1):
        ranking.append(
            {
                "rank": idx,
                "slug": item.get("slug"),
                "name_zh": item.get("name_zh"),
                "name_ja": item.get("name_ja"),
                "name_en": item.get("name_en"),
                "value": item.get(key),
                "chara_img": item.get("chara_img"),
            }
        )
    return ranking


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    def metric_stats(key: str) -> dict[str, float] | None:
        values = [float(item[key]) for item in items if isinstance(item.get(key), (int, float))]
        if not values:
            return None
        return {
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "avg": round(mean(values), 4),
        }

    return {
        "bust_cm": metric_stats("bust_cm"),
        "waist_cm": metric_stats("waist_cm"),
        "hip_cm": metric_stats("hip_cm"),
        "height_cm": metric_stats("height_cm"),
        "waist_to_hip": metric_stats("waist_to_hip"),
        "waist_to_bust": metric_stats("waist_to_bust"),
        "bust_to_hip": metric_stats("bust_to_hip"),
    }


def run(
    *,
    uma_root: Path = Path("uma"),
    index_path: Path = Path("uma/index.json"),
    output_path: Path = Path("data/body_metrics.json"),
) -> dict[str, Any]:
    index_items = load_index(index_path)
    index_by_slug = build_index_lookup(index_items)

    entries: list[dict[str, Any]] = []
    for info_path in sorted(uma_root.glob("*/info/kouryaku_tools.json")):
        entry = build_entry(info_path, index_by_slug)
        if entry is not None:
            entries.append(entry)

    entries.sort(key=lambda x: str(x.get("slug") or ""))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_index": index_path.as_posix(),
        "source_root": uma_root.as_posix(),
        "count": len(entries),
        "summary": summarize(entries),
        "items": entries,
        "rankings": {
            "waist_to_hip_asc": build_ranking(entries, "waist_to_hip", descending=False),
            "waist_to_bust_asc": build_ranking(entries, "waist_to_bust", descending=False),
            "bust_cm_desc": build_ranking(entries, "bust_cm", descending=True),
            "hip_cm_desc": build_ranking(entries, "hip_cm", descending=True),
            "waist_cm_asc": build_ranking(entries, "waist_cm", descending=False),
            "height_cm_desc": build_ranking(entries, "height_cm", descending=True),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "output_path": output_path.as_posix(),
        "count": len(entries),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build body metrics dataset for Uma characters.")
    parser.add_argument("--uma-root", default="uma", help="Uma root folder")
    parser.add_argument("--index", default="uma/index.json", help="Index json path")
    parser.add_argument("--output", default="data/body_metrics.json", help="Output json path")
    args = parser.parse_args()

    result = run(
        uma_root=Path(args.uma_root),
        index_path=Path(args.index),
        output_path=Path(args.output),
    )
    print(f"Body metrics generated: {result['output_path']} (count={result['count']})")


if __name__ == "__main__":
    main()
