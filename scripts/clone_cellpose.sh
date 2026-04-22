#!/usr/bin/env bash
# Shallow-clone Cellpose for local reference (BSD-3-Clause). Not committed by default.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${ROOT}/third_party/cellpose"
mkdir -p "${ROOT}/third_party"
if [[ -d "${TARGET}/.git" ]]; then
  echo "Already exists: ${TARGET}"
  exit 0
fi
git clone --depth 1 https://github.com/MouseLand/cellpose.git "${TARGET}"
echo "Cloned Cellpose to ${TARGET}. See third_party/README.md for license."
