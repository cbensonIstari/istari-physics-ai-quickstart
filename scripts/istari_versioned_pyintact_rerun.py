from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from istari_digital_client import Client, Configuration
from istari_digital_client.v2.models.new_snapshot import NewSnapshot
from istari_digital_client.v2.models.new_snapshot_tag import NewSnapshotTag
from istari_digital_client.v2.models.new_source import NewSource
from istari_digital_client.v2.models.new_system import NewSystem
from istari_digital_client.v2.models.new_system_configuration import NewSystemConfiguration
from istari_digital_client.v2.models.new_tracked_file import NewTrackedFile
from istari_digital_client.v2.models.tracked_file_specifier_type import TrackedFileSpecifierType


def page_items(page_like):
    if page_like is None:
        return []
    if isinstance(page_like, list):
        return page_like
    items = getattr(page_like, "items", None)
    if items is not None:
        return list(items)
    return []


def job_status(job) -> str:
    status = getattr(job, "status", None)
    if status is not None:
        name = getattr(status, "name", None)
        if name is not None:
            return str(getattr(name, "value", name)).lower()
    status_name = getattr(job, "status_name", None)
    if status_name is not None:
        return str(getattr(status_name, "value", status_name)).lower()
    return "unknown"


def latest_revision_id(model) -> str:
    revisions = getattr(getattr(model, "file", None), "revisions", [])
    if not revisions:
        raise RuntimeError(f"No revisions found for model: {getattr(model, 'id', '<unknown>')}")
    return revisions[0].id


def snapshot_id(create_snapshot_response):
    actual = getattr(create_snapshot_response, "actual_instance", None)
    return getattr(actual, "id", None)


def latest_snapshot_id(client: Client, configuration_id: str) -> str | None:
    snapshots = page_items(client.list_snapshots(configuration_id=configuration_id, size=100))
    if not snapshots:
        return None
    snapshots.sort(key=lambda s: getattr(s, "created", None), reverse=True)
    return getattr(snapshots[0], "id", None)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def latest_agent_display_name(agent) -> str:
    history = list(getattr(agent, "display_name_history", []) or [])
    if not history:
        return ""
    history.sort(key=lambda x: getattr(x, "created", None), reverse=True)
    return str(getattr(history[0], "display_name", "") or "")


