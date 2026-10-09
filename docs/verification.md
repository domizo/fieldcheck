# Verified locally on 2026-10-09

Environment: macOS arm64; Python 3.14.8. Runtime packages: Python standard library only. Optional development tools are locked in `requirements-dev.lock`: Ruff 0.16.10, mypy 2.4.0 and their transitive dependencies. The project virtual environment is gitignored.

| Command                                                                   | Observed result                                            |
| ------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `python3 -m unittest discover -s tests -v`                                | 37 tests passed                                            |
| `python3 -m compileall -q fieldcheck tests fixtures`                      | Passed                                                     |
| `ruff check fieldcheck tests fixtures/make_negative_controls.py`          | Passed                                                     |
| `ruff format --check fieldcheck tests fixtures/make_negative_controls.py` | Passed                                                     |
| `mypy fieldcheck` (strict)                                                | No issues in 3 source files                                |
| Baseline evaluator                                                        | 9/9 cases passed; exit 0                                   |
| Negative-control evaluator                                                | 0/4 cases passed; all deliberate failures detected; exit 1 |

Unit checks include changed bytes/digests, stale/missing approval, evidence references, audit gaps, unaudited attempts, fallback after refusal, bundle manifest mismatch, incorrect expected outcome and malformed structures. CLI tests execute a separate Python process and verify report output, failure exit codes, invalid JSON/NaN/empty input, duplicate keys, excessive nesting, duplicate case IDs and protection against overwriting the input.

Local fixture timing is copied from supplied traces. Cases include repeated snapshots of individual runs; timings are not independent samples and are not a model benchmark. No live model, provider network or account operation is performed by Fieldcheck.

## Remote CI on 2026-10-09

[GitHub Actions run 37888544940](https://github.com/domizo/fieldcheck/actions/runs/37888544940) passed for commit `4e251a7501ad7838737a37a5e85af813e38cf0ac` on 2026-10-09. The repository is owned by `domizo` and remains private. This records the verified source revision; subsequent documentation or license changes require their own [workflow run](https://github.com/domizo/fieldcheck/actions/workflows/ci.yml).

Both Ubuntu matrix jobs, Python 3.11 and 3.14, passed Ruff lint/format, strict mypy, compile checks and 37 tests each. Each job accepted 9/9 baseline cases and detected all 4 negative controls with exit 1. Job conclusions and counts were checked through the authenticated GitHub connector, including job logs.

## Contract-validation follow-up on 2026-10-09

The review reproduced false acceptance when no current provider succeeded, when the approval-request/rejection audit did not match the state, and when a timestamp, UUID variant, integer or UTF-16 string length contradicted the producer contract. An escaped lone surrogate in a case ID also produced a CLI traceback during report writing. Regression tests were run before the fixes and failed for these cases; the fixes now validate the latest current-input review and decisions, match the producer's scalar bounds, and reject invalid Unicode before evaluation/report creation.

Current local checks: **37 tests pass**, baseline **9/9** accepted, negative controls **4/4** detected. Ruff lint/format, strict mypy and compile checks pass. The linked CI run above also passed the expanded 37-test suite on both supported Python versions. These checks remain limited to the explicit offline v1 contract and unsigned internal consistency.

## Remaining limits

The frozen schema was copied from Switchyard's generated v1 contract. Generic Unicode/number canonicalization, signed-log authenticity, live-model quality and production-scale data are not claimed as verified.
