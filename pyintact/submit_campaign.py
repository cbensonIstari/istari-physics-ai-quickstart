"""Submit many PyIntact simulations to Istari from a campaign spec."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from istari_client import get_client
from pyintact.campaign_utils import dump_json, generate_cases, load_json, make_job_parameters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Path to campaign spec JSON")
    parser.add_argument("--function-key", default="@istari:run_pyintact_simulation")
    parser.add_argument("--output", default="campaign_jobs.json")
    parser.add_argument("--throttle-seconds", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def require_field(spec: dict, key: str) -> str:
    value = str(spec.get(key, "")).strip()
    if not value:
        raise ValueError(f"campaign spec missing required field: {key}")
    return value


def main() -> None:
    args = parse_args()
    spec = load_json(args.spec)

    campaign_root_model_id = require_field(spec, "campaign_root_model_id")
    cases = generate_cases(spec)

    print(f"Campaign: {spec.get('campaign_name', '<unnamed>')}")
    print(f"Function: {args.function_key}")
    print(f"Cases: {len(cases)}")

    manifest: list[dict] = []

    if args.dry_run:
        for case in cases[:5]:
            params = make_job_parameters(spec, case)
            manifest.append(
                {
                    "case_id": case["case_id"],
                    "job_id": None,
                    "status": "dry_run",
                    "parameters": params,
                }
            )
        dump_json(args.output, manifest)
        print(f"Wrote dry-run payload preview to: {Path(args.output).resolve()}")
        return

    client = get_client()
    for idx, case in enumerate(cases, start=1):
        params = make_job_parameters(spec, case)
        job = client.add_job(
            model_id=campaign_root_model_id,
            function=args.function_key,
            parameters=params,
        )
        job_id = str(getattr(job, "id", ""))
        manifest.append({"case_id": case["case_id"], "job_id": job_id, "status": "submitted"})

        if idx % 25 == 0 or idx == len(cases):
            print(f"Submitted {idx}/{len(cases)}")
        time.sleep(args.throttle_seconds)

    dump_json(args.output, manifest)
    print(f"Wrote manifest: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
