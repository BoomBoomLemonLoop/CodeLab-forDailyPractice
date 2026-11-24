#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
test -s mapping_report.json
if interFoam > log.interFoam 2>&1; then
    echo 'interFoam exit=0' | tee -a execution_status.log
else
    rc=$?; echo "interFoam exit=$rc" | tee -a execution_status.log
    tail -60 log.interFoam; exit "$rc"
fi
tail -25 log.interFoam
