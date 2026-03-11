import { startTransition, useDeferredValue, useState } from "react";

import type { CharacterSummary } from "../types/api";
import { characterName } from "../utils/format";

type SearchPickerProps = {
  items: CharacterSummary[];
  excludeSlugs?: string[];
  onPick: (slug: string) => void;
};

export function SearchPicker({ items, excludeSlugs = [], onPick }: SearchPickerProps) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim().toLowerCase());
  const excluded = new Set(excludeSlugs);
  const results = items
    .filter((item) => !excluded.has(item.slug))
    .filter((item) => {
      if (!deferredQuery) {
        return true;
      }
      const haystack = `${item.name_zh || ""} ${item.name_ja || ""} ${item.name_en || ""} ${item.slug}`.toLowerCase();
      return haystack.includes(deferredQuery);
    })
    .slice(0, 6);

  return (
    <div className="search-picker">
      <input
        className="search-picker__input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="搜索中文、日文、英文名"
      />
      <div className="search-picker__list">
        {results.map((item) => (
          <button
            key={item.slug}
            className="search-picker__option"
            type="button"
            onClick={() => {
              onPick(item.slug);
              startTransition(() => setQuery(""));
            }}
          >
            <span>{characterName(item)}</span>
            <small>{item.name_ja || item.name_en}</small>
          </button>
        ))}
      </div>
    </div>
  );
}
