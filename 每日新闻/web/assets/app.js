/* 每日 AI 新闻看板 —— 客户端动态渲染
 * 通过 GitHub API 列出仓库目录，用 raw.githubusercontent 拉取 markdown 内容，
 * 解析后渲染时间线、卡片、每日新闻数柱状图以及周报/月报。
 */

const CONFIG = {
  OWNER: "CD168888",
  REPO: "My-Workspace",
  BRANCH: "main",
  NEWS_ROOT: "每日新闻", // 仓库内新闻根目录
};

const API_BASE = `https://api.github.com/repos/${CONFIG.OWNER}/${CONFIG.REPO}/contents`;
const RAW_BASE = `https://raw.githubusercontent.com/${CONFIG.OWNER}/${CONFIG.REPO}/${CONFIG.BRANCH}`;

// 会话内缓存，减少 API 调用
const cache = {
  months: null,            // ["2026-08", ...]
  daysByMonth: {},         // { "2026-08": [{name, path}] }
  dayContent: {},          // { path: parsedObject }
};

let chartInstance = null;
let currentMonth = null;
let currentParsed = [];    // 当前月份已解析的每日数据（用于搜索/渲染）

/* ---------- 网络 ---------- */
async function fetchJson(path) {
  const url = `${API_BASE}/${encodeURIComponent(path)}`;
  const res = await fetch(url, { headers: { Accept: "application/vnd.github+json" } });
  if (res.status === 403) throw new Error("GitHub API 速率受限（公开仓库未登录约 60 次/小时），请稍后重试。");
  if (!res.ok) throw new Error(`加载失败：HTTP ${res.status}`);
  return res.json();
}

