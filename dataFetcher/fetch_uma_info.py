#!/usr/bin/env python3
"""
Fetch all character info from https://ウマ娘.攻略.tools and write JSON files to:
  uma/<中文或日文马名>/info/kouryaku_tools.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

UNICODE_BASE_URL = "https://ウマ娘.攻略.tools"
PUNYCODE_BASE_URL = "https://xn--gck1f423k.xn--1bvt37a.tools"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

CHUNK_PATTERN = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', re.S)
SLUG_PATTERN = re.compile(r"/characters/([a-z0-9_-]+)")
CHARACTER_PATTERN = re.compile(r'"character":\{')
EXCLUDED_SLUGS = {"attributes", "rankings"}


def http_get_text(url: str, timeout: int = 30, retries: int = 3, sleep_seconds: float = 1.0) -> str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(req, timeout=timeout) as response:
                encoding = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(encoding, errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise RuntimeError(f"Request failed: {url}; error={last_error}")


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def extract_slugs(characters_page_html: str) -> list[str]:
    slugs = [slug for slug in SLUG_PATTERN.findall(characters_page_html) if slug not in EXCLUDED_SLUGS]
    return dedupe_keep_order(slugs)


def decode_next_payload(page_html: str) -> str:
    chunks = CHUNK_PATTERN.findall(page_html)
    if not chunks:
        raise ValueError("Could not find __next_f payload chunks")

    decoded: list[str] = []
    for chunk in chunks:
        # chunk itself is a JSON string literal body, so wrapping it in quotes
        # and json.loads gives us the decoded text safely.
        decoded.append(json.loads(f'"{chunk}"'))
    return "".join(decoded)


def find_matching_brace(text: str, start_index: int) -> int | None:
    if start_index >= len(text) or text[start_index] != "{":
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start_index, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def extract_character_object(decoded_payload: str, slug: str) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for match in CHARACTER_PATTERN.finditer(decoded_payload):
        start = match.start() + len('"character":')
        end = find_matching_brace(decoded_payload, start)
        if end is None:
            continue
        raw_obj = decoded_payload[start : end + 1]
        try:
            obj = json.loads(raw_obj)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("alphabetId"), str):
            candidates.append(obj)

    if not candidates:
        raise ValueError("No valid character object found in decoded payload")

    slug_matched = [obj for obj in candidates if obj.get("alphabetId") == slug]
    pool = slug_matched if slug_matched else candidates

    def score(obj: dict[str, Any]) -> int:
        keys = ("characterProfile", "supportCards", "characterCards", "mainComics", "comics")
        return sum(1 for k in keys if k in obj)

    return max(pool, key=score)


def load_name_map(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"name_map.json not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"name_map.json must be an object, got {type(raw).__name__}")
    return {str(k): str(v) for k, v in raw.items()}


def sanitize_folder_name(name: str) -> str:
    cleaned = name.strip().replace("/", "／").replace("\0", "")
    return cleaned if cleaned else "unknown"


def resolve_folder_name(out_root: Path, preferred_name: str, slug: str, ja_name: str) -> str:
    base = sanitize_folder_name(preferred_name)
    base_dir = out_root / base
    info_file = base_dir / "info" / "kouryaku_tools.json"

    if not base_dir.exists():
        return base

    if info_file.exists():
        try:
            existing = json.loads(info_file.read_text(encoding="utf-8"))
            existing_slug = existing.get("slug")
            existing_name = existing.get("name_ja")
            if existing_slug == slug or existing_name == ja_name:
                return base
        except Exception:
            pass

    return f"{base}_{slug}"


def write_character_info(
    out_root: Path,
    slug: str,
    character_obj: dict[str, Any],
    name_map: dict[str, str],
) -> tuple[Path, bool]:
    ja_name = str(character_obj.get("name") or slug)
    mapped_name = name_map.get(ja_name)
    preferred_folder_name = mapped_name if mapped_name else ja_name
    folder_name = resolve_folder_name(out_root, preferred_folder_name, slug, ja_name)

    info_dir = out_root / folder_name / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    output_path = info_dir / "kouryaku_tools.json"

    payload = {
        "source_site": UNICODE_BASE_URL,
        "source_url": f"{UNICODE_BASE_URL}/characters/{slug}",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "slug": slug,
        "name_ja": ja_name,
        "name_zh": mapped_name,
        "folder_name": folder_name,
        "data": character_obj,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path, mapped_name is None


def build_existing_slug_index(out_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not out_root.exists():
        return index

    for info_file in out_root.glob("*/info/kouryaku_tools.json"):
        try:
            payload = json.loads(info_file.read_text(encoding="utf-8"))
            slug = payload.get("slug")
            if isinstance(slug, str) and slug and slug not in index:
                index[slug] = info_file
        except Exception:
            # Ignore invalid/corrupt files and keep scanning.
            continue

    return index


def load_existing_index_chara(index_path: Path) -> dict[str, dict[str, str]]:
    if not index_path.exists():
        return {}

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if isinstance(payload, dict):
        entries = payload.get("uma_list")
    elif isinstance(payload, list):
        entries = payload
    else:
        return {}

    if not isinstance(entries, list):
        return {}

    out: dict[str, dict[str, str]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug:
            continue
        chara_img = item.get("chara_img")
        if isinstance(chara_img, str):
            out[slug] = {"chara_img": chara_img}
            chara_img_source = item.get("chara_img_source")
            if isinstance(chara_img_source, str):
                out[slug]["chara_img_source"] = chara_img_source
    return out


def build_index_list(out_root: Path) -> list[dict[str, Any]]:
    existing = load_existing_index_chara(out_root / "index.json")
    items: list[dict[str, Any]] = []

    for info_file in out_root.glob("*/info/kouryaku_tools.json"):
        try:
            payload = json.loads(info_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue

        slug = payload.get("slug")
        if not isinstance(slug, str) or not slug:
            continue

        data = payload.get("data")
        name_en = None
        if isinstance(data, dict):
            alphabet_name = data.get("alphabetName")
            if isinstance(alphabet_name, str) and alphabet_name.strip():
                name_en = alphabet_name

        folder_name = payload.get("folder_name")
        if not isinstance(folder_name, str) or not folder_name.strip():
            folder_name = info_file.parent.parent.name

        item = {
            "slug": slug,
            "name_ja": payload.get("name_ja"),
            "name_zh": payload.get("name_zh"),
            "name_en": name_en,
            "folder_name": folder_name,
            "info_path": info_file.as_posix(),
            "chara_img": "No",
        }

        existing_chara = existing.get(slug)
        if existing_chara:
            chara_img = existing_chara.get("chara_img")
            if isinstance(chara_img, str) and chara_img:
                item["chara_img"] = chara_img
            chara_img_source = existing_chara.get("chara_img_source")
            if isinstance(chara_img_source, str) and chara_img_source:
                item["chara_img_source"] = chara_img_source

        items.append(item)

    items.sort(key=lambda x: str(x.get("slug") or ""))
    return items


def write_index_file(out_root: Path) -> Path:
    items = build_index_list(out_root)
    payload = {
        "source": "local uma/*/info/kouryaku_tools.json",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "uma_list": items,
    }
    out_root.mkdir(parents=True, exist_ok=True)
    index_path = out_root / "index.json"
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return index_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch all Uma characters from https://ウマ娘.攻略.tools and write JSON to "
            "uma/<name>/info/kouryaku_tools.json"
        )
    )
    parser.add_argument("--base-url", default=PUNYCODE_BASE_URL, help="Base URL (default: punycode domain)")
    parser.add_argument("--name-map", default="ref/name_map.json", help="Path to name_map.json")
    parser.add_argument("--out-root", default="uma", help="Output root directory")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retry count")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep between requests in seconds")
    parser.add_argument("--only", nargs="*", help="Only fetch specified slugs")
    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        default=True,
        help="Skip character if an existing kouryaku_tools.json for the same slug is found (default: enabled)",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Disable skipping and overwrite by re-fetching existing character data",
    )
    args = parser.parse_args()

    name_map_path = Path(args.name_map)
    out_root = Path(args.out_root)
    name_map = load_name_map(name_map_path)

    list_url = f"{args.base_url.rstrip('/')}/characters"
    list_html = http_get_text(list_url, timeout=args.timeout, retries=args.retries)
    all_slugs = extract_slugs(list_html)

    if args.only:
        allowed = set(args.only)
        slugs = [s for s in all_slugs if s in allowed]
    else:
        slugs = all_slugs

    if not slugs:
        raise RuntimeError("No character slugs found.")

    print(f"Found {len(slugs)} character slugs.")
    print(f"Skip existing: {'ON' if args.skip_existing else 'OFF'}")

    success = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    missing_name_map: list[dict[str, str]] = []
    existing_slug_index = build_existing_slug_index(out_root) if args.skip_existing else {}

    for index, slug in enumerate(slugs, start=1):
        if args.skip_existing and slug in existing_slug_index:
            skipped += 1
            skip_path = existing_slug_index[slug]
            print(f"[{index}/{len(slugs)}] SKIP {slug} -> {skip_path}")
            continue

        detail_url = f"{args.base_url.rstrip('/')}/characters/{slug}"
        try:
            detail_html = http_get_text(
                detail_url,
                timeout=args.timeout,
                retries=args.retries,
                sleep_seconds=max(0.5, args.sleep),
            )
            payload_text = decode_next_payload(detail_html)
            character_obj = extract_character_object(payload_text, slug)
            output_path, is_missing_map = write_character_info(out_root, slug, character_obj, name_map)
            success += 1
            if is_missing_map:
                missing_name_map.append({"slug": slug, "name_ja": str(character_obj.get("name") or slug)})
            print(f"[{index}/{len(slugs)}] OK   {slug} -> {output_path}")
        except Exception as exc:  # keep running through all characters
            failures.append({"slug": slug, "error": str(exc)})
            print(f"[{index}/{len(slugs)}] FAIL {slug} -> {exc}")

        if args.sleep > 0:
            time.sleep(args.sleep)

    index_path = write_index_file(out_root)
    print(
        f"Done. Success={success}, Skipped={skipped}, "
        f"Failed={len(failures)}, MissingMap={len(missing_name_map)}"
    )
    print(f"Index: {index_path}")


if __name__ == "__main__":
    main()
