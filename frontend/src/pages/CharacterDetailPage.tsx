import type { CSSProperties } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { ParallaxArt } from "../components/ParallaxArt";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharacterResponse } from "../types/api";
import { hexToRgba } from "../utils/color";
import { characterName, metricValue } from "../utils/format";

export function CharacterDetailPage() {
  const { slug = "" } = useParams();
  const detailQuery = useRemoteData<CharacterResponse>(() => fetchJson(`/api/site/characters/${slug}`), [slug]);
  const item = detailQuery.data?.item;

  if (detailQuery.loading) {
    return <p className="empty-state">正在加载角色详情…</p>;
  }

  if (detailQuery.error || !item) {
    return <p className="error-state">{detailQuery.error || "角色不存在"}</p>;
  }

  const heroStyle = {
    "--theme-main": item.theme.main,
    "--theme-sub": item.theme.sub,
    "--theme-border": hexToRgba(item.theme.border, 0.28),
  } as CSSProperties;

  return (
    <div className="page page-detail" style={heroStyle}>
      <section className="detail-hero">
        <div className="detail-hero__copy">
          <p className="eyebrow">Character Detail</p>
          <h1>{characterName(item)}</h1>
          <p className="detail-hero__sub">{item.name_ja || item.name_en}</p>
          <p className="detail-hero__text">{item.description}</p>
          <div className="detail-hero__actions">
            <Link className="primary-link" to={`/compare?slugs=${item.slug}`}>
              加入对比
            </Link>
            <Link className="secondary-link" to="/rankings">
              查看排行
            </Link>
          </div>
          <div className="metric-chip-row">
            <span>身高 {metricValue(item.metrics?.height_cm, "cm")}</span>
            <span>三围 B{metricValue(item.metrics?.bust_cm)} / W{metricValue(item.metrics?.waist_cm)} / H{metricValue(item.metrics?.hip_cm)}</span>
            <span>衣装 {item.counts.character_cards}</span>
            <span>支援卡 {item.counts.support_cards}</span>
          </div>
        </div>
        <div className="detail-hero__art">
          <ParallaxArt image={item.image} name={characterName(item)} theme={item.theme} />
        </div>
      </section>

      <div className="detail-grid">
        <GlowPanel className="detail-grid__wide">
          <div className="section-head">
            <div>
              <p className="eyebrow">Profile</p>
              <h2>资料卡</h2>
            </div>
          </div>
          <div className="profile-sections">
            {item.profile_sections.map((section) => (
              <article key={section.title} className="profile-section">
                <h3>{section.title}</h3>
                <div className="profile-facts">
                  {section.items.map((fact) => (
                    <div key={fact.key} className="profile-fact">
                      <span>{fact.label}</span>
                      <strong>{fact.value}</strong>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel>
          <div className="section-head">
            <div>
              <p className="eyebrow">Relations</p>
              <h2>关系网络</h2>
            </div>
          </div>
          <div className="relation-cloud">
            {item.relations.map((relation) => (
              <Link
                key={relation.slug}
                className="relation-pill"
                to={`/characters/${relation.slug}`}
                style={
                  {
                    "--pill-main": relation.theme.main,
                    "--pill-sub": relation.theme.sub,
                  } as CSSProperties
                }
              >
                <strong>{relation.name_ja || relation.name_en || relation.slug}</strong>
                <small>{relation.slug}</small>
              </Link>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="detail-grid__wide">
          <div className="section-head">
            <div>
              <p className="eyebrow">Dress Timeline</p>
              <h2>衣装与适性</h2>
            </div>
          </div>
          <div className="timeline-list">
            {item.character_cards.map((card) => (
              <article key={String(card.id)} className="timeline-card">
                <header>
                  <div>
                    <h3>{card.title || "未命名衣装"}</h3>
                    <p>{card.published_at || "-"}</p>
                  </div>
                  <div className="timeline-card__flags">
                    {card.limited ? <span>限定</span> : null}
                    {card.event_bonus ? <span>活动</span> : null}
                  </div>
                </header>
                <p className="timeline-card__aliases">{card.aliases || "暂无别名信息"}</p>
                <div className="detail-table">
                  {Object.entries(card.aptitudes).map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <strong>{value || "-"}</strong>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="detail-grid__wide">
          <div className="section-head">
            <div>
              <p className="eyebrow">Support Cards</p>
              <h2>支援卡时间线</h2>
            </div>
          </div>
          <div className="support-grid">
            {item.support_cards.map((card) => (
              <article key={String(card.id)} className="support-card">
                <span className="support-card__meta">
                  {card.command_label} · SSR/SR {card.rarity ?? "-"}
                </span>
                <h3>{card.title || card.name || "未命名支援卡"}</h3>
                <p>{card.name}</p>
                <footer>
                  <span>{card.published_at || "-"}</span>
                  {card.event_bonus ? <strong>活动</strong> : null}
                </footer>
              </article>
            ))}
          </div>
        </GlowPanel>
      </div>
    </div>
  );
}
