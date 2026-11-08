# Results evidence index

All new technical runs belong to `lokesh1-cell/cloud-assignmnet` on 8 November 2026. The report and audit link their actual run IDs.

- Root `pred_*.jsonl`, `teacher_validation.json`, `score_*.json`, `clean_counts.json`, and `loss_v*.csv`: current raw predictions, provided-scorer reports, cleaning counts, and actual epoch losses. Every prediction set has 100 validation IDs.
- `fresh/`: aggregation/training evidence and local independent dataset/model verification. Data SHA-256 is recorded alongside model lineage. Trained files/raw datasets themselves are Release assets, not Git model blobs.
- `fresh/live/`: complete downloaded live run artifact, including constrained container, model-storage streaming hashes, readiness/cold starts, load/rollout/recovery/HPA output, per-Pod metrics, image files/history and teardown.
- `ci_release_v1/` and `ci_release_v2/`: successful independent release-model evaluations and run metadata.
- `raw_gate_demo/`: actual deliberately bad untrained-model quality-gate failure (0% validity), with lint/tests/secret scan status.
- `image_build/`: actual first successful CPU-only image build evidence. The final live image size is recorded in `fresh/live/`.
- `performance_analysis.json`: cost, SLO, sampled resource ranges and counting-snapshot explanation derived from the raw live artifacts.
- `historical/`: unchanged supplied old evidence; superseded and excluded from final reported measurements.

Locust's CSV writer stops before the final in-flight completions are drained. Standard CSV: 353/0 failures, p50 1200ms; final console: 356/0, p50 1400ms; both p95 2500ms. Final headers are 180+176 successes. Preserve and identify these snapshots; do not combine their totals. Rollout/recovery snapshots have the same timing distinction.

The live artifact's final `limited_container_failure_logs.txt` says the container no longer exists, and its final inspection is empty: cleanup diagnostics occurred after successful removal. Valid earlier `limited_container_inspect.json`, all 50 request records, cgroup peak and logs provide the actual constrained-container result. No raw evidence has been removed to conceal this cleanup artifact.
