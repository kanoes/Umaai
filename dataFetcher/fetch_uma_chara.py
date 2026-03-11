#!/usr/bin/env python3
"""
Fetch one character standing image for entries in uma/index.json where chara_img == "No".
Source: official umamusume.jp microCMS character API.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

MICROCMS_API_BASE = "https://6azuq3sitt-aw4monxblm4y4x0oos66.microcms.io/api/v1/character"
MICROCMS_API_KEY_ENV = "UMA_MICROCMS_API_KEY"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def http_get_json(
    url: str,
    *,
    timeout: int,
    retries: int,
    sleep_seconds: float,
    headers: dict[str, str] | None = None,
) -> Any:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = Request(url, headers=request_headers)
        try:
            with urlopen(req, timeout=timeout) as response:
                encoding = response.headers.get_content_charset() or "utf-8"
                text = response.read().decode(encoding, errors="replace")
                return json.loads(text)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise RuntimeError(f"Request failed: {url}; error={last_error}")


def download_binary(
    url: str,
    output_path: Path,
    *,
    timeout: int,
    retries: int,
    sleep_seconds: float,
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(req, timeout=timeout) as response:
                data = response.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(data)
            return
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise RuntimeError(f"Download failed: {url}; error={last_error}")


def normalize_ascii_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def load_index(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        raise FileNotFoundError(f"index.json not found: {index_path}")

    raw = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if not isinstance(raw.get("uma_list"), list):
            raise ValueError(f"index.json missing 'uma_list' list: {index_path}")
        return raw
    if isinstance(raw, list):
        return {
            "source": "legacy_list",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "count": len(raw),
            "uma_list": raw,
        }
    raise ValueError(f"index.json must be object or list, got {type(raw).__name__}")


def is_uma_character(character: dict[str, Any]) -> bool:
    category = character.get("category")
    if isinstance(category, list):
        return any(isinstance(item, str) and item == "ウマ娘" for item in category)
    return False


def fetch_all_characters(
    *,
    api_base: str,
    api_key: str,
    timeout: int,
    retries: int,
    sleep_seconds: float,
    limit: int,
) -> list[dict[str, Any]]:
    offset = 0
    all_items: list[dict[str, Any]] = []
    total_count: int | None = None

    while True:
        query = urlencode({"limit": limit, "offset": offset})
        url = f"{api_base}?{query}"
        payload = http_get_json(
            url,
            timeout=timeout,
            retries=retries,
            sleep_seconds=sleep_seconds,
            headers={"X-MICROCMS-API-KEY": api_key},
        )
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid API payload type at offset={offset}: {type(payload).__name__}")

        contents = payload.get("contents")
        if not isinstance(contents, list):
            raise RuntimeError("Invalid API payload: missing contents list")

        for item in contents:
            if isinstance(item, dict):
                all_items.append(item)

        count = payload.get("totalCount")
        if isinstance(count, int):
            total_count = count

        if not contents:
            break

        offset += len(contents)
        if total_count is not None and offset >= total_count:
            break

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return all_items


def build_character_lookup(
    characters: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_slug: dict[str, dict[str, Any]] = {}
    by_name_ja: dict[str, dict[str, Any]] = {}
    by_name_en_norm: dict[str, dict[str, Any]] = {}

    for character in characters:
        if not is_uma_character(character):
            continue

        char_id = character.get("id")
        if isinstance(char_id, str) and char_id:
            by_slug.setdefault(char_id, character)
            by_slug.setdefault(normalize_ascii_key(char_id), character)

        name_ja = character.get("name")
        if isinstance(name_ja, str) and name_ja:
            by_name_ja.setdefault(name_ja, character)

        name_en = character.get("en")
        if isinstance(name_en, str):
            key = normalize_ascii_key(name_en)
            if key:
                by_name_en_norm.setdefault(key, character)

    return by_slug, by_name_ja, by_name_en_norm


def select_best_visual(character: dict[str, Any]) -> tuple[str | None, str | None]:
    visuals = character.get("visual")
    if not isinstance(visuals, list):
        return None, None

    fallback: tuple[str, str] | None = None
    for item in visuals:
        if not isinstance(item, dict):
            continue
        image = item.get("image")
        if not isinstance(image, dict):
            continue
        image_url = image.get("url")
        if not isinstance(image_url, str) or not image_url:
            continue

        title = ""
        name_field = item.get("name")
        if isinstance(name_field, dict):
            title_value = name_field.get("title")
            if isinstance(title_value, str):
                title = title_value

        if fallback is None:
            fallback = (image_url, title)
        if "勝負服" in title:
            return image_url, title

    if fallback is None:
        return None, None
    return fallback


def detect_extension(image_url: str) -> str:
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return suffix
    return ".png"


def find_match(
    entry: dict[str, Any],
    by_slug: dict[str, dict[str, Any]],
    by_name_ja: dict[str, dict[str, Any]],
    by_name_en_norm: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    slug = entry.get("slug")
    if isinstance(slug, str) and slug:
        matched = by_slug.get(slug) or by_slug.get(normalize_ascii_key(slug))
        if matched is not None:
            return matched

    name_ja = entry.get("name_ja")
    if isinstance(name_ja, str) and name_ja:
        matched = by_name_ja.get(name_ja)
        if matched is not None:
            return matched

    name_en = entry.get("name_en")
    if isinstance(name_en, str) and name_en:
        matched = by_name_en_norm.get(normalize_ascii_key(name_en))
        if matched is not None:
            return matched

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch missing Uma character images for entries where index.json chara_img == 'No'."
    )
    parser.add_argument("--index", default="uma/index.json", help="Path to index.json")
    parser.add_argument("--out-root", default="uma", help="Output root for image files")
    parser.add_argument("--api-base", default=MICROCMS_API_BASE, help="microCMS character endpoint")
    parser.add_argument("--api-key", default="", help=f"microCMS API key (default: ${MICROCMS_API_KEY_ENV})")
    parser.add_argument("--api-limit", type=int, default=100, help="Page size for character API")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retry count")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep between HTTP requests in seconds")
    parser.add_argument(
        "--overwrite-file",
        action="store_true",
        help="Overwrite existing local chara file if it already exists",
    )
    args = parser.parse_args()

    index_path = Path(args.index)
    out_root = Path(args.out_root)
    api_key = args.api_key or os.getenv(MICROCMS_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"microCMS API key is required. Pass --api-key or set environment variable {MICROCMS_API_KEY_ENV}."
        )

    index_payload = load_index(index_path)
    entries_raw = index_payload.get("uma_list")
    if not isinstance(entries_raw, list):
        raise RuntimeError("index.json has no valid uma_list")

    entries: list[dict[str, Any]] = []
    for item in entries_raw:
        if isinstance(item, dict):
            entries.append(item)

    targets = [
        entry
        for entry in entries
        if isinstance(entry.get("chara_img"), str) and str(entry.get("chara_img")) == "No"
    ]
    if not targets:
        print("No entries with chara_img == 'No'. Nothing to do.")
        return

    characters = fetch_all_characters(
        api_base=args.api_base,
        api_key=api_key,
        timeout=args.timeout,
        retries=args.retries,
        sleep_seconds=args.sleep,
        limit=max(1, args.api_limit),
    )
    by_slug, by_name_ja, by_name_en_norm = build_character_lookup(characters)

    matched = 0
    downloaded = 0
    reused = 0
    failed = 0
    no_remote_image = 0
    unmatched = 0

    for idx, entry in enumerate(targets, start=1):
        slug = str(entry.get("slug") or "")
        found = find_match(entry, by_slug, by_name_ja, by_name_en_norm)
        if found is None:
            unmatched += 1
            print(f"[{idx}/{len(targets)}] SKIP {slug} -> no remote match")
            continue

        image_url, image_title = select_best_visual(found)
        if not image_url:
            no_remote_image += 1
            print(f"[{idx}/{len(targets)}] SKIP {slug} -> matched but no visual image")
            continue

        folder_name = entry.get("folder_name")
        if not isinstance(folder_name, str) or not folder_name.strip():
            folder_name = slug if slug else str(found.get("id") or "unknown")
        extension = detect_extension(image_url)
        output_path = out_root / folder_name / "images" / f"chara{extension}"

        try:
            if output_path.exists() and not args.overwrite_file:
                reused += 1
            else:
                download_binary(
                    image_url,
                    output_path,
                    timeout=args.timeout,
                    retries=args.retries,
                    sleep_seconds=max(0.5, args.sleep),
                )
                downloaded += 1

            entry["chara_img"] = output_path.as_posix()
            entry["chara_img_source"] = image_url
            if image_title:
                entry["chara_img_title"] = image_title
            entry["chara_img_updated_at_utc"] = datetime.now(timezone.utc).isoformat()
            matched += 1
            print(f"[{idx}/{len(targets)}] OK   {slug} -> {output_path}")
        except Exception as exc:
            failed += 1
            print(f"[{idx}/{len(targets)}] FAIL {slug} -> {exc}")

        if args.sleep > 0:
            time.sleep(args.sleep)

    index_payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    index_payload["count"] = len(entries)
    index_payload["uma_list"] = entries
    index_payload["chara_img_last_fetch_utc"] = datetime.now(timezone.utc).isoformat()
    index_payload["chara_img_stats"] = {
        "target_count": len(targets),
        "matched_count": matched,
        "downloaded_count": downloaded,
        "reused_file_count": reused,
        "failed_count": failed,
        "unmatched_count": unmatched,
        "no_remote_image_count": no_remote_image,
    }
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Done. Targets={len(targets)}, Matched={matched}, Downloaded={downloaded}, "
        f"Reused={reused}, Failed={failed}, Unmatched={unmatched}, NoRemoteImage={no_remote_image}"
    )
    print(f"Updated index: {index_path}")


if __name__ == "__main__":
    main()
