from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
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
DATA_DIR = ROOT / "data"
INDEX_PATH = ROOT / "uma" / "index.json"
UMA_ROOT = ROOT / "uma"

MANIFEST_PATH = DATA_DIR / "site_manifest.json"
SUMMARIES_PATH = DATA_DIR / "site_characters.json"
DETAILS_PATH = DATA_DIR / "site_details.json"
RANKINGS_PATH = DATA_DIR / "site_rankings.json"
SEARCH_INDEX_PATH = DATA_DIR / "site_search_index.json"
QUALITY_REPORT_PATH = DATA_DIR / "site_quality_report.json"
RELATIONS_PATH = DATA_DIR / "site_relations.json"

DERIVED_PATHS = {
    "manifest": MANIFEST_PATH,
    "summaries": SUMMARIES_PATH,
    "details": DETAILS_PATH,
    "rankings": RANKINGS_PATH,
    "search_index": SEARCH_INDEX_PATH,
    "quality_report": QUALITY_REPORT_PATH,
    "relations": RELATIONS_PATH,
}

DISTANCE_FIELDS = [
    ("short", "短距离", "aptitudeShort"),
    ("mile", "英里", "aptitudeMile"),
    ("middle", "中距离", "aptitudeMiddle"),
    ("long", "长距离", "aptitudeLong"),
]

STYLE_FIELDS = [
    ("runner", "逃", "aptitudeRunner"),
    ("leader", "先", "aptitudeLeader"),
    ("betweener", "差", "aptitudeBetweener"),
    ("chaser", "追", "aptitudeChaser"),
]

