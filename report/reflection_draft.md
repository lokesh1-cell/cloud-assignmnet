# Handwritten reflection guidance - not a submission scan

Name: Lokesh Yadav  
Roll: 230101039  
GitHub: https://github.com/lokesh1-cell/cloud-assignmnet.git

Write your own reflection by hand, then scan it as exactly `230101039.pdf`, at most three pages. Include your name, roll and full repository link. This typed guidance cannot fulfil the handwriting requirement. Describe what you personally understood and did, and distinguish assistant-executed tests from your own manual work.

## Learning

Explain sequence-level distillation (teacher-generated text targets), how it differs from soft-logit matching, and why this saved text pipeline lacks the teacher distributions/aligned vocabulary needed for the latter. Explain S3 model loading, readiness versus liveness, limits versus requests, HPA and stateless reply rules.

## Challenges and findings to reflect on

CPU teacher generation required parallel resumable shards. Strict cleaning retained 2848/3000 records, with 103 rejected labels and 49 duplicate commands. Teacher raw text was preserved. Training used the first 1500 cleaned examples only.

Teacher full frame was 49%; student v1 41%, v2 42%. JSON validity was 100%/99% for v1/v2, so well-formed output still has semantic errors. V2's V091 error was not repaired or hidden.

The weight-free image was 1.267 GB. All 50 constrained requests succeeded; cgroup peak was 757.18 MiB. Standard CSV p95 was 2500ms at 2.942516rps, zero failures; cold start median was 9s. Rollout failures were 0.1825%, recovery 0%, and HPA scaled 1->2->1. Cost under the hypothetical card was 0.74577 INR per 1000 requests.

CSV and final console totals differ because shutdown drained in-flight requests: documenting that difference is better than changing original evidence. A single-host test cannot prove machine-failure tolerance.

## Improvements and AI use

Discuss better label prompts/error analysis, request batching or quantisation measured under the same limits, repeated failures on independent hosts, API authentication/TLS, and a fuller cost model. Explain Codex assistance honestly using `AI_USE.md`; do not copy claims that you personally performed every automated action. Add your own observations, challenges and learning in your own words.
