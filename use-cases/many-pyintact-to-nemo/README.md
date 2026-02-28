# Use Case: Can We Turn Many Simulations Into a Physics AI Model?

## Intent

A simulation engineer wants to run many structural simulations, train a surrogate model, and know quickly whether the model is good enough to use in design loops. The question is: **can we go from simulation campaign to trustworthy PhysicsNeMo model in one tracked workflow?**

## The Old Way

```text
Simulation Engineer         Data Engineer             ML Engineer
      |                         |                         |
      v                         |                         |
Run FEA cases manually          |                         |
      |                         |                         |
      +---- send files -------->|                         |
      |                         v                         |
      |                  Clean/reshape data              |
      |                         |                         |
      |<--- async fixes --------+                         |
      |                                                   v
      +------------------------ more handoffs ----------> Train model
                                                        |
                                                        v
                                                  Offline report
```

**Problems:** file handoffs, weak provenance, delayed failure detection, and no shared record of which simulation data trained which model revision.

## The New Way (with Istari)

```text
+--- Outer Dev Loop: Istari -- version - lineage - compare -----------------------------+
|                                                                                       |
|  +- Inner Dev Loop 1 --------+  +- Inner Dev Loop 2 --------+  +- Inner Dev Loop 3 -+ |
|  | PyIntact: Sim Campaign    |  | Dataset: Build Training   |  | PhysicsNeMo: Train  | |
|  | (Simulation Engineer)     |  | Set (Data/ML Engineer)    |  | Surrogate (ML Eng)  | |
|  +-------------+-------------+  +-------------+-------------+  +-------------+--------+ |
|                |                              |                              |          |
|                v                              v                              v          |
+-----------------------------------------------------------------------------------------+
| Outer-loop gates in Istari: throughput <-> data quality <-> model quality              |
| --> Readiness report: PASS / FAIL per gate                                              |
+-----------------------------------------------------------------------------------------+
```

Everyone works in parallel. Istari tracks the full lineage from campaign spec to surrogate model.

## Tools Used

| Tool | Role |
|------|------|
| **Istari Platform** | Outer dev loop: job orchestration, artifact versioning, lineage, and model promotion |
| **PyIntact** (`@istari:run_pyintact_simulation`) | Inner dev loop 1: structural simulation sweeps |
| **Dataset assembly** (`@istari:assemble_dataset`) | Inner dev loop 2: convert sim outputs to ML-ready tensors |
| **PhysicsNeMo** (`@istari:train_nemo_surrogate`) | Inner dev loop 3: train physics AI surrogate |
| **campaign_checks.py** | Produces a pass/fail report on campaign quality and model readiness |

## Milestones

### Milestone 1: Campaign runs in Istari

Submit parameter sweeps as many PyIntact jobs and track case outcomes in one manifest.

### Milestone 2: Dataset assembly is validated

Confirm enough successful cases and schema validity before training.

### Milestone 3: First surrogate is trained

Launch PhysicsNeMo training and capture validation metrics in Istari.

### Milestone 4: Model readiness decision

Run quality checks and decide whether to promote the surrogate for downstream usage.

## K-Script

| Step | Interaction / Process | Unobservable Actions or Assumptions |
|------|------------------------|-------------------------------------|
| 1 | Engineer fills `campaign_spec.json` with geometry IDs and parameter grid | IDs point to existing models in Istari |
| 2 | Engineer runs dry-run submit script | Payload shape is validated before any jobs are created |
| 3 | Engineer submits full campaign | Script creates many `@istari:run_pyintact_simulation` jobs |
| 4 | Istari agents process jobs in parallel | Effective concurrency depends on agent capacity and licenses |
| 5 | Engineer polls statuses | Manifest updates to `succeeded` / `failed` / other terminal states |
| 6 | Engineer launches dataset assembly | Failed jobs are excluded; successful artifacts are normalized |
| 7 | Engineer launches PhysicsNeMo training | Dataset revision and training config are attached to job lineage |
| 8 | Team lead runs quality checks | Report compares campaign throughput and model metrics to thresholds |
| 9 | Team lead approves promotion (or requests rerun) | Decision is based on versioned artifacts, not ad hoc files |

## Expected Results

### Initial run (before campaign tuning)

| Check | Target | Actual | Status |
|------|--------|--------|--------|
| Successful simulations | >= 10 cases | 8 cases | FAIL |
| Failure rate | <= 20% | 33.3% | FAIL |
| Dataset samples ready | >= 10 | 8 | FAIL |
| Surrogate val normalized MAE | <= 0.08 | 0.14 | FAIL |
| Surrogate val R2 | >= 0.90 | 0.81 | FAIL |

### Tuned run (after grid cleanup + rerun)

| Check | Target | Actual | Status |
|------|--------|--------|--------|
| Successful simulations | >= 10 cases | 11 cases | PASS |
| Failure rate | <= 20% | 8.3% | PASS |
| Dataset samples ready | >= 10 | 11 | PASS |
| Surrogate val normalized MAE | <= 0.08 | 0.06 | PASS |
| Surrogate val R2 | >= 0.90 | 0.94 | PASS |

## Live Integration Evidence

A real single-case SDK run using `@istari:run_pyintact_simulation` was completed on **2026-02-28** and produced:

- `summary.json` (solve time + stress extrema)
- `results.vtu` (field output)
- `visualization.png` (quick visual check)

See full evidence and links:
- [`../../docs/validated-pyintact-run-2026-02-28.md`](../../docs/validated-pyintact-run-2026-02-28.md)

## Check Script

The quick checks live in [`campaign_checks.py`](campaign_checks.py):

```python
from campaign_checks import run_all_checks, format_report, load_json

manifest = load_json("example-output/campaign_jobs_final.json")
dataset = load_json("example-output/dataset_summary_final.json")
metrics = load_json("example-output/surrogate_metrics_final.json")

results = run_all_checks(manifest, dataset, metrics)
print(format_report(results))
```

## Example Files

### [`example-input/`](example-input/) — what goes in

| File | Milestone | Description |
|------|-----------|-------------|
| `campaign_spec.json` | 1 | Campaign sweep definition with parameter grid and geometry model IDs |
| `training_config.json` | 3 | PhysicsNeMo training hyperparameters |

### [`example-output/`](example-output/) — what comes out

| File | Milestone | Description |
|------|-----------|-------------|
| `campaign_jobs_initial.json` | 1 | Initial campaign manifest with many failed/timeout cases |
| `campaign_jobs_final.json` | 1 | Tuned campaign manifest with high completion rate |
| `dataset_summary_initial.json` | 2 | Initial dataset stats (insufficient sample count) |
| `dataset_summary_final.json` | 2 | Final dataset stats (ready for training) |
| `surrogate_metrics_initial.json` | 3 | First model validation metrics (below threshold) |
| `surrogate_metrics_final.json` | 3 | Improved model validation metrics |
| `quality_report_initial.md` | 4 | Initial quality decision report (not ready) |
| `quality_report_final.md` | 4 | Final quality decision report (ready) |

## Try It

- Notebook: [`run_campaign.ipynb`](run_campaign.ipynb)
- Check script: [`campaign_checks.py`](campaign_checks.py)