RANKING_META = {
    "waist_to_hip_asc": {
        "label": "腰臀比",
        "description": "越低代表曲线越明显。",
        "direction": "asc",
        "category": "身体数据",
    },
    "waist_to_bust_asc": {
        "label": "腰乳比",
        "description": "越低代表上身与腰线反差更强。",
        "direction": "asc",
        "category": "身体数据",
    },
    "bust_cm_desc": {
        "label": "胸围",
        "description": "按胸围从高到低排序。",
        "direction": "desc",
        "unit": "cm",
        "category": "身体数据",
    },
    "hip_cm_desc": {
        "label": "臀围",
        "description": "按臀围从高到低排序。",
        "direction": "desc",
        "unit": "cm",
        "category": "身体数据",
    },
    "waist_cm_asc": {
        "label": "腰围",
        "description": "按腰围从低到高排序。",
        "direction": "asc",
        "unit": "cm",
        "category": "身体数据",
    },
    "height_cm_desc": {
        "label": "身高",
        "description": "按身高从高到低排序。",
        "direction": "desc",
        "unit": "cm",
        "category": "身体数据",
    },
    "support_card_count_desc": {
        "label": "支援卡持有量",
        "description": "适合直接找内容储备最厚的角色。",
        "direction": "desc",
        "category": "内容专题",
    },
    "character_card_count_desc": {
        "label": "衣装收藏量",
        "description": "看谁的衣装版本最多。",
        "direction": "desc",
        "category": "内容专题",
    },
    "relation_count_desc": {
        "label": "关系网络密度",
        "description": "以漫画联动为核心的关系广度排行。",
        "direction": "desc",
        "category": "内容专题",
    },
    "newest_outfit_desc": {
        "label": "最近上新",
        "description": "按最近衣装发布时间排序。",
        "direction": "desc",
        "category": "内容专题",
    },
    "content_density_desc": {
        "label": "内容密度",
        "description": "综合衣装、支援卡、关系与详情丰富度的趣味分数。",
        "direction": "desc",
        "category": "内容专题",
    },
    "curve_presence_desc": {
        "label": "曲线存在感",
        "description": "趣味指标：胸臀总量减去腰围，数值越高越突出。",
        "direction": "desc",
        "category": "内容专题",
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

PERSONALITY_RULES = [
    ("元气感", ["明朗", "快活", "元気", "活発", "ハツラツ", "天真", "朗らか"]),
    ("努力家", ["頑張り", "努力", "ひたむき", "真面目", "ガッツ", "熱心"]),
    ("名门气质", ["名門", "お嬢様", "優雅", "品格", "上品"]),
    ("自由派", ["自由", "気まま", "奔放", "縛られない", "マイペース"]),
    ("冷静派", ["冷静", "理知", "クール", "寡黙", "沈着"]),
    ("创作者", ["音楽", "芸術", "漫画", "創作", "アート", "演奏"]),
    ("亲和力", ["人懐っこい", "友達", "誰とでも", "甘え", "寂しがり", "ハグ"]),
    ("偶像感", ["アイドル", "スター", "舞台", "ファン", "キラキラ"]),
    ("挑战者", ["挑戦", "負けず嫌い", "1番", "高み", "ライバル"]),
]

THEME_GROUPS = [
    ("主角气场", ["元气感", "努力家", "挑战者"]),
    ("名门优雅", ["名门气质"]),
    ("自由灵感", ["自由派", "创作者"]),
    ("冷静知性", ["冷静派"]),
    ("亲和偶像", ["亲和力", "偶像感"]),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def compact_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def safe_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def grade_score(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0


def aptitude_grade(value: Any) -> str | None:
    if isinstance(value, int):
        return APTITUDE_LABELS.get(value, str(value))
    return None


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


def group_support_cards(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_command: dict[str, list[dict[str, Any]]] = {}
    by_rarity: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        command_label = str(card.get("command_label") or "其他")
        rarity_label = f"{card.get('rarity') or '?'}星"
        by_command.setdefault(command_label, []).append(card)
        by_rarity.setdefault(rarity_label, []).append(card)

    command_groups = [
        {"label": label, "count": len(items), "items": items}
        for label, items in sorted(by_command.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    rarity_groups = [
        {"label": label, "count": len(items), "items": items}
        for label, items in sorted(by_rarity.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    return {"by_command": command_groups, "by_rarity": rarity_groups}


def serialize_character_cards(cards: Any) -> list[dict[str, Any]]:
    if not isinstance(cards, list):
        return []

    out = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        published_at = to_date_string(item.get("publishedAt"))
        published_at_ts = to_timestamp(item.get("publishedAt"))
        out.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "aliases": item.get("commonName"),
                "published_at": published_at,
                "published_at_ts": published_at_ts,
                "published_year": published_at[:4] if isinstance(published_at, str) and len(published_at) >= 4 else None,
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
                "aptitude_scores": {
                    "草地": grade_score(item.get("aptitudeTurf")),
                    "泥地": grade_score(item.get("aptitudeDirt")),
                    "短距离": grade_score(item.get("aptitudeShort")),
                    "英里": grade_score(item.get("aptitudeMile")),
                    "中距离": grade_score(item.get("aptitudeMiddle")),
                    "长距离": grade_score(item.get("aptitudeLong")),
                    "逃": grade_score(item.get("aptitudeRunner")),
                    "先": grade_score(item.get("aptitudeLeader")),
                    "差": grade_score(item.get("aptitudeBetweener")),
                    "追": grade_score(item.get("aptitudeChaser")),
                },
            }
        )
    out.sort(key=lambda x: x["published_at_ts"])
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


def build_metric_bundle(index_by_slug: dict[str, dict[str, Any]]) -> dict[str, Any]:
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


def build_best_aptitudes(character_cards_raw: Any) -> tuple[dict[str, str | None], dict[str, str | None], list[str], list[str]]:
    distance_scores = {key: 0 for key, _, _ in DISTANCE_FIELDS}
    style_scores = {key: 0 for key, _, _ in STYLE_FIELDS}

    if isinstance(character_cards_raw, list):
        for item in character_cards_raw:
            if not isinstance(item, dict):
                continue
            for key, _label, field in DISTANCE_FIELDS:
                distance_scores[key] = max(distance_scores[key], grade_score(item.get(field)))
            for key, _label, field in STYLE_FIELDS:
                style_scores[key] = max(style_scores[key], grade_score(item.get(field)))

    distance_profile = {key: aptitude_grade(score) for key, score in distance_scores.items()}
    style_profile = {key: aptitude_grade(score) for key, score in style_scores.items()}
    distance_tags = [key for key, score in distance_scores.items() if score >= 6]
    style_tags = [key for key, score in style_scores.items() if score >= 6]
    return distance_profile, style_profile, distance_tags, style_tags


def infer_personality(profile: dict[str, Any], description: str) -> tuple[list[str], str, str]:
    search_text = " ".join(
        compact_text(value)
        for value in [
            description,
            profile.get("good"),
            profile.get("bad"),
            profile.get("ear"),
            profile.get("tail"),
            profile.get("family"),
        ]
        if value
    )
    tags = []
    for label, patterns in PERSONALITY_RULES:
        if any(pattern in search_text for pattern in patterns):
            tags.append(label)
    if not tags:
        tags.append("经典竞马")

    theme_group = "经典竞马"
    for label, group_tags in THEME_GROUPS:
        if any(tag in tags for tag in group_tags):
            theme_group = label
            break

    good = compact_text(profile.get("good"))
    if good:
        persona_line = f"{theme_group} · 擅长{good}"
    else:
        persona_line = f"{theme_group} · {' / '.join(tags[:2])}"
    return tags[:4], theme_group, persona_line


def support_command_tags(cards: list[dict[str, Any]]) -> list[str]:
    tags = {str(card.get("command_label") or "其他") for card in cards}
    return sorted(tags)


def build_timeline_groups(character_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for card in character_cards:
        year = str(card.get("published_year") or "未标注")
        grouped.setdefault(year, []).append(card)

    groups = []
    for year, items in sorted(grouped.items(), key=lambda item: item[0]):
        groups.append({"label": year, "items": items})
    return groups


def build_search_blob(summary: dict[str, Any], detail: dict[str, Any]) -> str:
    parts = [
        summary.get("name_zh"),
        summary.get("name_ja"),
        summary.get("name_en"),
        summary.get("slug"),
        summary.get("theme_group"),
        " ".join(summary.get("personality_tags", [])),
        detail.get("description"),
    ]
    for section in detail.get("profile_sections", []):
        for item in section.get("items", []):
            parts.append(item.get("value"))
    return " ".join(str(part).lower() for part in parts if part)


def build_filter_meta(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    personality_tags = sorted({tag for item in summaries for tag in item.get("personality_tags", [])})
    theme_groups = sorted({str(item.get("theme_group") or "") for item in summaries if item.get("theme_group")})
    distance_tags = sorted({tag for item in summaries for tag in item.get("filters", {}).get("distance_tags", [])})
    style_tags = sorted({tag for item in summaries for tag in item.get("filters", {}).get("style_tags", [])})
    support_tags = sorted({tag for item in summaries for tag in item.get("filters", {}).get("support_command_tags", [])})
    birthday_months = sorted(
        {int(item["filters"]["birthday_month"]) for item in summaries if isinstance(item.get("filters", {}).get("birthday_month"), int)}
    )
    return {
        "theme_groups": theme_groups,
        "personality_tags": personality_tags,
        "distance_tags": distance_tags,
        "style_tags": style_tags,
        "support_command_tags": support_tags,
        "birthday_months": birthday_months,
        "numeric_ranges": {
            "height_cm": range_meta(summaries, "height_cm"),
            "bust_cm": range_meta(summaries, "bust_cm"),
            "waist_cm": range_meta(summaries, "waist_cm"),
            "hip_cm": range_meta(summaries, "hip_cm"),
            "support_cards": range_meta(summaries, "support_cards", source="counts"),
            "character_cards": range_meta(summaries, "character_cards", source="counts"),
            "relations": range_meta(summaries, "relations", source="counts"),
        },
    }


def range_meta(items: list[dict[str, Any]], key: str, *, source: str = "metrics") -> dict[str, int | None]:
    values: list[int] = []
    for item in items:
        if source == "metrics":
            value = item.get("metrics", {}).get(key) if isinstance(item.get("metrics"), dict) else None
        elif source == "counts":
            value = item.get("counts", {}).get(key) if isinstance(item.get("counts"), dict) else None
        else:
            value = item.get("filters", {}).get(key) if isinstance(item.get("filters"), dict) else None
        number = safe_number(value)
        if number is not None:
            values.append(number)
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def compute_content_density(summary: dict[str, Any]) -> int:
    counts = summary.get("counts", {})
    metrics = summary.get("metrics", {}) or {}
    score = (
        int(counts.get("support_cards", 0)) * 2
        + int(counts.get("character_cards", 0)) * 4
        + int(counts.get("relations", 0)) * 3
        + (4 if metrics.get("height_cm") is not None else 0)
        + len(summary.get("personality_tags", []))
    )
    return score


def build_fun_rankings(summaries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    enriched = []
    for summary in summaries:
        metrics = summary.get("metrics") or {}
        counts = summary.get("counts") or {}
        latest_outfit_at_ts = int(summary.get("latest_outfit_at_ts") or 0)
        curve_presence = None
        bust = safe_number(metrics.get("bust_cm"))
        waist = safe_number(metrics.get("waist_cm"))
        hip = safe_number(metrics.get("hip_cm"))
        if bust is not None and waist is not None and hip is not None:
            curve_presence = bust + hip - waist
        enriched.append(
            {
                **summary,
                "support_card_count": counts.get("support_cards", 0),
                "character_card_count": counts.get("character_cards", 0),
                "relation_count": counts.get("relations", 0),
                "newest_outfit_at_ts": latest_outfit_at_ts,
                "content_density": compute_content_density(summary),
                "curve_presence": curve_presence,
            }
        )

    return {
        "support_card_count_desc": build_summary_ranking(enriched, "support_card_count", descending=True),
        "character_card_count_desc": build_summary_ranking(enriched, "character_card_count", descending=True),
        "relation_count_desc": build_summary_ranking(enriched, "relation_count", descending=True),
        "newest_outfit_desc": build_summary_ranking(enriched, "newest_outfit_at_ts", descending=True),
        "content_density_desc": build_summary_ranking(enriched, "content_density", descending=True),
        "curve_presence_desc": build_summary_ranking(enriched, "curve_presence", descending=True),
    }


def build_summary_ranking(items: list[dict[str, Any]], key: str, *, descending: bool) -> list[dict[str, Any]]:
    filtered = [item for item in items if isinstance(item.get(key), (int, float))]
    ordered = sorted(filtered, key=lambda item: float(item[key]), reverse=descending)
    ranking = []
    for index, item in enumerate(ordered, start=1):
        ranking.append(
            {
                "rank": index,
                "slug": item.get("slug"),
                "name_zh": item.get("name_zh"),
                "name_ja": item.get("name_ja"),
                "name_en": item.get("name_en"),
                "value": item.get(key),
                "theme_group": item.get("theme_group"),
                "personality_tags": item.get("personality_tags"),
            }
        )
    return ranking


def build_overview(summaries: list[dict[str, Any]], rankings: dict[str, Any]) -> dict[str, Any]:
    featured = sorted(
        summaries,
        key=lambda item: (
            compute_content_density(item),
            int(item.get("latest_outfit_at_ts") or 0),
        ),
        reverse=True,
    )
    latest_outfits = sorted(summaries, key=lambda item: int(item.get("latest_outfit_at_ts") or 0), reverse=True)
    ranking_previews = {key: values[:5] for key, values in rankings.items()}
    return {
        "featured": [strip_internal_summary(item) for item in featured[:8]],
        "latest_outfits": [strip_internal_summary(item) for item in latest_outfits[:6]],
        "ranking_previews": ranking_previews,
    }


def build_stats(details: list[dict[str, Any]], metric_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_characters": len(details),
        "with_images": sum(1 for item in details if item.get("image", {}).get("ready")),
        "with_metrics": len(metric_summary.get("items", [])),
        "support_card_total": sum(item.get("counts", {}).get("support_cards", 0) for item in details),
        "character_card_total": sum(item.get("counts", {}).get("character_cards", 0) for item in details),
        "relation_total": sum(item.get("counts", {}).get("relations", 0) for item in details),
    }


def build_similarity_map(summaries: list[dict[str, Any]]) -> dict[str, list[str]]:
    score_map: dict[str, list[tuple[float, str]]] = {}
    for item in summaries:
        candidates = []
        for other in summaries:
            if item["slug"] == other["slug"]:
                continue
            score = 0.0
            if item.get("theme_group") == other.get("theme_group"):
                score += 4
            score += len(set(item.get("personality_tags", [])) & set(other.get("personality_tags", []))) * 2
            score += len(set(item.get("filters", {}).get("distance_tags", [])) & set(other.get("filters", {}).get("distance_tags", []))) * 1.5
            score += len(set(item.get("filters", {}).get("style_tags", [])) & set(other.get("filters", {}).get("style_tags", []))) * 1.5
            item_height = safe_number(item.get("metrics", {}).get("height_cm") if isinstance(item.get("metrics"), dict) else None)
            other_height = safe_number(other.get("metrics", {}).get("height_cm") if isinstance(other.get("metrics"), dict) else None)
            if item_height is not None and other_height is not None:
                diff = abs(item_height - other_height)
                if diff <= 2:
                    score += 1.6
                elif diff <= 5:
                    score += 0.8
            score += max(0, 2 - abs(item.get("counts", {}).get("character_cards", 0) - other.get("counts", {}).get("character_cards", 0)) * 0.5)
            if score > 0:
                candidates.append((score, other["slug"]))
        candidates.sort(key=lambda pair: (-pair[0], pair[1]))
        score_map[item["slug"]] = [slug for _score, slug in candidates[:4]]
    return score_map


def build_relation_payload(details: list[dict[str, Any]], summary_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    outgoing: dict[str, set[str]] = {}
    incoming: dict[str, set[str]] = {}
    for detail in details:
        slug = detail["slug"]
        outgoing.setdefault(slug, set())
        for relation in detail.get("relations", []):
            target = relation["slug"]
            outgoing[slug].add(target)
            incoming.setdefault(target, set()).add(slug)
            edges.append({"source": slug, "target": target, "kind": "comic"})

    nodes = [
        {
            "slug": item["slug"],
            "name": item.get("name_zh") or item.get("name_ja") or item["slug"],
            "theme": item.get("theme"),
            "theme_group": item.get("theme_group"),
        }
        for item in details
    ]

    for detail in details:
        slug = detail["slug"]
        neighbors = sorted(outgoing.get(slug, set()) | incoming.get(slug, set()))
        graph_nodes = [
            {
                "slug": slug,
                "name": detail.get("name_zh") or detail.get("name_ja") or slug,
                "x": 0.5,
                "y": 0.5,
                "size": 1.2,
                "role": "center",
                "theme": detail.get("theme"),
            }
        ]
        graph_edges = []
        radius = 0.34
        for index, neighbor_slug in enumerate(neighbors[:8]):
            angle = (math.tau * index) / max(1, len(neighbors[:8]))
            neighbor_summary = summary_lookup.get(neighbor_slug)
            if not neighbor_summary:
                continue
            graph_nodes.append(
                {
                    "slug": neighbor_slug,
                    "name": neighbor_summary.get("name_zh") or neighbor_summary.get("name_ja") or neighbor_slug,
                    "x": round(0.5 + math.cos(angle) * radius, 4),
                    "y": round(0.5 + math.sin(angle) * radius, 4),
                    "size": 0.88,
                    "role": "relation",
                    "theme": neighbor_summary.get("theme"),
                }
            )
            edge_kind = "outgoing"
            if neighbor_slug in outgoing.get(slug, set()) and neighbor_slug in incoming.get(slug, set()):
                edge_kind = "both"
            elif neighbor_slug in incoming.get(slug, set()):
                edge_kind = "incoming"
            graph_edges.append({"source": slug, "target": neighbor_slug, "kind": edge_kind})
        detail["relation_graph"] = {"nodes": graph_nodes, "edges": graph_edges}

    return {"nodes": nodes, "edges": edges}


def strip_internal_summary(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload.pop("search_blob", None)
    payload.pop("latest_outfit_at_ts", None)
    return payload


def quality_issue(slug: str, name: str, severity: int, messages: list[str]) -> dict[str, Any]:
    return {"slug": slug, "name": name, "severity": severity, "issues": messages}


def build_quality_report(
    *,
    details: list[dict[str, Any]],
    summary_lookup: dict[str, dict[str, Any]],
    generated_at_utc: str,
    raw_updated_at_utc: str | None,
) -> dict[str, Any]:
    missing_name_zh = []
    image_missing = []
    image_invalid = []
    description_missing = []
    sparse_content = []
    issues = []

    translated_name_map: dict[str, list[str]] = {}
    for detail in details:
        slug = detail["slug"]
        name = detail.get("name_zh") or detail.get("name_ja") or slug
        severity = 0
        messages: list[str] = []
        name_zh = detail.get("name_zh")
        if isinstance(name_zh, str) and name_zh.strip():
            translated_name_map.setdefault(name_zh.strip(), []).append(slug)
        else:
            missing_name_zh.append(slug)
            severity += 2
            messages.append("缺少中文译名")

        if not detail.get("description"):
            description_missing.append(slug)
            severity += 1
            messages.append("缺少角色简介")

        image = detail.get("image", {})
        image_path = image.get("path") if isinstance(image, dict) else None
        if not image.get("ready"):
            image_missing.append(slug)
            severity += 2
            messages.append("缺少立绘")
        elif not isinstance(image_path, str) or not image_path.startswith("uma/") or not (ROOT / image_path).exists():
            image_invalid.append(slug)
            severity += 2
            messages.append("立绘路径异常")

        counts = detail.get("counts", {})
        if (
            counts.get("support_cards", 0) == 0
            and counts.get("character_cards", 0) <= 1
            and counts.get("relations", 0) == 0
        ):
            sparse_content.append(slug)
            severity += 1
            messages.append("内容较薄，建议补充联动或支援卡数据")

        if messages:
            issues.append(quality_issue(slug, str(name), severity, messages))

    duplicate_groups = [
        {"name_zh": key, "slugs": sorted(values)}
        for key, values in translated_name_map.items()
        if len(values) > 1
    ]

    for group in duplicate_groups:
        for slug in group["slugs"]:
            name = summary_lookup.get(slug, {}).get("name_zh") or summary_lookup.get(slug, {}).get("name_ja") or slug
            issues.append(quality_issue(slug, str(name), 3, [f"中文译名冲突：{group['name_zh']}"]))

    issues.sort(key=lambda item: (-item["severity"], item["slug"]))
    return {
        "generated_at_utc": generated_at_utc,
        "raw_updated_at_utc": raw_updated_at_utc,
        "summary": {
            "missing_name_zh_count": len(missing_name_zh),
            "duplicate_name_zh_group_count": len(duplicate_groups),
            "image_missing_count": len(image_missing),
            "image_invalid_count": len(image_invalid),
            "description_missing_count": len(description_missing),
            "sparse_content_count": len(sparse_content),
            "issue_character_count": len({item["slug"] for item in issues}),
        },
        "duplicate_name_zh_groups": duplicate_groups[:20],
        "issues": issues[:80],
        "stale_prompt": None,
    }


def ranking_meta_payload() -> list[dict[str, Any]]:
    return [{"key": key, **value} for key, value in RANKING_META.items()]


def build_characters_from_raw() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        return {
            "manifest": empty_manifest(),
            "summaries": [],
            "details": {},
            "rankings": {"meta": ranking_meta_payload(), "rankings": {}},
            "search_index": [],
            "quality_report": empty_quality_report(),
            "relations": {"nodes": [], "edges": []},
        }

    index_payload = load_json(INDEX_PATH)
    index_items = index_payload.get("uma_list", []) if isinstance(index_payload, dict) else []
    index_items = [item for item in index_items if isinstance(item, dict)]
    index_by_slug = build_index_lookup(load_metric_index(INDEX_PATH))
    metric_bundle = build_metric_bundle(index_by_slug)
    metrics_by_slug = metric_bundle["by_slug"]

    raw_records = []
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

        description = compact_text(profile.get("description"))
        support_cards = serialize_support_cards(data.get("supportCards"))
        support_groups = group_support_cards(support_cards)
        character_cards = serialize_character_cards(data.get("characterCards"))
        relations = serialize_relations(data.get("comics"))
        distance_profile, style_profile, distance_tags, style_tags = build_best_aptitudes(data.get("characterCards"))
        metric = public_metric(metrics_by_slug.get(slug))
        personality_tags, theme_group, persona_line = infer_personality(profile, description)
        latest_outfit_at_ts = max((card["published_at_ts"] for card in character_cards), default=0)
        birthday_month = safe_number(profile.get("birthMonth"))
        filters = {
            "birthday_month": birthday_month,
            "distance_tags": distance_tags,
            "style_tags": style_tags,
            "support_command_tags": support_command_tags(support_cards),
            "theme_group": theme_group,
            "personality_tags": personality_tags,
            "limited": any(card.get("limited") for card in character_cards),
            "height_cm": metric.get("height_cm") if metric else None,
            "bust_cm": metric.get("bust_cm") if metric else None,
            "waist_cm": metric.get("waist_cm") if metric else None,
            "hip_cm": metric.get("hip_cm") if metric else None,
        }
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
            "theme": character_theme(data),
            "tagline": description[:100],
            "counts": {
                "support_cards": len(support_cards),
                "character_cards": len(character_cards),
                "relations": len(relations),
                "main_comics": len(data.get("mainComics") or []),
            },
            "metrics": metric,
            "personality_tags": personality_tags,
            "theme_group": theme_group,
            "persona_line": persona_line,
            "distance_profile": distance_profile,
            "style_profile": style_profile,
            "filters": filters,
            "latest_outfit_at_ts": latest_outfit_at_ts,
            "updated_at_utc": payload.get("fetched_at_utc"),
        }
        detail = {
            **summary,
            "description": description,
            "profile_sections": profile_sections(profile),
            "support_cards": list(reversed(support_cards)),
            "support_groups": support_groups,
            "character_cards": list(reversed(character_cards)),
            "timeline_groups": list(reversed(build_timeline_groups(character_cards))),
            "relations": relations,
            "main_comics": data.get("mainComics") if isinstance(data.get("mainComics"), list) else [],
            "similar_characters": [],
            "relation_graph": {"nodes": [], "edges": []},
        }
        blob = build_search_blob(summary, detail)
        summary["search_blob"] = blob
        detail["search_blob"] = blob
        raw_records.append({"summary": summary, "detail": detail})

    raw_records.sort(
        key=lambda item: str(
            item["summary"].get("name_zh") or item["summary"].get("name_ja") or item["summary"].get("slug")
        )
    )
    summaries = [item["summary"] for item in raw_records]
    details = [item["detail"] for item in raw_records]
    summary_lookup = {item["slug"]: item for item in summaries}
    detail_lookup = {item["slug"]: item for item in details}

    similarity_map = build_similarity_map(summaries)
    for detail in details:
        detail["similar_characters"] = [
            strip_internal_summary(summary_lookup[slug])
            for slug in similarity_map.get(detail["slug"], [])
            if slug in summary_lookup
        ]

    relations_payload = build_relation_payload(details, summary_lookup)
    filter_meta = build_filter_meta(summaries)
    rankings = {**metric_bundle["rankings"], **build_fun_rankings(summaries)}
    overview = build_overview(summaries, rankings)
    stats = build_stats(details, metric_bundle)
    generated_at_utc = now_iso()
    manifest = {
        "generated_at_utc": generated_at_utc,
        "raw_updated_at_utc": index_payload.get("updated_at_utc") if isinstance(index_payload, dict) else None,
        "counts": stats,
        "filter_meta": filter_meta,
        "ranking_keys": [item["key"] for item in ranking_meta_payload()],
        "derived_files": {name: path.name for name, path in DERIVED_PATHS.items()},
        "source_mode": "derived",
        "stale": False,
    }
    quality_report = build_quality_report(
        details=details,
        summary_lookup=summary_lookup,
        generated_at_utc=generated_at_utc,
        raw_updated_at_utc=manifest["raw_updated_at_utc"],
    )
    return {
        "manifest": manifest,
        "stats": stats,
        "overview": overview,
        "ranking_meta": ranking_meta_payload(),
        "summaries": summaries,
        "character_lookup": detail_lookup,
        "rankings": rankings,
        "search_index": [
            {
                "slug": summary["slug"],
                "text": summary["search_blob"],
                "theme_group": summary.get("theme_group"),
                "personality_tags": summary.get("personality_tags"),
                "distance_tags": summary.get("filters", {}).get("distance_tags", []),
                "style_tags": summary.get("filters", {}).get("style_tags", []),
            }
            for summary in summaries
        ],
        "quality_report": quality_report,
        "relations": relations_payload,
    }


def empty_manifest() -> dict[str, Any]:
    return {
        "generated_at_utc": None,
        "raw_updated_at_utc": None,
        "counts": {
            "total_characters": 0,
            "with_images": 0,
            "with_metrics": 0,
            "support_card_total": 0,
            "character_card_total": 0,
            "relation_total": 0,
        },
        "filter_meta": build_filter_meta([]),
        "ranking_keys": [],
        "derived_files": {name: path.name for name, path in DERIVED_PATHS.items()},
        "source_mode": "derived",
        "stale": False,
    }


def empty_quality_report() -> dict[str, Any]:
    return {
        "generated_at_utc": None,
        "raw_updated_at_utc": None,
        "summary": {
            "missing_name_zh_count": 0,
            "duplicate_name_zh_group_count": 0,
            "image_missing_count": 0,
            "image_invalid_count": 0,
            "description_missing_count": 0,
            "sparse_content_count": 0,
            "issue_character_count": 0,
        },
        "duplicate_name_zh_groups": [],
        "issues": [],
        "stale_prompt": None,
    }


def write_site_dataset(output_dir: Path = DATA_DIR) -> dict[str, Any]:
    dataset = build_characters_from_raw()
    write_json(output_dir / MANIFEST_PATH.name, dataset["manifest"])
    write_json(output_dir / SUMMARIES_PATH.name, {"items": dataset["summaries"]})
    write_json(
        output_dir / DETAILS_PATH.name,
        {"items": dataset["character_lookup"]},
    )
    write_json(output_dir / RANKINGS_PATH.name, {"meta": dataset["ranking_meta"], "rankings": dataset["rankings"]})
    write_json(output_dir / SEARCH_INDEX_PATH.name, {"items": dataset["search_index"]})
    write_json(output_dir / QUALITY_REPORT_PATH.name, dataset["quality_report"])
    write_json(output_dir / RELATIONS_PATH.name, dataset["relations"])
    return dataset
def derived_files_exist() -> bool:
    return all(path.exists() for path in DERIVED_PATHS.values())


def latest_raw_mtime_ns() -> int:
    files = [INDEX_PATH]
    files.extend(sorted(UMA_ROOT.glob("*/info/kouryaku_tools.json")))
    latest = 0
    for path in files:
        if path.exists():
            latest = max(latest, path.stat().st_mtime_ns)
    return latest


def recent_raw_updates(after_iso: str | None, limit: int = 8) -> list[dict[str, Any]]:
    if not after_iso:
        return []
    after = parse_iso(after_iso)
    if after is None:
        return []
    updates = []
    for info_path in sorted(UMA_ROOT.glob("*/info/kouryaku_tools.json")):
        try:
            payload = load_json(info_path)
        except Exception:
            continue
        fetched_at = parse_iso(payload.get("fetched_at_utc"))
        if fetched_at is None or fetched_at <= after:
            continue
        updates.append(
            {
                "slug": payload.get("slug"),
                "name_zh": payload.get("name_zh"),
                "name_ja": payload.get("name_ja"),
                "fetched_at_utc": payload.get("fetched_at_utc"),
            }
        )
    updates.sort(key=lambda item: item.get("fetched_at_utc") or "", reverse=True)
    return updates[:limit]


def apply_runtime_flags(dataset: dict[str, Any], *, source_mode: str) -> dict[str, Any]:
    manifest = dataset.get("manifest", empty_manifest())
    quality_report = dataset.get("quality_report", empty_quality_report())
    raw_updated_at = manifest.get("raw_updated_at_utc")
    generated_at = manifest.get("generated_at_utc")
    derived_mtime_ns = MANIFEST_PATH.stat().st_mtime_ns if MANIFEST_PATH.exists() else 0
    stale = source_mode == "derived" and latest_raw_mtime_ns() > derived_mtime_ns
    manifest["source_mode"] = source_mode
    manifest["stale"] = stale
    if stale:
        updates = recent_raw_updates(generated_at)
        quality_report["stale_prompt"] = {
            "title": "派生站点数据已过期",
            "message": "原始资料有更新，但站点派生文件还没重建。建议运行 build_site_bundle。",
            "raw_updated_at_utc": raw_updated_at,
            "generated_at_utc": generated_at,
            "recent_updates": updates,
        }
    else:
        quality_report["stale_prompt"] = None
    dataset["manifest"] = manifest
    dataset["quality_report"] = quality_report
    dataset["updated_at_utc"] = generated_at or raw_updated_at
    dataset["stats"] = manifest.get("counts", {})
    return dataset


def load_derived_dataset() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    summaries_payload = load_json(SUMMARIES_PATH)
    details_payload = load_json(DETAILS_PATH)
    rankings_payload = load_json(RANKINGS_PATH)
    search_index_payload = load_json(SEARCH_INDEX_PATH)
    quality_report = load_json(QUALITY_REPORT_PATH)
    relations_payload = load_json(RELATIONS_PATH)

    summaries = summaries_payload.get("items", [])
    detail_lookup = details_payload.get("items", {})
    overview = build_overview(summaries, rankings_payload.get("rankings", {}))
    dataset = {
        "manifest": manifest,
        "stats": manifest.get("counts", {}),
        "overview": overview,
        "ranking_meta": rankings_payload.get("meta", ranking_meta_payload()),
        "summaries": summaries,
        "character_lookup": detail_lookup,
        "rankings": rankings_payload.get("rankings", {}),
        "search_index": search_index_payload.get("items", []),
        "quality_report": quality_report,
        "relations": relations_payload,
    }
    return apply_runtime_flags(dataset, source_mode="derived")


def build_runtime_dataset() -> dict[str, Any]:
    dataset = build_characters_from_raw()
    return apply_runtime_flags(dataset, source_mode="runtime_fallback")


def parse_list_filter(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def sort_summaries(items: list[dict[str, Any]], sort_key: str) -> list[dict[str, Any]]:
    if sort_key == "name_asc":
        return sorted(items, key=lambda item: str(item.get("name_zh") or item.get("name_ja") or item.get("slug")))
    if sort_key == "name_desc":
        return sorted(items, key=lambda item: str(item.get("name_zh") or item.get("name_ja") or item.get("slug")), reverse=True)
    if sort_key == "height_cm_desc":
        return sorted(items, key=lambda item: safe_number(item.get("metrics", {}).get("height_cm")) or -1, reverse=True)
    if sort_key == "height_cm_asc":
        return sorted(items, key=lambda item: safe_number(item.get("metrics", {}).get("height_cm")) or 10**9)
    if sort_key == "newest_outfit_desc":
        return sorted(items, key=lambda item: int(item.get("latest_outfit_at_ts") or 0), reverse=True)
    if sort_key == "support_card_count_desc":
        return sorted(items, key=lambda item: int(item.get("counts", {}).get("support_cards", 0)), reverse=True)
    if sort_key == "character_card_count_desc":
        return sorted(items, key=lambda item: int(item.get("counts", {}).get("character_cards", 0)), reverse=True)
    if sort_key == "relation_count_desc":
        return sorted(items, key=lambda item: int(item.get("counts", {}).get("relations", 0)), reverse=True)
    if sort_key == "content_density_desc":
        return sorted(items, key=compute_content_density, reverse=True)
    return items


def filter_summaries(dataset: dict[str, Any], query: dict[str, str]) -> list[dict[str, Any]]:
    search = query.get("query", "").strip().lower()
    birthday_months = {int(item) for item in parse_list_filter(query.get("birthday_month")) if item.isdigit()}
    distance_tags = set(parse_list_filter(query.get("distance")))
    style_tags = set(parse_list_filter(query.get("style")))
    theme_groups = set(parse_list_filter(query.get("theme_group")))
    personality_tags = set(parse_list_filter(query.get("personality")))
    support_command_tags = set(parse_list_filter(query.get("support_command")))
    limited_only = query.get("limited") == "1"
    min_height = safe_number(query.get("min_height"))
    max_height = safe_number(query.get("max_height"))
    min_bust = safe_number(query.get("min_bust"))
    max_bust = safe_number(query.get("max_bust"))
    min_support_cards = safe_number(query.get("min_support_cards"))
    min_character_cards = safe_number(query.get("min_character_cards"))
    min_relations = safe_number(query.get("min_relations"))
    sort_key = query.get("sort", "name_asc")

    filtered = []
    for item in dataset.get("summaries", []):
        filters = item.get("filters", {})
        metrics = item.get("metrics") or {}
        counts = item.get("counts") or {}
        if search and search not in str(item.get("search_blob", "")):
            continue
        if birthday_months and filters.get("birthday_month") not in birthday_months:
            continue
        if distance_tags and not distance_tags.intersection(set(filters.get("distance_tags", []))):
            continue
        if style_tags and not style_tags.intersection(set(filters.get("style_tags", []))):
            continue
        if theme_groups and str(item.get("theme_group") or "") not in theme_groups:
            continue
        if personality_tags and not personality_tags.intersection(set(item.get("personality_tags", []))):
            continue
        if support_command_tags and not support_command_tags.intersection(set(filters.get("support_command_tags", []))):
            continue
        if limited_only and not filters.get("limited"):
            continue
        height = safe_number(metrics.get("height_cm"))
        bust = safe_number(metrics.get("bust_cm"))
        if min_height is not None and (height is None or height < min_height):
            continue
        if max_height is not None and (height is None or height > max_height):
            continue
        if min_bust is not None and (bust is None or bust < min_bust):
            continue
        if max_bust is not None and (bust is None or bust > max_bust):
            continue
        if min_support_cards is not None and counts.get("support_cards", 0) < min_support_cards:
            continue
        if min_character_cards is not None and counts.get("character_cards", 0) < min_character_cards:
            continue
        if min_relations is not None and counts.get("relations", 0) < min_relations:
            continue
        filtered.append(item)

    return sort_summaries(filtered, sort_key)


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
        files = list(DERIVED_PATHS.values())
        files.extend([INDEX_PATH])
        signature = []
        for path in files:
            if path.exists():
                signature.append((path.as_posix(), path.stat().st_mtime_ns))
        return tuple(signature)

    def get(self) -> dict[str, Any]:
        signature = self._signature()
        if self._cache is None or self._cache.signature != signature:
            if derived_files_exist():
                payload = load_derived_dataset()
            else:
                payload = build_runtime_dataset()
            self._cache = CachedDataset(signature=signature, payload=payload)
        return self._cache.payload


STORE = SiteDataStore()
