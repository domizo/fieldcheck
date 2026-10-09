# Fieldcheck technical walkthrough

[English](walkthrough.md) | [日本語](walkthrough.ja.md)

Fieldcheck evaluates the internal consistency of synthetic workflow traces. It checks the frozen `switchyard.run.v1` contract, evidence hashes, provider attempts, approval and delivery, and expected outcomes. It does not evaluate live-model quality or prove log authenticity.

## Validation flow

| Component                                        | Responsibility                                                                                                                                                                                                |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fieldcheck/__main__.py`                         | Reads bounded JSONL; rejects duplicate keys/case IDs, non-finite constants, excessive size/depth and invalid Unicode. It executes no commands from trace content.                                             |
| `validate_shape` in `fieldcheck/evaluator.py`    | Checks UTC timestamp form, UUID version/variant, JavaScript's safe integer range and UTF-16 string bounds. It implements an explicit v1 contract, not a general JSON Schema interpreter.                      |
| `state_consistency` in `fieldcheck/evaluator.py` | Requires a successful provider in the current input's latest review, an approval request after success, and audit decisions matching the state. Success for an older input cannot justify the current review. |
| Evaluation report                                | Records each invariant and expected outcome. Exit 0 means all cases pass; exit 1 means an invariant/outcome failed; exit 2 means an input/output error.                                                       |

## Design decisions

| Decision                                    | Rationale and boundary                                                                                                                                          |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Independent Python runtime                  | JSONL is the boundary. The evaluator runs without Node, the UI, a server, an API key or runtime packages.                                                       |
| Correlate audit decisions with state fields | A review object alone does not show that a provider succeeded for the current input. Related events expose contradictory histories.                             |
| Match JavaScript scalar limits              | The producer owns the portable contract. Python integers and string lengths otherwise accept values the TypeScript producer rejects.                            |
| Separate consistency from authenticity      | A fully fabricated but internally consistent unsigned trace can pass. Authentication or signatures require a separate trust design.                             |
| Evaluate known fixture outcomes             | The supplied cases have explicit expected state and failure outcomes. Their timing measures local fixture execution, not live inference speed or model quality. |

## Reproducible verification

The [README commands](../README.md#run) execute the baseline and negative controls. An expected outage can pass because its outcome matches the case expectation; a contradictory trace fails an invariant. Tests cover altered bytes/digests, stale approval, unknown evidence, refusal routing, current-input review/decision ordering, producer scalar bounds and invalid Unicode.

The contract-validation regressions first reproduced acceptance of invalid values and a Unicode traceback, then passed after the fixes. Commands, measured results and limits are recorded in [verification](verification.md).

## Limits

The evaluator checks the exported delivery manifest. Switchyard's integration tests and download endpoint check actual bundle bytes. Generic JSON Schema interpretation, signed audit verification, live-model scoring, statistical quality estimation and cloud reporting are not implemented. Valid output shape and internally consistent events do not prove factual correctness. See [the exchange contract](contract.md) for the frozen format and hashing rules.
