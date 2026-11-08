# Cloud Assignment — Command Parser

**Name:** Lokesh Yadav  
**Roll number:** 230101039  
**Course:** CS3081 — Cloud Computing  
**GitHub:** [lokesh1-cell/cloud-assignmnet](https://github.com/lokesh1-cell/cloud-assignmnet.git)

This project converts English commands into structured JSON. An Ollama `phi3.5`
teacher labels commands, a `pythia-70m` student learns from those labels, and a
FastAPI service serves the student on a local k3d Kubernetes cluster. SeaweedFS
provides S3-compatible storage for datasets and model files.

## Submission audit status

The source is organized into task commits, and the compiled report is at
[`report/report.pdf`](report/report.pdf). This is **not yet a complete submission**:
trained model releases, raw teacher shards, the cleaned dataset, and several
required live-run checks remain unavailable. Saved scores reproduce from saved
predictions, but that does not verify the missing model weights. See the
[task-by-task audit](docs/SUBMISSION_AUDIT.md) before submitting.

## Pipeline and output

```text
Command pool → teacher workers → cleaning → student training
                                             ↓
                              model storage → FastAPI → /parse
```

The parser returns `intent`, `date`, `time`, and `place`. For example, a valid
response for `weather in london` is:

```json
{"intent": "weather_query", "date": null, "time": null, "place": "london"}
```

Model predictions can be incorrect. The service checks the output schema and
returns HTTP 500 for invalid model output. Valid JSON does not guarantee a correct
prediction.

## Repository layout

| Directory | Purpose |
| --- | --- |
| `cluster/` | Local k3d configuration |
| `data/` | Command pool, validation set, schema, and indicative rate card |
| `prompts/` | Teacher instructions and examples |
| `worker/` | Sharded labelling, cleaning, and storage helpers |
| `training/` | Student training, prediction, and hyperparameters |
| `service/` | FastAPI endpoints, model loader, and Docker image |
| `k8s/` | Storage, worker Job, deployment, service, ingress, and HPA |
| `network/` | Subnet plan, access rules, and packet samples |
| `scripts/`, `tools/` | Setup, evaluation, scoring, load testing, and cost tools |
| `tests/` | Unit and API tests |
| `results/` | Saved predictions, scores, logs, and measurements |
| `report/`, `docs/` | Report sources, reflection draft, and runbook |

## Setup

Use Python 3.11, Bash, and Make. Cluster deployment also requires Docker, k3d, and
kubectl. Teacher labelling requires Ollama; downloading release models requires
GitHub CLI (`gh`). Use a Bash environment for the shell helpers.

```bash
git clone https://github.com/lokesh1-cell/cloud-assignmnet.git
cd cloud-assignmnet
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r training/requirements.txt -r service/requirements.txt -r worker/requirements.txt
python -m pip install pytest pyflakes httpx locust
cp .env.example .env
```

Run commands from the folder containing `Makefile`. Edit the development secret
in `.env` before deploying. Keep credentials and model weights out of Git.

## 1. Label and clean the data

Download the teacher and start Ollama:

```bash
ollama pull phi3.5
ollama serve
```

If Ollama is already running, use the existing server. In another terminal with
the Python environment activated, generate the initial local dataset:

```bash
bash scripts/run_workers_local.sh
make clean-data
```

The two workers write `datasets/teacher/shard-0.jsonl` and `shard-1.jsonl`.
Cleaning produces `datasets/v1/train.jsonl`, its SHA-256 checksum, and
`results/clean_counts.json`. It filters invalid replies, incorrect keys,
unsupported intents, invented slot values, and duplicate commands.

For cluster-based labelling, bring up the cluster, ensure Ollama is reachable
from it, and run `make label`. The indexed Job is defined in
[`k8s/worker-job.yaml`](k8s/worker-job.yaml). See the [runbook](docs/RUNBOOK.md)
for the cluster workflow and storage setup.

## 2. Train and evaluate the student

```bash
make train SUBSET=50   # optional smoke run
make train            # full v1 run
make train-v2         # second version, seed 7
make eval
```

Training reads [`training/config.yaml`](training/config.yaml), saves weights and
tokenizer files under `models/v1/` and `models/v2/`, and creates
`models/v1.tar.gz` and `models/v2.tar.gz`. Object storage uploads are attempted
when configured. Evaluation compares the teacher, untrained base, and v1 student;
teacher evaluation is skipped if Ollama is unavailable.

For release-based setup, upload `v1.tar.gz` and `v2.tar.gz` to the `model-v1`
release in [this repository](https://github.com/lokesh1-cell/cloud-assignmnet).
Keep each archive consistent with its `model.sha256`. The fetch helper uses those
asset names. Do not commit weights.

## 3. Deploy and query the service

With trained local model files or downloadable release assets available:

```bash
make up
kubectl -n app get deploy,svc,ingress,hpa,pods
curl -i http://localhost:8080/parse \
  -H 'Content-Type: application/json' \
  -d '{"text":"weather in london"}'
```

`make up` creates the cluster, builds and imports images, deploys SeaweedFS,
initializes buckets, seeds model files, and deploys the service. The model must
load before the readiness probe permits traffic. Use `make build` to rebuild
images and `make deploy` to reapply the deployment.

| Endpoint | Behavior |
| --- | --- |
| `GET /healthz` | HTTP 200 while the process is alive |
| `GET /readyz` | HTTP 503 until the model is ready, then 200 |
| `POST /parse` | Four-key JSON on success; 503 if unready; 500 for invalid output |

Parse responses include `X-Model-Version` and `X-Served-By` headers.
`FAULT_INJECT=1` forces the invalid-output path for testing.

## 4. Test, measure, and estimate cost

```bash
make lint
make test
python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check
python scripts/subnet_calc.py
make load
```

The load target runs four Locust users against `http://localhost:8080` for two
minutes and saves CSV output under `results/loadtest`. Replace `MEASURED_RPS`
with the positive request rate from your run:

```bash
python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps MEASURED_RPS
```

The rate card is indicative. Existing files in `results/` are saved evidence;
rerun the commands to obtain measurements for a new environment.

## Documentation and submission

- [Project report](report/report.md) and [LaTeX source](report/report.tex).
- [Runbook](docs/RUNBOOK.md) for rollout, rollback, recovery, and cold-start checks.
- [Subnet and access-control explanation](network/subnets.md).
- [AI assistance record](AI_USE.md).
- [Reflection draft](report/reflection_draft.md); name the handwritten scan `230101039.pdf`.

Both report sources contain the student details and repository link. To compile
the LaTeX report (run twice to update links):

```bash
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
```

Alternatively, generate a PDF from the Markdown source:

```bash
python -m pip install markdown xhtml2pdf
python scripts/render_report.py
```

## Teardown

```bash
make down
```

This deletes the `cloud-mini` k3d cluster.

## CI and model release contract

The Actions workflow runs lint, tests, release-model inference, a 95% validity
gate, and a separate Gitleaks history scan. Publish `v1.tar.gz`, `v2.tar.gz`,
and the v1 archive's `model.sha256` to release `model-v1`. The checksum file
must name `v1.tar.gz`, and the archives must contain the tokenizer and model
files at their root. Model weights remain outside Git.

Use the workflow's manual `untrained` input to demonstrate the deliberately
failing quality gate with the base Pythia model. A missing release is an
artifact failure, not a quality-gate demonstration.
