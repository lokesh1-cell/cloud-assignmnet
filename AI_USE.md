# AI use and verification

**Name:** Lokesh Yadav  
**Roll:** 230101039  
**GitHub:** https://github.com/lokesh1-cell/cloud-assignmnet.git

OpenAI Codex assisted with reviewing the supplied project against the assignment, personalising documentation, restructuring the README/report, repository setup and task commits, correctness fixes, regression tests, dependency locks, GitHub Actions workflows, release publication and execution orchestration. Codex also analysed the actual resulting artifacts and compiled/visually checked the report. These executions were performed by the assistant using the student's repository and free GitHub runner resources; this document does not claim the student manually ran every command.

The initially supplied project included a statement attributing scaffolding to Claude/Claude Code. That earlier development history cannot be independently verified here. Its old measurements remain under `results/historical/` and are not evidence for the regenerated models or new live tests.

Ollama with the assignment's fixed `phi3.5` teacher generated all new training labels at temperature 0, seed 42. It is part of the required machine-learning pipeline. No Codex-generated labels, manually corrected labels, other students' models, or validation labels were substituted for teacher training replies.

Verification included exact 3000-ID shard coverage; byte-for-byte strict-cleaner reproduction and checksum; first-1500 training lineage; actual 50-row smoke training; raw teacher/base/student evaluation with the provided scorer; independent release-model CI for v1/v2; archive and seven-file manifests checked locally and against S3; container image/limits/fault tests; real rollout/recovery/HPA/cold-start/load tests; 30 unit/API tests, lint and the provided NACL simulator. A deliberate untrained-model run really failed the 95% quality gate. Gitleaks history scanning found zero secrets. The final evidence commit triggered seven generic-key false positives: six tokenizer SHA-256 entries and the CPython base-image public GPG fingerprint. Each was inspected and its exact historical fingerprint recorded in `.gitleaksignore`; no directory or rule was disabled.

AI suggestions required corrections: malformed intent types could raise errors, whitespace stripping altered raw teacher output, normalisation could accept nonexact spans, decoded-text extraction could hide invalid output, and missing artifacts made old score claims unverifiable. These were corrected and the necessary data, training and cluster experiments were actually executed. CPU thread limits and graceful shutdown addressed runtime constraints. Report numbers come from saved output files, with mismatched Locust shutdown snapshots identified explicitly rather than silently edited.

Limits remain: teacher noise, small-model semantic errors, no hidden-test access, one-host serving, short benchmark windows and sampled resource metrics. The handwritten reflection must be written by the student in their own words and genuinely scanned; AI drafting guidance is not a substitute for that requirement.
