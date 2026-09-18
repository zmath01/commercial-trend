"""Static site generator: renders dist/index.html (Chart.js, light theme).

No JS build step, no framework — one self-contained HTML file plus CDN.
The JSON payload is embedded so GitHub Pages needs nothing else.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Commercial Trend — 研究领域的商业化信号看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  :root { --ink:#1a2332; --muted:#5b6779; --line:#e3e8ef; --bg:#f7f9fc;
          --card:#ffffff; --accent:#2563eb; --hot:#dc2626; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:-apple-system,"Segoe UI","PingFang SC",
         "Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); }
  .wrap { max-width:1080px; margin:0 auto; padding:32px 20px 64px; }
  h1 { font-size:28px; margin:0 0 4px; }
  h2 { font-size:20px; margin:40px 0 12px; }
  .sub { color:var(--muted); font-size:14px; }
  .card { background:var(--card); border:1px solid var(--line);
          border-radius:12px; padding:20px; margin-top:16px; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; font-size:12px;
       text-transform:uppercase; letter-spacing:.04em; }
  .badge { display:inline-block; padding:1px 8px; border-radius:999px;
           font-size:12px; background:#fee2e2; color:var(--hot);
           font-weight:600; margin-left:6px; }
  .num { font-variant-numeric:tabular-nums; }
  .note { color:var(--muted); font-size:13px; line-height:1.7; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:800px){ .grid{grid-template-columns:1fr;} }
  footer { margin-top:48px; color:var(--muted); font-size:12px;
           border-top:1px solid var(--line); padding-top:16px; }
  code { background:#eef2f7; padding:1px 5px; border-radius:4px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Commercial Trend</h1>
  <div class="sub">研究 / 工程活动的商业化相关信号监测 · 数据更新时间 __STAMP__</div>
  <div class="card note">
    <b>Current status:</b> this dashboard is a live activity-signal snapshot, not an
    independently validated commercialization forecast. The current target is future
    CSI growth, and the latest panel covers 2015–2025. The latest mechanical ranking is
    dominated by the explosive recent repository / Stack Overflow growth of Quantum and
    Chips / Hardware. Source completeness and query semantics still require auditing.
  </div>

  <h2>当前排名（综合 CSI + 动量）</h2>
  <div class="card">
    <table id="ranking">
      <thead><tr>
        <th>#</th><th>领域</th><th>CSI</th><th>仓库 CAGR</th>
        <th>提问 CAGR</th><th>共现度</th><th>状态</th>
      </tr></thead>
      <tbody></tbody>
    </table>
    <p class="note">CSI = 商业化信号综合指数（0–1，逐年归一化的 GitHub 新建仓库数、
      StackOverflow 提问量、论文数的加权和，权重见 README）。<span class="badge">BURST</span>
      表示 Kleinberg 突发检测判定该信号正处于统计显著的爆发期。</p>
  </div>

  <h2>商业化信号指数（CSI）走势</h2>
  <div class="card"><canvas id="csiChart" height="110"></canvas></div>

  <div class="grid">
    <div>
      <h2>新建 GitHub 仓库</h2>
      <div class="card"><canvas id="repoChart" height="150"></canvas></div>
    </div>
    <div>
      <h2>StackOverflow 提问量</h2>
      <div class="card"><canvas id="dlChart" height="150"></canvas></div>
    </div>
  </div>

  <h2>模型评估（walk-forward 时间切分，无泄漏）</h2>
  <div class="card">
    <table id="eval">
      <thead><tr><th>模型</th><th>样本</th><th>ROC-AUC</th>
        <th>PR-AUC</th><th>Brier ↓</th></tr></thead>
      <tbody></tbody>
    </table>
    <p class="note">任务：预测某领域 CSI 在未来 __HORIZON__ 年的增长是否超过横截面中位数。
      这不是独立的商业化结果标签。<code>graph_only</code> 基线仅使用共现图启发式
      （含两跳有效电导）；full 相对它的增量才是多源信号价值的诚实检验。
      小规模 field×year 测试集上的高 AUC 不应被视为稳定预测能力。</p>
  </div>

  <h2>方法论</h2>
  <div class="card note">
    与"短语共现 + 电导"类项目的区别：① 当前预测目标是<b>构造的 CSI 增长代理</b>而非真实商业化事件；
    ② 多源数据三角验证；③ 强基线对比（持续性 / 先验 / 纯共现图）；
    ④ walk-forward 时间验证。详见
    <a href="https://github.com/zmath01/commercial-trend">仓库</a> 的
    <code>docs/THEORY.md</code>。
  </div>

  <footer>
    Built by CI · <a href="https://github.com/zmath01/commercial-trend">zmath01/commercial-trend</a>
    · 数据模式：__MODE__ · current target = future CSI growth proxy
  </footer>
</div>

<script>
const PAYLOAD = __PAYLOAD__;
const years = PAYLOAD.years;
const palette = ["#2563eb","#dc2626","#059669","#d97706","#7c3aed",
                 "#0891b2","#be185d","#65a30d"];

function mkChart(id, seriesFn, yLabel) {
  const ctx = document.getElementById(id);
  new Chart(ctx, {
    type: "line",
    data: {
      labels: years,
      datasets: PAYLOAD.ranking.map((r, i) => ({
        label: r.label,
        data: seriesFn(r),
        borderColor: palette[i % palette.length],
        backgroundColor: palette[i % palette.length],
        borderWidth: 2, pointRadius: 2, tension: 0.25,
      })),
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom", labels: { boxWidth: 12 } } },
      scales: { y: { title: { display: true, text: yLabel } } },
    },
  });
}

mkChart("csiChart", r => r.csi_series, "CSI (0-1)");
mkChart("repoChart", r => r.series.repos_new, "new repos / yr");
mkChart("dlChart", r => r.series.questions, "questions / yr");

const tbody = document.querySelector("#ranking tbody");
PAYLOAD.ranking.forEach((r, i) => {
  const badges = (r.repos_burst ? '<span class="badge">BURST·repo</span>' : "")
               + (r.questions_burst ? '<span class="badge">BURST·so</span>' : "");
  const tr = document.createElement("tr");
  tr.innerHTML = `<td class="num">${i + 1}</td><td>${r.label}</td>
    <td class="num">${r.csi.toFixed(3)}</td>
    <td class="num">${(r.repos_cagr * 100).toFixed(1)}%</td>
    <td class="num">${(r.questions_cagr * 100).toFixed(1)}%</td>
    <td class="num">${r.graph_degree}</td><td>${badges}</td>`;
  tbody.appendChild(tr);
});

const etbody = document.querySelector("#eval tbody");
const names = { full: "full（多源信号）", graph_only: "graph_only（纯共现图基线）",
                persistence: "persistence（持续性基线）", prior: "prior（先验基线）" };
for (const [k, label] of Object.entries(names)) {
  const m = PAYLOAD.evaluation[k] || {};
  const fmt = v => (v === null || v === undefined) ? "—" : v;
  const tr = document.createElement("tr");
  tr.innerHTML = `<td>${label}</td><td class="num">${fmt(m.n)}</td>
    <td class="num">${fmt(m.roc_auc)}</td><td class="num">${fmt(m.pr_auc)}</td>
    <td class="num">${fmt(m.brier)}</td>`;
  etbody.appendChild(tr);
}
</script>
</body>
</html>
"""


def render_site(panel: dict, ranking: list[dict], evaluation: dict,
                mode: str, out_dir: str = "dist") -> Path:
    payload = {
        "years": panel["years"],
        "ranking": ranking,
        "evaluation": evaluation,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = (TEMPLATE
            .replace("__PAYLOAD__", json.dumps(payload))
            .replace("__STAMP__", stamp)
            .replace("__MODE__", mode)
            .replace("__HORIZON__", "2"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    return out / "index.html"
