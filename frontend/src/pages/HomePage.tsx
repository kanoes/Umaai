import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";

import { fetchJson } from "../api/client";
import { CharacterCard } from "../components/CharacterCard";
import { GlowPanel } from "../components/GlowPanel";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharactersResponse, OverviewResponse } from "../types/api";
import { characterName, metricValue } from "../utils/format";

const PREVIEW_LABELS: Record<string, string> = {
  waist_to_hip_asc: "腰臀比",
  waist_to_bust_asc: "腰乳比",
  bust_cm_desc: "胸围",
  hip_cm_desc: "臀围",
  waist_cm_asc: "腰围",
  height_cm_desc: "身高",
};

export function HomePage() {
  const overviewQuery = useRemoteData<OverviewResponse>(() => fetchJson("/api/site/overview"), []);
  const charactersQuery = useRemoteData<CharactersResponse>(() => fetchJson("/api/site/characters?limit=200"), []);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search.trim().toLowerCase());

  const characters = charactersQuery.data?.items ?? [];
  const filtered = characters.filter((item) => {
    if (!deferredSearch) {
      return true;
    }
    const haystack = `${item.name_zh || ""} ${item.name_ja || ""} ${item.name_en || ""} ${item.slug}`.toLowerCase();
    return haystack.includes(deferredSearch);
  });

  return (
    <div className="page page-home">
      <section className="hero-banner">
        <div className="hero-banner__copy">
          <p className="eyebrow">Public Site</p>
          <h1>把原来的控制台，改造成真正能逛的马娘内容站。</h1>
          <p className="hero-banner__text">
            这里不再把抓取按钮摆在首页，而是用角色主题色、衣装时间线、关系链和排行页把内容感做出来。
          </p>
          <div className="hero-banner__actions">
            <Link className="primary-link" to="/rankings">
              查看排行
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
              <span>有立绘</span>
              <strong>{overviewQuery.data?.stats.with_images ?? "-"}</strong>
            </article>
            <article>
              <span>支援卡总数</span>
              <strong>{overviewQuery.data?.stats.support_card_total ?? "-"}</strong>
            </article>
            <article>
              <span>关系链条</span>
              <strong>{overviewQuery.data?.stats.relation_total ?? "-"}</strong>
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
              <h2>重点排行</h2>
            </div>
            <Link className="inline-link" to="/rankings">
              全部排行
            </Link>
          </div>
          <div className="ranking-preview">
            {Object.entries(overviewQuery.data?.overview.ranking_previews ?? {})
              .slice(0, 3)
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
            <h2>角色发现页</h2>
          </div>
          <input
            className="site-search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="搜索角色名、译名或英文名"
          />
        </div>
        {charactersQuery.loading ? <p className="empty-state">正在加载角色列表…</p> : null}
        {charactersQuery.error ? <p className="error-state">{charactersQuery.error}</p> : null}
        <div className="character-grid">
          {filtered.map((character) => (
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
              <small>{character.counts.character_cards} 套衣装</small>
            </Link>
          ))}
        </div>
      </GlowPanel>
    </div>
  );
}
