"""Assign state/gravity to an unsolved reused local-frame mesh only."""
import json
import sys
from pathlib import Path
from make_cases import foam, G0

case=Path(sys.argv[1]); name=sys.argv[2]
assert not (case/'log.interFoam').exists(), 'do not change a solved case'
state=json.loads((G0/'artifacts/g2_fixed_state.json').read_text())['cases'][name]
g=state['constant_gravity_spout_m_s2']
(case/'constant/g').write_text(foam('g','uniformDimensionedVectorField','constant')+f'dimensions [0 1 -2 0 0 0 0]; value ({g[0]} {g[1]} {g[2]});\n')
(case/'CASE_STATUS.json').write_text(json.dumps(dict(source_case=name,beta_deg=state['fixed_beta_deg'],status='MESH_REUSED_AWAITING_MAPPING'),indent=2))
