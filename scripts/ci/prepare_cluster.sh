#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/fresh
curl -fsSL https://github.com/k3d-io/k3d/releases/download/v5.9.0/k3d-linux-amd64 -o /tmp/k3d
chmod +x /tmp/k3d
sudo install /tmp/k3d /usr/local/bin/k3d
python - <<'PY'
import secrets
from pathlib import Path
text=Path('.env.example').read_text().replace('change-me-local-dev-secret',secrets.token_hex(24))
Path('.env').write_text(text)
PY
k3d cluster create --config cluster/k3d.yaml
kubectl apply -f k8s/00-namespaces.yaml
bash scripts/create_secrets.sh
kubectl apply -f k8s/seaweedfs.yaml
kubectl -n data rollout status deploy/seaweedfs --timeout=240s
kubectl -n data port-forward svc/seaweedfs 8333:8333 > /tmp/storage-port-forward.log 2>&1 &
echo $! > /tmp/storage-port-forward.pid
for attempt in $(seq 1 60); do
  if curl -sf http://localhost:8333/status >/dev/null; then break; fi
  sleep 1
done
set -a
source .env
set +a
export S3_ENDPOINT=http://localhost:8333
python scripts/init_storage.py
