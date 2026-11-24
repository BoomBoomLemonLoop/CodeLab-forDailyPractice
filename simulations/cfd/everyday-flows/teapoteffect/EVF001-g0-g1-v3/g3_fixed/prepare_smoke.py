"""Add v2606 alpha solver and integral monitors before the startup test."""
import sys
from pathlib import Path

case = Path(sys.argv[1])
p = case/'system/fvSolution'
s = p.read_text()
if 'MULESCorr' not in s:
    s = s.replace('cAlpha 1;', 'cAlpha 1; MULESCorr yes; nLimiterIter 5; solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0;')
p.write_text(s)
p = case/'system/controlDict'
s = p.read_text()
if 'functions' not in s:
    s += '''\nfunctions {
waterVolume { type volFieldValue; libs (fieldFunctionObjects); regionType all; operation volIntegrate; fields (alpha.water); writeControl timeStep; writeInterval 1; log true; }
'''
    for patch in ('waterInlet', 'inlet', 'atmosphere'):
        s += f'{patch}Flux {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name {patch}; operation sum; fields (phi rhoPhi); writeControl timeStep; writeInterval 1; log true; }}\n'
    s += '}\n'
s = s.replace('operation volIntegrate;', 'operation volIntegrate; writeFields false;') if 'operation volIntegrate; writeFields' not in s else s
s = s.replace('operation sum;', 'operation sum; writeFields false;') if 'operation sum; writeFields' not in s else s
p.write_text(s)
