# Slurm cloud cold-start timing data

Anonymized timing data and code for the paper
*"Measuring and Attributing Provisioning Delay in Elastic Cloud Slurm Clusters: An Empirical Case Study"*
(Vadivel, Rijhwani, Varakala).

The study measures how long a Slurm job waits for a new cloud node on AWS ParallelCluster 3.16.1
(Slurm 25.11.8, c7i.large, default Amazon Linux 2023 AMI `ami-05e09ce5fe655ed86`, us-west-2a),
and attributes that delay to eight timeline boundaries, `t0`–`t7`.

| Cell | Start type | Jobs | Nodes per job | Timelines | Dates (UTC) |
|---|---|---|---|---|---|
| `pilot-c7i-1n` | cold | 10 | 1 | 10 | 2026-09-19 21:34–23:02 |
| `pilot-c7i-4n` | cold | 10 | 4 | 40 | 2026-09-19 23:39 – 09-20 01:04 |
| `warm-c7i-1n` | warm | 5 | 1 | 5 | 2026-09-20 01:04–01:07 |

## Reproduce the paper's phase table

```
python3 analysis/paper_tables.py
```

Standard library only (Python 3.8+). It prints, for each cell, the median, 95% bootstrap CI and
share of the total for every phase in Table III of the paper.

## Contents

| Path | What it is |
|---|---|
| `data/timelines.csv` | One row per (job, node): every boundary as a Unix timestamp (UTC) plus the phase durations |
| `data/phase_ci.csv` | Per-phase median and p95 with 95% CIs (`unit=node`, plus job-resampled CIs; `unit=job` rows for multi-node cells) |
| `data/job_level_totals.csv` | One row per job: end-to-end latency |
| `data/run_counts.csv` | Attempted, completed, flagged, excluded and analyzed runs per cell |
| `data/cell_dates.csv` | UTC window, job IDs and driver parameters per cell |
| `data/additivity_check.csv` | Sum of phase medians vs. median total |
| `data/cookbook_d45.csv` | Cluster-configuration phase, pooled and per cell |
| `data/controller_match_rows.csv`, `data/controller_match_summary.json` | Cross-check of every cold-start timeline against `slurmctld.log` |
| `data/agent_files.csv` | Every node-agent file mapped to its timeline row or launching job |
| `data/facts.json` | How each boundary was measured, software versions, workload, warm-start procedure, `t0` source, clock synchronization |
| `data/scontrol_show_config_excerpt.txt`, `data/chronyc_tracking_headnode.txt` | Verbatim captures from the head node |
| `data/example-trace/` | One complete run (pilot-c7i-1n job 9): 135 time-ordered log lines and events from submission to instance termination |
| `analysis/paper_tables.py` | Recomputes the paper's phase table from `data/timelines.csv` |

## Boundary definitions and column names

The CSV columns use the measurement harness's names, which differ from the paper's numbering:

| Paper | Column | Event | Source |
|---|---|---|---|
| `t0` | `t0` | Job submitted/eligible (whole seconds, truncated) | `squeue` / `scontrol show job` |
| `t1` | `t_alloc` | Resources allocated | Poller (1 s) |
| `t2` | `t1` | Node enters POWERING_UP | Poller (1 s) |
| `t3` | `t2` | `CreateFleet` recorded | CloudTrail `eventTime` (1 s) |
| `t4` | `t3` | Instance `running` | EventBridge (1 s) |
| `t5` | `t4` | `cloud-final.service` starts (OS boot complete) | Node agent, systemd (≈1 s) |
| `t6` | `t5` | Node registered with controller | Poller (1 s) |
| `t7` | `t7` | Job RUNNING | Poller (1 s) |

Phase columns: `d_alloc1` = t1→t2 (paper), `d12` = t2→t3, `d23` = t3→t4, `d34` = t4→t5,
`d45` = t5→t6, `d57` = t6→t7, `d01` = t0→t2, `total` = t0→t7.

## Known caveats

- `t0` is Slurm's submit time truncated to whole seconds; it is 0.02–0.99 s (mean 0.53 s) earlier than
  the millisecond `slurmctld.log` submit line. Rows flagged `acct_synthesized_from_squeue` (pilot-c7i-1n)
  took it from `squeue`; the other cells from `scontrol show job`. No Slurm accounting database was used.
- CloudTrail and EventBridge timestamps have one-second resolution, so `d23` is 3 or 4 s.
- Warm-start rows reuse the launch timestamps of the node started for the last pilot-c7i-4n job
  (flagged `nonmonotonic`); only their `total` is meaningful.
- Compute-node clock offsets were not measured; see `data/facts.json` (`chrony`).

## Anonymization

EC2 instance IDs are replaced with consistent placeholders (`i-node001`, ...); the example trace
uses its own placeholders (`i-instanceNN`), independent of those in the tables. Account,
subnet, VPC, launch-template, fleet, request and hosted-zone IDs, private IPs, the IAM role suffix
and personal names are replaced in the trace. The public AMI ID, node names, cluster name,
instance type, availability zone, software versions and timestamps are kept. The mapping to real
identifiers was not saved.

## Measurement code

The measurement harness (poller, node agent, experiment driver and merge pipeline) is not part of
this release; it is available from the authors on request.

## License

Code (`analysis/`): MIT (`LICENSE`). Data (`data/`): CC BY 4.0 (`LICENSE-DATA.md`).
