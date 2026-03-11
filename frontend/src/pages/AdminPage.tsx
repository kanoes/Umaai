import { useEffect, useState } from "react";

import { fetchJson, postJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { StatusBadge } from "../components/StatusBadge";
import { useRemoteData } from "../hooks/useRemoteData";
import type { AdminOverviewResponse, Job, JobResponse, JobsResponse } from "../types/api";
import { formatDateTime } from "../utils/format";

export function AdminPage() {
  const overviewQuery = useRemoteData<AdminOverviewResponse>(() => fetchJson("/api/admin/overview"), []);
  const jobsQuery = useRemoteData<JobsResponse>(() => fetchJson("/api/admin/jobs"), []);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [pollingJobId, setPollingJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pollingJobId) {
      return;
    }

    let timer = 0;
    let cancelled = false;

    const tick = async () => {
      try {
        const payload = await fetchJson<JobResponse>(`/api/admin/jobs/${pollingJobId}`);
        if (cancelled) {
          return;
        }
        setActiveJob(payload.job);
        if (payload.job.status === "success" || payload.job.status === "error") {
          setPollingJobId(null);
          overviewQuery.reload();
          jobsQuery.reload();
          return;
        }
      } catch (pollError) {
        if (!cancelled) {
          setError((pollError as Error).message);
          setPollingJobId(null);
        }
        return;
      }
      timer = window.setTimeout(tick, 1200);
    };

    tick();

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [pollingJobId]);

  const startAction = async (action: string) => {
    try {
      setError(null);
      const payload = await postJson<JobResponse>(`/api/admin/actions/${action}`);
      setActiveJob(payload.job);
      setPollingJobId(payload.job.id);
      jobsQuery.reload();
    } catch (submitError) {
      setError((submitError as Error).message);
    }
  };

  return (
    <div className="page page-admin">
      <section className="page-header">
        <p className="eyebrow">Admin</p>
        <h1>抓取、生成、维护都挪到后台，不再污染公开首页。</h1>
        <p>前台负责体验，后台只负责数据工作流。</p>
      </section>

      <div className="content-grid admin">
        <GlowPanel className="content-grid__main">
          <div className="section-head">
            <div>
              <p className="eyebrow">Actions</p>
              <h2>数据任务</h2>
            </div>
          </div>
          <div className="admin-actions">
            {overviewQuery.data?.actions.map((action) => (
              <button key={action} className="admin-action" type="button" onClick={() => startAction(action)}>
                <strong>{action}</strong>
                <small>点击触发任务</small>
              </button>
            ))}
          </div>
          {error ? <p className="error-state">{error}</p> : null}
        </GlowPanel>

        <GlowPanel className="content-grid__side">
          <div className="section-head">
            <div>
              <p className="eyebrow">Overview</p>
              <h2>数据状态</h2>
            </div>
          </div>
          <div className="stat-grid compact">
            <article>
              <span>角色</span>
              <strong>{overviewQuery.data?.stats.total_characters ?? "-"}</strong>
            </article>
            <article>
              <span>立绘</span>
              <strong>{overviewQuery.data?.stats.with_images ?? "-"}</strong>
            </article>
            <article>
              <span>可排行</span>
              <strong>{overviewQuery.data?.stats.with_metrics ?? "-"}</strong>
            </article>
            <article>
              <span>更新时间</span>
              <strong>{formatDateTime(overviewQuery.data?.updated_at_utc)}</strong>
            </article>
          </div>
        </GlowPanel>
      </div>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Live Job</p>
            <h2>任务日志</h2>
          </div>
        </div>
        {activeJob ? (
          <>
            <div className="job-head">
              <strong>{activeJob.action}</strong>
              <StatusBadge status={activeJob.status} />
            </div>
            <pre className="job-console">{activeJob.logs.join("\n")}</pre>
          </>
        ) : (
          <p className="empty-state">暂无正在查看的任务。</p>
        )}
      </GlowPanel>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">History</p>
            <h2>最近任务</h2>
          </div>
        </div>
        <div className="job-history">
          {(jobsQuery.data?.jobs ?? []).map((job) => (
            <button key={job.id} className="job-history__item" type="button" onClick={() => setActiveJob(job)}>
              <div>
                <strong>{job.action}</strong>
                <small>{formatDateTime(job.created_at_utc)}</small>
              </div>
              <StatusBadge status={job.status} />
            </button>
          ))}
        </div>
      </GlowPanel>
    </div>
  );
}
