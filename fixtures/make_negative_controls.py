"""Make deliberate, reviewable mutations from original baseline traces; no model calls."""

import json
from copy import deepcopy
from pathlib import Path

root = Path(__file__).parent
baseline = [
    json.loads(line) for line in (root / "baseline.jsonl").read_text().splitlines()
]


def case(name):
    return deepcopy(next(item for item in baseline if item["caseId"] == name))


broken = case("healthy")
broken["caseId"] = "altered-asset"
broken["run"]["manifest"]["assets"][0]["content"] += "intentional mutation"
stale = case("approval-invalidated")
stale["caseId"] = "stale-approval"
stale["run"]["approval"] = case("completed-bundle")["run"]["approval"]
reference = case("healthy")
reference["caseId"] = "unknown-evidence"
reference["run"]["review"]["findings"][0]["assetId"] = "missing-asset"
outcome = case("timeout")
outcome["caseId"] = "wrong-expectation"
outcome["expected"]["status"] = "completed"
(root / "negative-controls.jsonl").write_text(
    "".join(
        json.dumps(item, separators=(",", ":")) + "\n"
        for item in [broken, stale, reference, outcome]
    ),
    encoding="utf-8",
)
print("Wrote four intentional invariant failures.")
