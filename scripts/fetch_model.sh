#!/usr/bin/env bash
# Fetch verified release models and the original teacher-generated dataset.
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${MODEL_RELEASE_TAG:-model-v1}"
mkdir -p models

fetch() {
  local version="$1"
  local checksum=model.sha256
  [ "$version" = v1 ] || checksum=model-v2.sha256
  if [ -f "models/$version/config.json" ] && [ -f "models/$version/files.sha256" ]; then
    (cd "models/$version" && sha256sum --check files.sha256)
    return
  fi
  gh release download "$TAG" --pattern "${version}.tar.gz" --pattern "$checksum" \
    --dir models --clobber
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
  gh release download "$TAG" --pattern teacher-data.tar.gz --dir models --clobber
  tar -xzf models/teacher-data.tar.gz datasets
fi
(cd datasets/v1 && sha256sum --check train.sha256)
