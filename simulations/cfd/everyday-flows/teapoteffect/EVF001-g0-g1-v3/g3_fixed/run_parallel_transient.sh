#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
test -s mapping_report.json
test ! -e log.interFoam
decomposePar -force > log.decomposePar 2>&1
mpirun --allow-run-as-root -np 8 interFoam -parallel > log.interFoam 2>&1
reconstructPar > log.reconstructPar 2>&1
postProcess -func writeCellVolumes -time 0 > log.cellVolumes 2>&1
echo 'parallel interFoam and reconstruction exit=0' > execution_status.log
tail -12 log.interFoam
