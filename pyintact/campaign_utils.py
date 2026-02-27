"""Utilities for generating and tracking PyIntact simulation campaigns."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

TERMINAL_SUCCESS = {"succeeded", "completed", "success", "done"}
TERMINAL_FAILURE = {"failed", "error", "cancelled", "canceled", "timed_out", "timeout"}
TERMINAL_STATES = TERMINAL_SUCCESS | TERMINAL_FAILURE


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def dump_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=False))


def generate_cases(spec: dict[str, Any]) -> list[dict[str, Any]]:
    grid = spec.get("grid", {})
    if not grid:
        raise ValueError("campaign spec must define a non-empty 'grid' object")

    keys = list(grid.keys())
    values = [grid[k] for k in keys]
    if any(not isinstance(v, list) or not v for v in values):
        raise ValueError("every entry in 'grid' must be a non-empty list")

    base_material = spec.get("base_material", {})
    scenario = spec.get("scenario", {})

    all_cases: list[dict[str, Any]] = []
    for idx, combo in enumerate(itertools.product(*values), start=1):
        combo_dict = dict(zip(keys, combo))
        case = {
            "case_id": f"case_{idx:05d}",
            "inputs": combo_dict,
            "material": {
                "density": combo_dict.get("density", base_material.get("density", 7800.0)),
                "poisson_ratio": combo_dict["poisson_ratio"],
                "youngs_modulus": combo_dict["youngs_modulus"],
            },
            "load": {
                "type": "pressure",
                "magnitude": combo_dict["pressure_pa"],
            },
            "scenario": {
                "resolution": scenario.get("resolution", 1000),
                "units": scenario.get("units", "MKS"),
            },
        }
        all_cases.append(case)

    max_cases = spec.get("max_cases")
    if isinstance(max_cases, int) and max_cases > 0:
        return all_cases[:max_cases]
    return all_cases


def make_job_parameters(spec: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    geometry = spec.get("geometry", {})
    return {
        "case_id": case["case_id"],
        # These keys are a common shape for custom Istari modules.
        # Adapt names here if your tenant's function schema differs.
        "geometry_model_id": geometry.get("body_model_id"),
        "load_geometry_model_id": geometry.get("load_face_model_id"),
        "restraint_geometry_model_id": geometry.get("restraint_face_model_id"),
        "simulation_config": {
            "simulation_type": spec.get("simulation_type", "linear_elastic"),
            "material": case["material"],
            "load": case["load"],
            "scenario": case["scenario"],
        },
        "campaign_id": spec.get("campaign_name", "pyintact_campaign"),
    }


def normalize_status(job: Any) -> str:
    raw = getattr(job, "status_name", None)
    if hasattr(raw, "value"):
        raw = raw.value
    if raw is None:
        raw = getattr(job, "status", None)
    return str(raw).strip().lower()
