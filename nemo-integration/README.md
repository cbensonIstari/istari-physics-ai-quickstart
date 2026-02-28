# NeMo Integration (Scaffold)

This module scaffolds an Istari function:

- `@istari:train_nemo_surrogate`

It is designed for first-time setup and smoke testing of the Istari integration path before a full GPU PhysicsNeMo trainer is wired in.

## Platform Note (2026-02)

Current `stari module lint` validation accepts OS values:
- `Ubuntu 24.04`, `Ubuntu 22.04`, `Ubuntu 20.04`
- `RHEL 9`, `RHEL 8`
- `Windows 10`, `Windows 11`, `Windows Server 2019`, `Windows Server 2022`

Because of this, this manifest is published with `Ubuntu 22.04` support.
You can still run local smoke tests on macOS via `scripts/test.sh`, but production Istari job routing should target a Linux agent.

## What This Scaffold Does

- Accepts a model file (`.csv` or `.json`) as training data input.
- Accepts `dataset_job_id` and `training_config` as parameters.
- Runs a lightweight baseline surrogate fit (ridge regression) that works on macOS/CPU.
- Produces three Istari artifacts:
  - `metrics.json`
  - `model_checkpoint.npz`
  - `training_report.md`

## What This Scaffold Does Not Do (Yet)

- It does **not** run full PhysicsNeMo GPU training.
- If `training_config.backend` is set to `"physicsnemo"`, it exits with a clear not-implemented error.

## Why This Is Useful

It unblocks integration work:

1. Module packaging and agent loading
2. Function publication in tenant
3. SDK job submission and artifact lineage

Then you can replace `src/train_nemo_surrogate.py` with your production trainer implementation.

## Quickstart

From module root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/install.sh
```

Restart agent, then verify in logs:

```bash
grep "Adding module" ~/Library/Application\ Support/istari_agent/istari_agent.log | tail -n 20
```

Publish:

```bash
stari module lint module_manifest.json
stari client publish module_manifest.json
stari client list functions --os | rg train_nemo_surrogate
```

## Install Location

- macOS local test: `~/Library/Application Support/istari_agent/istari_modules/nemo/`
- Linux production agent: `/opt/local/istari_agent/istari_modules/nemo/`

Do not nest under `@istari/` subdirectories.
