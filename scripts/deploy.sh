#!/usr/bin/env bash
# make up: cluster + storage + images + app. NOT RUN yet (needs docker, k3d, kubectl).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "copy .env.example to .env first"; exit 1; }
set -a; . ./.env; set +a
CLUSTER=cloud-assignment

k3d cluster list | grep -q "^$CLUSTER" || k3d cluster create --config cluster/k3d.yaml

for ns in data pipeline app; do kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -; done
for ns in pipeline app; do
  kubectl -n "$ns" create secret generic s3-credentials \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" --dry-run=client -o yaml | kubectl apply -f -
done
cat > /tmp/s3.json <<JSON
{"identities":[{"name":"svc","credentials":[{"accessKey":"$AWS_ACCESS_KEY_ID","secretKey":"$AWS_SECRET_ACCESS_KEY"}],"actions":["Admin","Read","Write","List"]}]}
JSON
kubectl -n data create secret generic seaweedfs-s3-config --from-file=s3.json=/tmp/s3.json --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/s3.json
kubectl apply -f cluster/seaweedfs.yaml
kubectl -n data rollout status deploy/seaweedfs --timeout=180s

docker build -f service/Dockerfile -t command-parser:v1 .
docker build -f worker/Dockerfile -t cloud-assignment/worker:v1 .
k3d image import command-parser:v1 cloud-assignment/worker:v1 -c "$CLUSTER"

# Models must already be in the `models` bucket (python scripts/upload.py ...) before the pods can become Ready.
kubectl apply -f k8s/app.yaml
echo "applied. check: kubectl -n app get pods ; curl -X POST localhost:8080/parse -H 'content-type: application/json' -d '{\"text\":\"what is the weather in london\"}'"
