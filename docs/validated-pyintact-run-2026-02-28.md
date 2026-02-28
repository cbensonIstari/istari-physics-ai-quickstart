# Validated PyIntact Integration Run (2026-02-28)

This document captures the concrete outputs and SDK implementation notes from a successful end-to-end run of `@istari:run_pyintact_simulation` using the Istari Python SDK.

## Run Record

| Item | Value |
|------|-------|
| Date | 2026-02-28 (UTC) |
| System | [`89690e3c-f99d-426e-9cbf-98d0cf5f5653`](https://demo.istari.app/systems/89690e3c-f99d-426e-9cbf-98d0cf5f5653) |
| Configuration | [`d26674dc-d6c0-44f8-bced-74fb38e806bc`](https://demo.istari.app/systems/89690e3c-f99d-426e-9cbf-98d0cf5f5653/config/d26674dc-d6c0-44f8-bced-74fb38e806bc) |
| Job | `a21fa8e8-85bb-4301-b73b-e786555ad343` |
| Function | `@istari:run_pyintact_simulation` (`@istari:pyintact` `0.1.0`) |
| Baseline snapshot/tag | `0650c525-89b4-4dc1-87c2-20585868e82d` / `v1.0.0-20260228-062757-baseline` |
| Post-run snapshot/tag | `2fcf6c23-7099-4317-bd2c-fd3ceb34a01c` / `v1.1.0-20260228-062757-post-run` |

## Input Configuration

The job used:

```json
{
  "simulation_type": "linear_elastic",
  "material": {
    "density": 7800.0,
    "poisson_ratio": 0.3,
    "youngs_modulus": 210000000000.0
  },
  "load": {
    "type": "pressure",
    "magnitude": 1000000.0
  },
  "scenario": {
    "resolution": 1000,
    "units": "MKS"
  }
}
```

Required named source bindings:

- `load_geometry_file`
- `restraint_geometry_file`

## Outputs Produced

All outputs were published as job products for model `27a0e775-ebfc-49bd-89f4-7f7eb080f702`.

| Artifact | Artifact ID | Revision ID | Size | Link |
|---------|-------------|-------------|------|------|
| `visualization.png` | `0cfd0cd0-9432-4173-bb44-22f764a66415` | `56f448cb-e56b-46cd-ab04-33f32535de84` | 256,408 bytes | [open](https://demo.istari.app/files/27a0e775-ebfc-49bd-89f4-7f7eb080f702/artifact/0cfd0cd0-9432-4173-bb44-22f764a66415/56f448cb-e56b-46cd-ab04-33f32535de84) |
| `summary.json` | `d9992274-605a-405c-b63e-cbf52ae33915` | `d8871fbf-a11b-471a-b997-584171fbdc29` | 315 bytes | [open](https://demo.istari.app/files/27a0e775-ebfc-49bd-89f4-7f7eb080f702/artifact/d9992274-605a-405c-b63e-cbf52ae33915/d8871fbf-a11b-471a-b997-584171fbdc29) |
| `results.vtu` | `e8554067-16e6-4b6a-b2e3-ecaeec54b7ce` | `7aca08c1-751f-4ebf-8bb9-2fdd8bfd8024` | 1,818,873 bytes | [open](https://demo.istari.app/files/27a0e775-ebfc-49bd-89f4-7f7eb080f702/artifact/e8554067-16e6-4b6a-b2e3-ecaeec54b7ce/7aca08c1-751f-4ebf-8bb9-2fdd8bfd8024) |

`summary.json` results:

| Metric | Value |
|-------|-------|
| `solve_time_seconds` | `5.529` |
| `max_von_mises_stress` | `1002390.1692623853` Pa |
| `min_von_mises_stress` | `663182.9699018181` Pa |
| `units` | `MKS` |
| `resolution` | `1000` |
| `completed_at` | `2026-02-28T06:28:30.891295+00:00` |

Job status timeline (UTC):

- `Pending` at `2026-02-28T06:28:06.513246+00:00`
- `Claimed` at `2026-02-28T06:28:15.216136+00:00`
- `Validating` at `2026-02-28T06:28:17.145095+00:00`
- `Running` at `2026-02-28T06:28:20.983419+00:00`
- `Uploading` at `2026-02-28T06:28:54.766686+00:00`
- `Completed` at `2026-02-28T06:28:58.963102+00:00`

## SDK Learnings

1. `list_functions()` matching should use `name`, not `key`, and the filter should be exact:
   - `name='@istari:run_pyintact_simulation'`
2. `list_agents()` returns `Agent` objects with `display_name_history`, not a top-level `display_name` string.
3. `create_snapshot()` can return a `NoOpResponse` (`"No change from the last snapshot."`); for tagging logic, fall back to latest snapshot ID when no ID is returned directly.
4. `add_job()` for this function requires named MLA sources:
   - `relationship_identifier='load_geometry_file'`
   - `relationship_identifier='restraint_geometry_file'`

## Re-run Command

Use:

```bash
export ISTARI_DIGITAL_REGISTRY_URL=https://fileservice-v2.demo.istari.app
export ISTARI_DIGITAL_REGISTRY_AUTH_TOKEN=<your_pat>
python scripts/istari_versioned_pyintact_rerun.py
```

The script performs:

- System creation
- Configuration creation with tracked files
- Baseline snapshot + tag
- PyIntact job run
- Post-run file revision update (run-state model)
- Post-run snapshot + tag

