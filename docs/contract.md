# Portable boundary and trade-offs

Input is JSONL: one `{caseId, expected: {status, failureCode}, run}` envelope per nonempty line. The complete run uses `switchyard.run.v1`, whose frozen JSON Schema is [run.schema.json](run.schema.json). The evaluator implements explicit checks for this synthetic contract, without a generic schema library.

The input digest uses compact UTF-8 JSON with these keys in order: `version`, `title`, `durationSeconds`, `assets`. Each ordered asset entry has `id`, `name`, `sha256`, `mediaType`, in that order. Content bytes are hashed independently; they are not duplicated in the digest metadata. In the TypeScript producer this is `JSON.stringify`; in Python it is `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`. This v1 fixture contract uses integer metadata and known strings, avoiding general cross-language number/canonicalization claims.

Delivery digest covers compact JSON of the ordered `{name, sha256}` list. Fieldcheck checks that list and its links to current assets, not filesystem bytes. The application verifies bytes when creating and downloading a bundle. The bundle audit ends at approval; the producer's run audit records delivery afterward.

The audit is not signed or cryptographically chained. Sequential IDs are useful to detect malformed exports, not to prove authenticity. Approval is a demo decision without authenticated actor identity. The evaluator cannot detect a consistently forged trace from an adversarial producer.

A dependency-free runner is easy to inspect and execute in a clean checkout. The cost is maintaining the explicit contract checks. A broader evaluation system would need schema generation or an established validator, independent human labels, richer datasets, quality metrics and statistical analysis. Those are not part of this implementation.

Negative controls show that selected invariant failures are detected. They do not establish detection rates on unseen errors or live model behavior. The expected labels are deliberately declared regression outcomes; they are not independent human assessments of review quality.
