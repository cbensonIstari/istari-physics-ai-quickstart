# Architecture: Physics AI Quickstart in Istari

## ASCII Workflow

```text
Campaign spec
  |
  v
submit_campaign.py
  |
  v
@istari:run_pyintact_simulation (many jobs)
  |
  v
Per-case VTU + summary artifacts
  |
  v
@istari:assemble_dataset
  |
  v
@istari:train_nemo_surrogate
  |
  v
Versioned surrogate model + metrics + lineage
```

```mermaid
flowchart LR
    A[Campaign Spec JSON] --> B[submit_campaign.py]
    B --> C[Istari Jobs: @istari:run_pyintact_simulation]
    C --> D[Per-case outputs: VTU/summary artifacts]
    D --> E[Dataset job: @istari:assemble_dataset]
    E --> F[Training job: @istari:train_nemo_surrogate]
    F --> G[Versioned surrogate model + metrics]
```

## Control Plane

- Local notebook/scripts: campaign design, dispatch, monitoring
- Istari: execution, artifact storage, lineage, versioning

## Data Plane

- Inputs: geometry models + parameter grid
- Mid artifacts: PyIntact result files and metadata
- Output: PhysicsNeMo model revision with validation report
