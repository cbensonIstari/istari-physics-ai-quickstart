# K-Script: Quickstart Physics AI Model in Istari

80% case: engineer launches a simulation campaign, builds a dataset, and trains a first PhysicsNeMo surrogate.

| Who | Observable Action | Unobservable Action / Notes |
|---|---|---|
| Engineer | Opens quickstart and fills `campaign_spec.example.json` | IDs reference existing geometry and campaign root model in Istari |
| Engineer | Runs `submit_campaign.py --dry-run` | Script validates grid and writes payload preview |
| Engineer | Runs `submit_campaign.py` | Script creates many Istari jobs using `@istari:run_pyintact_simulation` |
| Istari Agent | Starts processing jobs | Concurrency governed by available workers and license seats |
| Engineer | Runs `poll_campaign.py` | Script polls job states and writes an updated manifest |
| Engineer | Launches dataset assembly in Istari | Successful case outputs are normalized into training tensors |
| Engineer | Runs `launch_training.py` | Istari creates PhysicsNeMo training job and tracks lineage |
| Team Lead | Reviews metrics and lineage in Istari | Promotion decision based on validation thresholds |

## Error Condition

| Who | Observable Action | Unobservable Action / Notes |
|---|---|---|
| Istari | Several case jobs fail | Typical causes: invalid geometry/load combinations |
| Engineer | Sees failed counts in polling summary | Failed case IDs remain in manifest for triage |
| Engineer | Narrows parameter grid and resubmits | New jobs are added without losing prior successful artifacts |
