# Use Case: Many PyIntact Simulations -> PhysicsNeMo Model

This is the minimal end-to-end flow for building a first physics AI model with Istari.

## Goal

Train a surrogate model that predicts structural response fields from parameterized simulation inputs.

## Inputs You Need in Istari

- One root model for the campaign (`campaign_root_model_id`)
- 3 geometry models (STL): body, load face, restraint face
- Function availability:
  - `@istari:run_pyintact_simulation`
  - `@istari:assemble_dataset`
  - `@istari:train_nemo_surrogate`

## Step-by-Step

1. Edit `campaign_spec.example.json` with real model IDs.
2. Validate payload shape:

```bash
python pyintact/submit_campaign.py --spec use-cases/many-pyintact-to-nemo/campaign_spec.example.json --dry-run
```

3. Submit campaign:

```bash
python pyintact/submit_campaign.py --spec use-cases/many-pyintact-to-nemo/campaign_spec.example.json
```

4. Monitor:

```bash
python pyintact/poll_campaign.py --manifest campaign_jobs.json
```

5. Assemble dataset in Istari (`@istari:assemble_dataset`) and capture `dataset_job_id`.

6. Launch PhysicsNeMo training:

```bash
python nemo/launch_training.py \
  --campaign-root-model-id <campaign_root_model_id> \
  --dataset-job-id <dataset_job_id>
```

## Success Criteria for MVP

- At least 100 successful simulation runs
- Dataset assembly job completes with no schema/units mismatch
- Surrogate training converges and logs validation metrics in Istari
