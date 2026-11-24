#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
{ printf 'WM_PROJECT_VERSION=%s\n' "$WM_PROJECT_VERSION"; command -v blockMesh; command -v interFoam; } > environment.log
for step in blockMesh surfaceCheck surfaceFeatureExtract snappyHexMesh checkMesh; do
    case "$step" in
      surfaceCheck) args=(constant/triSurface/spout.stl);;
      snappyHexMesh) args=(-overwrite);;
      checkMesh) args=(-allTopology -allGeometry);;
      *) args=();;
    esac
    echo "Running $step"
    if "$step" "${args[@]}" > "log.$step" 2>&1; then
        echo "$step exit=0" | tee -a execution_status.log
    else
        rc=$?; echo "$step exit=$rc" | tee -a execution_status.log
        tail -50 "log.$step"; exit "$rc"
    fi
done
tail -30 log.checkMesh
