#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
createPatch -overwrite > log.createPatch 2>&1
echo 'createPatch exit=0' >> execution_status.log
checkMesh > log.checkMesh.final 2>&1
echo 'checkMesh.final exit=0' >> execution_status.log
checkMesh -allTopology -allGeometry > log.checkMesh.detailed 2>&1
echo 'checkMesh.detailed exit=0 (inspect diagnostic text)' >> execution_status.log
tail -12 log.checkMesh.final
