# Verified locally on 2026-10-09

Environment: macOS arm64; Python 3.14.8. Runtime packages: Python standard library only. Optional development tools are locked in `requirements-dev.lock`: Ruff 0.16.10, mypy 2.4.0 and their transitive dependencies. The project virtual environment is gitignored.

| Command | Observed result |
|---|---|
| `python3 -m unittest discover -s tests -v` | 25 tests passed |
| `python3 -m compileall -q fieldcheck tests fixtures` | Passed |
| `ruff check fieldcheck tests fixtures/make_negative_controls.py` | Passed |
| `ruff format --check fieldcheck tests fixtures/make_negative_controls.py` | Passed |
| `mypy fieldcheck` (strict) | No issues in 3 source files |
| Baseline evaluator | 9/9 cases passed; exit 0 |
| Negative-control evaluator | 0/4 cases passed; all deliberate failures detected; exit 1 |

Unit checks include changed bytes/digests, stale/missing approval, evidence references, audit gaps, unaudited attempts, fallback after refusal, bundle manifest mismatch, incorrect expected outcome and malformed structures. CLI tests execute a separate Python process and verify report output, failure exit codes, invalid JSON/NaN/empty input, duplicate keys, excessive nesting, duplicate case IDs and protection against overwriting the input.

Local fixture timing is copied from supplied traces. Cases include repeated snapshots of individual runs; timings are not independent samples and are not a model benchmark. No live model, provider network or account operation is performed by Fieldcheck.

The frozen schema was copied from Switchyard's generated v1 contract. Remote CI for Python 3.11/3.14 on Linux is configured but has not run. Python 3.11 behavior, generic Unicode/number canonicalization, signed-log authenticity, live-model quality and production-scale data are not claimed as verified.
