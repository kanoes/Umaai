import { useDeferredValue } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { fetchJson } from "../api/client";
import { CharacterCard } from "../components/CharacterCard";
import { GlowPanel } from "../components/GlowPanel";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharactersResponse, FilterMeta, OverviewResponse } from "../types/api";
import { characterName, metricValue } from "../utils/format";

const PREVIEW_LABELS: Record<string, string> = {
  waist_to_hip_asc: "腰臀比",
  waist_to_bust_asc: "腰乳比",
  bust_cm_desc: "胸围",
  hip_cm_desc: "臀围",
  waist_cm_asc: "腰围",
  height_cm_desc: "身高",
  support_card_count_desc: "支援卡量",
  character_card_count_desc: "衣装量",
  relation_count_desc: "关系密度",
  newest_outfit_desc: "最近上新",
  content_density_desc: "内容密度",
  curve_presence_desc: "曲线存在感",
};

function buildCharactersUrl(searchParams: URLSearchParams) {
  const params = new URLSearchParams(searchParams);
  params.set("limit", "200");
  return `/api/site/characters?${params.toString()}`;
}

function toggleCsvValue(searchParams: URLSearchParams, key: string, value: string) {
  const current = (searchParams.get(key) || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const next = current.includes(value) ? current.filter((item) => item !== value) : [...current, value];
  if (next.length === 0) {
    searchParams.delete(key);
  } else {
    searchParams.set(key, next.join(","));
  }
}

type FilterChipGroupProps = {
  title: string;
  values: string[];
  selected: string[];
  onToggle: (value: string) => void;
  labels?: Record<string, string>;
};

function FilterChipGroup({ title, values, selected, onToggle, labels = {} }: FilterChipGroupProps) {
  if (values.length === 0) {
    return null;
  }
  return (
    <div className="filter-block">
      <span className="filter-block__title">{title}</span>
      <div className="filter-chip-row">
        {values.map((value) => {
          const active = selected.includes(value);
          return (
            <button
              key={value}
              className={`filter-chip ${active ? "active" : ""}`.trim()}
              type="button"
              onClick={() => onToggle(value)}
            >
              {labels[value] || value}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function rangePlaceholder(meta: FilterMeta, key: string, mode: "min" | "max") {
  const range = meta.numeric_ranges[key];
  if (!range) {
    return mode === "min" ? "最小值" : "最大值";
  }
  return mode === "min" ? `≥ ${range.min ?? "-"}` : `≤ ${range.max ?? "-"}`;
}

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const deferredQueryString = useDeferredValue(searchParams.toString());
  const overviewQuery = useRemoteData<OverviewResponse>(() => fetchJson("/api/site/overview"), []);
  const charactersQuery = useRemoteData<CharactersResponse>(
    () => fetchJson(buildCharactersUrl(new URLSearchParams(deferredQueryString))),
    [deferredQueryString]
  );

  const selectedDistances = (searchParams.get("distance") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const selectedStyles = (searchParams.get("style") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const selectedThemeGroups = (searchParams.get("theme_group") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const selectedSupportCommands = (searchParams.get("support_command") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const filters = overviewQuery.data?.filters;
  const manifest = overviewQuery.data?.manifest;
  const characters = charactersQuery.data?.items ?? [];

  return (
    <div className="page page-home">
      <section className="hero-banner">
        <div className="hero-banner__copy">
          <p className="eyebrow">Public Site</p>
          <h1>把角色发现页真正做成可以筛、可以逛、可以延展的资料站。</h1>
          <p className="hero-banner__text">
            现在公开站已经和后台拆开。发现页支持 URL 同步筛选，底层数据也切成了标准化派生文件，后续加专题或新功能不会再卡在原始控制台结构上。
          </p>
          <div className="hero-banner__actions">
            <Link className="primary-link" to="/rankings">
              查看排行 2.0
            </Link>
            <Link className="secondary-link" to="/compare">
              角色对比
            </Link>
          </div>
        </div>
        <GlowPanel className="hero-banner__stats">
          <div className="stat-grid">
            <article>
              <span>角色总数</span>
              <strong>{overviewQuery.data?.stats.total_characters ?? "-"}</strong>
            </article>
            <article>
              <span>派生模式</span>
              <strong>{manifest?.source_mode === "derived" ? "Derived" : "Runtime"}</strong>
            </article>
            <article>
              <span>支援卡总数</span>
              <strong>{overviewQuery.data?.stats.support_card_total ?? "-"}</strong>
            </article>
            <article>
              <span>派生状态</span>
              <strong>{manifest?.stale ? "待重建" : "最新"}</strong>
            </article>
          </div>
        </GlowPanel>
      </section>

      <section className="content-grid">
        <GlowPanel className="content-grid__main">
          <div className="section-head">
            <div>
              <p className="eyebrow">Featured</p>
              <h2>先看最有内容密度的一批角色</h2>
            </div>
          </div>
          <div className="character-grid featured">
            {overviewQuery.data?.overview.featured.map((character) => (
              <CharacterCard key={character.slug} character={character} mode="compact" />
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="content-grid__side">
          <div className="section-head">
            <div>
              <p className="eyebrow">Ranking Preview</p>
              <h2>重点专题</h2>
            </div>
            <Link className="inline-link" to="/rankings">
              全部排行
            </Link>
          </div>
          <div className="ranking-preview">
            {Object.entries(overviewQuery.data?.overview.ranking_previews ?? {})
              .slice(0, 4)
              .map(([key, items]) => (
                <article key={key} className="ranking-preview__block">
                  <header>
                    <h3>{PREVIEW_LABELS[key] || key}</h3>
                  </header>
                  <div className="ranking-preview__list">
                    {items.slice(0, 3).map((item) => (
                      <div key={item.slug} className="ranking-preview__item">
                        <span>#{item.rank}</span>
                        <strong>{item.name_zh || item.name_ja || item.slug}</strong>
                        <small>{metricValue(item.value)}</small>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
          </div>
        </GlowPanel>
      </section>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Discovery</p>
            <h2>高级筛选</h2>
          </div>
          <button
            className="secondary-link"
            type="button"
            onClick={() => {
              setSearchParams(new URLSearchParams());
            }}
          >
            清空筛选
          </button>
        </div>

        <div className="filter-toolbar">
          <input
            className="site-search"
            value={searchParams.get("query") || ""}
            onChange={(event) => {
              const next = new URLSearchParams(searchParams);
              if (event.target.value.trim()) {
                next.set("query", event.target.value);
              } else {
                next.delete("query");
              }
              setSearchParams(next);
            }}
            placeholder="搜索角色名、译名、英文名、人格标签"
          />

          <select
            className="site-select"
            value={searchParams.get("sort") || "name_asc"}
            onChange={(event) => {
              const next = new URLSearchParams(searchParams);
              next.set("sort", event.target.value);
              setSearchParams(next);
            }}
          >
            <option value="name_asc">按名称</option>
            <option value="newest_outfit_desc">按最近衣装</option>
            <option value="content_density_desc">按内容密度</option>
            <option value="support_card_count_desc">按支援卡数量</option>
            <option value="character_card_count_desc">按衣装数量</option>
            <option value="relation_count_desc">按关系数量</option>
            <option value="height_cm_desc">按身高从高到低</option>
          </select>

          <select
            className="site-select"
            value={searchParams.get("personality") || ""}
            onChange={(event) => {
              const next = new URLSearchParams(searchParams);
              if (event.target.value) {
                next.set("personality", event.target.value);
              } else {
                next.delete("personality");
              }
              setSearchParams(next);
            }}
          >
            <option value="">人格标签</option>
            {(filters?.personality_tags || []).map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>

          <label className="toggle-check">
            <input
              checked={searchParams.get("limited") === "1"}
              type="checkbox"
              onChange={(event) => {
                const next = new URLSearchParams(searchParams);
                if (event.target.checked) {
                  next.set("limited", "1");
                } else {
                  next.delete("limited");
                }
                setSearchParams(next);
              }}
            />
            <span>只看有限定衣装</span>
          </label>
        </div>

        <div className="filter-layout">
          <div className="filter-column">
            <FilterChipGroup
              title="距离适性"
              values={filters?.distance_tags || []}
              selected={selectedDistances}
              labels={{ short: "短距离", mile: "英里", middle: "中距离", long: "长距离" }}
              onToggle={(value) => {
                const next = new URLSearchParams(searchParams);
                toggleCsvValue(next, "distance", value);
                setSearchParams(next);
              }}
            />

            <FilterChipGroup
              title="跑法适性"
              values={filters?.style_tags || []}
              selected={selectedStyles}
              labels={{ runner: "逃", leader: "先", betweener: "差", chaser: "追" }}
              onToggle={(value) => {
                const next = new URLSearchParams(searchParams);
                toggleCsvValue(next, "style", value);
                setSearchParams(next);
              }}
            />
          </div>

          <div className="filter-column">
            <FilterChipGroup
              title="主题分组"
              values={filters?.theme_groups || []}
              selected={selectedThemeGroups}
              onToggle={(value) => {
                const next = new URLSearchParams(searchParams);
                toggleCsvValue(next, "theme_group", value);
                setSearchParams(next);
              }}
            />

            <FilterChipGroup
              title="支援卡类型"
              values={filters?.support_command_tags || []}
              selected={selectedSupportCommands}
              onToggle={(value) => {
                const next = new URLSearchParams(searchParams);
                toggleCsvValue(next, "support_command", value);
                setSearchParams(next);
              }}
            />
          </div>

          <div className="filter-column">
            <div className="filter-block">
              <span className="filter-block__title">生日月份</span>
              <select
                className="site-select wide"
                value={searchParams.get("birthday_month") || ""}
                onChange={(event) => {
                  const next = new URLSearchParams(searchParams);
                  if (event.target.value) {
                    next.set("birthday_month", event.target.value);
                  } else {
                    next.delete("birthday_month");
                  }
                  setSearchParams(next);
                }}
              >
                <option value="">不限月份</option>
                {(filters?.birthday_months || []).map((month) => (
                  <option key={month} value={String(month)}>
                    {month} 月
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-block">
              <span className="filter-block__title">数值阈值</span>
              <div className="filter-range-grid">
                <input
                  className="site-input"
                  inputMode="numeric"
                  placeholder={filters ? rangePlaceholder(filters, "height_cm", "min") : "最低身高"}
                  value={searchParams.get("min_height") || ""}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams);
                    if (event.target.value) next.set("min_height", event.target.value);
                    else next.delete("min_height");
                    setSearchParams(next);
                  }}
                />
                <input
                  className="site-input"
                  inputMode="numeric"
                  placeholder={filters ? rangePlaceholder(filters, "bust_cm", "min") : "最低胸围"}
                  value={searchParams.get("min_bust") || ""}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams);
                    if (event.target.value) next.set("min_bust", event.target.value);
                    else next.delete("min_bust");
                    setSearchParams(next);
                  }}
                />
                <input
                  className="site-input"
                  inputMode="numeric"
                  placeholder={filters ? rangePlaceholder(filters, "support_cards", "min") : "最少支援卡"}
                  value={searchParams.get("min_support_cards") || ""}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams);
                    if (event.target.value) next.set("min_support_cards", event.target.value);
                    else next.delete("min_support_cards");
                    setSearchParams(next);
                  }}
                />
                <input
                  className="site-input"
                  inputMode="numeric"
                  placeholder={filters ? rangePlaceholder(filters, "character_cards", "min") : "最少衣装"}
                  value={searchParams.get("min_character_cards") || ""}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams);
                    if (event.target.value) next.set("min_character_cards", event.target.value);
                    else next.delete("min_character_cards");
                    setSearchParams(next);
                  }}
                />
                <input
                  className="site-input"
                  inputMode="numeric"
                  placeholder={filters ? rangePlaceholder(filters, "relations", "min") : "最少关系"}
                  value={searchParams.get("min_relations") || ""}
                  onChange={(event) => {
                    const next = new URLSearchParams(searchParams);
                    if (event.target.value) next.set("min_relations", event.target.value);
                    else next.delete("min_relations");
                    setSearchParams(next);
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="filter-result-head">
          <p className="result-copy">
            当前筛到 <strong>{charactersQuery.data?.total ?? characters.length}</strong> 位角色
          </p>
          <span className="result-copy subtle">URL 已同步，可直接分享当前筛选结果。</span>
        </div>

        {charactersQuery.loading ? <p className="empty-state">正在加载角色列表…</p> : null}
        {charactersQuery.error ? <p className="error-state">{charactersQuery.error}</p> : null}
        <div className="character-grid">
          {characters.map((character) => (
            <CharacterCard key={character.slug} character={character} />
          ))}
        </div>
      </GlowPanel>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Fresh Looks</p>
            <h2>最近值得点进去看的衣装页</h2>
          </div>
        </div>
        <div className="latest-strip">
          {overviewQuery.data?.overview.latest_outfits.map((character) => (
            <Link key={character.slug} className="latest-strip__item" to={`/characters/${character.slug}`}>
              <span>{characterName(character)}</span>
              <small>{character.persona_line}</small>
            </Link>
          ))}
        </div>
      </GlowPanel>
    </div>
  );
}
