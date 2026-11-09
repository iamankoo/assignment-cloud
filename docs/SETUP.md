# Build, setup, deployment, testing and shutdown

Aniket Raj · 230103030 · iamankoo. Status key: **[RAN]** executed locally with a log in `results/`; **[NOT RUN]** written but never executed.

## 1. Setup
```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git && cd Cloud-Assignment
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
cp .env.example .env        # development-only values; never commit .env
```
Needed for the cluster steps (not available on the machine used so far): Docker, k3d, kubectl, GNU Make, Ollama with `phi3.5`.

## 2. Test **[RAN]**
```bash
make test        # 29 unit tests passed (results/pytest_local.txt)
make lint        # pyflakes clean
make check       # lint + test + nacl + subnets in one go
make nacl        # own evaluator: 11/11 (results/nacl_eval_local.txt)
make subnets     # subnet plan (results/subnet_calc_local.txt)
```

## 2b. Demonstration without Docker, Kubernetes or a model **[RAN]**
`tools/demo_server.py` runs the real `service/app.py` with a keyword-rule **stub** instead of Pythia-70M (output: `results/demo_api_stub.txt`).
```bash
make demo                                  # terminal 1, http://127.0.0.1:8000
curl -i localhost:8000/healthz ; curl -i localhost:8000/readyz
curl -i -X POST localhost:8000/parse -H 'Content-Type: application/json' -d '{"text":"what is the weather in london"}'
FAULT_INJECT=1 python tools/demo_server.py --port 8001      # then POST /parse -> 500 {"error":"invalid_model_output"}
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 20s --host http://localhost:8000 --csv results/stub_smoke
make cost RPS=0.57                         # example (hypothetical) rate card -> 3.8499 INR per 1,000 requests
make slo REQUESTS=1000 FAILED=7            # 99% SLO -> budget 10 requests, 70% used
```
The stub proves the endpoints, headers, validation and Locust tooling work. It says nothing about model quality, latency or throughput of the real service.

## 2c. What to do when infrastructure is missing
| Missing | Consequence | Reproducible substitute |
|---|---|---|
| Docker daemon | Task 3 image build/size/50-request test not possible | `make demo` (stub) + the commands in section 3 on a machine with Docker |
| k3d / kubectl cluster | Task 4 and the cluster half of Task 7 not possible | unit tests of manifest fields (`make test`); commands in section 6 |
| Ollama + `commands_pool.jsonl` | Task 1 labelling not possible | sharding/cleaning logic tested on toy data; `make label` on a capable machine |
| `transformers` + labelled data | Task 2 training/scoring not possible | config and loop reviewed; `make train SUBSET=50` once data exists |
| Instructor's `score.py`, `nacl_sim.py` | evaluation/gate jobs cannot run | own NACL evaluator (11/11); add the kit files and trigger the manual CI jobs |

## 3. Build **[NOT RUN]**
```bash
docker build -f service/Dockerfile -t command-parser:v1 .
docker build -f worker/Dockerfile -t cloud-assignment/worker:v1 .
docker image inspect command-parser:v1 --format '{{.Size}}'    # must be <= 2 GB
```

## 4. Teacher labelling and cleaning **[NOT RUN]**
Requires the instructor's `commands_pool.jsonl` in `data/` and Ollama reachable from the cluster.

Start the host Ollama server with these settings (server-side; they are settings, not a record of a run):
```bash
export OLLAMA_HOST=0.0.0.0:11434     # listen on all interfaces so pods in k3d can reach it (default is localhost only)
export OLLAMA_NUM_PARALLEL=2         # two concurrent requests, one per labelling worker
export OLLAMA_FLASH_ATTENTION=true   # Flash Attention enabled (value as written in the reflection)
ollama serve
```
SeaweedFS (`cluster/seaweedfs.yaml`): 2 GiB PersistentVolumeClaim mounted at `/data` and a 1.5 GiB memory limit, matching the configuration described in the reflection. These values are in my own manifest; the student's original file was not provided, so whether the OOM described in the reflection occurred is unverified.

The worker Job reaches it through `OLLAMA_HOST=http://host.k3d.internal:11434` (a client-side URL set in `k8s/worker-job.yaml`; the same variable name, but a different meaning from the server setting above).
```bash
make up
python scripts/upload.py --bucket datasets --src data/commands_pool.jsonl --key commands_pool.jsonl
make label            # Indexed Job, 2 pods, shard = n mod 2
make clean-data       # counts and SHA-256
```

## 5. Training and evaluation **[NOT RUN]**
```bash
make train SUBSET=50
make train VERSION=v1
make eval VERSION=v1  # needs the instructor's tools/score.py and data/validation.jsonl
python scripts/upload.py --bucket models --src training/output/v1 --key v1
```

## 6. Deployment **[NOT RUN]**
```bash
make up
curl -X POST http://localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"what is the weather in london"}'
kubectl -n app get pods,svc,ingress,hpa
```
Rolling update and rollback: `kubectl -n app set env deploy/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2`, then `kubectl -n app rollout undo deploy/command-parser`.

## 7. Load test **[NOT RUN]**
```bash
make load
python scripts/cost.py --rate-card data/rate_card.json --replicas 2 --cpu 1 --mem-gib 1 --rps <measured>   # the kit's rate card; data/rate_card.example.json is hypothetical
python scripts/slo.py --requests <n> --failed <f> --target 99
```

## 8. Shutdown **[NOT RUN]**
```bash
make down
```

## 9. Model artifacts
Weights are never committed. The Releases `reference-nanoparse-v1.0` (provenance record) and `mock-demo-v1.0` (mock package) contain **no model archives**: the externally sourced archives were removed because redistribution permission could not be established, and this project has not trained a model yet. Your own v1/v2 archives, checksums and Release are still to be produced; see `RELEASE_METADATA.md`.
