"""Usage: python3 -m fieldcheck fixtures/baseline.jsonl --output report.json"""

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, NoReturn

from .evaluator import evaluate


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise ValueError(f"Non-finite number: {value}")


def bounded_depth(value: Any) -> None:
    pending: list[tuple[Any, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > 64:
            raise ValueError("JSON nesting exceeds 64 levels")
        if isinstance(current, dict):
            for key in current:
                key.encode("utf-8")
            pending.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
        elif isinstance(current, str):
            current.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check offline trace invariants; this is not a live-model benchmark."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = []
    try:
        if args.output and args.output.resolve() == args.input.resolve():
            raise ValueError("Report output must not overwrite the input")
        if args.input.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Input exceeds 16 MiB")
        with args.input.open(encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                if len(line.encode("utf-8")) > 1024 * 1024:
                    raise ValueError(f"Line {number} exceeds 1 MiB")
                try:
                    case = json.loads(
                        line,
                        parse_constant=reject_constant,
                        object_pairs_hook=strict_object,
                    )
                    bounded_depth(case)
                except (ValueError, RecursionError) as error:
                    raise ValueError(f"Invalid JSON at line {number}") from error
                results.append(evaluate(case))
        if not results:
            raise ValueError("Input has no cases")
        if len({item.case_id for item in results}) != len(results):
            raise ValueError("Case identifiers must be unique")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    elapsed = [value for result in results for value in result.local_fixture_elapsed_ms]
    report = {
        "reportVersion": "fieldcheck.report.v1",
        "scope": "offline synthetic regression invariants; no live-model quality claims",
        "cases": len(results),
        "passed": sum(item.passed for item in results),
        "failed": sum(not item.passed for item in results),
        "localFixtureTiming": {
            "attempts": len(elapsed),
            "medianMs": statistics.median(elapsed) if elapsed else None,
            "meaning": "Local fixture execution from input traces, not provider inference latency",
        },
        "results": [item.to_dict() for item in results],
    }
    serialized = (
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    if args.output:
        try:
            args.output.write_text(serialized, encoding="utf-8")
        except OSError:
            print("Output error: could not write report", file=sys.stderr)
            return 2
    print(
        f"{report['passed']}/{report['cases']} cases passed; {report['failed']} failed (offline invariants only)."
    )
    for result in results:
        if not result.passed:
            print(
                f"  {result.case_id}: {', '.join(check.name for check in result.checks if not check.passed)}"
            )
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
