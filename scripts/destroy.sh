#!/usr/bin/env bash
# make down: delete the whole k3d cluster. NOT RUN yet.
set -euo pipefail
k3d cluster delete cloud-assignment
