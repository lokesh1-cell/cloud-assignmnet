#!/usr/bin/env bash
# Fetch verified release models and the original teacher-generated dataset.
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${MODEL_RELEASE_TAG:-model-v1}"
mkdir -p models
REPOSITORY="${MODEL_REPOSITORY:-lokesh1-cell/cloud-assignmnet}"

download_asset() {
  local asset="$1"
  if command -v gh >/dev/null 2>&1 && gh release download "$TAG" --repo "$REPOSITORY" \
    --pattern "$asset" --dir models --clobber; then
    return
  fi
  curl --fail --location --retry 3 \
    "https://github.com/$REPOSITORY/releases/download/$TAG/$asset" -o "models/$asset"
}

fetch() {
  local version="$1"
  local checksum=model.sha256
  [ "$version" = v1 ] || checksum=model-v2.sha256
  if [ -f "models/$version/config.json" ] && [ -f "models/$version/files.sha256" ]; then
    (cd "models/$version" && sha256sum --check files.sha256)
    return
  fi
  download_asset "${version}.tar.gz"
  download_asset "$checksum"
  (cd models && sha256sum --check "$checksum")
  mkdir -p "models/$version"
  tar -xzf "models/${version}.tar.gz" -C "models/$version"
  cp "models/$checksum" "models/$version/model.sha256"
  (cd "models/$version" && sha256sum --check files.sha256)
  echo "verified models/$version from release $TAG"
}
fetch v1
fetch v2

if [ ! -f datasets/v1/train.jsonl ]; then
  download_asset teacher-data.tar.gz
  tar -xzf models/teacher-data.tar.gz datasets
fi
(cd datasets/v1 && sha256sum --check train.sha256)
