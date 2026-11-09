.PHONY: up down label clean-data train eval eval-teacher package test lint load nacl subnets demo cost slo check
SUBSET ?= 0
VERSION ?= v1

up:            ## cluster + storage + images + app   [NOT RUN]
	bash scripts/deploy.sh
down:          ## delete the k3d cluster            [NOT RUN]
	bash scripts/destroy.sh
label:         ## 2 parallel teacher workers        [NOT RUN]
	kubectl apply -f k8s/worker-job.yaml
	kubectl -n pipeline wait --for=condition=complete job/teacher-label --timeout=6h
clean-data:    ## merge shards -> datasets/v1/train.jsonl [NOT RUN on real output]
	python worker/clean.py --shards datasets/teacher/shard-0.jsonl datasets/teacher/shard-1.jsonl
train:         ## make train / make train SUBSET=50 [NOT RUN]
	python training/train.py --version $(VERSION) $(if $(filter-out 0,$(SUBSET)),--subset $(SUBSET),)
eval:          ## predict + score (needs kit score.py)  [NOT RUN]
	python tools/predict.py --model training/output/$(VERSION) --input data/validation.jsonl --out results/pred_$(VERSION).jsonl
	python tools/score.py results/pred_$(VERSION).jsonl data/validation.jsonl --out results/score_$(VERSION).json --min-validity 95
eval-teacher:  ## teacher raw outputs on validation.jsonl (needs Ollama + kit data)   [NOT RUN]
	python tools/predict_teacher.py --input data/validation.jsonl --out results/pred_teacher.jsonl
package:       ## tar.gz + sha256 + manifest of a trained model: make package VERSION=v1   [NOT RUN: no trained model]
	python scripts/package_model.py --model-dir training/output/$(VERSION) --version $(VERSION) --out-dir dist
test:          ## unit tests                         [TESTED]
	python -m pytest -q
lint:          ## pyflakes                           [TESTED]
	python -m pyflakes service tools scripts tests worker training
load:          ## standard Locust run at :8080       [NOT RUN]
	mkdir -p results
	locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
nacl:
	python tools/nacl_eval.py network/nacl.json network/packets_own.jsonl
subnets:
	python scripts/subnet_calc.py
demo:          ## local stub-model service on :8000 (no Docker, no model)   [TESTED]
	python tools/demo_server.py
cost:          ## cost per 1,000 requests: make cost RPS=<measured>
	python scripts/cost.py --rate-card data/rate_card.example.json --replicas 2 --cpu 1 --mem-gib 1 --rps $(RPS)
slo:           ## error budget: make slo REQUESTS=<n> FAILED=<f>
	python scripts/slo.py --requests $(REQUESTS) --failed $(FAILED) --target 99
check: lint test nacl subnets
