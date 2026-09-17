"""Data ingestion: OpenAlex (research), GitHub (engineering),
StackOverflow (community adoption).

Two modes:
  --live    hit the real APIs (disk-cached, polite)
  --sample  generate a deterministic synthetic panel (offline, CI-safe)

The tracked fields and their canonical 23-category arXiv mapping live in
pipeline/topics.py.
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

import requests

from .topics import FIELDS

CACHE_DIR = Path("data/cache")
YEARS = list(range(2015, 2026))
UA = "commercial-trend/0.1 (mailto:commercial-trend@users.noreply.github.com)"


def _cache_path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
    return CACHE_DIR / f"{safe}.json"


def _get_json(url: str, params: dict | None = None, cache_key: str | None = None,
              headers: dict | None = None, retries: int = 3) -> dict:
    if cache_key:
        p = _cache_path(cache_key)
        if p.exists():
            return json.loads(p.read_text())
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    for attempt in range(retries):
        resp = requests.get(url, params=params, headers=h, timeout=30)
        if resp.status_code in (403, 429) and attempt < retries - 1:
            wait = int(resp.headers.get("Retry-After", 30 * (attempt + 1)))
            print(f"[ingest] rate-limited, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        if cache_key:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _cache_path(cache_key).write_text(json.dumps(data))
        time.sleep(0.4)
        return data
    raise RuntimeError(f"failed after {retries} attempts: {url}")


def _read_cache(cache_key: str) -> dict | None:
    p = _cache_path(cache_key)
    return json.loads(p.read_text()) if p.exists() else None


def openalex_yearly(query: str) -> list[int]:
    """Papers per year aligned to YEARS (OpenAlex /works group_by)."""
    ck = f"openalex_{query}"
    cached = _read_cache(ck)
    if cached is not None:
        data = cached
    else:
        try:
            data = _get_json(
                "https://api.openalex.org/works",
                params={
                    "search": query,
                    "filter": f"from_publication_date:{YEARS[0]}-01-01,to_publication_date:{YEARS[-1]}-12-31",
                    "group_by": "publication_year",
                },
                cache_key=ck,
            )
        except requests.exceptions.RequestException as e:
            print(f"[ingest] openalex {query}: network error -> zeros ({type(e).__name__})")
            return [0] * len(YEARS)
    papers = {y: 0 for y in YEARS}
    for bucket in data.get("group_by", []):
        try:
            y = int(bucket["key"])
        except (KeyError, ValueError):
            continue
        if y in papers:
            papers[y] = bucket.get("count", 0)
    return [papers[y] for y in YEARS]


def github_repos_new(keyword: str) -> list[int]:
    """New repos per year for a GitHub topic keyword."""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else None
    out = []
    for y in YEARS:
        ck = f"github_{keyword}_{y}"
        cached = _read_cache(ck)
        if cached is not None:
            out.append(cached.get("total_count", 0))
            continue
        try:
            data = _get_json(
                "https://api.github.com/search/repositories",
                params={"q": f"topic:{keyword} created:{y}-01-01..{y}-12-31", "per_page": 1},
                cache_key=ck,
                headers=headers,
            )
            out.append(data.get("total_count", 0))
        except requests.exceptions.RequestException as e:
            print(f"[ingest] github {keyword} {y}: network error -> 0 ({type(e).__name__})")
            out.append(0)
    return out


def _year_epoch(y: int, end: bool = False) -> int:
    import calendar
    import datetime as dt
    if end:
        return calendar.timegm(dt.datetime(y, 12, 31, 23, 59, 59).timetuple())
    return calendar.timegm(dt.datetime(y, 1, 1).timetuple())


def so_questions_yearly(tag: str) -> list[int]:
    """Total questions per year for a StackOverflow tag."""
    out = []
    for y in YEARS:
        ck = f"so_{tag}_{y}"
        cached = _read_cache(ck)
        if cached is not None:
            out.append(cached.get("total", 0))
            continue
        try:
            data = _get_json(
                "https://api.stackexchange.com/2.3/questions",
                params={"site": "stackoverflow", "tagged": tag,
                        "fromdate": _year_epoch(y), "todate": _year_epoch(y, True),
                        "filter": "total"},
                cache_key=ck,
            )
            out.append(data.get("total", 0))
        except requests.exceptions.RequestException as e:
            print(f"[ingest] so {tag} {y}: network error -> 0 ({type(e).__name__})")
            out.append(0)
    return out


def fetch_live_panel() -> dict:
    panel = {"years": YEARS, "fields": {}}
    for key, spec in FIELDS.items():
        print(f"[ingest] {spec['label']}")
        papers = [0] * len(YEARS)
        for q in spec["openalex_queries"]:
            p = openalex_yearly(q)
            papers = [a + b for a, b in zip(papers, p)]
        repos = [0] * len(YEARS)
        for kw in spec["github_keywords"]:
            r = github_repos_new(kw)
            repos = [a + b for a, b in zip(repos, r)]
        questions = [0] * len(YEARS)
        for tag in spec["so_tags"]:
            qs = so_questions_yearly(tag)
            questions = [a + b for a, b in zip(questions, qs)]
        panel["fields"][key] = {
            "label": spec["label"], "papers": papers,
            "repos_new": repos, "questions": questions,
        }
    return panel


def make_sample_panel(seed: int = 42) -> dict:
    """Deterministic synthetic panel; never presented as real data."""
    rng = random.Random(seed)
    n = len(YEARS)
    panel = {"years": YEARS, "fields": {}}

    def growth_series(base: float, rate: float, noise: float = 0.08) -> list[int]:
        out, v = [], base
        for _ in range(n):
            v *= rate * (1 + rng.uniform(-noise, noise))
            out.append(max(1, int(v)))
        return out

    def late_accel(base: float, rate: float, kick_year: int, kick: float) -> list[int]:
        out, v = [], base
        for y in YEARS:
            r = rate * (kick if y >= kick_year else 1.0)
            v *= r * (1 + rng.uniform(-0.06, 0.06))
            out.append(max(1, int(v)))
        return out

    def boom_bust(base: float, up: float, down: float, peak_year: int) -> list[int]:
        out, v = [], base
        for y in YEARS:
            r = up if y <= peak_year else down
            v *= r * (1 + rng.uniform(-0.07, 0.07))
            out.append(max(1, int(v)))
        return out

    for key, spec in FIELDS.items():
        papers = growth_series(5_000, 1.10)
        if key in ("quantum_computing", "chips_hardware"):
            repos = late_accel(200, 1.25, 2021, 1.9)
            dls = late_accel(50_000, 1.30, 2021, 2.2)
        elif key == "fintech":
            repos = boom_bust(500, 1.8, 0.75, 2021)
            dls = boom_bust(80_000, 1.9, 0.7, 2021)
        else:
            repos = growth_series(300, 1.18)
            dls = growth_series(60_000, 1.22)
        panel["fields"][key] = {
            "label": spec["label"], "papers": papers,
            "repos_new": repos, "questions": dls,
        }
    return panel


def build_panel_from_cache() -> dict:
    panel = {"years": YEARS, "fields": {}}
    for key, spec in FIELDS.items():
        papers = [0] * len(YEARS)
        for q in spec["openalex_queries"]:
            d = _read_cache(f"openalex_{q}")
            if d is None:
                continue
            by_year = {y: 0 for y in YEARS}
            for b in d.get("group_by", []):
                try:
                    y = int(b["key"])
                except (KeyError, ValueError):
                    continue
                if y in by_year:
                    by_year[y] = b.get("count", 0)
            papers = [a + b for a, b in zip(papers, [by_year[y] for y in YEARS])]
        repos = [0] * len(YEARS)
        for kw in spec["github_keywords"]:
            for i, y in enumerate(YEARS):
                d = _read_cache(f"github_{kw}_{y}")
                if d is not None:
                    repos[i] += d.get("total_count", 0)
        questions = [0] * len(YEARS)
        for tag in spec["so_tags"]:
            for i, y in enumerate(YEARS):
                d = _read_cache(f"so_{tag}_{y}")
                if d is not None:
                    questions[i] += d.get("total", 0)
        panel["fields"][key] = {
            "label": spec["label"], "papers": papers,
            "repos_new": repos, "questions": questions,
        }
    return panel


def cache_coverage() -> dict:
    cov = {"years": YEARS, "fields": {}}
    for key, spec in FIELDS.items():
        cell = {"papers": [], "repos_new": [], "questions": []}
        has_oa = any(_read_cache(f"openalex_{q}") is not None for q in spec["openalex_queries"])
        cell["papers"] = [int(has_oa)] * len(YEARS)
        cell["repos_new"] = [int(any(_read_cache(f"github_{kw}_{y}") is not None
                                      for kw in spec["github_keywords"])) for y in YEARS]
        cell["questions"] = [int(any(_read_cache(f"so_{tag}_{y}") is not None
                                       for tag in spec["so_tags"])) for y in YEARS]
        cov["fields"][key] = cell
    return cov


def load_panel(mode: str) -> dict:
    if mode == "live":
        return fetch_live_panel()
    if mode == "cached":
        return build_panel_from_cache()
    return make_sample_panel()
