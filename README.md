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

## Fast Pointers

- Quickstart use-case: [`use-cases/many-pyintact-to-nemo/README.md`](use-cases/many-pyintact-to-nemo/README.md)
- K-script: [`docs/k-script-many-pyintact-to-nemo.md`](docs/k-script-many-pyintact-to-nemo.md)
- Notebook: [`notebooks/pyintact_to_nemo_campaign.ipynb`](notebooks/pyintact_to_nemo_campaign.ipynb)
