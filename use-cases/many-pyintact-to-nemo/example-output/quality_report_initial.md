# Quality Report (Initial)

## Summary

Campaign and surrogate do **not** meet readiness thresholds.

## Results

- Successful simulations: 8 / 12 (target >= 10) -> FAIL
- Failure rate: 33.3% (target <= 20%) -> FAIL
- Dataset samples ready: 8 (target >= 10) -> FAIL
- Validation normalized MAE: 0.14 (target <= 0.08) -> FAIL
- Validation R2: 0.81 (target >= 0.90) -> FAIL

## Recommendation

Narrow unstable parameter ranges, rerun failed cases, and retrain surrogate.
