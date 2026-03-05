const state = {
  index: null,
  metrics: null,
  currentJobId: null,
  pollingTimer: null,
};

const els = {
  total: document.getElementById("stat-total"),
  img: document.getElementById("stat-img"),
  metrics: document.getElementById("stat-metrics"),
  job: document.getElementById("stat-job"),
  jobStatus: document.getElementById("job-status"),
  jobLogs: document.getElementById("job-logs"),
  rankMetric: document.getElementById("rank-metric"),
  rankLimit: document.getElementById("rank-limit"),
  rankList: document.getElementById("rank-list"),
  searchInput: document.getElementById("search-input"),
  cardGrid: document.getElementById("card-grid"),
};

function escapeHtml(raw) {
  return String(raw ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(json.error || `HTTP ${res.status}`);
  }
  return json;
}

async function loadIndex() {
  const payload = await apiFetch("/api/data/index");
  state.index = payload.data;
}

async function loadMetrics() {
  try {
    const payload = await apiFetch("/api/data/body-metrics");
    state.metrics = payload.data;
  } catch (_err) {
    state.metrics = null;
  }
}

function renderStats() {
  const list = state.index?.uma_list ?? [];
  const total = list.length;
  const withImg = list.filter((x) => typeof x.chara_img === "string" && x.chara_img !== "No").length;
  const metricsCount = Number(state.metrics?.count || 0);

  els.total.textContent = total || "-";
  els.img.textContent = withImg || "-";
  els.metrics.textContent = metricsCount || "-";
}

function renderRankings() {
  const metric = els.rankMetric.value;
  const limit = Number(els.rankLimit.value);
  const rankings = state.metrics?.rankings?.[metric] ?? [];
  const top = rankings.slice(0, limit);

  if (!top.length) {
    els.rankList.innerHTML = `<p>暂无排行数据，请先点击“生成三围排行”。</p>`;
    return;
  }

  els.rankList.innerHTML = top
    .map(
      (item) => `
      <article class="rank-item">
        <div class="rank-top">
          <span>#${escapeHtml(item.rank)}</span>
          <span>${escapeHtml(metric)}</span>
        </div>
        <p class="rank-name">${escapeHtml(item.name_zh || item.name_ja || item.slug)}</p>
        <p class="rank-value">${escapeHtml(item.value)}</p>
      </article>
    `
    )
    .join("");
}

function metricBySlug() {
  const out = new Map();
  for (const item of state.metrics?.items ?? []) {
    if (item.slug) out.set(item.slug, item);
  }
  return out;
}

function renderCards() {
  const list = state.index?.uma_list ?? [];
  const key = els.searchInput.value.trim().toLowerCase();
  const metricsMap = metricBySlug();

  const filtered = list.filter((item) => {
    if (!key) return true;
    const text = `${item.name_zh || ""} ${item.name_ja || ""} ${item.name_en || ""}`.toLowerCase();
    return text.includes(key);
  });

  els.cardGrid.innerHTML = filtered
    .slice(0, 150)
    .map((item) => {
      const m = metricsMap.get(item.slug) || {};
      const imgOk = typeof item.chara_img === "string" && item.chara_img !== "No";
      const img = imgOk ? `<img loading="lazy" src="/${encodeURI(item.chara_img)}" alt="${escapeHtml(item.name_zh)}" />` : "";

      return `
        <article class="uma-card">
          <div class="img-wrap">${img}</div>
          <div class="txt">
            <h3>${escapeHtml(item.name_zh || item.name_ja || item.slug)}</h3>
            <p>${escapeHtml(item.name_ja || "")}</p>
            <p>${escapeHtml(item.name_en || "")}</p>
            <div class="chips">
              <span class="chip ${imgOk ? "ok" : "warn"}">${imgOk ? "立绘已就绪" : "无立绘"}</span>
              <span class="chip">B${escapeHtml(m.bust_cm ?? "-")} W${escapeHtml(m.waist_cm ?? "-")} H${escapeHtml(
        m.hip_cm ?? "-"
      )}</span>
              <span class="chip">腰臀比 ${escapeHtml(m.waist_to_hip ?? "-")}</span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderJob(job) {
  if (!job) {
    els.job.textContent = "-";
    els.jobStatus.textContent = "暂无任务";
    els.jobLogs.textContent = "";
    return;
  }
  const latestLog = (job.logs || []).slice(-1)[0] || "";
  els.job.textContent = `${job.action} / ${job.status}`;
  els.jobStatus.textContent = `${job.status.toUpperCase()} · ${job.action}${job.error ? ` · ${job.error}` : ""}`;
  els.jobLogs.textContent = (job.logs || []).join("\n");
  if (latestLog) {
    els.jobLogs.scrollTop = els.jobLogs.scrollHeight;
  }
}

async function pollJob(jobId) {
  if (!jobId) return;
  if (state.pollingTimer) clearInterval(state.pollingTimer);

  state.currentJobId = jobId;
  state.pollingTimer = setInterval(async () => {
    try {
      const payload = await apiFetch(`/api/jobs/${jobId}`);
      const job = payload.job;
      renderJob(job);
      if (job.status === "success" || job.status === "error") {
        clearInterval(state.pollingTimer);
        state.pollingTimer = null;
        await refreshData();
      }
    } catch (err) {
      clearInterval(state.pollingTimer);
      state.pollingTimer = null;
      els.jobStatus.textContent = `任务轮询失败: ${err.message}`;
    }
  }, 1200);
}

async function triggerAction(action) {
  try {
    const payload = await apiFetch(`/api/actions/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const job = payload.job;
    renderJob(job);
    await pollJob(job.id);
  } catch (err) {
    els.jobStatus.textContent = `触发失败: ${err.message}`;
  }
}

async function refreshData() {
  try {
    await loadIndex();
    await loadMetrics();
    renderStats();
    renderRankings();
    renderCards();
  } catch (err) {
    els.jobStatus.textContent = `加载数据失败: ${err.message}`;
  }
}

function bindEvents() {
  document.querySelectorAll(".action-btn").forEach((btn) => {
    btn.addEventListener("click", () => triggerAction(btn.dataset.action));
  });

  els.rankMetric.addEventListener("change", renderRankings);
  els.rankLimit.addEventListener("change", renderRankings);
  els.searchInput.addEventListener("input", renderCards);
}

async function bootstrap() {
  bindEvents();
  await refreshData();

  try {
    const jobs = await apiFetch("/api/jobs");
    const latest = jobs.jobs?.[0];
    if (latest) renderJob(latest);
  } catch (_err) {
    // no-op
  }
}

bootstrap();
