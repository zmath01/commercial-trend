"""Signal extraction: growth, burst detection, composite index, graph metrics.

All functions operate on plain lists/dicts aligned to panel["years"].
No heavy graph library: yearly topic graphs are small (<= few thousand nodes),
adjacency dicts are exact and dependency-free.
"""

from __future__ import annotations

import math

from .topics import CSI_WEIGHTS


# --------------------------------------------------------------------------- #
# Growth / momentum
# --------------------------------------------------------------------------- #

def yoy_growth(series: list[float]) -> list[float | None]:
    """Year-over-year growth; first element is None."""
    out: list[float | None] = [None]
    for a, b in zip(series, series[1:]):
        out.append((b - a) / a if a > 0 else None)
    return out


def cagr(series: list[float], window: int = 3) -> list[float | None]:
    """Trailing CAGR over `window` years; None where undefined."""
    out: list[float | None] = [None] * len(series)
    for i in range(window, len(series)):
        a, b = series[i - window], series[i]
        if a > 0 and b > 0:
            out[i] = (b / a) ** (1 / window) - 1
    return out


def zscore_cross_section(values_by_field: dict[str, float]) -> dict[str, float]:
    """Cross-sectional z-score across fields for a single year."""
    vals = list(values_by_field.values())
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / max(len(vals), 1)
    sd = math.sqrt(var) or 1.0
    return {k: (v - mu) / sd for k, v in values_by_field.items()}


# --------------------------------------------------------------------------- #
# Kleinberg burst detection (2-state, geometric/gamma cost)
# --------------------------------------------------------------------------- #

def kleinberg_bursts(series: list[float], gamma: float = 1.0,
                     s: float = 2.0) -> list[tuple[int, int]]:
    """2-state Kleinberg burst detection on an event-count series.

    States: 0 = quiet (rate r0 = mean), 1 = burst (rate r1 = s * r0).
    Transition cost: gamma * ln(n) for quiet->burst, 0 for burst->quiet.
    Emission: Poisson log-likelihood. Solved exactly by Viterbi DP.

    Returns list of (start_idx, end_idx) inclusive burst intervals.
    Reference: Kleinberg, KDD 2002.
    """
    n = len(series)
    if n == 0:
        return []
    total = sum(series)
    if total == 0:
        return []
    r0 = total / n
    r1 = s * r0
    trans_cost = gamma * math.log(n)

    def emit(x: float, rate: float) -> float:
        # negative Poisson log-likelihood (dropped constant cancels in DP)
        return rate - x * math.log(rate)

    # Viterbi
    INF = float("inf")
    cost = [[INF] * n for _ in range(2)]
    prev = [[0] * n for _ in range(2)]
    cost[0][0] = emit(series[0], r0)
    cost[1][0] = emit(series[0], r1) + trans_cost
    for t in range(1, n):
        x = series[t]
        # quiet
        stay = cost[0][t - 1]
        down = cost[1][t - 1]  # burst->quiet is free
        cost[0][t] = emit(x, r0) + min(stay, down)
        prev[0][t] = 0 if stay <= down else 1
        # burst
        up = cost[0][t - 1] + trans_cost
        stay1 = cost[1][t - 1]
        cost[1][t] = emit(x, r1) + min(up, stay1)
        prev[1][t] = 1 if stay1 <= up else 0

    # backtrace
    state = 0 if cost[0][n - 1] <= cost[1][n - 1] else 1
    states = [0] * n
    for t in range(n - 1, -1, -1):
        states[t] = state
        state = prev[state][t]

    bursts = []
    t = 0
    while t < n:
        if states[t] == 1:
            start = t
            while t < n and states[t] == 1:
                t += 1
            bursts.append((start, t - 1))
        else:
            t += 1
    return bursts


def burst_features(series: list[float]) -> dict:
    """Summarize burst structure of a series into scalar features."""
    bursts = kleinberg_bursts(series)
    n = len(series)
    in_burst_now = bool(bursts) and bursts[-1][1] == n - 1
    return {
        "n_bursts": len(bursts),
        "in_burst_now": in_burst_now,
        "last_burst_end": bursts[-1][1] if bursts else -1,
        "burst_years": [i for iv in bursts for i in range(iv[0], iv[1] + 1)],
    }


# --------------------------------------------------------------------------- #
# Commercial Signal Index (CSI)
# --------------------------------------------------------------------------- #

