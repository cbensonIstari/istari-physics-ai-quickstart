"""Launch a PhysicsNeMo surrogate training job in Istari."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from istari_client import get_client, page_items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root-model-id", required=True)
    parser.add_argument("--dataset-job-id", required=True)
    parser.add_argument("--function-key", default="@istari:train_nemo_surrogate")
    parser.add_argument("--target-fields", default="", help="Comma-delimited override for target fields")
    parser.add_argument(
        "--training-config",
        default="use-cases/many-pyintact-to-nemo/example-input/training_config.json",
        help="Optional training config JSON to pass through as job parameters",
    )
    parser.add_argument("--agent-id", default="", help="Optional assigned agent id")
    parser.add_argument("--list-functions", action="store_true", help="List available functions and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print payload and exit without submitting")
    return parser.parse_args()


def parse_target_fields(raw: str) -> list[str]:
    return [f.strip() for f in raw.split(",") if f.strip()]


def load_training_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"training config must be a JSON object: {path}")
    return payload


def list_function_names(client) -> list[str]:
    all_names: set[str] = set()
    for page in range(1, 20):
        functions = page_items(client.list_functions(page=page, size=100))
        if not functions:
            break
        for fn in functions:
            name = str(getattr(fn, "name", "")).strip()
            if name:
                all_names.add(name)
    return sorted(all_names)


def main() -> None:
    args = parse_args()
    client = get_client()

    available_functions = list_function_names(client)
    if args.list_functions:
        for fn in available_functions:
            print(fn)
        return
    if args.function_key not in available_functions:
        raise RuntimeError(
            "Requested function is not available in this tenant: "
            f"{args.function_key}\nAvailable functions:\n- " + "\n- ".join(available_functions)
        )

    training_config = load_training_config(args.training_config)
    target_fields = parse_target_fields(args.target_fields)
    if not target_fields:
        cfg_fields = training_config.get("target_fields", [])
        if isinstance(cfg_fields, list):
            target_fields = [str(v).strip() for v in cfg_fields if str(v).strip()]
    if not target_fields:
        target_fields = ["von_mises", "displacement"]

    parameters: dict = {
        "dataset_job_id": args.dataset_job_id,
        "target_fields": target_fields,
    }
    if training_config:
        parameters["training_config"] = training_config

    if args.dry_run:
        print(
            json.dumps(
                {
                    "model_id": args.campaign_root_model_id,
                    "function": args.function_key,
                    "assigned_agent_id": args.agent_id or None,
                    "parameters": parameters,
                },
                indent=2,
            )
        )
        return

    job = client.add_job(
        model_id=args.campaign_root_model_id,
        function=args.function_key,
        assigned_agent_id=args.agent_id or None,
        parameters=parameters,
    )

    print(f"Launched training job: {getattr(job, 'id', '<unknown-id>')}")


if __name__ == "__main__":
    main()
