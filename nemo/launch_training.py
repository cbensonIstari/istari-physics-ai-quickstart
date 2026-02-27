"""Launch a PhysicsNeMo surrogate training job in Istari."""

from __future__ import annotations

import argparse

from istari_client import get_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root-model-id", required=True)
    parser.add_argument("--dataset-job-id", required=True)
    parser.add_argument("--function-key", default="@istari:train_nemo_surrogate")
    parser.add_argument("--target-fields", default="von_mises,displacement")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = get_client()

    target_fields = [f.strip() for f in args.target_fields.split(",") if f.strip()]

    job = client.add_job(
        model_id=args.campaign_root_model_id,
        function=args.function_key,
        parameters={
            "dataset_job_id": args.dataset_job_id,
            "target_fields": target_fields,
        },
    )

    print(f"Launched training job: {getattr(job, 'id', '<unknown-id>')}")


if __name__ == "__main__":
    main()
