# commercial-trend

> Reproducible monitoring of research / engineering signals associated with commercialization.
> This is a monitoring and forecasting experiment, **not a validated commercial-outcome predictor**.

[![Build & Deploy](https://github.com/zmath01/commercial-trend/actions/workflows/pages.yml/badge.svg)](https://github.com/zmath01/commercial-trend/actions/workflows/pages.yml)

**Live dashboard:** https://zmath01.github.io/commercial-trend/

## Current status — 2026-09-18

The repository contains a **live multi-source panel snapshot covering 2015–2025**. The committed `data/panel.json` currently has 8 populated monitoring fields:

- AI / Machine Learning
- Applied Mathematics
- Computer Science (general)
- Software Engineering
- Quantitative Finance
- Cryptocurrency / FinTech
- Quantum Computing / Cryptography
- Chips / GPU / Memory Hardware

The Chips field is currently all-zero and provides no usable evidence. The canonical taxonomy in `pipeline/topics.py` is broader (15 monitoring fields), but the current live panel is not populated for all of them.

### Current 2025 snapshot

| Field | Papers | New GitHub repos | Stack Overflow questions |
|---|---:|---:|---:|
| AI / Machine Learning | 11,468 | 1,705 | 528,242 |
| Applied Mathematics | 15,427 | 1,469 | 625,461 |
| Computer Science | 13,320 | 1,808 | 487,752 |
| Software Engineering | 14,499 | 2,005 | 501,158 |
| Quantitative Finance | 13,877 | 1,955 | 444,100 |
| Cryptocurrency / FinTech | 13,186 | 9,618 | 1,515,859 |
| Quantum Computing / Cryptography | 15,909 | 65,233 | 48,837,440 |
| Chips / GPU / Memory Hardware | 0 | 0 | 0 |

These are **activity proxies, not commercialization outcomes**. The very large recent Quantum and Stack Overflow values require source-level auditing of query semantics and current-year completeness before interpretation.

## What the code actually does

Each field is represented by annual **papers + newly created GitHub repositories + Stack Overflow questions**. The pipeline computes growth/CAGR, cross-sectional z-scores, Kleinberg burst indicators, a weighted Commercial Signal Index (CSI), graph heuristics including two-hop effective conductance, logistic regression, and walk-forward evaluation against graph-only, persistence, and prior baselines.

The current target is **not an independently observed commercialization event**. It is future CSI growth above the cross-sectional median. Thus the current model tests temporal predictive structure in the constructed monitoring signal; it does **not yet establish** prediction of patents, funding, hiring, company formation, revenue, market share, or another independent commercialization outcome.

## Current evaluation status

The methodology is implemented, but the evaluation is small:

- observations are field × year;
- yearly test slices contain only a handful of fields;
- ROC-AUC can reach 1.0 in a tiny test slice without being strong evidence;
- years with one class have undefined ROC-AUC/PR-AUC;
- graph features are heuristic features derived from the monitoring panel, not an independent commercialization network;
- the live snapshot has not yet been linked to an independent outcome dataset.

**Status:** reproducible monitoring pipeline + public live data snapshot; **not yet a demonstrated reliable commercialization forecast**.

## Research roadmap

1. Audit live 2025 source counts and query semantics.
2. Audit temporal alignment / leakage in the target.
3. Make graph construction explicitly time-indexed and empirically grounded.
4. Add one independent commercialization outcome dataset.
5. Evaluate current signals against that independent future outcome with expanding-window / walk-forward tests.
6. Only then increase model complexity or expand the taxonomy.

## GitHub Pages and Actions

The Pages workflow currently runs the live pipeline on push, monthly schedule, or manual dispatch. It uses `concurrency: cancel-in-progress: true`, so overlapping attempts can appear as **cancelled** when a newer run supersedes an older one.

A cancelled Action is an operational event, not a statistical result. Distinguish:

- **live pipeline output:** generated during the Action run;
- **committed snapshot:** `data/panel.json`;
- **Pages:** renders the generated dashboard artifact.

Check the run logs and committed panel before interpreting an Action result.

## Taxonomy

The canonical taxonomy in `pipeline/topics.py` defines 15 monitoring fields and intended arXiv categories. FinTech has no dedicated arXiv category and is monitored through OpenAlex/GitHub/Stack Overflow.

## Quickstart

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python main.py --sample
    .venv/bin/python main.py --live --save-panel data/panel.json
    .venv/bin/python main.py --cached --report

## Limitations

- The current target is a **proxy target**, not commercialization itself.
- OpenAlex/GitHub/Stack Overflow have different coverage, query semantics, and population biases.
- GitHub and Stack Overflow strongly favor software/engineering topics.
- Current-year data can be incomplete or unstable.
- CSI is a constructed index; source definitions or weights can change it.
- The sample is small at the field × year level.
- No causal claim is made.
- The current live panel does not populate the full canonical taxonomy.

## License

MIT — see [LICENSE](LICENSE).
