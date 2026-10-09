"""Explicit contract checks, with no network, model calls, or third-party dependencies."""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any

CONTRACT = "switchyard.run.v1"
MAX_SAFE_INTEGER = 9007199254740991
UUID_PATTERN = re.compile(
    r"(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|"
    r"00000000-0000-0000-0000-000000000000|"
    r"ffffffff-ffff-ffff-ffff-ffffffffffff)"
)
UTC_TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)
STATUSES = {
    "reviewing",
    "awaiting_approval",
    "failed",
    "rejected",
    "approved",
    "completed",
}
FAILURES = {
    "timeout",
    "invalid_output",
    "refusal",
    "unavailable",
    "interrupted",
    "input_invalid",
    "delivery_failed",
}
FIELDS = {
    "contractVersion",
    "id",
    "scenario",
    "revision",
    "status",
    "createdAt",
    "manifest",
    "inputDigest",
    "checks",
    "review",
    "attempts",
    "round",
    "failure",
    "approval",
    "delivery",
    "audit",
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Result:
    case_id: str
    passed: bool
    checks: list[Check]
    local_fixture_elapsed_ms: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def manifest_digest(manifest: dict[str, Any]) -> str:
    metadata = {
        "version": manifest["version"],
        "title": manifest["title"],
        "durationSeconds": manifest["durationSeconds"],
        "assets": [
            {key: asset[key] for key in ("id", "name", "sha256", "mediaType")}
            for asset in manifest["assets"]
        ],
    }
    return digest_text(compact(metadata))


def is_hash(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def integer(value: Any, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= MAX_SAFE_INTEGER


def utf16_length(value: str) -> int:
    """Match JavaScript/Zod string bounds for valid Unicode scalar values."""
    return len(value.encode("utf-16-le")) // 2


def timestamp(value: Any) -> bool:
    if not isinstance(value, str) or UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_shape(run: dict[str, Any]) -> None:
    require(set(run) == FIELDS, "Run fields do not match v1")
    require(run["contractVersion"] == CONTRACT, "Unsupported contract version")
    require(
        isinstance(run["id"], str) and UUID_PATTERN.fullmatch(run["id"]) is not None,
        "Invalid run identity",
    )
    require(
        run["status"] in STATUSES
        and run["scenario"]
        in {"healthy", "fallback", "timeout", "invalid", "refusal", "retry"},
        "Unknown state or fixture",
    )
    require(
        integer(run["revision"])
        and integer(run["round"])
        and timestamp(run["createdAt"]),
        "Invalid revision, round, or timestamp",
    )
    require(is_hash(run["inputDigest"]), "Invalid input digest")
    manifest = run["manifest"]
    require(
        isinstance(manifest, dict)
        and set(manifest) == {"version", "title", "durationSeconds", "assets"},
        "Invalid manifest fields",
    )
    require(
        type(manifest["version"]) is int
        and manifest["version"] in {1, 2}
        and manifest["title"] == "Harbor launch kit"
        and integer(manifest["durationSeconds"], 1)
        and manifest["durationSeconds"] <= 30,
        "Invalid manifest metadata",
    )
    require(
        isinstance(manifest["assets"], list) and len(manifest["assets"]) == 3,
        "Expected three synthetic assets",
    )
    for asset in manifest["assets"]:
        require(
            isinstance(asset, dict)
            and set(asset) == {"id", "name", "content", "sha256", "mediaType"},
            "Invalid asset fields",
        )
        require(
            all(isinstance(asset[key], str) for key in asset),
            "Asset fields must be strings",
        )
        require(
            re.fullmatch(r"[a-z0-9-]+", asset["id"]) is not None
            and re.fullmatch(r"[a-z0-9-]+\.(svg|json|txt)", asset["name"]) is not None
            and is_hash(asset["sha256"])
            and utf16_length(asset["content"]) <= 4096,
            "Invalid asset identity, checksum, or size",
        )
    for key in ("checks", "attempts", "audit"):
        require(isinstance(run[key], list), f"{key} must be a list")
    for item in run["checks"]:
        require(
            isinstance(item, dict)
            and set(item) == {"assetId", "passed", "reason"}
            and isinstance(item["assetId"], str)
            and type(item["passed"]) is bool
            and isinstance(item["reason"], str),
            "Invalid manifest check",
        )
    for attempt in run["attempts"]:
        require(
            isinstance(attempt, dict)
            and set(attempt) == {"provider", "outcome", "elapsedMs", "round"},
            "Invalid attempt fields",
        )
        require(
            attempt["provider"] in {"Atlas fixture", "Cedar fixture"}
            and attempt["outcome"]
            in {"valid", "timeout", "invalid_output", "refusal", "unavailable"}
            and integer(attempt["round"], 1),
            "Invalid attempt outcome",
        )
        value = attempt["elapsedMs"]
        require(
            type(value) in {int, float} and math.isfinite(value) and value >= 0,
            "Invalid measured local duration",
        )
    for event in run["audit"]:
        require(
            isinstance(event, dict)
            and set(event)
            == {"seq", "at", "event", "inputVersion", "inputDigest", "result"},
            "Invalid audit fields",
        )
        require(
            integer(event["seq"], 1)
            and integer(event["inputVersion"], 1)
            and is_hash(event["inputDigest"])
            and timestamp(event["at"])
            and isinstance(event["event"], str)
            and isinstance(event["result"], str),
            "Invalid audit values",
        )
    failure = run["failure"]
    if failure is not None:
        require(
            isinstance(failure, dict)
            and set(failure) == {"code", "message"}
            and failure["code"] in FAILURES
            and isinstance(failure["message"], str),
            "Invalid failure",
        )
    approval = run["approval"]
    if approval is not None:
        require(
            isinstance(approval, dict)
            and set(approval) == {"inputVersion", "inputDigest", "at"}
            and integer(approval["inputVersion"], 1)
            and is_hash(approval["inputDigest"])
            and timestamp(approval["at"]),
            "Invalid approval",
        )
    review = run["review"]
    if review is not None:
        require(
            isinstance(review, dict)
            and set(review) == {"summary", "findings"}
            and isinstance(review["summary"], str)
            and 1 <= utf16_length(review["summary"]) <= 500
            and isinstance(review["findings"], list)
            and 1 <= len(review["findings"]) <= 10,
            "Invalid review",
        )
        for finding in review["findings"]:
            require(
                isinstance(finding, dict)
                and set(finding) == {"assetId", "message", "severity"}
                and isinstance(finding["assetId"], str)
                and isinstance(finding["message"], str)
                and 1 <= utf16_length(finding["message"]) <= 300
                and finding["severity"] in {"info", "attention"},
                "Invalid finding",
            )
    delivery = run["delivery"]
    if delivery is not None:
        require(
            isinstance(delivery, dict)
            and set(delivery) == {"directory", "bundleDigest", "files"}
            and isinstance(delivery["directory"], str)
            and is_hash(delivery["bundleDigest"])
            and isinstance(delivery["files"], list),
            "Invalid delivery",
        )
        for file in delivery["files"]:
            require(
                isinstance(file, dict)
                and set(file) == {"name", "sha256"}
                and isinstance(file["name"], str)
                and is_hash(file["sha256"]),
                "Invalid delivery file",
            )


def evaluate(case: Any) -> Result:
    case_id = case.get("caseId", "unknown") if isinstance(case, dict) else "unknown"
    if not isinstance(case_id, str):
        case_id = "unknown"
    checks: list[Check] = []

    def check(name: str, operation: Any) -> bool:
        try:
            operation()
            checks.append(Check(name, True, "passed"))
            return True
        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            AttributeError,
            StopIteration,
        ):
            checks.append(Check(name, False, "Contract or invariant mismatch"))
            return False

    def envelope() -> None:
        require(
            isinstance(case, dict) and set(case) == {"caseId", "expected", "run"},
            "Invalid case envelope",
        )
        require(
            isinstance(case["expected"], dict)
            and set(case["expected"]) == {"status", "failureCode"},
            "Invalid expected outcome",
        )
        require(
            case["expected"]["status"] in STATUSES
            and (
                case["expected"]["failureCode"] is None
                or case["expected"]["failureCode"] in FAILURES
            ),
            "Invalid expected values",
        )
        require(isinstance(case["run"], dict), "Run must be an object")
        validate_shape(case["run"])

    if not check("contract", envelope):
        return Result(case_id, False, checks, [])
    run = case["run"]
    manifest = run["manifest"]
    assets = manifest["assets"]
    ids = {asset["id"] for asset in assets}

    def evidence() -> None:
        require(
            len(ids) == len(assets)
            and len({asset["name"] for asset in assets}) == len(assets),
            "Duplicate asset identity",
        )
        require(
            all(digest_text(asset["content"]) == asset["sha256"] for asset in assets),
            "Checksum mismatch",
        )
        motion = next(asset for asset in assets if asset["id"] == "motion")
        require(
            json.loads(motion["content"])["durationSeconds"]
            == manifest["durationSeconds"],
            "Motion metadata mismatch",
        )
        require(
            len(run["checks"]) == len(assets)
            and {item["assetId"] for item in run["checks"]} == ids
            and all(item["passed"] is True for item in run["checks"]),
            "Invalid evidence checks",
        )

    check("evidence_hashes", evidence)
    check(
        "input_digest",
        lambda: require(
            manifest_digest(manifest) == run["inputDigest"], "Input digest mismatch"
        ),
    )

    def policy() -> None:
        # A changed input restarts round numbering, so partition attempts by review.started events.
        segments: list[list[dict[str, Any]]] = []
        cursor = 0
        for event in run["audit"]:
            if event["event"] == "review.started":
                segments.append([])
            elif event["event"] == "provider.attempt":
                require(
                    bool(segments) and cursor < len(run["attempts"]),
                    "Attempt has no review",
                )
                attempt = run["attempts"][cursor]
                require(
                    event["result"] == f"{attempt['provider']}: {attempt['outcome']}",
                    "Attempt audit mismatch",
                )
                segments[-1].append(attempt)
                cursor += 1
        require(cursor == len(run["attempts"]), "Unaudited attempts")
        for segment in segments:
            require(len(segment) <= 2, "Attempt budget exceeded")
            require(
                not segment or segment[0]["provider"] == "Atlas fixture",
                "Routing order mismatch",
            )
            if len(segment) == 2:
                require(
                    segment[0]["outcome"] not in {"refusal", "valid"}
                    and segment[1]["provider"] == "Cedar fixture",
                    "Fallback after terminal output",
                )
            require(
                all(attempt["round"] == segment[0]["round"] for attempt in segment),
                "Round mismatch",
            )

    check("provider_policy", policy)
    check(
        "finding_references",
        lambda: require(
            run["review"] is None
            or all(finding["assetId"] in ids for finding in run["review"]["findings"]),
            "Unknown evidence reference",
        ),
    )

    def approval_binding() -> None:
        approval = run["approval"]
        require(
            run["status"] not in {"approved", "completed"} or approval is not None,
            "Missing approval",
        )
        require(
            run["status"]
            not in {"reviewing", "awaiting_approval", "failed", "rejected"}
            or approval is None,
            "Stale approval retained",
        )
        if approval:
            require(
                approval["inputVersion"] == manifest["version"]
                and approval["inputDigest"] == run["inputDigest"],
                "Approval does not bind current input",
            )
            grants = [
                event
                for event in run["audit"]
                if event["event"] == "approval.granted"
                and event["inputDigest"] == run["inputDigest"]
            ]
            require(
                bool(grants) and grants[-1]["at"] == approval["at"],
                "Approval has no matching audit",
            )

    check("approval_binding", approval_binding)

    def audit_chain() -> None:
        require(bool(run["audit"]), "Missing audit")
        require(
            [event["seq"] for event in run["audit"]]
            == list(range(1, len(run["audit"]) + 1)),
            "Audit sequence gap",
        )
        require(
            run["audit"][-1]["inputVersion"] == manifest["version"]
            and run["audit"][-1]["inputDigest"] == run["inputDigest"],
            "Audit does not end at current input",
        )
        deliveries = [
            event for event in run["audit"] if event["event"] == "delivery.created"
        ]
        for delivery in deliveries:
            require(
                any(
                    event["event"] == "approval.granted"
                    and event["seq"] < delivery["seq"]
                    and event["inputVersion"] == delivery["inputVersion"]
                    and event["inputDigest"] == delivery["inputDigest"]
                    for event in run["audit"]
                ),
                "Delivery occurred without matching approval",
            )

    check("audit_chain", audit_chain)

    def delivery_integrity() -> None:
        delivery = run["delivery"]
        require(
            (run["status"] == "completed") == (delivery is not None),
            "Delivery/state mismatch",
        )
        if delivery:
            files = delivery["files"]
            require(
                len(files) == 6 and len({file["name"] for file in files}) == 6,
                "Invalid bundle entries",
            )
            require(
                digest_text(compact(files)) == delivery["bundleDigest"],
                "Bundle digest mismatch",
            )
            require(
                all(
                    any(
                        file["name"] == asset["name"]
                        and file["sha256"] == asset["sha256"]
                        for file in files
                    )
                    for asset in assets
                ),
                "Bundle assets do not match input",
            )
            require(
                {file["name"] for file in files}
                == {asset["name"] for asset in assets}
                | {"manifest.json", "audit.json", "checksums.sha256"},
                "Unexpected bundle file",
            )

    check("delivery_manifest", delivery_integrity)

    def state_consistency() -> None:
        failure = run["failure"]
        require(
            run["status"] != "failed" or failure is not None,
            "Failed state needs a reason",
        )
        require(
            run["status"]
            not in {"awaiting_approval", "approved", "completed", "rejected"}
            or run["review"] is not None,
            "State requires reviewed evidence",
        )
        if run["status"] in {"awaiting_approval", "approved", "completed", "rejected"}:
            starts = [
                i
                for i, event in enumerate(run["audit"])
                if event["event"] == "review.started"
            ]
            require(bool(starts) and bool(run["attempts"]), "Missing current review")
            events = run["audit"][starts[-1] :]
            require(
                all(
                    event["inputVersion"] == manifest["version"]
                    and event["inputDigest"] == run["inputDigest"]
                    for event in events
                ),
                "Current review belongs to another input",
            )
            attempts = [
                event for event in events if event["event"] == "provider.attempt"
            ]
            last = run["attempts"][-1]
            require(
                bool(attempts)
                and last["outcome"] == "valid"
                and last["round"] == run["round"]
                and attempts[-1]["result"] == f"{last['provider']}: valid",
                "Current review has no successful provider",
            )
            requests = [
                event for event in events if event["event"] == "approval.requested"
            ]
            require(
                bool(requests) and requests[-1]["seq"] > attempts[-1]["seq"],
                "Current review has no approval request after success",
            )
            decisions = [
                event
                for event in events
                if event["event"]
                in {
                    "approval.requested",
                    "approval.granted",
                    "approval.rejected",
                    "delivery.created",
                    "delivery.failed",
                }
            ]
            require(
                decisions[-1]["event"]
                in {
                    "awaiting_approval": {"approval.requested"},
                    "approved": {"approval.granted", "delivery.failed"},
                    "completed": {"delivery.created"},
                    "rejected": {"approval.rejected"},
                }[run["status"]],
                "State does not match the latest decision",
            )
            if run["status"] in {"approved", "completed", "rejected"}:
                decision_type = (
                    "approval.rejected"
                    if run["status"] == "rejected"
                    else "approval.granted"
                )
                approvals = [
                    event for event in decisions if event["event"] == decision_type
                ]
                require(
                    bool(approvals) and approvals[-1]["seq"] > requests[-1]["seq"],
                    "Human decision precedes the current review request",
                )
        if failure:
            require(
                run["status"] == "failed"
                or (
                    run["status"] == "approved" and failure["code"] == "delivery_failed"
                ),
                "Failure/state mismatch",
            )
        if run["status"] == "failed" and failure["code"] in {
            "timeout",
            "invalid_output",
            "refusal",
            "unavailable",
        }:
            require(
                bool(run["attempts"])
                and run["attempts"][-1]["outcome"] == failure["code"],
                "Failure does not match attempt",
            )

    check("state_consistency", state_consistency)
    check(
        "expected_outcome",
        lambda: require(
            run["status"] == case["expected"]["status"]
            and (run["failure"]["code"] if run["failure"] else None)
            == case["expected"]["failureCode"],
            "Unexpected regression outcome",
        ),
    )
    return Result(
        case_id,
        all(item.passed for item in checks),
        checks,
        [attempt["elapsedMs"] for attempt in run["attempts"]],
    )
