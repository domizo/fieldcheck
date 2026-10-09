# Fixture provenance

All content is original synthetic portfolio data. No company repository, customer asset, private project, credentials or historical work was used.

`baseline.jsonl` was produced on 2026-10-09 by actual execution of Switchyard's `scripts/demo.ts` in this workspace. It includes six provider scenarios plus completed delivery, changed-input approval invalidation and explicit retry recovery (9 snapshots total). Expectations are separately declared in the script, not copied from observed outcomes.

Run UUIDs, wall-clock audit timestamps, bundle audit hashes and measured local durations vary on regeneration. Asset bytes, fixture responses and scenario outcomes are deterministic. The snapshots are a frozen regression corpus, not independent samples of model behavior.

`make_negative_controls.py` derives four explicit mutations from the baseline. `negative-controls.jsonl` is intentionally invalid in semantic checks: modified asset bytes, retained v1 approval on v2, unknown evidence reference, and a mismatched expected status. Regenerate it after replacing the baseline.

The baseline intentionally includes local-only bundle manifests, not the delivery directory. Switchyard tests independently verify actual delivery files.
