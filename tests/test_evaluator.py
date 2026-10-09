import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from fieldcheck.evaluator import evaluate

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    json.loads(line)
    for line in (ROOT / "fixtures/baseline.jsonl").read_text().splitlines()
]


class EvaluatorTests(unittest.TestCase):
    def case(self, name="healthy"):
        return deepcopy(next(case for case in CASES if case["caseId"] == name))

    def assert_failed(self, case, check_name):
        result = evaluate(case)
        self.assertFalse(result.passed)
        self.assertIn(
            check_name, [check.name for check in result.checks if not check.passed]
        )

    def test_all_exported_regression_cases_pass(self):
        for case in CASES:
            with self.subTest(case=case["caseId"]):
                self.assertTrue(evaluate(case).passed)

    def test_contract_version_is_explicit(self):
        case = self.case()
        case["run"]["contractVersion"] = "switchyard.run.v2"
        self.assert_failed(case, "contract")

    def test_unknown_fields_are_rejected(self):
        case = self.case()
        case["run"]["unrecognized"] = True
        self.assert_failed(case, "contract")

    def test_altered_asset_is_detected(self):
        case = self.case()
        case["run"]["manifest"]["assets"][0]["content"] += "changed"
        self.assert_failed(case, "evidence_hashes")

    def test_wrong_manifest_digest_is_detected(self):
        case = self.case()
        case["run"]["inputDigest"] = "0" * 64
        self.assert_failed(case, "input_digest")

    def test_evidence_references_are_checked(self):
        case = self.case()
        case["run"]["review"]["findings"][0]["assetId"] = "unknown"
        self.assert_failed(case, "finding_references")

    def test_current_approval_is_required(self):
        case = self.case("completed-bundle")
        case["run"]["approval"]["inputDigest"] = "0" * 64
        self.assert_failed(case, "approval_binding")

    def test_completed_state_cannot_omit_approval(self):
        case = self.case("completed-bundle")
        case["run"]["approval"] = None
        self.assert_failed(case, "approval_binding")

    def test_pending_state_cannot_retain_old_approval(self):
        case = self.case("approval-invalidated")
        case["run"]["approval"] = self.case("completed-bundle")["run"]["approval"]
        self.assert_failed(case, "approval_binding")

    def test_audit_sequence_gap_is_detected(self):
        case = self.case()
        case["run"]["audit"][1]["seq"] = 12
        self.assert_failed(case, "audit_chain")

    def test_unlogged_attempts_are_detected(self):
        case = self.case()
        case["run"]["attempts"].append(deepcopy(case["run"]["attempts"][0]))
        self.assert_failed(case, "provider_policy")

    def test_refusal_cannot_be_followed_by_fallback(self):
        case = self.case("refusal")
        run = case["run"]
        run["attempts"].append(
            {
                "provider": "Cedar fixture",
                "outcome": "valid",
                "elapsedMs": 0,
                "round": 1,
            }
        )
        run["audit"].insert(
            -1,
            {
                **run["audit"][-1],
                "event": "provider.attempt",
                "result": "Cedar fixture: valid",
            },
        )
        for i, event in enumerate(run["audit"], 1):
            event["seq"] = i
        self.assert_failed(case, "provider_policy")

    def test_modified_bundle_manifest_is_detected(self):
        case = self.case("completed-bundle")
        case["run"]["delivery"]["files"][0]["sha256"] = "0" * 64
        self.assert_failed(case, "delivery_manifest")

    def test_wrong_expected_outcome_fails(self):
        case = self.case()
        case["expected"]["status"] = "completed"
        self.assert_failed(case, "expected_outcome")

    def test_non_finite_timing_is_rejected(self):
        case = self.case()
        case["run"]["attempts"][0]["elapsedMs"] = float("nan")
        self.assert_failed(case, "contract")

    def test_boolean_revision_is_rejected(self):
        case = self.case()
        case["run"]["revision"] = True
        self.assert_failed(case, "contract")

    def test_missing_motion_fails_without_crashing(self):
        case = self.case()
        case["run"]["manifest"]["assets"][1]["id"] = "other"
        self.assert_failed(case, "evidence_hashes")

    def test_malformed_structures_do_not_crash(self):
        for malformed in [
            None,
            [],
            {},
            {"caseId": "bad", "run": {}},
            {"caseId": [], "expected": None, "run": None},
        ]:
            with self.subTest(value=malformed):
                self.assertFalse(evaluate(malformed).passed)


class CliTests(unittest.TestCase):
    def test_duplicate_keys_and_excessive_nesting_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.jsonl"
            for text in [
                '{"caseId":"a","caseId":"b"}\n',
                "[" * 2000 + "0" + "]" * 2000,
            ]:
                source.write_text(text)
                self.assertEqual(self.invoke(source).returncode, 2)

    def test_report_does_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            original = json.dumps(CASES[0]) + "\n"
            source.write_text(original)
            self.assertEqual(self.invoke(source, "--output", str(source)).returncode, 2)
            self.assertEqual(source.read_text(), original)

    def invoke(self, path, *options):
        return subprocess.run(
            [sys.executable, "-m", "fieldcheck", str(path), *options],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_independent_cli_outputs_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            result = self.invoke(
                ROOT / "fixtures/baseline.jsonl", "--output", str(output)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report["passed"], 9)
            self.assertEqual(report["failed"], 0)
            self.assertIn("no live-model quality", report["scope"])

    def test_negative_controls_exit_one(self):
        result = self.invoke(ROOT / "fixtures/negative-controls.jsonl")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("0/4", result.stdout)

    def test_invalid_json_and_empty_input_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.jsonl"
            for text in ["{bad json}\n", "\n", '{"value":NaN}\n']:
                source.write_text(text)
                self.assertEqual(self.invoke(source).returncode, 2)

    def test_duplicate_case_ids_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "duplicate.jsonl"
            line = json.dumps(CASES[0])
            source.write_text(line + "\n" + line + "\n")
            self.assertEqual(self.invoke(source).returncode, 2)

    def test_report_write_error_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                self.invoke(
                    ROOT / "fixtures/baseline.jsonl", "--output", directory
                ).returncode,
                2,
            )


if __name__ == "__main__":
    unittest.main()
