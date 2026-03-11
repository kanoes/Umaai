import { startTransition } from "react";
import { useSearchParams } from "react-router-dom";

import { fetchJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { SearchPicker } from "../components/SearchPicker";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharacterDetail, CharactersResponse, CompareResponse } from "../types/api";
import { characterName, profileValue } from "../utils/format";

function nextSearchParams(slugs: string[]) {
  const params = new URLSearchParams();
  if (slugs.length > 0) {
    params.set("slugs", slugs.join(","));
  }
  return params;
}

export function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedSlugs = (searchParams.get("slugs") || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .slice(0, 3);

  const characterQuery = useRemoteData<CharactersResponse>(() => fetchJson("/api/site/characters?limit=200"), []);
  const compareQuery = useRemoteData<CompareResponse>(
    () => fetchJson(`/api/site/compare?slugs=${encodeURIComponent(selectedSlugs.join(","))}`),
    [selectedSlugs.join(",")]
  );

  const selected = compareQuery.data?.items ?? [];
  const compareRows: Array<{ label: string; resolve: (item: CharacterDetail) => string | number }> = [
    { label: "身高", resolve: (item) => item.metrics?.height_cm ?? "-" },
    { label: "胸围", resolve: (item) => item.metrics?.bust_cm ?? "-" },
    { label: "腰围", resolve: (item) => item.metrics?.waist_cm ?? "-" },
    { label: "臀围", resolve: (item) => item.metrics?.hip_cm ?? "-" },
    { label: "腰臀比", resolve: (item) => item.metrics?.waist_to_hip ?? "-" },
    { label: "生日", resolve: (item) => String(profileValue(item, "birthday")) },
    { label: "擅长", resolve: (item) => String(profileValue(item, "good")) },
    { label: "苦手", resolve: (item) => String(profileValue(item, "bad")) },
  ];

  return (
    <div className="page page-compare">
      <section className="page-header">
        <p className="eyebrow">Compare</p>
        <h1>对比不只看三围，还能看衣装量、关系链和角色设定。</h1>
        <p>先选角色，再横向看她们的资料强度与内容密度。</p>
      </section>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Picker</p>
            <h2>加入对比角色</h2>
          </div>
        </div>
        <SearchPicker
          items={characterQuery.data?.items ?? []}
          excludeSlugs={selectedSlugs}
          onPick={(slug) => {
            const merged = [...selectedSlugs, slug].slice(0, 3);
            startTransition(() => setSearchParams(nextSearchParams(merged)));
          }}
        />
        <div className="compare-selected">
          {selectedSlugs.map((slug) => (
            <button
              key={slug}
              className="compare-selected__chip"
              type="button"
              onClick={() =>
                startTransition(() =>
                  setSearchParams(nextSearchParams(selectedSlugs.filter((item) => item !== slug)))
                )
              }
            >
              {slug} ×
            </button>
          ))}
        </div>
      </GlowPanel>

      {selected.length === 0 ? (
        <GlowPanel>
          <p className="empty-state">还没有选角色。上面输入名字即可开始。</p>
        </GlowPanel>
      ) : (
        <>
          <GlowPanel>
            <div className="compare-grid">
              {selected.map((item) => (
                <article key={item.slug} className="compare-card">
                  <span className="compare-card__eyebrow">{item.name_ja || item.name_en}</span>
                  <h2>{characterName(item)}</h2>
                  <p>{item.description}</p>
                  <div className="compare-card__stats">
                    <span>身高 {item.metrics?.height_cm ?? "-"}</span>
                    <span>衣装 {item.counts.character_cards}</span>
                    <span>支援卡 {item.counts.support_cards}</span>
                    <span>关系 {item.counts.relations}</span>
                  </div>
                </article>
              ))}
            </div>
          </GlowPanel>

          <GlowPanel>
            <div className="section-head">
              <div>
                <p className="eyebrow">Metrics</p>
                <h2>核心对比</h2>
              </div>
            </div>
            <div className="compare-table">
              {compareRows.map((row) => (
                <div key={row.label} className="compare-table__row">
                  <div className="compare-table__label">{row.label}</div>
                  {selected.map((item) => (
                    <div key={`${row.label}-${item.slug}`} className="compare-table__value">
                      {String(row.resolve(item))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </GlowPanel>
        </>
      )}
    </div>
  );
}
