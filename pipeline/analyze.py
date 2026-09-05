"""Statistical analysis of the cached panel (zero network, no sample).

Produces:
  - data/cache_report.md   coverage matrix + descriptive stats per field
  - data/cache_report.csv   machine-readable per-field stats table
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from . import ingest, signals
from .topics import FIELDS


def _stats(name: str, series: list[float]) -> dict:
    vals = [v for v in series if v is not None]
    if not vals:
        return {f"{name}_latest": None, f"{name}_mean": None,
                f"{name}_cagr": None, f"{name}_burst": None}
    latest = vals[-1]
    mean = statistics.mean(vals)
    cagr = signals.cagr(series)[-1]
    bf = signals.burst_features([float(v) for v in series])
    return {
        f"{name}_latest": round(latest, 1),
        f"{name}_mean": round(mean, 1),
        f"{name}_cagr": round(cagr, 3) if cagr is not None else None,
        f"{name}_burst": int(bf["in_burst_now"]),
    }


def write_report(panel: dict, coverage: dict, out_dir: str = "data") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    md = ["# Cache data report", "",
          f"years: {panel['years'][0]}–{panel['years'][-1]}",
          "mode: cached-only (no network, no synthetic sample)", ""]
    md.append("## Signal coverage (1 = cached, 0 = missing)")
    md.append("")
    md.append("| field | papers | repos (latest yr) | questions (latest yr) |")
    md.append("|---|---|---|---|")
    for k, f in panel["fields"].items():
        cov = coverage["fields"][k]
        p_cov = sum(cov["papers"]) and "full" or "—"
        r_cov = sum(cov["repos_new"])
        q_cov = sum(cov["questions"])
        md.append(f"| {f['label']} | {p_cov} | {r_cov}/{len(panel['years'])} yrs | "
                  f"{q_cov}/{len(panel['years'])} yrs |")
    md.append("")

    md.append("## Descriptive statistics")
    md.append("")
    md.append("| field | papers_latest | papers_CAGR | repos_latest | repos_CAGR | "
              "q_latest | q_CAGR | repos_burst | q_burst | CSI_latest |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    csi = {k: signals.commercial_index(f) for k, f in panel["fields"].items()}
    for k, f in panel["fields"].items():
        s = {}
        s.update(_stats("papers", f["papers"]))
        s.update(_stats("repos_new", f["repos_new"]))
        s.update(_stats("questions", f["questions"]))
        row = {
            "field": f["label"],
            **s,
            "csi_latest": round(csi[k][-1], 3),
        }
        rows.append(row)
        md.append(
            f"| {f['label']} "
            f"| {s['papers_latest']} | {s['papers_cagr']} "
            f"| {s['repos_new_latest']} | {s['repos_new_cagr']} "
            f"| {s['questions_latest']} | {s['questions_cagr']} "
            f"| {s['repos_new_burst']} | {s['questions_burst']} "
            f"| {round(csi[k][-1], 3)} |"
        )
    md.append("")
    md.append("## Cross-field correlation of CSI (latest 5 years)")
    md.append("")
    keys = list(panel["fields"].keys())
    import math
    def corr(a, b):
        n = len(a)
        if n < 2:
            return None
        ma, mb = sum(a) / n, sum(b) / n
        dx = math.sqrt(sum((x - ma) ** 2 for x in a))
        dy = math.sqrt(sum((y - mb) ** 2 for y in b))
        if dx == 0 or dy == 0:
            return None
        return round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (dx * dy), 2)
    md.append("| | " + " | ".join(panel["fields"][k]["label"][:10] for k in keys) + " |")
    for i, a in enumerate(keys):
        sa = csi[a][-5:]
        cells = " | ".join(
            str(corr(sa, csi[b][-5:])) for b in keys)
        md.append(f"| {panel['fields'][a]['label'][:10]} | {cells} |")
    md.append("")
    md.append("> Generated from disk cache only. Constant (all-zero) signals are "
              "dropped from CSI with weight renormalization, so a missing GitHub "
              "source does not silently zero a field.")

    (out / "cache_report.md").write_text("\n".join(md), encoding="utf-8")
    with (out / "cache_report.csv").open("w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"[analyze] -> {out/'cache_report.md'}")
    print(f"[analyze] -> {out/'cache_report.csv'}")
    return {"rows": len(rows), "md": str(out / "cache_report.md")}
