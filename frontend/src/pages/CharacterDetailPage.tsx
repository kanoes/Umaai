import type { CSSProperties } from "react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchJson } from "../api/client";
import { CharacterCard } from "../components/CharacterCard";
import { GlowPanel } from "../components/GlowPanel";
import { ParallaxArt } from "../components/ParallaxArt";
import { useRemoteData } from "../hooks/useRemoteData";
import type { CharacterResponse, RelationGraph, SupportCardGroup } from "../types/api";
import { hexToRgba } from "../utils/color";
import { characterName, metricValue } from "../utils/format";

function RelationGraphView({ graph }: { graph: RelationGraph }) {
  if (graph.nodes.length <= 1) {
    return <p className="empty-state">当前还没有足够的关系数据。</p>;
  }

  return (
    <svg className="relation-graph" viewBox="0 0 100 100" aria-label="角色关系图">
      {graph.edges.map((edge) => {
        const source = graph.nodes.find((node) => node.slug === edge.source);
        const target = graph.nodes.find((node) => node.slug === edge.target);
        if (!source || !target) {
          return null;
        }
        return (
          <line
            key={`${edge.source}-${edge.target}`}
            className={`relation-graph__edge ${edge.kind}`.trim()}
            x1={source.x * 100}
            y1={source.y * 100}
            x2={target.x * 100}
            y2={target.y * 100}
          />
        );
      })}
      {graph.nodes.map((node) => (
        <g key={node.slug} transform={`translate(${node.x * 100} ${node.y * 100})`}>
          <circle
            className={`relation-graph__node ${node.role}`.trim()}
            cx={0}
            cy={0}
            r={node.role === "center" ? 8 : 5}
            style={
              {
                "--node-main": node.theme.main,
                "--node-sub": node.theme.sub,
              } as CSSProperties
            }
          />
          <text x={0} y={node.role === "center" ? 13 : 9} textAnchor="middle">
            {node.name}
          </text>
        </g>
      ))}
    </svg>
  );
}

export function CharacterDetailPage() {
  const { slug = "" } = useParams();
  const detailQuery = useRemoteData<CharacterResponse>(() => fetchJson(`/api/site/characters/${slug}`), [slug]);
  const item = detailQuery.data?.item;
  const [supportMode, setSupportMode] = useState<"by_command" | "by_rarity">("by_command");

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

  const supportGroups: SupportCardGroup[] = item.support_groups[supportMode];

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
            <span>{item.theme_group}</span>
            <span>{item.personality_tags.join(" / ")}</span>
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
              <p className="eyebrow">Persona</p>
              <h2>人格标签与适性概览</h2>
            </div>
          </div>
          <div className="persona-grid">
            <article className="persona-card">
              <span className="persona-card__label">一句话印象</span>
              <h3>{item.persona_line}</h3>
              <p>{item.personality_tags.join(" / ")}</p>
            </article>
            <article className="persona-card">
              <span className="persona-card__label">距离适性</span>
              <div className="aptitude-chip-row">
                {Object.entries(item.distance_profile).map(([key, value]) => (
                  <span key={key}>
                    {key} {value || "-"}
                  </span>
                ))}
              </div>
            </article>
            <article className="persona-card">
              <span className="persona-card__label">跑法适性</span>
              <div className="aptitude-chip-row">
                {Object.entries(item.style_profile).map(([key, value]) => (
                  <span key={key}>
                    {key} {value || "-"}
                  </span>
                ))}
              </div>
            </article>
          </div>
        </GlowPanel>

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
              <h2>关系图</h2>
            </div>
          </div>
          <RelationGraphView graph={item.relation_graph} />
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
              <h2>衣装时间线</h2>
            </div>
          </div>
          <div className="timeline-year-groups">
            {item.timeline_groups.map((group) => (
              <section key={group.label} className="timeline-year-group">
                <header>
                  <span className="timeline-year-group__year">{group.label}</span>
                </header>
                <div className="timeline-list">
                  {group.items.map((card) => (
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
              </section>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="detail-grid__wide">
          <div className="section-head">
            <div>
              <p className="eyebrow">Support Cards</p>
              <h2>支援卡分类</h2>
            </div>
            <div className="tab-row">
              <button
                className={`tab-row__item ${supportMode === "by_command" ? "active" : ""}`.trim()}
                type="button"
                onClick={() => setSupportMode("by_command")}
              >
                按类型
              </button>
              <button
                className={`tab-row__item ${supportMode === "by_rarity" ? "active" : ""}`.trim()}
                type="button"
                onClick={() => setSupportMode("by_rarity")}
              >
                按稀有度
              </button>
            </div>
          </div>
          <div className="support-group-list">
            {supportGroups.map((group) => (
              <section key={group.label} className="support-group">
                <header>
                  <h3>{group.label}</h3>
                  <span>{group.count} 张</span>
                </header>
                <div className="support-grid">
                  {group.items.map((card) => (
                    <article key={String(card.id)} className="support-card">
                      <span className="support-card__meta">
                        {card.command_label} · 稀有度 {card.rarity ?? "-"}
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
              </section>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="detail-grid__wide">
          <div className="section-head">
            <div>
              <p className="eyebrow">Similar Picks</p>
              <h2>相似角色推荐</h2>
            </div>
          </div>
          <div className="character-grid featured">
            {item.similar_characters.map((character) => (
              <CharacterCard key={character.slug} character={character} mode="compact" />
            ))}
          </div>
        </GlowPanel>
      </div>
    </div>
  );
}
