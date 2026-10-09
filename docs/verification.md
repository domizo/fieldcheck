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

## Remote CI on 2026-10-09

[GitHub Actions run 37884067927](https://github.com/domizo/fieldcheck/actions/runs/37884067927) passed for implementation commit `25bdfd7470e044c0648bb7154c07f8585cd01337`. The private repository is owned by `domizo`. Its published tree `91055aaad450a26aaa5b82c5a134d36afa3dba8f` exactly matched the verified local checkout, including both language READMEs; remote commits are a fresh, disclosed import rather than copied local history.

Both Ubuntu matrix jobs, Python 3.11 and 3.14, passed Ruff lint/format, strict mypy, compile checks and 25 tests each. Each job accepted 9/9 baseline cases and detected all 4 negative controls with exit 1. Job conclusions and counts were checked through the authenticated GitHub connector, including job logs.

## Remaining limits

The frozen schema was copied from Switchyard's generated v1 contract. Generic Unicode/number canonicalization, signed-log authenticity, live-model quality and production-scale data are not claimed as verified.
