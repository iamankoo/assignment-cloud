# Build, setup, deployment, testing and shutdown

Aniket Raj · 230103030 · iamankoo. Status key: **[RAN]** executed locally with a log in `results/`; **[NOT RUN]** written but never executed.

## 1. Setup
```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git && cd Cloud-Assignment
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
cp .env.example .env        # development-only values; never commit .env
```
Needed for the cluster steps (not available on the machine used so far): Docker, k3d, kubectl, GNU Make, Ollama with `phi3.5`.

## 2. Test **[RAN]**
```bash
make test        # 14 unit tests passed (results/pytest_local.txt)
make lint        # pyflakes clean
make nacl        # own evaluator: 11/11 (results/nacl_eval_local.txt)
make subnets     # subnet plan (results/subnet_calc_local.txt)
```

## 3. Build **[NOT RUN]**
```bash
docker build -f service/Dockerfile -t command-parser:v1 .
docker build -f worker/Dockerfile -t cloud-assignment/worker:v1 .
docker image inspect command-parser:v1 --format '{{.Size}}'    # must be <= 2 GB
```

## 4. Teacher labelling and cleaning **[NOT RUN]**
Requires the instructor's `commands_pool.jsonl` in `data/` and Ollama reachable from the cluster.
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
python scripts/cost.py --rate-card data/rate_card.json --replicas 2 --cpu 1 --mem-gib 1 --rps <measured>
```

## 8. Shutdown **[NOT RUN]**
```bash
make down
```

## 9. Model artifacts
Weights are never committed. The Release `reference-nanoparse-v1.0` contains externally sourced reference archives; see `RELEASE_METADATA.md`.
