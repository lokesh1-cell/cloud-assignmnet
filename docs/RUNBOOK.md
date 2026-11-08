# Build, measure and submit runbook

**Lokesh Yadav - 230101039**  
https://github.com/lokesh1-cell/cloud-assignmnet.git

Use the host dependency setup in README. Run from the project root. Keep `.env` credentials private; do not save Kubernetes Secret YAML or Docker Env inspection in evidence.

## Bring-up and shutdown

```bash
cp .env.example .env
# Set a local secret in .env before deploying.
make up
kubectl -n app get deploy,svc,ingress,hpa,pods
make down
```

The release assets are public and verified by SHA-256. `make up` restores teacher data and both models to SeaweedFS. To regenerate instead, configure Ollama's reachable endpoint, run `make label`, then `make clean-data`. `SHARD_COUNT=4` and each indexed worker's distinct index implement zero-based modulo selection. The successful final generation used two free runner groups with two concurrent workers per group.

## Repeat the complete live benchmark

The manual `.github/workflows/live-cluster.yml` workflow performs fresh-clone bring-up, weight-free image inspection, object-streaming checksums, actual container/cluster tests, diagnostics and teardown, saving its artifact. This is the most direct reproducible route. It uses free GitHub-hosted CPU runners and the public release.

For a prepared local running cluster, install `locust==2.47.0` and the worker host dependencies. Start a temporary `kubectl -n data port-forward svc/seaweedfs 8333:8333`, load your own `.env`, set S3_ENDPOINT to localhost, then run `python scripts/ci/verify_storage.py` and `python scripts/ci/live_checks.py`. The latter is an integration benchmark that changes deployments/HPA, kills Pods and starts/stops a test container; use the project's disposable cluster. It reads constrained-container credentials from the Kubernetes Secret. It writes `results/fresh/`, so archive an earlier local run before repeating.

`live_checks.py` captures 50 sequential requests under 1 CPU/1 GiB and no extra swap; exact fault output; three creation-to-Ready cohorts with S3-download logs and endpoint observations; the standard two-replica load; rollout/rollback and recovery under separate loads; and HPA scale-up/down. `memory.peak` is the constrained-container peak; `kubectl top` values are samples. The workflow then runs `make down` and records the cluster list.

## Manual rollout and recovery

For the standard balancing/load run, temporarily remove the HPA before forcing exactly two replicas; reapply it after the fixed-replica tests. Verify two Ready Pods before load.

```bash
kubectl -n app delete hpa command-parser
kubectl -n app scale deployment/command-parser --replicas=2
kubectl -n app rollout status deployment/command-parser
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m \
  --host http://localhost:8080 --csv results/loadtest
```

For rollout use a longer load window in terminal A, with a unique header output:

```bash
LOADTEST_HEADERS_OUT=results/rollout_headers.json locust -f tools/locustfile.py \
  --headless --users 4 --spawn-rate 4 --run-time 3m \
  --host http://localhost:8080 --csv results/rollout
```

In terminal B while it runs:

```bash
kubectl -n app set env deployment/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2
kubectl -n app rollout status deployment/command-parser
curl -i http://localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"weather in london"}'
kubectl -n app rollout undo deployment/command-parser
kubectl -n app rollout status deployment/command-parser
curl -i http://localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"weather in london"}'
```

Check actual v2 then v1 response headers and total failures <=0.5%. For recovery, start a separate two-minute load and delete a selected Pod:

```bash
kubectl -n app delete "$(kubectl -n app get pod -l app=command-parser -o name | head -1)"
kubectl -n app rollout status deployment/command-parser
kubectl -n app get pods
kubectl apply -f k8s/hpa.yaml
```

Require restored two Ready replicas and recovery failures <=2%. A successful rollout command alone is not failure-rate evidence. Use the integration helper for timestamped cold starts and HPA 1->2->1 observations; a shell timer around `kubectl wait` is not equivalent to Pod creation-to-Ready time.

## Read measurements

Keep CSV, final console and header snapshots unchanged. Locust's periodic CSV can precede completions during graceful shutdown. Compute error percentages and SLO with a single explicit denominator; balance shares use final successful-header totals. Require normal-load errors <=1%, p95 <=5000ms and each replica share >=30%.

```bash
kubectl -n app top pods
python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps 2.9425162385250454
make lint
make test
python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check
```

The rate must be replaced by your new measured throughput if repeating. Hypothetical per-replica hourly cost is 3.95 INR. Store sampled metrics during load, not only after it. The serving cluster has a single physical host.

## Report and packaging

```bash
python scripts/build_report_tex.py
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
python scripts/package_submission.py --technical-only
# After the student's genuine handwritten scan is available:
python scripts/package_submission.py --reflection /absolute/path/230101039.pdf
```

The final packaging command requires a <=3-page reflection and <=8-page report. It creates `../230101039.zip` with sources, results, report, README and dataset outputs, without model weights or credentials. Check the generated ZIP before uploading it to Classroom. The interim `-technical.zip` is not the complete submission. Git tag `final` points to the completed technical repository commit; model assets are in Release `model-v1`.
