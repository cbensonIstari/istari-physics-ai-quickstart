# First NeMo Training in Istari (Beginner Runbook)

This is the fastest path from "never trained NeMo before" to a runnable `@istari:train_nemo_surrogate` function in your Istari tenant.

It mirrors the working deployment pattern from:
- https://github.com/cbensonIstari/sysgit-integration
- https://github.com/cbensonIstari/pyintact-integration

## Current State (as of 2026-02-28)

Your tenant currently exposes `@istari:run_pyintact_simulation` but not:
- `@istari:assemble_dataset`
- `@istari:train_nemo_surrogate`

That is why NeMo launch is blocked today.

## Do You Need Special Hardware?

For real PhysicsNeMo training:
- Use Linux/WSL + NVIDIA CUDA GPU (cloud or workstation).
- Do not buy hardware first. Run small cloud experiments, measure run-time/cost, then decide.
- MacBook Air is fine for SDK orchestration and notebooks, not ideal for production GPU training.
- Current `stari module lint` schema also favors Linux/Windows OS labels for publishable modules.

## Deployment Model (Important)

A function appears and runs only when **both** are true:

1. The module is installed on a running agent machine:
   - `~/Library/Application Support/istari_agent/istari_modules/<module_name>/`
2. The module is published to the platform:
   - `stari client publish module_manifest.json`

If either step is missing, jobs stay blocked or function won't show in tenant listings.

## Phase 1: Build the NeMo Function Module

Create a module repo/folder (for example `nemo-integration`) with:

- `module_manifest.json`
- `function_schemas/train_nemo_surrogate.json`
- `src/run_docker.sh`
- `src/train_nemo_surrogate.py`
- `scripts/build.sh`
- `scripts/install.sh`
- `scripts/test.sh`

This repository now includes that scaffold at:

- `nemo-integration/`

### Module manifest essentials

Use sysgit/pyintact conventions:

- `module_type`: `"function"`
- `module_key`: e.g. `"@istari:nemo"`
- `tool_key`: e.g. `"physicsnemo"`
- function key: `"@istari:train_nemo_surrogate"`
- `entrypoint`: `"src/run_docker.sh"`
- `run_command`: `"bash {entrypoint} {input_file} {output_file} {temp_dir}"`

Critical gotcha from sysgit:
- `operating_systems` and `tool_versions` must be present at **both**
  - module level and
  - function level.

### Function schema essentials

At minimum, define inputs:
- `dataset_job_id` (`parameter`)
- `training_config` (`parameter`)

And outputs:
- `metrics_json` (`file`, required, upload as artifact)
- `model_checkpoint` (`file`, required, upload as artifact)

## Phase 2: Install on Agent Machine

From module root:

```bash
stari module lint module_manifest.json
bash scripts/build.sh
bash scripts/install.sh
```

Install path should end up as:

- macOS: `~/Library/Application Support/istari_agent/istari_modules/nemo/`

Do not nest under `@istari/` subdirectories.

## Phase 3: Restart Agent and Verify Module Load

Restart agent after installing:

```bash
open /Applications/istari_agent/istari_agent_11.1.3.app
```

Verify log:

```bash
grep "Adding module" ~/Library/Application\ Support/istari_agent/istari_agent.log | tail -n 20
```

Expected:

```text
Adding module @istari:nemo <version>
```

## Phase 4: Publish Function to Tenant

From module root:

```bash
stari client publish module_manifest.json
stari client list functions --os | rg train_nemo_surrogate
```

If using tool access controls, grant users access to the new tool in Admin settings.

## Phase 5: Launch Training Job (SDK)

After publish/install succeeds, use:

```bash
python nemo/launch_training.py \
  --campaign-root-model-id <model_id> \
  --dataset-job-id <dataset_job_id> \
  --function-key @istari:train_nemo_surrogate
```

The launcher in this repo now preflights function availability and prints a clear error if the function is missing.

## Practical First-Time Recommendation

1. Start with a tiny training run:
   - small dataset
   - few epochs
   - single GPU
2. Confirm artifacts and metrics in Istari.
3. Scale dataset/model only after baseline is stable.
