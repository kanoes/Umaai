from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dataGenerator.build_body_metrics import (
    build_entry as build_metric_entry,
    build_index_lookup,
    build_ranking,
    load_index as load_metric_index,
    summarize as summarize_metrics,
)

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "uma" / "index.json"
UMA_ROOT = ROOT / "uma"

RANKING_META = {
    "waist_to_hip_asc": {
        "label": "腰臀比",
        "description": "越低代表曲线越明显。",
        "direction": "asc",
    },
    "waist_to_bust_asc": {
        "label": "腰乳比",
        "description": "越低代表上身与腰线反差更强。",
        "direction": "asc",
    },
    "bust_cm_desc": {
        "label": "胸围",
        "description": "按胸围从高到低排序。",
        "direction": "desc",
        "unit": "cm",
    },
    "hip_cm_desc": {
        "label": "臀围",
        "description": "按臀围从高到低排序。",
        "direction": "desc",
        "unit": "cm",
    },
    "waist_cm_asc": {
        "label": "腰围",
        "description": "按腰围从低到高排序。",
        "direction": "asc",
        "unit": "cm",
    },
    "height_cm_desc": {
        "label": "身高",
        "description": "按身高从高到低排序。",
        "direction": "desc",
        "unit": "cm",
    },
}

SUPPORT_COMMAND_LABELS = {
    0: "速度",
    1: "耐力",
    2: "力量",
    3: "根性",
    4: "智力",
    5: "友人",
    6: "团队",
}

APTITUDE_LABELS = {
    1: "G",
    2: "F",
    3: "E",
    4: "D",
    5: "C",
    6: "B",
    7: "A",
    8: "S",
}

PROFILE_SECTIONS = [
    (
        "基础资料",
        [
            ("birthday", "生日"),
            ("height", "身高"),
            ("weight", "体重"),
            ("threesize", "三围"),
            ("prizeMoney", "生涯赏金"),
            ("schoolGrade", "学年"),
            ("dormitory", "宿舍"),
            ("shoes", "鞋码"),
        ],
    ),
    (
        "角色小设定",
        [
            ("good", "擅长"),
            ("bad", "苦手"),
            ("ear", "耳朵小情报"),
            ("tail", "尾巴小情报"),
            ("family", "家庭轶事"),
            ("before", "比赛前仪式"),
            ("buy", "常买的东西"),
            ("myrule", "个人守则"),
            ("boast", "得意事件"),
            ("spbg", "手机壁纸"),
            ("subject", "拿手科目"),
        ],
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_hex(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    value = value.strip()
    return value if value.startswith("#") else f"#{value}"


def to_date_string(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    raw = value[2:] if value.startswith("$D") else value
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def to_timestamp(value: Any) -> int:
    if not isinstance(value, str) or not value:
        return 0
    raw = value[2:] if value.startswith("$D") else value
    try:
        return int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def compact_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def format_birthday(profile: dict[str, Any]) -> str | None:
    month = profile.get("birthMonth")
    day = profile.get("birthDate")
    if isinstance(month, int) and isinstance(day, int):
        return f"{month}月{day}日"
    return None


def format_prize_money(value: Any) -> str | None:
    if isinstance(value, int):
        return f"{value:,}"
    return None


def profile_sections(profile: dict[str, Any]) -> list[dict[str, Any]]:
    values = dict(profile)
    values["birthday"] = format_birthday(profile)
    values["prizeMoney"] = format_prize_money(profile.get("prizeMoney"))
    sections: list[dict[str, Any]] = []
    for title, fields in PROFILE_SECTIONS:
        items = []
        for key, label in fields:
            raw = values.get(key)
            if raw in (None, "", []):
                continue
            items.append({"key": key, "label": label, "value": raw})
        if items:
            sections.append({"title": title, "items": items})
    return sections


def serialize_support_cards(cards: Any) -> list[dict[str, Any]]:
    if not isinstance(cards, list):
        return []

    out = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        command = item.get("command")
        out.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "title": item.get("title"),
                "rarity": item.get("rarity"),
                "published_at": to_date_string(item.get("publishedAt")),
                "published_at_ts": to_timestamp(item.get("publishedAt")),
                "command": command,
                "command_label": SUPPORT_COMMAND_LABELS.get(command, f"类型 {command}"),
                "event_bonus": bool(item.get("ev")),
            }
        )
    out.sort(key=lambda x: x["published_at_ts"], reverse=True)
    return out


def aptitude_grade(value: Any) -> str | None:
    if isinstance(value, int):
        return APTITUDE_LABELS.get(value, str(value))
    return None


def serialize_character_cards(cards: Any) -> list[dict[str, Any]]:
    if not isinstance(cards, list):
        return []

    out = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "aliases": item.get("commonName"),
                "published_at": to_date_string(item.get("publishedAt")),
                "published_at_ts": to_timestamp(item.get("publishedAt")),
                "limited": bool(item.get("limited")),
                "event_bonus": bool(item.get("ev")),
                "talents": {
                    "速度": item.get("talentSpeed"),
                    "耐力": item.get("talentStamina"),
                    "力量": item.get("talentPow"),
                    "根性": item.get("talentGuts"),
                    "智力": item.get("talentWiz"),
                },
                "aptitudes": {
                    "草地": aptitude_grade(item.get("aptitudeTurf")),
                    "泥地": aptitude_grade(item.get("aptitudeDirt")),
                    "短距离": aptitude_grade(item.get("aptitudeShort")),
                    "英里": aptitude_grade(item.get("aptitudeMile")),
                    "中距离": aptitude_grade(item.get("aptitudeMiddle")),
                    "长距离": aptitude_grade(item.get("aptitudeLong")),
                    "逃": aptitude_grade(item.get("aptitudeRunner")),
                    "先": aptitude_grade(item.get("aptitudeLeader")),
                    "差": aptitude_grade(item.get("aptitudeBetweener")),
                    "追": aptitude_grade(item.get("aptitudeChaser")),
                },
            }
        )
    out.sort(key=lambda x: x["published_at_ts"], reverse=True)
    return out