def minmax_norm(series: list[float]) -> list[float]:
    lo, hi = min(series), max(series)
    if hi == lo:
        return [0.0] * len(series)
    return [(v - lo) / (hi - lo) for v in series]


def commercial_index(field: dict) -> list[float]:
    """CSI per year for one field: weighted sum of per-year-normalized signals.

    Normalization is per-signal across years (temporal profile), which keeps
    the index interpretable as 'where in its own history is this field'.
    Signals that are constant (e.g. all-zero because the source was
    unreachable / uncached) are dropped and the remaining weights are
    renormalized — so a missing data source never silently zeroes a field.
    """
    n = len(field["papers"])
    csi = [0.0] * n
    active_w = 0.0
    for sig, w in CSI_WEIGHTS.items():
        series = field[sig]
        if min(series) == max(series):
            continue  # constant signal -> no information, skip
        norm = minmax_norm(series)
        csi = [a + w * b for a, b in zip(csi, norm)]
        active_w += w
    if active_w == 0:
        return [0.0] * n
    return [v / active_w for v in csi]


# --------------------------------------------------------------------------- #
# Topic co-occurrence graph + link-prediction baselines
# --------------------------------------------------------------------------- #

class TopicGraph:
    """Adjacency-dict graph. Nodes = field keys; edge weight = coupling strength.

    In live mode you'd build edges from papers sharing OpenAlex topics.
    Here we derive coupling from signal correlation so the sample mode also
    produces a meaningful graph.
    """

    def __init__(self) -> None:
        self.adj: dict[str, dict[str, float]] = {}

    def add_edge(self, a: str, b: str, w: float) -> None:
        if a == b:
            return
        self.adj.setdefault(a, {})[b] = w
        self.adj.setdefault(b, {})[a] = w

    def neighbors(self, u: str) -> dict[str, float]:
        return self.adj.get(u, {})

    def common_neighbors(self, a: str, b: str) -> float:
        na, nb = set(self.neighbors(a)), set(self.neighbors(b))
        return float(len(na & nb))

    def jaccard(self, a: str, b: str) -> float:
        na, nb = set(self.neighbors(a)), set(self.neighbors(b))
        union = len(na | nb)
        return len(na & nb) / union if union else 0.0

    def adamic_adar(self, a: str, b: str) -> float:
        na, nb = set(self.neighbors(a)), set(self.neighbors(b))
        score = 0.0
        for v in na & nb:
            deg = max(len(self.neighbors(v)), 2)
            score += 1.0 / math.log(deg)
        return score

    def preferential_attachment(self, a: str, b: str) -> float:
        return float(len(self.neighbors(a)) * len(self.neighbors(b)))

    def effective_conductance_2hop(self, a: str, b: str) -> float:
        """Two-hop effective conductance G(a,b) via common neighbors.

        G = sum over common neighbors v of the parallel-path conductance
        (w_av * w_vb) / (w_av + w_vb)  -- series resistances add, parallel
        conductances add. This is the metric used by the reference project,
        included here strictly as a *baseline* for honest comparison.
        """
        na, nb = self.neighbors(a), self.neighbors(b)
        g = 0.0
        for v in set(na) & set(nb):
            w1, w2 = na[v], nb[v]
            if w1 + w2 > 0:
                g += (w1 * w2) / (w1 + w2)
        return g


def build_coupling_graph(panel: dict, year_idx: int,
                         lookback: int = 5) -> TopicGraph:
    """Edge weight = correlation of paper-growth profiles over a trailing window.

    A pragmatic stand-in for true co-occurrence: fields whose research output
    moves together are coupled. Deterministic and cheap.
    """
    g = TopicGraph()
    keys = list(panel["fields"].keys())
    lo = max(0, year_idx - lookback + 1)

    def profile(k: str) -> list[float]:
        return panel["fields"][k]["papers"][lo:year_idx + 1]

    def corr(x: list[float], y: list[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mx, my = sum(x) / n, sum(y) / n
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        dx = math.sqrt(sum((a - mx) ** 2 for a in x))
        dy = math.sqrt(sum((b - my) ** 2 for b in y))
        return num / (dx * dy) if dx > 0 and dy > 0 else 0.0

    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            w = corr(profile(a), profile(b))
            if w > 0.3:  # threshold: only keep meaningful coupling
                g.add_edge(a, b, w)
    return g
