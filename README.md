# CS3081 Cloud Computing Mini Project

**Name:** Lokesh Yadav  
**Roll number:** 230101039  
**GitHub:** https://github.com/lokesh1-cell/cloud-assignmnet.git

CPU-only sequence distillation of `phi3.5` into `EleutherAI/pythia-70m`, served by FastAPI on k3d with SeaweedFS object storage. The API parses English commands into `intent`, `date`, `time`, and `place`.

The seven technical tasks have new execution evidence. The four-page [report](report/report.pdf), [audit](docs/SUBMISSION_AUDIT.md), and [raw results index](results/README.md) describe what was verified and its limits. **The student's genuine handwritten reflection scan is still required to finish the submission ZIP.**

| Check | Measured result |
| --- | --- |
| Teacher generation / cleaning | 3000 unique IDs; 2848 retained; exact checksum reproduced |
| Teacher / base / v1 / v2 full-frame accuracy | 49% / 0% / 41% / 42% on 100 validation commands |
| v1 / v2 JSON validity | 100% / 99%; release CI passes the 95% gate |
| Image / constrained container | 1.267 GB; 50/50 requests at 1 CPU/1 GiB; peak 757.18 MiB |
| Standard 4-user, 2-minute load, CSV snapshot | 353 requests; 0 failures; p50 1200 ms; p95 2500 ms; 2.942516 rps |
| Rollout / recovery | 0.1825% / 0% failures; rollback header v1 verified |
| Cold start / HPA | 9, 8, 9 s; median 9 s; scale 1 -> 2 -> 1 verified |

The final drained load console has 356 successful requests and p50 1400 ms; its headers total 180+176. CSV is an earlier snapshot. Both original files are retained; see the report for denominator and cost details. Hidden model/network tests are unavailable.

## Build and deploy

Prerequisites: Docker, k3d, kubectl, Bash, Make, Python 3.11, curl and Internet access for the public release. GitHub CLI is optional for downloads. Docker must have sufficient memory for k3d, storage and two model replicas.

After cloning, create a host environment for storage helpers (the service and worker have their own isolated Docker environments):

```bash
git clone https://github.com/lokesh1-cell/cloud-assignmnet.git
cd cloud-assignmnet
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r worker/requirements.lock.txt
```

Bring-up from a prepared fresh clone uses two commands:

```bash
cp .env.example .env
# Edit the development secret in .env, then:
make up
```

`make up` creates `cluster/k3d.yaml`, builds/imports pinned CPU images, deploys storage, verifies/downloads the [model-v1 release](https://github.com/lokesh1-cell/cloud-assignmnet/releases/tag/model-v1), seeds both models and datasets to S3, and deploys the service. Credentials are injected through Kubernetes Secrets. `.env` and all model/data outputs are ignored by Git.

```bash
kubectl -n app get deploy,svc,ingress,hpa,pods
curl -i http://localhost:8080/parse -H 'Content-Type: application/json' \
  -d '{"text":"weather in london"}'
make down
```

The example may return a semantically incorrect prediction: the service validates schema, not intent correctness. `/healthz` is liveness; `/readyz` becomes 200 only after loading. `/parse` returns 503 while unready and 500 with `{"error":"invalid_model_output"}` for invalid raw output. Responses identify model version and Pod. `FAULT_INJECT=1` exercises the 500 path. Weights are downloaded from S3 at startup and excluded from the image.

## Reproduce training and evaluation

Use a separate Python 3.11 environment for training. Do not combine the training/service/worker lockfiles in one environment; they freeze independently tested runtimes.

```bash
python3.11 -m venv .venv-training
source .venv-training/bin/activate
python -m pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r training/requirements.lock.txt
bash scripts/fetch_model.sh
make train SUBSET=50
make train
make train-v2
make eval
```

The release supplies the genuine raw shards and cleaned dataset in `teacher-data.tar.gz`; the fetch helper restores them and checks the cleaned-data hash. Training is CPU-only, uses the first 1500 cleaned rows, and records every epoch loss, data hash, library versions, and seed. V1 uses seed 42, v2 seed 7. Models/tokenizers are saved locally and to configured S3 storage. The exact training environment is also under `results/fresh/`.

To regenerate teacher data rather than restore it, run Ollama with `ollama pull phi3.5` and `ollama serve`, then `bash scripts/run_workers_local.sh` and `make clean-data`. For actual concurrent cluster workers, configure the reachable Ollama endpoint in `k8s/worker-job.yaml`, then use `make label`; the indexed Job uses four global modulo shards in `pipeline`. Replies are never manually edited. `prompts/teacher_prompt.txt` and teacher generation settings are versioned. `make eval` evaluates base/v1 and, when Ollama is reachable, the teacher; v2 can be scored with `training/predict.py` and the provided scorer.

## Test and measure

```bash
python -m pip install pytest==8.3.3 pyflakes==3.2.0 fastapi==0.111.1 pydantic==2.8.2 httpx==0.27.2
make lint
make test
python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check
python scripts/subnet_calc.py
python -m pip install locust==2.47.0
make load
python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps 2.9425162385250454
```

`make load` uses the supplied Locust file, four users for two minutes through Ingress. Replace the cost command's rate with your own measured rate on a new machine. [The runbook](docs/RUNBOOK.md) covers rollout, recovery, cold starts and the automated live-check helper. Cost is hypothetical, not a cloud bill.

CI runs lint -> 30 tests -> actual release-model evaluation -> 95% JSON-validity gate, plus a history secret scan. [V1 CI](https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493781600) and [v2 CI](https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493785783) passed. The [deliberate untrained-model run](https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42475597603) fails at the gate with 0% validity. Workflow inputs select model source/version. The [live-cluster run](https://github.com/lokesh1-cell/cloud-assignmnet/actions/runs/42493789838) proves actual bring-up, benchmarks and teardown on a free single-host runner.

## Files and submission

`cluster/`, `k8s/`, `worker/`, `training/`, `service/`, `network/`, `scripts/`, `tools/`, `tests/`, and `.github/workflows/` contain executable/configuration deliverables. `data/` retains the supplied pool/validation/schema/rate card. `results/fresh/` contains new measurements; `results/historical/` preserves the supplied old evidence without treating it as the final experiment.

[AI_USE.md](AI_USE.md) explains assistance and checks. [Reflection guidance](report/reflection_draft.md) is a writing aid: the final scan must be genuinely handwritten, at most three pages, named `230101039.pdf` and include name, roll, and repository link.

Build the report from its Markdown source:

```bash
python scripts/build_report_tex.py
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
```

After supplying the handwritten scan:

```bash
python scripts/package_submission.py --reflection /absolute/path/230101039.pdf
```

This checks page limits and ZIP integrity and creates `../230101039.zip` with report, reflection, tracked sources/evidence, README and datasets, excluding weights and `.env`. `--technical-only` creates a clearly labelled interim archive while the scan is absent. The technical repository commit is tagged `final`; model assets remain in the Release. The serving cluster runs on one host, so these tests do not demonstrate physical host fault tolerance.
