import { useEffect, useState } from "react";

import { fetchJson, postJson } from "../api/client";
import { GlowPanel } from "../components/GlowPanel";
import { StatusBadge } from "../components/StatusBadge";
import { useRemoteData } from "../hooks/useRemoteData";
import type { AdminOverviewResponse, AdminQualityResponse, Job, JobResponse, JobsResponse } from "../types/api";
import { formatDateTime } from "../utils/format";

export function AdminPage() {
  const overviewQuery = useRemoteData<AdminOverviewResponse>(() => fetchJson("/api/admin/overview"), []);
  const qualityQuery = useRemoteData<AdminQualityResponse>(() => fetchJson("/api/admin/quality"), []);
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
          qualityQuery.reload();
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

  const retryJob = async (jobId: string) => {
    try {
      setError(null);
      const payload = await postJson<JobResponse>(`/api/admin/jobs/${jobId}/retry`);
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
        <h1>后台现在不只是“点按钮跑脚本”，而是一个数据维护台。</h1>
        <p>这里可以看派生是否过期、质量问题、失败任务并直接重试。</p>
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
                <small>{action === "build_site_bundle" ? "重建标准化派生站点文件" : "点击触发任务"}</small>
              </button>
            ))}
          </div>
          {error ? <p className="error-state">{error}</p> : null}
        </GlowPanel>

        <GlowPanel className="content-grid__side">
          <div className="section-head">
            <div>
              <p className="eyebrow">Overview</p>
              <h2>站点状态</h2>
            </div>
          </div>
          <div className="stat-grid compact">
            <article>
              <span>角色</span>
              <strong>{overviewQuery.data?.stats.total_characters ?? "-"}</strong>
            </article>
            <article>
              <span>派生模式</span>
              <strong>{overviewQuery.data?.manifest.source_mode || "-"}</strong>
            </article>
            <article>
              <span>派生时间</span>
              <strong>{formatDateTime(overviewQuery.data?.manifest.generated_at_utc)}</strong>
            </article>
            <article>
              <span>源数据时间</span>
              <strong>{formatDateTime(overviewQuery.data?.manifest.raw_updated_at_utc)}</strong>
            </article>
          </div>
        </GlowPanel>
      </div>

      {overviewQuery.data?.diff_prompt ? (
        <GlowPanel className="warning-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Diff Prompt</p>
              <h2>{overviewQuery.data.diff_prompt.title}</h2>
            </div>
          </div>
          <p>{overviewQuery.data.diff_prompt.message}</p>
          <div className="compare-card__stats">
            <span>原始更新时间 {formatDateTime(overviewQuery.data.diff_prompt.raw_updated_at_utc)}</span>
            <span>派生更新时间 {formatDateTime(overviewQuery.data.diff_prompt.generated_at_utc)}</span>
          </div>
          <div className="latest-strip">
            {overviewQuery.data.diff_prompt.recent_updates.map((item) => (
              <div key={item.slug} className="latest-strip__item">
                <span>{item.name_zh || item.name_ja || item.slug}</span>
                <small>{formatDateTime(item.fetched_at_utc)}</small>
              </div>
            ))}
          </div>
        </GlowPanel>
      ) : null}

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Quality</p>
            <h2>数据质量总览</h2>
          </div>
        </div>
        <div className="stat-grid compact">
          <article>
            <span>缺少中文译名</span>
            <strong>{qualityQuery.data?.report.summary.missing_name_zh_count ?? "-"}</strong>
          </article>
          <article>
            <span>译名冲突组</span>
            <strong>{qualityQuery.data?.report.summary.duplicate_name_zh_group_count ?? "-"}</strong>
          </article>
          <article>
            <span>立绘异常</span>
            <strong>
              {(qualityQuery.data?.report.summary.image_missing_count || 0) +
                (qualityQuery.data?.report.summary.image_invalid_count || 0)}
            </strong>
          </article>
          <article>
            <span>内容较薄角色</span>
            <strong>{qualityQuery.data?.report.summary.sparse_content_count ?? "-"}</strong>
          </article>
        </div>
      </GlowPanel>

      <div className="content-grid admin">
        <GlowPanel className="content-grid__main">
          <div className="section-head">
            <div>
              <p className="eyebrow">Issues</p>
              <h2>问题角色</h2>
            </div>
          </div>
          <div className="admin-issues">
            {(qualityQuery.data?.report.issues || []).slice(0, 18).map((issue) => (
              <article key={issue.slug} className="admin-issue">
                <header>
                  <strong>{issue.name}</strong>
                  <span className={`severity severity-${Math.min(issue.severity, 3)}`}>S{issue.severity}</span>
                </header>
                <p>{issue.slug}</p>
                <ul>
                  {issue.issues.map((message) => (
                    <li key={message}>{message}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </GlowPanel>

        <GlowPanel className="content-grid__side">
          <div className="section-head">
            <div>
              <p className="eyebrow">Conflicts</p>
              <h2>译名冲突</h2>
            </div>
          </div>
          <div className="job-history">
            {(qualityQuery.data?.report.duplicate_name_zh_groups || []).slice(0, 12).map((group) => (
              <div key={group.name_zh} className="job-history__item static">
                <div>
                  <strong>{group.name_zh}</strong>
                  <small>{group.slugs.join(", ")}</small>
                </div>
              </div>
            ))}
          </div>
        </GlowPanel>
      </div>

      <GlowPanel>
        <div className="section-head">
          <div>
            <p className="eyebrow">Failed Jobs</p>
            <h2>失败任务与重试</h2>
          </div>
        </div>
        <div className="job-history">
          {(overviewQuery.data?.failed_jobs || []).map((job) => (
            <div key={job.id} className="job-history__item static">
              <div>
                <strong>{job.action}</strong>
                <small>
                  {formatDateTime(job.created_at_utc)}
                  {job.error ? ` · ${job.error}` : ""}
                </small>
              </div>
              <div className="job-history__actions">
                <StatusBadge status={job.status} />
                <button className="secondary-link compact" type="button" onClick={() => retryJob(job.id)}>
                  重试
                </button>
              </div>
            </div>
          ))}
        </div>
      </GlowPanel>

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
            <h2>持久化任务历史</h2>
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
