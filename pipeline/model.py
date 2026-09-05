"""Prediction model with honest, leak-free evaluation.

Task: predict whether a field's Commercial Signal Index will rise by more
than the cross-sectional median over horizon H years.

Discipline (per THEORY.md):
  * walk-forward temporal splits — NEVER random splits
  * report ROC-AUC / PR-AUC / Brier for the full model AND baselines:
      - persistence ("next delta = last delta")
      - global prior (class frequency)
      - graph-only model (co-occurrence heuristics incl. the reference
        project's effective conductance) — the increment over THIS baseline
        is the honest test of whether multi-source signals add value.
"""

from __future__ import annotations

import math

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import signals

HORIZON = 2
WARMUP = 3  # need this many years before features are defined

FEATURE_NAMES = [
    "papers_cagr", "repos_cagr", "questions_cagr",
    "repos_z", "questions_z",
    "repos_in_burst", "questions_in_burst",
    "csi_now", "csi_slope",
    "graph_degree", "graph_aa_max", "graph_conductance_max",
]

GRAPH_ONLY = ["graph_degree", "graph_aa_max", "graph_conductance_max"]


def build_dataset(panel: dict) -> list[dict]:
    """One sample per (field, prediction-year) where label is computable."""
    years = panel["years"]
    n = len(years)
    fields = panel["fields"]
    csi = {k: signals.commercial_index(f) for k, f in fields.items()}

    # label threshold: median of all realized CSI deltas
    deltas = [csi[k][i + HORIZON] - csi[k][i]
              for k in fields for i in range(n - HORIZON)]
    theta = float(np.median(deltas))

    samples = []
    for i in range(WARMUP, n - HORIZON):
        g = signals.build_coupling_graph(panel, i)
        repos_z = signals.zscore_cross_section(
            {k: fields[k]["repos_new"][i] for k in fields})
        dls_z = signals.zscore_cross_section(
            {k: fields[k]["questions"][i] for k in fields})

        for k in fields:
            f = fields[k]
            papers_cagr = signals.cagr(f["papers"])[i]
            repos_cagr = signals.cagr(f["repos_new"])[i]
            qs_cagr = signals.cagr(f["questions"])[i]
            if papers_cagr is None or repos_cagr is None or qs_cagr is None:
                continue

            bf_repos = signals.burst_features(f["repos_new"][:i + 1])
            bf_qs = signals.burst_features(f["questions"][:i + 1])
            slope = csi[k][i] - csi[k][i - 1]

            nbrs = g.neighbors(k)
            deg = float(len(nbrs))
            aa_max = max((g.adamic_adar(k, o) for o in nbrs), default=0.0)
            g_max = max((g.effective_conductance_2hop(k, o) for o in nbrs),
                        default=0.0)

            label = int(csi[k][i + HORIZON] - csi[k][i] > theta)
            samples.append({
                "field": k, "year_idx": i, "year": years[i],
                "label": label,
                "x": [papers_cagr, repos_cagr, qs_cagr,
                      repos_z[k], dls_z[k],
                      float(bf_repos["in_burst_now"]),
                      float(bf_qs["in_burst_now"]),
                      csi[k][i], slope,
                      deg, aa_max, g_max],
            })
    return samples


def _metrics(y_true: list[int], p: list[float]) -> dict:
    out = {"n": len(y_true), "positives": sum(y_true)}
    if len(set(y_true)) < 2:
        out.update(roc_auc=None, pr_auc=None, brier=None)
        return out
    out["roc_auc"] = round(float(roc_auc_score(y_true, p)), 3)
    out["pr_auc"] = round(float(average_precision_score(y_true, p)), 3)
    out["brier"] = round(float(brier_score_loss(y_true, p)), 3)
    return out


def walk_forward_eval(samples: list[dict]) -> dict:
    """Train on all samples with year < Y, predict year Y; roll forward."""
    years = sorted({s["year"] for s in samples})
    if len(years) < 2:
        return {"error": "not enough years for walk-forward"}

    idx_graph = [FEATURE_NAMES.index(n) for n in GRAPH_ONLY]
    results = {"full": [], "graph_only": [], "persistence": [], "prior": []}
    truths: list[int] = []

    for cutoff in years[1:]:
        train = [s for s in samples if s["year"] < cutoff]
        test = [s for s in samples if s["year"] == cutoff]
        if not train or not test:
            continue
        if len({s["label"] for s in train}) < 2:
            continue

        Xtr = np.array([s["x"] for s in train])
        ytr = np.array([s["label"] for s in train])
        Xte = np.array([s["x"] for s in test])
        yte = [s["label"] for s in test]

        # Standardized, strongly regularized LR: sample size is small
        # (field x year), so we trade variance for robustness on purpose.
        clf = make_pipeline(StandardScaler(),
                            LogisticRegression(max_iter=2000, C=0.1))
        clf.fit(Xtr, ytr)
        p_full = clf.predict_proba(Xte)[:, 1].tolist()

        clf_g = make_pipeline(StandardScaler(),
                              LogisticRegression(max_iter=2000, C=0.1))
        clf_g.fit(Xtr[:, idx_graph], ytr)
        p_graph = clf_g.predict_proba(Xte[:, idx_graph])[:, 1].tolist()

        prior = float(ytr.mean())
        p_prior = [prior] * len(test)

        # persistence: use csi_slope (FEATURE index 8) as probability-ish score
        i_slope = FEATURE_NAMES.index("csi_slope")
        raw = [s["x"][i_slope] for s in test]
        lo, hi = min(raw + [0.0]), max(raw + [1e-9])
        p_pers = [(r - lo) / (hi - lo + 1e-12) for r in raw]

        results["full"].extend(p_full)
        results["graph_only"].extend(p_graph)
        results["persistence"].extend(p_pers)
        results["prior"].extend(p_prior)
        truths.extend(yte)

    return {name: _metrics(truths, preds) for name, preds in results.items()}


def current_ranking(panel: dict) -> list[dict]:
    """Rank fields by latest CSI + momentum + burst status for the dashboard."""
    years = panel["years"]
    n = len(years)
    i = n - 1
    g = signals.build_coupling_graph(panel, i)
    csi = {k: signals.commercial_index(f) for k, f in panel["fields"].items()}

    rows = []
    for k, f in panel["fields"].items():
        repos_cagr = signals.cagr(f["repos_new"])[i] or 0.0
        qs_cagr = signals.cagr(f["questions"])[i] or 0.0
        bf_repos = signals.burst_features(f["repos_new"])
        bf_qs = signals.burst_features(f["questions"])
        rows.append({
            "key": k,
            "label": f["label"],
            "csi": round(csi[k][i], 3),
            "csi_series": [round(v, 3) for v in csi[k]],
            "repos_cagr": round(repos_cagr, 3),
            "questions_cagr": round(qs_cagr, 3),
            "repos_burst": bf_repos["in_burst_now"],
            "questions_burst": bf_qs["in_burst_now"],
            "graph_degree": len(g.neighbors(k)),
            "score": round(0.5 * csi[k][i] + 0.3 * repos_cagr
                           + 0.2 * qs_cagr, 4),
            "series": {
                "papers": f["papers"],
                "repos_new": f["repos_new"],
                "questions": f["questions"],
            },
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows
