#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
set -eo pipefail
cd "$1"
postProcess -func writeCellVolumes -time 0 > log.cellVolumes 2>&1
tail -12 log.cellVolumes
