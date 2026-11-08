# Submission audit - CS3081

**Name:** Lokesh Yadav  
**Roll:** 230101039  
**Repository:** https://github.com/lokesh1-cell/cloud-assignmnet.git  
**Audit date:** 8 November 2026

All seven technical tasks now have newly generated execution evidence. The remaining submission input is the student's genuine handwritten reflection PDF (maximum three pages). Hidden 300-command model and 20-packet network tests are unavailable; no hidden-test pass is claimed. See the four-page report for architecture, decisions, limitations and measured results.

| Task | Verified evidence |
| --- | --- |
| 1 | Two runner groups with two simultaneous pipeline workers each; all four modulo shards cover exactly 3000 IDs. Strict re-clean gives 2848 rows and reproduces SHA-256 `5cda236a5762e5b0d56b0d502be90410e3b321205f5007b18c7154d453823f40`. Counts sum to 3000. |
| 2 | 50-row make smoke run and two real CPU-trained 1500-example models. v1/v2 are distinct; seven files per model and release archives verified, including streaming S3 hashes. Teacher/base/v1/v2 validity 100/0/100/99%; full frame 49/0/41/42%. Raw outputs retained. |
| 3 | Fresh image 1,267,334,183 bytes, no weights. 50/50 requests with 1 CPU/1 GiB, OOM false, cgroup peak 793,964,544 bytes. Live fault request exact HTTP 500 body. Runtime dependencies frozen; immutable base image. |
| 4 | Ingress, probes and no-endpoints-while-loading observed. HPA 1->2->1. Cold cohorts 9/8/9 seconds (median 9). Rollout 1/548 failures=0.1825%; rollback header v1. Recovery 0/354 failures, restored in 7.42 seconds. Final balancing 180/176 (each >=30%). |
| 5 | Minimal contiguous /22,/24,/25,/27 allocation; NACL checker passes 6/6 public packets. |
| 6 | Fresh-clone make up and make down succeeded. 30 tests/lint pass. Both release-model CI runs pass. Actual base-model bad gate fails at 0% validity. Gitleaks reports zero unsuppressed findings; seven inspected checksum/public-GPG false positives have exact historical fingerprint exceptions. AI use disclosed. |
| 7 | Required two-minute four-user load: CSV p50 1200ms, p95 2500ms, 2.942516rps, 0/353 failures. Per-Pod resource samples retained. Hypothetical cost 0.74577 INR/1000 requests. 99% SLO budget=3.53 failures (3 whole), zero used. Six review rows in report. |

## Execution links

- Teacher label jobs and teacher evaluation: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42475264293 (parent deliberately cancelled after completed label/evaluation jobs to use corrected downstream cleaner/trainer).
- Successful aggregation/smoke/full training: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42482536228
- Model/tokenizer/data assets: https://github.com/lokesh1-cell/cloud-assignmnet/releases/tag/model-v1
- Passing v1 CI: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493781600
- Passing v2 CI: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493785783
- Deliberate bad-model quality gate: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42475597603
- Actual live cluster/container checks: https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493789838

## Evidence qualifications

The Locust CSV is its last periodic snapshot, before graceful shutdown drained in-flight work. Standard CSV totals are 353 with zero failures and p50 1200ms; the final console/header totals are 356 with zero failures and p50 1400ms. Both p95 values are 2500ms. Per-replica balancing uses only the matching final headers (180+176). Cost and SLO use the CSV snapshot explicitly. The original logs/CSVs have not been rewritten to force matching totals.

`kubectl top` is sampled, not a continuous peak. The constrained container's cgroup `memory.peak` separately measures peak memory. The final cleanup diagnostic reports no limited-parser container because that successfully tested container had already been removed; its earlier valid inspection, request log and cgroup evidence are canonical. All raw diagnostics remain preserved.

Earlier supplied scores and incomplete reliability logs are in `results/historical/`; they are superseded, not merged into current measurements. Correctness fixes preserve the intended pipeline: exact unedited teacher/model text, type-safe intents, exact nonempty spans, secure/paginated storage downloads, retries, CPU thread limits and graceful shutdown. Teacher data, models and live tests were regenerated because the original weights/shards were absent.

## Submission finishing step

The technical report is `report/report.pdf` (four pages). Place the student's real handwritten scan at `230101039.pdf` (at most three pages), then run `python scripts/package_submission.py`. The required final ZIP is `230101039.zip`, containing report, reflection, final sources, results, datasets and README. The technical commit is tagged `final`. A `230101039-technical.zip` interim archive intentionally excludes the unavailable scan and is not the complete Classroom submission. The stated deadline is 9 November, 11 AM.
