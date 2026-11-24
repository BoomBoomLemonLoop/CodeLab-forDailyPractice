#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
tag="$2"
test ! -e "log.interFoam.$tag"
mpirun --allow-run-as-root -np 8 interFoam -parallel > "log.interFoam.$tag" 2>&1
reconstructPar -newTimes -fields '(alpha.water U p_rgh)' > "log.reconstructPar.$tag" 2>&1
echo "interFoam and reconstruction $tag exit=0" >> execution_status.log