def main() -> int:
    registry_url = os.getenv("ISTARI_DIGITAL_REGISTRY_URL", "https://fileservice-v2.demo.istari.app")
    pat = require_env("ISTARI_DIGITAL_REGISTRY_AUTH_TOKEN")
    root = Path(__file__).resolve().parent.parent

    models_dir = root / "pyintact-integration" / "models"
    notebook_path = root / "notebooks" / "howto_pyintact_integration_test.ipynb"
    beam_path = models_dir / "beam.stl"
    load_path = models_dir / "end-2.stl"
    restraint_path = models_dir / "end-1.stl"
    for path in [beam_path, load_path, restraint_path, notebook_path]:
        if not path.exists():
            raise FileNotFoundError(str(path))

    client = Client(Configuration(registry_url=registry_url, registry_auth_token=pat))
    user = client.get_current_user()
    print(f"connected_user={getattr(user, 'email', '<unknown>')}")

    function_name = "@istari:run_pyintact_simulation"
    functions = page_items(client.list_functions(name=function_name, size=50))
    names = [getattr(f, "name", None) for f in functions]
    if function_name not in names:
        raise RuntimeError(f"run function missing. functions={names}")

    agents = page_items(client.list_agents(size=100))
    if not agents:
        raise RuntimeError("No agents available in tenant.")
    preferred_agent = "Istari Slack Analytics Agent"
    agent = next((a for a in agents if latest_agent_display_name(a) == preferred_agent), None) or agents[0]
    print(f"agent_id={agent.id}")
    print(f"agent_display_name={latest_agent_display_name(agent)}")

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    system = client.create_system(
        NewSystem(
            name=f"PyIntact Integration Versioned Run {ts}",
            description="Versioned pyintact integration rerun with snapshots and tags",
        )
    )

    # Track a state file and update it after the run so the post-run snapshot has a deterministic delta.
    state_path = Path("/tmp") / f"istari_pyintact_run_state_{ts}.json"
    state_path.write_text(json.dumps({"phase": "baseline", "timestamp": ts}, indent=2), encoding="utf-8")

    notebook_model = client.add_model(
        path=notebook_path,
        display_name=f"pyintact-howto-notebook-{ts}",
        version_name="v1.0.0",
    )
    beam_model = client.add_model(path=beam_path, display_name=f"pyintact-beam-{ts}", version_name="v1.0.0")
    load_model = client.add_model(path=load_path, display_name=f"pyintact-load-face-{ts}", version_name="v1.0.0")
    restraint_model = client.add_model(
        path=restraint_path,
        display_name=f"pyintact-restraint-face-{ts}",
        version_name="v1.0.0",
    )
    state_model = client.add_model(
        path=state_path,
        display_name=f"pyintact-run-state-{ts}",
        version_name="v1.0.0",
    )

    tracked_files = [
        NewTrackedFile(specifier_type=TrackedFileSpecifierType.LATEST, file_id=notebook_model.file.id),
        NewTrackedFile(specifier_type=TrackedFileSpecifierType.LATEST, file_id=beam_model.file.id),
        NewTrackedFile(specifier_type=TrackedFileSpecifierType.LATEST, file_id=load_model.file.id),
        NewTrackedFile(specifier_type=TrackedFileSpecifierType.LATEST, file_id=restraint_model.file.id),
        NewTrackedFile(specifier_type=TrackedFileSpecifierType.LATEST, file_id=state_model.file.id),
    ]
    config = client.create_configuration(
        system_id=system.id,
        new_system_configuration=NewSystemConfiguration(name="Baseline", tracked_files=tracked_files),
    )

    baseline_snapshot_id = snapshot_id(client.create_snapshot(config.id, NewSnapshot()))
    if not baseline_snapshot_id:
        baseline_snapshot_id = latest_snapshot_id(client, config.id)
    if not baseline_snapshot_id:
        raise RuntimeError("Baseline snapshot did not return an id.")
    baseline_tag = client.create_tag(
        baseline_snapshot_id,
        NewSnapshotTag(tag=f"v1.0.0-{ts}-baseline"),
    )

    sim_config = {
        "simulation_type": "linear_elastic",
        "material": {"density": 7800.0, "poisson_ratio": 0.3, "youngs_modulus": 2.1e11},
        "load": {"type": "pressure", "magnitude": 1e6},
        "scenario": {"resolution": 1000, "units": "MKS"},
    }
    job = client.add_job(
        model_id=beam_model.id,
        function="@istari:run_pyintact_simulation",
        assigned_agent_id=agent.id,
        sources=[
            NewSource(revision_id=latest_revision_id(load_model), relationship_identifier="load_geometry_file"),
            NewSource(
                revision_id=latest_revision_id(restraint_model),
                relationship_identifier="restraint_geometry_file",
            ),
        ],
        parameters={"simulation_config": json.dumps(sim_config)},
        description="Versioned pyintact integration rerun",
        display_name=f"pyintact-versioned-job-{ts}",
        version_name="v1.1.0",
    )

    terminal_states = {"completed", "failed", "cancelled"}
    seen = None
    for _ in range(120):
        current = client.get_job(job.id)
        status = job_status(current)
        if status != seen:
            print(f"job_status={status}")
            seen = status
        if status in terminal_states:
            break
        time.sleep(5)
    else:
        raise TimeoutError(f"Job {job.id} did not reach terminal status in 10 minutes.")

    final_job = client.get_job(job.id)
    final_status = job_status(final_job)

    state_path.write_text(
        json.dumps(
            {
                "phase": "post_run",
                "timestamp": datetime.utcnow().isoformat(),
                "job_id": job.id,
                "job_status": final_status,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    client.update_model(
        model_id=state_model.id,
        path=state_path,
        version_name="v1.1.0",
        description="post-run state update",
    )

    post_snapshot_id = snapshot_id(client.create_snapshot(config.id, NewSnapshot()))
    if not post_snapshot_id:
        post_snapshot_id = latest_snapshot_id(client, config.id)
    if not post_snapshot_id:
        raise RuntimeError("Post-run snapshot did not return an id.")
    post_tag = client.create_tag(post_snapshot_id, NewSnapshotTag(tag=f"v1.1.0-{ts}-post-run"))

    print(f"RESULT_SYSTEM_ID={system.id}")
    print(f"RESULT_CONFIG_ID={config.id}")
    print(f"RESULT_BASELINE_SNAPSHOT_ID={baseline_snapshot_id}")
    print(f"RESULT_BASELINE_TAG={baseline_tag.tag}")
    print(f"RESULT_JOB_ID={job.id}")
    print(f"RESULT_JOB_STATUS={final_status}")
    print(f"RESULT_POST_SNAPSHOT_ID={post_snapshot_id}")
    print(f"RESULT_POST_TAG={post_tag.tag}")
    print(f"RESULT_SYSTEM_LINK=https://demo.istari.app/systems/{system.id}")
    print(f"RESULT_CONFIG_LINK=https://demo.istari.app/systems/{system.id}/config/{config.id}")
    print("RESULT_JOB_LINK=https://demo.istari.app/jobs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
