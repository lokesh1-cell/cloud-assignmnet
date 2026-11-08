# Runbook — build, run, measure, submit

**Name:** Lokesh Yadav  
**Roll number:** 230101039  
**GitHub:** [lokesh1-cell/cloud-assignmnet](https://github.com/lokesh1-cell/cloud-assignmnet.git)

Exact commands for the parts that need a running cluster, plus the project workflow.
Capture every command's output into `results/` (e.g. `... | tee results/<name>.txt`) — that is the
evidence the report and marking need.

---

## Workflow

1. Set up the cluster and object storage.
2. Label and clean the dataset.
3. Train and evaluate the models.
4. Deploy the service, run reliability and load tests, and update the report with your measurements.

## Task 1 — labelling evidence
```bash
make label
kubectl -n pipeline get pods -o wide | tee results/task1_workers.txt   # two pods, different index
make clean-data                                                        # writes results/clean_counts.json
```

## Task 4 — reliability tests (keep a load test running in another terminal where noted)

**Rolling update + rollback** (step 5):
```bash
# terminal A: load
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 4m \
  --host http://localhost:8080 --csv results/rollout | tee results/rollout.txt
# terminal B: while load runs
kubectl -n app set env deployment/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2
kubectl -n app rollout status deployment/command-parser
kubectl -n app rollout undo deployment/command-parser
kubectl -n app rollout status deployment/command-parser
```
Check `results/rollout_headers.json` for `X-Model-Version`: it should show v2 during, v1 after.
Failed requests must stay ≤ 0.5%.

**Recovery** (step 6) — delete a Pod under load:
```bash
kubectl -n app delete pod "$(kubectl -n app get pod -l app=command-parser -o name | head -1)"
kubectl -n app get pods -w | tee results/recovery.txt   # replica count returns to 2
```

**Cold start** (step 7) — three runs, report the median; show the model download in the logs:
```bash
for i in 1 2 3; do
  kubectl -n app delete pod -l app=command-parser
  start=$(date +%s)
  kubectl -n app wait --for=condition=ready pod -l app=command-parser --timeout=600s
  echo "run $i cold start: $(( $(date +%s) - start ))s"
done | tee results/coldstart.txt
kubectl -n app logs -l app=command-parser --tail=20 | tee results/coldstart_logs.txt   # shows the S3 download
```

**Load balancing** (step 8) — exactly two Ready replicas, read per-replica counts:
```bash
kubectl -n app scale deployment/command-parser --replicas=2
make load                                               # writes results/loadtest_headers.json
cat results/loadtest_headers.json                        # each replica should serve >= 30%
```

## Task 7 — performance, resources, cost
```bash
make load                                                # results/loadtest_stats.csv (p50, p95, rps, failures)
kubectl -n app top pods | tee results/top_pods.txt       # CPU + memory per pod during load
python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps <rps_from_csv> | tee results/cost.txt
```

## Container size + limits (Task 3)
```bash
docker images cloud-mini/service:v1 --format '{{.Size}}' | tee results/image_size.txt   # <= 2 GB
docker run --rm --cpus 1 --memory 1g ... cloud-mini/service:v1   # send 50 requests, watch for OOM
```
