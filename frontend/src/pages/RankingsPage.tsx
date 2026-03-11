import { startTransition, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { fetchJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { SearchPicker } from "../components/SearchPicker";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharactersResponse, RankingItem, RankingsResponse } from "../types/api";
import { metricValue } from "../utils/format";

function parseCsv(value: string | null) {
  return (value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function sortRankingItems(items: RankingItem[], mode: string) {
  const next = [...items];
  if (mode === "name_asc") {
    next.sort((a, b) => String(a.name_zh || a.name_ja || a.slug).localeCompare(String(b.name_zh || b.name_ja || b.slug)));
    return next;
  }
  if (mode === "value_asc") {
    next.sort((a, b) => Number(a.value) - Number(b.value));
    return next;
  }
  if (mode === "value_desc") {
    next.sort((a, b) => Number(b.value) - Number(a.value));
    return next;
  }
  return next;
}

export function RankingsPage() {
  const rankingsQuery = useRemoteData<RankingsResponse>(() => fetchJson("/api/site/rankings"), []);
  const characterQuery = useRemoteData<CharactersResponse>(() => fetchJson("/api/site/characters?limit=200"), []);
  const [searchParams, setSearchParams] = useSearchParams();

  const category = searchParams.get("category") || "身体数据";
  const metric = searchParams.get("metric") || "waist_to_hip_asc";
  const sort = searchParams.get("sort") || "rank";
  const highlights = parseCsv(searchParams.get("highlight"));
  const meta = rankingsQuery.data?.meta.find((item) => item.key === metric);

  const categoryMeta = (rankingsQuery.data?.meta || []).filter((item) => item.category === category);
  const list = useMemo(
    () => sortRankingItems(rankingsQuery.data?.rankings[metric] || [], sort),
    [rankingsQuery.data?.rankings, metric, sort]
  );

  const shareCurrentView = async () => {
    const url = `${window.location.origin}/rankings?${searchParams.toString()}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      window.prompt("复制这个链接", url);
    }
  };

  return (
    <div className="page page-rankings">
      <section className="page-header">
        <p className="eyebrow">Rankings</p>
        <h1>把原来的单块排行，扩成可筛、可高亮、可分享的排行 2.0。</h1>
        <p>除了身体数据，还加入了内容专题排行，比如衣装量、支援卡量、关系密度和内容密度。</p>
      </section>

      <GlowPanel>
        <div className="ranking-controls">
          <div className="tab-row">
            {["身体数据", "内容专题"].map((value) => (
              <button
                key={value}
                className={`tab-row__item ${category === value ? "active" : ""}`.trim()}
                onClick={() => {
                  const next = new URLSearchParams(searchParams);
                  next.set("category", value);
                  const firstMetric = rankingsQuery.data?.meta.find((item) => item.category === value)?.key;
                  if (firstMetric) {
                    next.set("metric", firstMetric);
                  }
                  setSearchParams(next);
                }}
                type="button"
              >
                {value}
              </button>
            ))}
          </div>

          <div className="tab-row">
            {categoryMeta.map((item) => (
              <button
                key={item.key}
                className={`tab-row__item ${metric === item.key ? "active" : ""}`.trim()}
                onClick={() => {
                  const next = new URLSearchParams(searchParams);
                  next.set("metric", item.key);
                  setSearchParams(next);
                }}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="ranking-toolbar">
            <div className="ranking-description">
              <h2>{meta?.label || "排行"}</h2>
              <p>{meta?.description}</p>
            </div>
            <div className="ranking-toolbar__controls">
              <select
                className="site-select"
                value={sort}
                onChange={(event) => {
                  const next = new URLSearchParams(searchParams);
                  next.set("sort", event.target.value);
                  setSearchParams(next);
                }}
              >
                <option value="rank">按原始名次</option>
                <option value="value_desc">按数值降序</option>
                <option value="value_asc">按数值升序</option>
                <option value="name_asc">按名称</option>
              </select>
              <button className="secondary-link" type="button" onClick={shareCurrentView}>
                分享当前视图
              </button>
            </div>
          </div>
        </div>

        <div className="ranking-highlight-box">
          <div>
            <span className="filter-block__title">高亮角色</span>
            <p className="ranking-highlight-box__copy">给排行加上你关心的角色，方便快速定位。</p>
          </div>
          <SearchPicker
            items={characterQuery.data?.items || []}
            excludeSlugs={highlights}
            onPick={(slug) => {
              const next = new URLSearchParams(searchParams);
              const merged = [...highlights, slug].slice(0, 4);
              next.set("highlight", merged.join(","));
              startTransition(() => setSearchParams(next));
            }}
          />
          <div className="compare-selected">
            {highlights.map((slug) => (
              <button
                key={slug}
                className="compare-selected__chip"
                type="button"
                onClick={() => {
                  const next = new URLSearchParams(searchParams);
                  const filtered = highlights.filter((value) => value !== slug);
                  if (filtered.length > 0) {
                    next.set("highlight", filtered.join(","));
                  } else {
                    next.delete("highlight");
                  }
                  setSearchParams(next);
                }}
              >
                {slug} ×
              </button>
            ))}
          </div>
        </div>

        {rankingsQuery.loading ? <p className="empty-state">正在加载排行…</p> : null}
        {rankingsQuery.error ? <p className="error-state">{rankingsQuery.error}</p> : null}

        <div className="ranking-board">
          {list.map((item) => (
            <Link
              key={item.slug}
              className={`ranking-card ${highlights.includes(item.slug) ? "highlight" : ""}`.trim()}
              to={`/characters/${item.slug}`}
            >
              <span className="ranking-card__rank">#{item.rank}</span>
              <div className="ranking-card__copy">
                <strong>{item.name_zh || item.name_ja || item.slug}</strong>
                <small>{item.theme_group || item.name_ja || item.name_en}</small>
              </div>
              <span className="ranking-card__value">{metricValue(item.value, meta?.unit || "")}</span>
            </Link>
          ))}
        </div>
      </GlowPanel>
    </div>
  );
}
