"""Poll Istari job status for a submitted campaign."""

from __future__ import annotations

import argparse
import time
from collections import Counter
from pathlib import Path

from istari_client import get_client
from pyintact.campaign_utils import (
    TERMINAL_STATES,
    dump_json,
    load_json,
    normalize_status,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="campaign_jobs.json")
    parser.add_argument("--output", default="campaign_jobs.updated.json")
    parser.add_argument("--poll-seconds", type=int, default=20)
    return parser.parse_args()


def summarize(rows: list[dict]) -> str:
    counts = Counter([str(r.get("status", "unknown")) for r in rows])
    return ", ".join([f"{k}={v}" for k, v in sorted(counts.items())])


def main() -> None:
    args = parse_args()
    rows = load_json(args.manifest)
    pending = [r for r in rows if r.get("job_id")]

    if not pending:
        print("No submitted jobs found in manifest.")
        return

    client = get_client()

    while True:
        done = 0
        for row in pending:
            if row.get("status") in TERMINAL_STATES:
                done += 1
                continue

            job = client.get_job(row["job_id"])
            row["status"] = normalize_status(job)
            if row["status"] in TERMINAL_STATES:
                done += 1

        print(f"Progress {done}/{len(pending)} | {summarize(rows)}")
        dump_json(args.output, rows)

        if done == len(pending):
            break
        time.sleep(args.poll_seconds)

    print(f"Final manifest written to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
