import { useState } from "react";
import { Link } from "react-router-dom";

import { fetchJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { useRemoteData } from "../hooks/useRemoteData";
import type { RankingsResponse } from "../types/api";
import { metricValue } from "../utils/format";

export function RankingsPage() {
  const rankingsQuery = useRemoteData<RankingsResponse>(() => fetchJson("/api/site/rankings"), []);
  const [metric, setMetric] = useState("waist_to_hip_asc");
  const meta = rankingsQuery.data?.meta.find((item) => item.key === metric);
  const list = rankingsQuery.data?.rankings[metric] ?? [];

  return (
    <div className="page page-rankings">
      <section className="page-header">
        <p className="eyebrow">Rankings</p>
        <h1>把原来的单块排行，扩成完整浏览页</h1>
        <p>这里已经从控制台里的一个小模块，变成站内一级内容入口。</p>
      </section>

      <GlowPanel>
        <div className="ranking-controls">
          <div className="tab-row">
            {rankingsQuery.data?.meta.map((item) => (
              <button
                key={item.key}
                className={`tab-row__item ${metric === item.key ? "active" : ""}`.trim()}
                onClick={() => setMetric(item.key)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="ranking-description">
            <h2>{meta?.label || "排行"}</h2>
            <p>{meta?.description}</p>
          </div>
        </div>

        {rankingsQuery.loading ? <p className="empty-state">正在加载排行…</p> : null}
        {rankingsQuery.error ? <p className="error-state">{rankingsQuery.error}</p> : null}

        <div className="ranking-board">
          {list.map((item) => (
            <Link key={item.slug} className="ranking-card" to={`/characters/${item.slug}`}>
              <span className="ranking-card__rank">#{item.rank}</span>
              <div className="ranking-card__copy">
                <strong>{item.name_zh || item.name_ja || item.slug}</strong>
                <small>{item.name_ja || item.name_en}</small>
              </div>
              <span className="ranking-card__value">{metricValue(item.value, meta?.unit || "")}</span>
            </Link>
          ))}
        </div>
      </GlowPanel>
    </div>
  );
}
