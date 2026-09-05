#!/usr/bin/env python3
"""commercial-trend CLI.

Usage:
  python main.py --sample     # offline, deterministic (used by CI)
  python main.py --live       # hit APIs, cache to data/cache/ (resilient to network errors)
  python main.py --cached     # build panel from data/cache/ ONLY, no network, no sample
  python main.py --cached --report   # also write data/cache_report.{md,csv}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline import ingest, model, site


def main() -> None:
    ap = argparse.ArgumentParser(description="commercial-trend pipeline")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--sample", action="store_true",
                   help="deterministic synthetic data (default)")
    g.add_argument("--live", action="store_true",
                   help="fetch real data from public APIs (resilient; cache to data/cache/)")
    g.add_argument("--cached", action="store_true",
                   help="build panel from existing data/cache/ only — no network, no sample")
    ap.add_argument("--report", action="store_true",
                    help="write data/cache_report.{md,csv} (descriptive stats + coverage)")
    ap.add_argument("--out", default="dist", help="output dir for the site")
    ap.add_argument("--save-panel", default="",
                    help="optional path to dump the panel JSON")
    args = ap.parse_args()

    mode = "live" if args.live else ("cached" if args.cached else "sample")
    print(f"[main] mode={mode}")
    panel = ingest.load_panel(mode)

    if args.report:
        from pipeline import analyze
        coverage = ingest.cache_coverage()
        analyze.write_report(panel, coverage)
        if mode == "cached" and not args.save_panel:
            # report-only run on cache: stop here
            print("[main] report written; skipping modeling (use --cached without --report to build the site)")
            return

    if args.save_panel:
        Path(args.save_panel).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save_panel).write_text(json.dumps(panel))
        print(f"[main] panel -> {args.save_panel}")

    print("[main] building dataset (features + labels)")
    samples = model.build_dataset(panel)
    print(f"[main] {len(samples)} samples")

    print("[main] walk-forward evaluation")
    evaluation = model.walk_forward_eval(samples)
    for name, m in evaluation.items():
        print(f"  {name:12s} {m}")

    print("[main] ranking fields")
    ranking = model.current_ranking(panel)

    out = site.render_site(panel, ranking, evaluation, mode, out_dir=args.out)
    print(f"[main] site -> {out}")


if __name__ == "__main__":
    main()