def serialize_relations(comics: Any) -> list[dict[str, Any]]:
    if not isinstance(comics, list):
        return []

    seen: set[str] = set()
    out = []
    for item in comics:
        if not isinstance(item, dict):
            continue
        main_character = item.get("mainCharacter")
        if not isinstance(main_character, dict):
            continue
        slug = main_character.get("alphabetId")
        if not isinstance(slug, str) or not slug or slug in seen:
            continue
        seen.add(slug)
        out.append(
            {
                "slug": slug,
                "name_ja": main_character.get("name"),
                "name_en": main_character.get("alphabetName"),
                "theme": {
                    "main": ensure_hex(main_character.get("uiColorMain"), "#3a69c7"),
                    "sub": ensure_hex(main_character.get("uiColorSub"), "#ffd8eb"),
                    "speech": ensure_hex(main_character.get("uiSpeechColor1"), "#63b5ff"),
                },
            }
        )
    return out


def character_theme(data: dict[str, Any]) -> dict[str, str]:
    return {
        "main": ensure_hex(data.get("uiColorMain"), "#e86aa9"),
        "sub": ensure_hex(data.get("uiColorSub"), "#ffdbe6"),
        "border": ensure_hex(data.get("uiBorderColor"), "#f5b74a"),
        "speech": ensure_hex(data.get("uiSpeechColor1"), "#63b5ff"),
        "nameplate_1": ensure_hex(data.get("uiNameplateColor1"), "#3f8df5"),
        "nameplate_2": ensure_hex(data.get("uiNameplateColor2"), "#a5d5ff"),
        "image_main": ensure_hex(data.get("imageColorMain"), "#fff5c1"),
        "image_sub": ensure_hex(data.get("imageColorSub"), "#ffd4ea"),
    }


def public_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metric:
        return None
    return {
        "slug": metric.get("slug"),
        "name_zh": metric.get("name_zh"),
        "name_ja": metric.get("name_ja"),
        "name_en": metric.get("name_en"),
        "threesize_text": metric.get("threesize_text"),
        "bust_cm": metric.get("bust_cm"),
        "waist_cm": metric.get("waist_cm"),
        "hip_cm": metric.get("hip_cm"),
        "height_cm": metric.get("height_cm"),
        "waist_to_hip": metric.get("waist_to_hip"),
        "waist_to_bust": metric.get("waist_to_bust"),
        "bust_to_hip": metric.get("bust_to_hip"),
    }


