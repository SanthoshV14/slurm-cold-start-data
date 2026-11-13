"""Recompute the paper's phase table (Table III) from data/timelines.csv.

Usage:  python3 analysis/paper_tables.py [path/to/timelines.csv]

Standard library only. Medians are exact. Confidence intervals use a 95% percentile
bootstrap with 2000 resamples (seed 0); for multi-node cells they resample whole jobs
(cluster bootstrap), because nodes launched for the same job are not independent.
The authoritative intervals are in data/phase_ci.csv; intervals from this script can
differ from them in the second decimal because of the resampling implementation.

Column mapping (paper boundary -> CSV column):
  t0 -> t0, t1 -> t_alloc, t2 -> t1, t3 -> t2, t4 -> t3, t5 -> t4, t6 -> t5, t7 -> t7
"""
import csv
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "timelines.csv")
N_BOOT, SEED = 2000, 0

# (label, start column, end column), in paper order
PHASES = [
    ("Scheduling (t0-t1)", "t0", "t_alloc"),
    ("Power-saving wait (t1-t2)", "t_alloc", "t1"),
    ("Resume program + CreateFleet (t2-t3)", "t1", "t2"),
    ("Instance launch (t3-t4)", "t2", "t3"),
    ("OS boot (t4-t5)", "t3", "t4"),
    ("Configuration + registration (t5-t6)", "t4", "t5"),
    ("Registration to job start (t6-t7)", "t5", "t7"),
    ("Total (t0-t7)", "t0", "t7"),
]


def ci(groups):
    """Percentile CI of the median, resampling groups (jobs) with replacement."""
    rnd = random.Random(SEED)
    meds = sorted(statistics.median([v for g in (rnd.choice(groups) for _ in groups) for v in g])
                  for _ in range(N_BOOT))
    return meds[int(0.025 * N_BOOT)], meds[int(0.975 * N_BOOT) - 1]


def main():
    rows = list(csv.DictReader(open(PATH)))
    for cell in ["pilot-c7i-1n", "pilot-c7i-4n", "warm-c7i-1n"]:
        R = [r for r in rows if r["cell"] == cell]
        print(f"\n{cell}: {len({r['job_id'] for r in R})} jobs, {len(R)} timelines")
        if cell.startswith("warm"):
            v = [float(r["t7"]) - float(r["t0"]) for r in R]
            print(f"  total median {statistics.median(v):.2f} s (range {min(v):.2f}-{max(v):.2f})")
            continue
        total_med = statistics.median({r["job_id"]: float(r["t7"]) - float(r["t0"]) for r in R}.values())
        for label, a, b in PHASES:
            jobs = {}
            for r in R:
                if r[a] and r[b]:
                    jobs.setdefault(r["job_id"], []).append(float(r[b]) - float(r[a]))
            per_job_constant = label.startswith(("Scheduling", "Total"))
            groups = [[g[0]] if per_job_constant else g for g in jobs.values()]
            vals = [v for g in groups for v in g]
            med = statistics.median(vals)
            lo, hi = ci(groups)
            share = f"  {100 * med / total_med:5.1f}%"
            print(f"  {label:40s} {med:8.2f}  [{lo:.2f}, {hi:.2f}]{share}")


if __name__ == "__main__":
    main()
