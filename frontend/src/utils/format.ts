import type { CharacterDetail, CharacterSummary, ProfileFact } from "../types/api";

export function characterName(character: Pick<CharacterSummary, "name_zh" | "name_ja" | "name_en" | "slug">) {
  return character.name_zh || character.name_ja || character.name_en || character.slug;
}

export function metricValue(value: number | string | null | undefined, unit = "") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `${value}${unit}`;
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function profileValue(detail: CharacterDetail, key: string) {
  for (const section of detail.profile_sections) {
    const item = section.items.find((fact) => fact.key === key);
    if (item) {
      return item.value;
    }
  }
  return "-";
}

export function factValue(fact: ProfileFact | undefined) {
  return fact ? fact.value : "-";
}
