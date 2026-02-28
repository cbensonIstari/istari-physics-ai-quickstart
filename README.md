# Quickstart: Build a Physics AI Model with Istari

This repository is a **quickstart guide** for creating a physics AI surrogate model by orchestrating:
1. Many PyIntact simulations in Istari
2. Dataset assembly from simulation outputs
3. PhysicsNeMo training as a tracked Istari job

It is modeled after the structure and workflow style of [`istari-digital-examples`](https://github.com/cbensonIstari/istari-digital-examples).

## What You Get

- A campaign spec format for batched simulation runs
- Python scripts to submit and poll many Istari jobs
- A launcher script for PhysicsNeMo training jobs
- A notebook for interactive execution
- A K-script for product/UX alignment

## Workflow Diagram (ASCII)

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

## 0) Prerequisites

- Python 3.10+
- Istari tenant + personal access token (PAT)
- Existing Istari function(s):
  - `@istari:run_pyintact_simulation`
  - `@istari:assemble_dataset`
  - `@istari:train_nemo_surrogate`
- Geometry models uploaded in Istari (body STL, load face STL, restraint face STL)

## 1) Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env`:

```dotenv
ISTARI_DIGITAL_REGISTRY_URL=https://your-registry-url
ISTARI_DIGITAL_REGISTRY_AUTH_TOKEN=your-pat
```

## 2) Verify Istari Connectivity

```bash
python istari_client.py
python getting-started/01_discover_functions.py
```

## 3) Fill Campaign Spec

Edit:
- `use-cases/many-pyintact-to-nemo/campaign_spec.example.json`

Required IDs:
- `campaign_root_model_id`
- `geometry.body_model_id`
- `geometry.load_face_model_id`
- `geometry.restraint_face_model_id`

## 4) Dry Run the Campaign Payload

```bash
python pyintact/submit_campaign.py \
  --spec use-cases/many-pyintact-to-nemo/campaign_spec.example.json \
  --dry-run
```

This writes `campaign_jobs.json` with preview payloads.

## 5) Submit Many PyIntact Jobs

```bash
python pyintact/submit_campaign.py \
  --spec use-cases/many-pyintact-to-nemo/campaign_spec.example.json
```

## 6) Poll Campaign Completion

```bash
python pyintact/poll_campaign.py --manifest campaign_jobs.json
```

## 7) Assemble Dataset + Train PhysicsNeMo

- Run your dataset assembly job in Istari (`@istari:assemble_dataset`) and capture `dataset_job_id`.
- Launch training:

```bash
python nemo/launch_training.py \
  --campaign-root-model-id <campaign_root_model_id> \
  --dataset-job-id <dataset_job_id>
```

## 8) Track and Compare in Istari

- Compare model revisions
- Review lineage from campaign spec -> simulation cases -> dataset -> surrogate model
- Promote only when validation criteria are met

## 9) Validated Integration Run + Learnings

A full SDK run was validated on **2026-02-28** with concrete artifacts and metrics.

- System: [`89690e3c-f99d-426e-9cbf-98d0cf5f5653`](https://demo.istari.app/systems/89690e3c-f99d-426e-9cbf-98d0cf5f5653)
- Configuration: [`d26674dc-d6c0-44f8-bced-74fb38e806bc`](https://demo.istari.app/systems/89690e3c-f99d-426e-9cbf-98d0cf5f5653/config/d26674dc-d6c0-44f8-bced-74fb38e806bc)
- Job: `a21fa8e8-85bb-4301-b73b-e786555ad343` (`Completed`)
- Produced outputs:
  - `summary.json`
  - `results.vtu`
  - `visualization.png`
- Key metrics:
  - `solve_time_seconds=5.529`
  - `max_von_mises_stress=1002390.1692623853 Pa`
  - `min_von_mises_stress=663182.9699018181 Pa`

Full run record, artifact links, and SDK edge cases:
- [`docs/validated-pyintact-run-2026-02-28.md`](docs/validated-pyintact-run-2026-02-28.md)

Reusable rerun script:

```bash
export ISTARI_DIGITAL_REGISTRY_URL=https://fileservice-v2.demo.istari.app
export ISTARI_DIGITAL_REGISTRY_AUTH_TOKEN=<your-pat>
python scripts/istari_versioned_pyintact_rerun.py
```

## Fast Pointers

- Quickstart use-case: [`use-cases/many-pyintact-to-nemo/README.md`](use-cases/many-pyintact-to-nemo/README.md)
- K-script: [`docs/k-script-many-pyintact-to-nemo.md`](docs/k-script-many-pyintact-to-nemo.md)
- Notebook: [`use-cases/many-pyintact-to-nemo/run_campaign.ipynb`](use-cases/many-pyintact-to-nemo/run_campaign.ipynb)
- Validated run evidence: [`docs/validated-pyintact-run-2026-02-28.md`](docs/validated-pyintact-run-2026-02-28.md)
- First-time NeMo runbook: [`docs/first-nemo-in-istari.md`](docs/first-nemo-in-istari.md)
- NeMo module scaffold: [`nemo-integration/README.md`](nemo-integration/README.md)

## Use Cases

| Use Case | Question It Answers |
|----------|---------------------|
| [`many-pyintact-to-nemo`](use-cases/many-pyintact-to-nemo/) | Can we run many simulations and produce a promotable PhysicsNeMo model with clear pass/fail quality gates? |

Use-case assets:
- Notebook: [`use-cases/many-pyintact-to-nemo/run_campaign.ipynb`](use-cases/many-pyintact-to-nemo/run_campaign.ipynb)
- Check script: [`use-cases/many-pyintact-to-nemo/campaign_checks.py`](use-cases/many-pyintact-to-nemo/campaign_checks.py)
- Example input/output: [`use-cases/many-pyintact-to-nemo/example-input/`](use-cases/many-pyintact-to-nemo/example-input/) and [`use-cases/many-pyintact-to-nemo/example-output/`](use-cases/many-pyintact-to-nemo/example-output/)