async function fetchRaw(path) {
  const url = `${RAW_BASE}/${encodeURIComponent(path)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`读取文件失败：HTTP ${res.status}`);
  return res.text();
}

/* ---------- 解析每日 markdown ---------- */
function parseDaily(md, dateLabel) {
  const lines = md.split(/\r?\n/);
  let section = "other";
  const items = [];
  const blue = [];
  const notes = [];
  let cur = null;

  const flushCur = () => {
    if (!cur) return;
    if (section === "items" && (cur.desc || cur.reason || cur.source)) items.push(cur);
    else if (section === "blue" && (cur.desc || cur.why || cur.source)) blue.push(cur);
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) continue;

    const h1 = line.match(/^#\s+(.*)$/);
    const h2 = line.match(/^##\s+(.*)$/);
    const h3 = line.match(/^###\s+(.*)$/);
    const field = line.match(/^\s*[-*]?\s*\*\*(.+?)\*\*[：:]\s*(.*)$/);
    const numbered = line.match(/^\d+[.、]\s+(.*)$/);

    if (h1) { continue; }
    if (h2) {
      flushCur();
      const t = h2[1];
      if (t.includes("今日高价值") || t.includes("新闻条目")) section = "items";
      else if (t.includes("蓝海") || t.includes("副业")) section = "blue";
      else if (t.includes("备注")) section = "notes";
      else section = "other";
      cur = null;
      continue;
    }
    if (h3) {
      flushCur();
      if (section === "items") cur = { title: h3[1].replace(/^\d+[.、]\s*/, "").trim(), desc: "", reason: "", source: "" };
      else if (section === "blue") cur = { title: h3[1].trim(), desc: "", why: "", source: "" };
      else cur = null;
      continue;
    }
    if (numbered && section === "items" && !cur) {
      cur = { title: numbered[1].trim(), desc: "", reason: "", source: "" };
      continue;
    }
    if (field) {
      const key = field[1];
      const val = field[2].trim();
      if (section === "items" && cur) {
        if (key.includes("简述") || key.includes("摘要")) cur.desc = val;
        else if (key.includes("值得关注") || key.includes("原因")) cur.reason = val;
        else if (key.includes("来源") || key.includes("链接")) cur.source = val;
        else cur.desc = (cur.desc ? cur.desc + " " : "") + val;
      } else if (section === "blue" && cur) {
        if (key.includes("机会描述")) cur.desc = val;
        else if (key.includes("为什么值得") || key.includes("关注")) cur.why = val;
        else if (key.includes("来源") || key.includes("链接")) cur.source = val;
        else cur.desc = (cur.desc ? cur.desc + " " : "") + val;
      }
      continue;
    }
    // 续行：偏接到当前条目的 reason / desc
    if (cur && section === "items" && !line.startsWith("#") && !line.startsWith("-")) {
      if (cur.reason) cur.reason += " " + line.trim();
      else if (cur.desc) cur.desc += " " + line.trim();
    }
  }
  flushCur();

  return { date: dateLabel, items, blue, notes };
}

/* ---------- 工具 ---------- */
function esc(s) {
  return String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderSource(src) {
  if (!src) return "—";
  const url = src.match(/https?:\/\/[^\s)]+/);
  if (url) return `<a href="${esc(url[0])}" target="_blank" rel="noopener">${esc(src)}</a>`;
  return esc(src);
}

/* ---------- 每日动态 ---------- */
async function loadMonths() {
  if (cache.months) return cache.months;
  const data = await fetchJson(`${CONFIG.NEWS_ROOT}/归档`);
  const months = data
    .filter((d) => d.type === "dir")
    .map((d) => d.name)
    .sort()
    .reverse();
  cache.months = months;
  return months;
}

async function loadMonthDays(month) {
  if (cache.daysByMonth[month]) return cache.daysByMonth[month];
  const data = await fetchJson(`${CONFIG.NEWS_ROOT}/归档/${month}`);
  const days = data
    .filter((d) => d.type === "file" && d.name.endsWith(".md"))
    .map((d) => ({ name: d.name.replace(/\.md$/, ""), path: d.path }))
    .sort()
    .reverse();
  cache.daysByMonth[month] = days;
  return days;
}

async function loadDayContent(day) {
  if (cache.dayContent[day.path]) return cache.dayContent[day.path];
  const md = await fetchRaw(day.path);
  const parsed = parseDaily(md, day.name);
  cache.dayContent[day.path] = parsed;
  return parsed;
}

async function selectMonth(month) {
  currentMonth = month;
  const timeline = document.getElementById("timeline");
  const detail = document.getElementById("day-detail");
  timeline.innerHTML = `<p class="hint">读取 ${esc(month)} 的每日文件…</p>`;
  detail.innerHTML = `<p class="hint">点击左侧日期查看当天动态。</p>`;

  try {
    const days = await loadMonthDays(month);
    if (!days.length) {
      timeline.innerHTML = `<p class="hint">${esc(month)} 暂无每日文件。</p>`;
      renderChart([]);
      return;
    }
    // 并行拉取内容
    const parsedList = await Promise.all(days.map((d) => loadDayContent(d).catch(() => null)));
    currentParsed = parsedList.filter(Boolean);
    renderTimeline(currentParsed);
    renderChart(currentParsed);
    // 默认展开最新一天
    if (currentParsed.length) selectDay(currentParsed[0]);
  } catch (e) {
    timeline.innerHTML = `<p class="error">${esc(e.message)}</p>`;
  }
}

function renderTimeline(parsedList) {
  const timeline = document.getElementById("timeline");
  timeline.innerHTML = parsedList
    .map(
      (p, i) => `
      <div class="day-item" data-i="${i}">
        <span>${esc(p.date)}</span>
        <span class="day-count">${p.items.length} 条</span>
      </div>`
    )
    .join("");
  timeline.querySelectorAll(".day-item").forEach((el) => {
    el.addEventListener("click", () => selectDay(currentParsed[+el.dataset.i], el));
  });
}

function renderChart(parsedList) {
  const canvas = document.getElementById("dailyChart");
  const labels = parsedList.map((p) => p.date.slice(5)); // MM-DD
  const counts = parsedList.map((p) => p.items.length);
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "每日新闻条数",
        data: counts,
        backgroundColor: "#378ADD",
        borderRadius: 6,
        maxBarThickness: 38,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
        x: { grid: { display: false } },
      },
    },
  });
}

function selectDay(parsed, el) {
  if (el) {
    document.querySelectorAll(".day-item").forEach((x) => x.classList.remove("active"));
    el.classList.add("active");
  }
  const detail = document.getElementById("day-detail");
  const q = (document.getElementById("search").value || "").trim().toLowerCase();

  const items = parsed.items.filter((it) => {
    if (!q) return true;
    return (it.title + it.desc + it.reason + it.source).toLowerCase().includes(q);
  });

  let html = "";
  if (!items.length) {
    html += `<p class="hint">${q ? "没有匹配搜索关键词的动态。" : "当天暂无动态。"}</p>`;
  } else {
    html += items
      .map(
        (it) => `
      <div class="card">
        <h3>${esc(it.title)}</h3>
        <div class="field"><span class="label">事件简述：</span>${esc(it.desc) || "—"}</div>
        <div class="field"><span class="label">值得关注：</span>${esc(it.reason) || "—"}</div>
        <div class="field"><span class="label">来源：</span>${renderSource(it.source)}</div>
      </div>`
      )
      .join("");
  }

  if (parsed.blue && parsed.blue.length) {
    const blueItems = parsed.blue.filter((b) =>
      !q || (b.title + b.desc + b.why + b.source).toLowerCase().includes(q)
    );
    if (blueItems.length) {
      html += `<div class="section-title">蓝海市场 / 副业机会</div>`;
      html += blueItems
        .map(
          (b) => `
        <div class="card blue-card">
          <h3>${esc(b.title)}</h3>
          <div class="field"><span class="label">机会描述：</span>${esc(b.desc) || "—"}</div>
          <div class="field"><span class="label">为什么值得关注：</span>${esc(b.why) || "—"}</div>
          <div class="field"><span class="label">来源：</span>${renderSource(b.source)}</div>
        </div>`
        )
        .join("");
    }
  }
  detail.innerHTML = html;
}

/* ---------- 周报 / 月报 ---------- */
async function loadSummary(kind) {
  // kind: "weekly" | "monthly"
  const folder = kind === "weekly" ? "周报" : "月报";
  const listEl = document.getElementById(`${kind}-list`);
  const detailEl = document.getElementById(`${kind}-detail`);
  listEl.innerHTML = `<p class="hint">加载中…</p>`;
  detailEl.innerHTML = `<p class="hint">选择一份${kind === "weekly" ? "周报" : "月报"}查看内容。</p>`;
  try {
    const data = await fetchJson(`${CONFIG.NEWS_ROOT}/汇总/${folder}`);
    const files = data
      .filter((d) => d.type === "file" && d.name.endsWith(".md"))
      .map((d) => ({ name: d.name.replace(/\.md$/, ""), path: d.path }))
      .sort()
      .reverse();
    if (!files.length) {
      listEl.innerHTML = `<p class="hint">暂无${kind === "weekly" ? "周报" : "月报"}文件。</p>`;
      return;
    }
    listEl.innerHTML = files
      .map((f, i) => `<div class="sum-item" data-i="${i}">${esc(f.name)}</div>`)
      .join("");
    listEl.querySelectorAll(".sum-item").forEach((el) => {
      el.addEventListener("click", async () => {
        listEl.querySelectorAll(".sum-item").forEach((x) => x.classList.remove("active"));
        el.classList.add("active");
        detailEl.innerHTML = `<p class="hint">渲染中…</p>`;
        try {
          const md = await fetchRaw(files[+el.dataset.i].path);
          detailEl.innerHTML = marked.parse(md);
        } catch (e) {
          detailEl.innerHTML = `<p class="error">${esc(e.message)}</p>`;
        }
      });
    });
  } catch (e) {
    listEl.innerHTML = `<p class="error">${esc(e.message)}</p>`;
  }
}

/* ---------- 标签页 ---------- */
function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.getElementById(`panel-${tab}`).classList.add("active");
  if (tab === "weekly") loadSummary("weekly");
  if (tab === "monthly") loadSummary("monthly");
}

/* ---------- 初始化 ---------- */
async function init() {
  document.getElementById("updated").textContent = "更新于 " + new Date().toLocaleString("zh-CN");

  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab))
  );
  document.getElementById("refresh").addEventListener("click", () => location.reload());
  document.getElementById("search").addEventListener("input", () => {
    if (currentParsed.length) {
      const active = document.querySelector(".day-item.active");
      selectDay(currentParsed[active ? +active.dataset.i : 0]);
    }
  });

  const sel = document.getElementById("month-select");
  try {
    const months = await loadMonths();
    if (!months.length) {
      sel.innerHTML = `<option>暂无月份</option>`;
      document.getElementById("timeline").innerHTML = `<p class="hint">归档目录暂无月份数据。</p>`;
      return;
    }
    sel.innerHTML = months.map((m) => `<option value="${esc(m)}">${esc(m)}</option>`).join("");
    sel.addEventListener("change", () => selectMonth(sel.value));
    await selectMonth(months[0]);
  } catch (e) {
    sel.innerHTML = `<option>加载失败</option>`;
    document.getElementById("timeline").innerHTML = `<p class="error">${esc(e.message)}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", init);
