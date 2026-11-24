"""Generate isolated STATIC OpenFOAM v2606 candidate cases; no solver execution."""
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
G0 = ROOT.parent
sys.path.insert(0, str(G0))
from geometry import load_config, solid_mesh, write_stl  # noqa: E402


def foam(name, cls, location):
    return f'FoamFile\n{{\n version 2.0; format ascii; class {cls}; location "{location}"; object {name};\n}}\n'


def field(name, cls, dimensions, internal, inlet, wall, atmosphere):
    return (foam(name, cls, '0')+f'dimensions {dimensions};\ninternalField uniform {internal};\nboundaryField\n{{\n'
        +f' inlet {{ {inlet} }}\n spout {{ {wall} }}\n atmosphere {{ {atmosphere} }}\n}}\n')


def create(case, state, g, label='smoke'):
    dest=ROOT/'cases'/f'{case}_{label}'
    if dest.exists(): raise FileExistsError(f'refusing to overwrite {dest}')
    for sub in ('0','constant/triSurface','system'):(dest/sub).mkdir(parents=True)
    inlet=state['baseline_section']; beta=state['fixed_beta_deg']
    v,f=solid_mesh(g)
    write_stl(dest/'constant/triSurface/spout.stl',v,f)
    box=(.8*g['length_m'],.070,-.030,.030,-.020,.045)
    x0,x1,y0,y1,z0,z1=box
    verts=[(x,y,z) for z in (z0,z1) for y in (y0,y1) for x in (x0,x1)]
    faces={'inlet':'(0 4 6 2)','atmosphere':'(1 3 7 5) (0 1 5 4) (2 6 7 3) (0 2 3 1) (4 5 7 6)'}
    block=foam('blockMeshDict','dictionary','system')+'convertToMeters 1;\nvertices\n(\n'
    block+='\n'.join(f'({x} {y} {z})' for x,y,z in verts)+'\n);\nblocks (hex (0 1 3 2 4 5 7 6) (32 60 65) simpleGrading (1 1 1));\nedges ();\nboundary\n(\n'
    block+='\n'.join(f'{k} {{ type patch; faces ({v}); }}' for k,v in faces.items())+'\n);\nmergePatchPairs ();\n'
    (dest/'system/blockMeshDict').write_text(block)
    snappy=foam('snappyHexMeshDict','dictionary','system')+'''castellatedMesh true; snap true; addLayers false;
geometry { spout.stl { type triSurfaceMesh; name spout; } }
castellatedMeshControls { maxLocalCells 1500000; maxGlobalCells 3500000; minRefinementCells 0; nCellsBetweenLevels 2;
 features ({ file "spout.eMesh"; level 3; }); refinementSurfaces { spout { level (2 3); patchInfo { type wall; } } }
 resolveFeatureAngle 35; refinementRegions {}; locationInMesh (0.065 0 0.040); allowFreeStandingZoneFaces true; }
snapControls { nSmoothPatch 5; tolerance 2; nSolveIter 50; nRelaxIter 8; nFeatureSnapIter 15; implicitFeatureSnap false; explicitFeatureSnap true; multiRegionFeatureSnap false; }
addLayersControls { relativeSizes true; layers {}; expansionRatio 1.2; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50; }
meshQualityControls { maxNonOrtho 65; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-13; minTetQuality 1e-15; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.02; minVolRatio 0.01; minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75; }
writeFlags (scalarLevels layerSets layerFields); mergeTolerance 1e-6;
'''
    (dest/'system/snappyHexMeshDict').write_text(snappy)
    (dest/'system/surfaceFeatureExtractDict').write_text(foam('surfaceFeatureExtractDict','dictionary','system')+
        'spout.stl { extractionMethod extractFromSurface; extractFromSurfaceCoeffs { includedAngle 150; } writeObj yes; }\n')
    (dest/'constant/g').write_text(foam('g','uniformDimensionedVectorField','constant')+f'dimensions [0 1 -2 0 0 0 0]; value ({state["constant_gravity_spout_m_s2"][0]} 0 {state["constant_gravity_spout_m_s2"][2]});\n')
    (dest/'constant/transportProperties').write_text(foam('transportProperties','dictionary','constant')+'''phases (water air);
water { transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1e-6; rho [1 -3 0 0 0 0 0] 998; }
air { transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1.5e-5; rho [1 -3 0 0 0 0 0] 1.2; }
sigma [1 0 -2 0 0 0 0] 0.072;
''')
    (dest/'constant/turbulenceProperties').write_text(foam('turbulenceProperties','dictionary','constant')+'simulationType laminar;\n')
    (dest/'0/alpha.water').write_text(field('alpha.water','volScalarField','[0 0 0 0 0 0 0]','0','type fixedValue; value uniform 0;','type constantAlphaContactAngle; theta0 60; limit gradient; value uniform 0;','type inletOutlet; inletValue uniform 0; value uniform 0;'))
    (dest/'0/U').write_text(field('U','volVectorField','[0 1 -1 0 0 0 0]','(0 0 0)','type fixedValue; value uniform (0 0 0);','type noSlip;','type pressureInletOutletVelocity; value uniform (0 0 0);'))
    (dest/'0/p_rgh').write_text(field('p_rgh','volScalarField','[1 -1 -2 0 0 0 0]','0','type fixedFluxPressure; value uniform 0;','type fixedFluxPressure; value uniform 0;','type prghTotalPressure; p0 uniform 0; value uniform 0;'))
    (dest/'system/controlDict').write_text(foam('controlDict','dictionary','system')+'''application interFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 0.02;
deltaT 1e-6; writeControl adjustableRunTime; writeInterval 0.00005; purgeWrite 0;
writeFormat ascii; writePrecision 8; runTimeModifiable yes; adjustTimeStep yes;
maxCo 0.25; maxAlphaCo 0.2; maxDeltaT 1e-5;
''')
    (dest/'system/fvSchemes').write_text(foam('fvSchemes','dictionary','system')+'''ddtSchemes { default Euler; } gradSchemes { default Gauss linear; }
divSchemes { default none; div(rhoPhi,U) Gauss linearUpwind grad(U); div(phi,alpha) Gauss vanLeer;
div(phirb,alpha) Gauss interfaceCompression; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; }
snGradSchemes { default corrected; } fluxRequired { default no; p_rgh; }
''')
    (dest/'system/fvSolution').write_text(foam('fvSolution','dictionary','system')+'''solvers { "alpha.water.*" { nAlphaCorr 2; nAlphaSubCycles 2; cAlpha 1; }
"pcorr.*" { solver PCG; preconditioner DIC; tolerance 1e-6; relTol 0; }
p_rgh { solver GAMG; tolerance 1e-7; relTol 0.05; smoother DICGaussSeidel; }
p_rghFinal { $p_rgh; relTol 0; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0.05; }
UFinal { $U; relTol 0; } }
PIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; }
''')
    control=dest/'system/controlDict'
    control.write_text(control.read_text().replace('endTime 0.02;', 'endTime 0.0002;'))
    (dest/'CASE_STATUS.json').write_text(json.dumps({'status':'GENERATED_AWAITING_MESH_AND_MAPPING','beta_deg':beta,'G2_area_m2':inlet['liquid_area_m2'],'s_in_m':x0,'source_case':case},indent=2))
    return dest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--case', choices=['case1','case2'], default='case1')
    parser.add_argument('--label', default='smoke')
    args=parser.parse_args()
    state=json.loads((G0/'artifacts/g2_fixed_state.json').read_text())
    g=load_config()['geometry']
    print(create(args.case,state['cases'][args.case],g,args.label))
