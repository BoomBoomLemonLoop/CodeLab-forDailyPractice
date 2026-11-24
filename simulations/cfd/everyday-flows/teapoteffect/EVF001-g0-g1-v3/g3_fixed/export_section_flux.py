"""pvpython: diagnostic interpolated water flux at two actual fluid cuts.

This is NOT the solver's conservative face flux; global conservation uses
rhoPhi. Integrates the product of linear nodal alpha and U_s exactly per triangle.
"""
import json
import sys
from pathlib import Path
import numpy as np
from paraview.simple import OpenFOAMReader,CellDatatoPointData,Slice,UpdatePipeline,servermanager
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersGeometry import vtkCompositeDataGeometryFilter,vtkGeometryFilter
from section_flux_math import linear_product_integral

case=Path(sys.argv[1]);name=json.loads((case/'CASE_STATUS.json').read_text())['source_case']
beta={'case1':25,'case2':55}[name];L=.045/np.sin(np.deg2rad(70))
reader=OpenFOAMReader(FileName=str(case/'view.foam'));reader.MeshRegions=['internalMesh'];reader.CellArrays=['alpha.water','U']
points=CellDatatoPointData(Input=reader);cut=Slice(Input=points);cut.SliceType='Plane';cut.SliceType.Normal=[1,0,0]
rows=[]
for time in reader.TimestepValues:
    row={'time_s':float(time)}
    for label,x in {'centreline_crest':L+.0006*np.sin(np.deg2rad(beta)),'beyond_lip':L+.0007}.items():
        cut.SliceType.Origin=[x,0,0];UpdatePipeline(time=time,proxy=cut);data=servermanager.Fetch(cut)
        geom=vtkCompositeDataGeometryFilter() if data.IsA('vtkMultiBlockDataSet') else vtkGeometryFilter()
        geom.SetInputData(data);geom.Update();tri=vtkTriangleFilter();tri.SetInputData(geom.GetOutput());tri.Update();data=tri.GetOutput()
        p=vtk_to_numpy(data.GetPoints().GetData());f=vtk_to_numpy(data.GetPolys().GetData()).reshape(-1,4)[:,1:]
        a=vtk_to_numpy(data.GetPointData().GetArray('alpha.water'));u=vtk_to_numpy(data.GetPointData().GetArray('U'))[:,0]
        row[label+'_s_m']=x;row[label+'_Q_m3_s']=linear_product_integral(p,f,a,u)
    rows.append(row);print(row,flush=True)
(case/'section_flux_diagnostic.json').write_text(json.dumps({'definition':__doc__,'series':rows},indent=2))
