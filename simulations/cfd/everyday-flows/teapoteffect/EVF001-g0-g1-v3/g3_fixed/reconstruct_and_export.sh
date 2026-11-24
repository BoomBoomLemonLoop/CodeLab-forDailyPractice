#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
reconstructPar -newTimes -fields '(alpha.water U p_rgh)' -time "0:${3:-100}" > log.reconstruct.interim 2>&1
pvpython "$2/export_interfaces.py" "$1" > log.interfaces 2>&1
tail -10 log.interfaces