def search_blob(summary: dict[str, Any], detail: dict[str, Any]) -> str:
    parts = [
        summary.get("name_zh"),
        summary.get("name_ja"),
        summary.get("name_en"),
        summary.get("slug"),
        detail.get("description"),
    ]
    for section in detail.get("profile_sections", []):
        for item in section.get("items", []):
            parts.append(item.get("value"))
    return " ".join(str(part).lower() for part in parts if part)


def load_metric_bundle(index_by_slug: dict[str, dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for info_path in sorted(UMA_ROOT.glob("*/info/kouryaku_tools.json")):
        entry = build_metric_entry(info_path, index_by_slug)
        if entry is not None:
            entries.append(entry)

    rankings = {
        "waist_to_hip_asc": build_ranking(entries, "waist_to_hip", descending=False),
        "waist_to_bust_asc": build_ranking(entries, "waist_to_bust", descending=False),
        "bust_cm_desc": build_ranking(entries, "bust_cm", descending=True),
        "hip_cm_desc": build_ranking(entries, "hip_cm", descending=True),
        "waist_cm_asc": build_ranking(entries, "waist_cm", descending=False),
        "height_cm_desc": build_ranking(entries, "height_cm", descending=True),
    }
    return {
        "items": entries,
        "by_slug": {entry["slug"]: entry for entry in entries},
        "summary": summarize_metrics(entries),
        "rankings": rankings,
    }


@dataclass
class CachedDataset:
    signature: tuple[tuple[str, int], ...]
    payload: dict[str, Any]


class SiteDataStore:
    def __init__(self) -> None:
        self._cache: CachedDataset | None = None

    def invalidate(self) -> None:
        self._cache = None

    def _signature(self) -> tuple[tuple[str, int], ...]:
        files = [INDEX_PATH]
        files.extend(sorted(UMA_ROOT.glob("*/info/kouryaku_tools.json")))
        signature = []
        for path in files:
            if path.exists():
                signature.append((path.as_posix(), path.stat().st_mtime_ns))
        return tuple(signature)

    def get(self) -> dict[str, Any]:
        signature = self._signature()
        if self._cache is None or self._cache.signature != signature:
            self._cache = CachedDataset(signature=signature, payload=self._load())
        return self._cache.payload

    def _load(self) -> dict[str, Any]:
        if not INDEX_PATH.exists():
            return {
                "updated_at_utc": None,
                "summaries": [],
                "character_lookup": {},
                "rankings": {},
                "ranking_meta": ranking_meta_payload(),
                "overview": empty_overview(),
                "stats": empty_stats(),
            }

        index_payload = load_json(INDEX_PATH)
        index_items = index_payload.get("uma_list", []) if isinstance(index_payload, dict) else []
        index_items = [item for item in index_items if isinstance(item, dict)]
        index_by_slug = build_index_lookup(load_metric_index(INDEX_PATH))
        metrics_bundle = load_metric_bundle(index_by_slug)
        metrics_by_slug = metrics_bundle["by_slug"]

        details: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        for item in index_items:
            slug = item.get("slug")
            if not isinstance(slug, str) or not slug:
                continue
            info_path = ROOT / str(item.get("info_path") or "")
            if not info_path.exists():
                continue
            try:
                payload = load_json(info_path)
            except Exception:
                continue

            data = payload.get("data")
            if not isinstance(data, dict):
                continue
            profile = data.get("characterProfile")
            if not isinstance(profile, dict):
                profile = {}

            support_cards = serialize_support_cards(data.get("supportCards"))
            character_cards = serialize_character_cards(data.get("characterCards"))
            relations = serialize_relations(data.get("comics"))
            metric = metrics_by_slug.get(slug)
            theme = character_theme(data)
            latest_outfit_at_ts = max((card["published_at_ts"] for card in character_cards), default=0)
            summary = {
                "slug": slug,
                "name_zh": payload.get("name_zh"),
                "name_ja": payload.get("name_ja"),
                "name_en": data.get("alphabetName"),
                "image": {
                    "path": item.get("chara_img"),
                    "title": item.get("chara_img_title"),
                    "ready": isinstance(item.get("chara_img"), str) and item.get("chara_img") != "No",
                },
                "theme": theme,
                "tagline": compact_text(profile.get("description"))[:100],
                "counts": {
                    "support_cards": len(support_cards),
                    "character_cards": len(character_cards),
                    "relations": len(relations),
                    "main_comics": len(data.get("mainComics") or []),
                },
                "metrics": public_metric(metric),
                "latest_outfit_at_ts": latest_outfit_at_ts,
            }
            detail = {
                **summary,
                "description": compact_text(profile.get("description")),
                "profile_sections": profile_sections(profile),
                "support_cards": support_cards,
                "character_cards": character_cards,
                "relations": relations,
                "main_comics": data.get("mainComics") if isinstance(data.get("mainComics"), list) else [],
            }
            blob = search_blob(summary, detail)
            detail["search_blob"] = blob
            summary["search_blob"] = blob
            details.append(detail)
            summaries.append(summary)

        details.sort(key=lambda x: str(x.get("name_zh") or x.get("name_ja") or x.get("slug")))
        summaries.sort(key=lambda x: str(x.get("name_zh") or x.get("name_ja") or x.get("slug")))

        overview = build_overview(summaries, metrics_bundle["rankings"])
        stats = build_stats(details, metrics_bundle)
        return {
            "updated_at_utc": index_payload.get("updated_at_utc") if isinstance(index_payload, dict) else None,
            "summaries": summaries,
            "character_lookup": {detail["slug"]: detail for detail in details},
            "rankings": metrics_bundle["rankings"],
            "ranking_meta": ranking_meta_payload(),
            "overview": overview,
            "stats": stats,
        }


def ranking_meta_payload() -> list[dict[str, Any]]:
    return [{"key": key, **value} for key, value in RANKING_META.items()]


def empty_overview() -> dict[str, Any]:
    return {
        "featured": [],
        "latest_outfits": [],
        "ranking_previews": {},
    }


def empty_stats() -> dict[str, Any]:
    return {
        "total_characters": 0,
        "with_images": 0,
        "with_metrics": 0,
        "support_card_total": 0,
        "character_card_total": 0,
        "relation_total": 0,
    }


def build_overview(summaries: list[dict[str, Any]], rankings: dict[str, Any]) -> dict[str, Any]:
    scored = sorted(
        summaries,
        key=lambda item: (
            item["counts"]["character_cards"] * 4
            + item["counts"]["support_cards"] * 2
            + item["counts"]["relations"],
            str(item.get("name_zh") or item.get("slug")),
        ),
        reverse=True,
    )
    latest_outfits = sorted(
        summaries,
        key=lambda item: int(item.get("latest_outfit_at_ts") or 0),
        reverse=True,
    )
    ranking_previews = {}
    for key, ranking in rankings.items():
        ranking_previews[key] = ranking[:5]

    return {
        "featured": [strip_search_blob(item) for item in scored[:8]],
        "latest_outfits": [strip_search_blob(item) for item in latest_outfits[:6]],
        "ranking_previews": ranking_previews,
    }


def build_stats(details: list[dict[str, Any]], metrics_bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_characters": len(details),
        "with_images": sum(1 for item in details if item["image"]["ready"]),
        "with_metrics": len(metrics_bundle["items"]),
        "support_card_total": sum(item["counts"]["support_cards"] for item in details),
        "character_card_total": sum(item["counts"]["character_cards"] for item in details),
        "relation_total": sum(item["counts"]["relations"] for item in details),
    }


def strip_search_blob(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out.pop("search_blob", None)
    out.pop("latest_outfit_at_ts", None)
    return out


def search_characters(dataset: dict[str, Any], query: str) -> list[dict[str, Any]]:
    if not query:
        return [strip_search_blob(item) for item in dataset["summaries"]]
    terms = [term.strip().lower() for term in query.split() if term.strip()]
    if not terms:
        return [strip_search_blob(item) for item in dataset["summaries"]]

    matched = []
    for item in dataset["summaries"]:
        blob = item.get("search_blob", "")
        if all(term in blob for term in terms):
            matched.append(strip_search_blob(item))
    return matched


def get_character(dataset: dict[str, Any], slug: str) -> dict[str, Any] | None:
    detail = dataset["character_lookup"].get(slug)
    if detail is None:
        return None
    return strip_search_blob(detail)


def get_compare(dataset: dict[str, Any], slugs: list[str]) -> list[dict[str, Any]]:
    out = []
    for slug in slugs:
        detail = get_character(dataset, slug)
        if detail is not None:
            out.append(detail)
    return out


STORE = SiteDataStore()
