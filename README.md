# Fieldcheck

[English](README.md) | [日本語](README.ja.md)

A small, independent Python CLI for evaluating **versioned AI-workflow trace invariants**. It validates synthetic Switchyard exports without Node, a running server, a model, an API key, or third-party Python packages.

It evaluates deterministic local fixture behavior, **not live-model quality**. All supplied traces are original synthetic data.

## Run

From this directory, with Python 3.11+:

```sh
python3 -m fieldcheck fixtures/baseline.jsonl --output report.json
python3 -m unittest discover -s tests -v
python3 -m compileall -q fieldcheck tests fixtures
```

The baseline contains 9 actual exported run snapshots with explicit regression expectations. All 9 should pass. The four negative controls are deliberately broken:

```sh
python3 -m fieldcheck fixtures/negative-controls.jsonl
# exits 1: altered asset, stale approval, unknown evidence, wrong expectation
```

Exit codes: **0** all cases pass; **1** at least one invariant/outcome fails; **2** malformed input, duplicate case IDs/JSON keys, size/depth limit or report-writing error. Inputs are bounded to 16 MiB, 1 MiB per line and 64 JSON levels. A report cannot overwrite its input. No commands or model operations are executed from input content.

## What it checks

Strict synthetic v1 shape; actual asset SHA-256 hashes; manifest digest; bounded provider routing and refusal stop; finding evidence IDs; approval bound to the current input; audit sequence and matching approval before delivery; bundle manifest hashes; consistent failure states; expected outcomes. Results include individual check names and local fixture durations read from traces.

`report.json` is a structured result, not a dashboard or a production evaluation service. Timing medians summarize the supplied local fixture execution; snapshots of one run may appear in multiple cases, so aggregate attempts are not independent experiments. Do not use these numbers as provider latency, quality or cost claims.

## Fresh export from Switchyard

```sh
cd ../switchyard
npm run demo -- ../fieldcheck/fixtures/baseline.jsonl
cd ../fieldcheck
python3 fixtures/make_negative_controls.py
python3 -m fieldcheck fixtures/baseline.jsonl
```

The runtime remains independent: checked-in fixtures work without the sibling project. `fixtures/PROVENANCE.md` documents how they were produced, and [the exchange contract](docs/contract.md) explains canonical hashes and limits.

Local verification: 25 tests passed on Python 3.14.8, baseline 9/9 accepted, and all 4 negative controls detected. Ruff lint/format and strict mypy checks pass. CI files cover Python 3.11 and 3.14 but remote CI has not run. See [verification](docs/verification.md) and [dependencies](DEPENDENCIES.md).

Not implemented: live-model scoring, statistical quality estimation, human annotation, provider invocation, arbitrary JSON Schema interpretation, signed audit verification, storage access to downloaded bundles, and cloud reporting. The evaluator checks the exported **delivery manifest**; Switchyard's integration tests and download endpoint check actual bundle bytes.

Shape-valid output is not proof of factual correctness. A project license has not been selected.
