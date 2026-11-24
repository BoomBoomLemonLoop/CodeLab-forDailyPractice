"""Run with installed WSL pvpython. Extract actual alpha=.5 isosurfaces and U."""
import sys
from pathlib import Path
import numpy as np
from paraview.simple import OpenFOAMReader,CellDatatoPointData,Contour,UpdatePipeline,servermanager
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersGeometry import vtkCompositeDataGeometryFilter
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter

case=Path(sys.argv[1]);out=case/'interface_exports';out.mkdir(exist_ok=True)
reader=OpenFOAMReader(FileName=str(case/'view.foam'))
reader.MeshRegions=['internalMesh'];reader.CellArrays=['alpha.water','U']
points=CellDatatoPointData(Input=reader)
iso=Contour(Input=points);iso.ContourBy=['POINTS','alpha.water'];iso.Isosurfaces=[.5]
for t in reader.TimestepValues:
    if (out/f'{t:.8g}.npz').exists() and (out/f'{t:.8g}.vtp').exists():continue
    UpdatePipeline(time=t,proxy=iso);data=servermanager.Fetch(iso)
    if data.IsA('vtkMultiBlockDataSet'):
        geom=vtkCompositeDataGeometryFilter();geom.SetInputData(data);geom.Update();data=geom.GetOutput()
    tri=vtkTriangleFilter();tri.SetInputData(data);tri.Update();data=tri.GetOutput()
    if data.GetNumberOfPoints()==0:continue
    np.savez_compressed(out/f'{t:.8g}.npz',points=vtk_to_numpy(data.GetPoints().GetData()),
        triangles=vtk_to_numpy(data.GetPolys().GetData()).reshape(-1,4)[:,1:],
        U=vtk_to_numpy(data.GetPointData().GetArray('U')))
    writer=vtkXMLPolyDataWriter();writer.SetFileName(str(out/f'{t:.8g}.vtp'));writer.SetInputData(data);writer.Write()
    print(t,data.GetNumberOfPoints(),flush=True)
