.PHONY: test lint nacl subnets up down
test:
	python -m pytest -q
lint:
	python -m pyflakes service tools scripts tests
nacl:
	python tools/nacl_eval.py network/nacl.json network/packets_own.jsonl
subnets:
	python scripts/subnet_calc.py
# NOT IMPLEMENTED / NOT RUN: cluster targets need k3d + SeaweedFS scripts that are not written yet.
up:
	@echo "not implemented: see README (Task 1/4 cluster setup not done)"; exit 1
down:
	k3d cluster delete cloud-assignment
