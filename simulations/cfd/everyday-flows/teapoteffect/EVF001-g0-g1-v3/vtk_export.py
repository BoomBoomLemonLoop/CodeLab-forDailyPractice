"""Dependency-free VTK XML export, SI units; ParaView-readable geometric data."""

from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np


def write_vtp(path, points, cells, height, lines=False):
    points = np.asarray(points).reshape(-1, 3)
    cells = np.asarray(cells, dtype=int).reshape(-1, 2 if lines else 3)
    root = ET.Element("VTKFile", type="PolyData", version="0.1", byte_order="LittleEndian")
    poly = ET.SubElement(root, "PolyData")
    piece = ET.SubElement(
        poly,
        "Piece",
        NumberOfPoints=str(len(points)),
        NumberOfVerts="0",
        NumberOfLines=str(len(cells) if lines else 0),
        NumberOfStrips="0",
        NumberOfPolys=str(0 if lines else len(cells)),
    )
    pdata = ET.SubElement(piece, "PointData", Scalars="z_minus_H_m")
    values = ET.SubElement(pdata, "DataArray", type="Float64", Name="z_minus_H_m", format="ascii")
    values.text = " ".join(f"{x:.10g}" for x in points[:, 2] - height)
    p = ET.SubElement(
        ET.SubElement(piece, "Points"),
        "DataArray",
        type="Float64",
        NumberOfComponents="3",
        format="ascii",
    )
    p.text = " ".join(f"{x:.10g}" for x in points.ravel())
    cell = ET.SubElement(piece, "Lines" if lines else "Polys")
    conn = ET.SubElement(cell, "DataArray", type="Int32", Name="connectivity", format="ascii")
    conn.text = " ".join(str(int(x)) for x in cells.ravel())
    offsets = ET.SubElement(cell, "DataArray", type="Int32", Name="offsets", format="ascii")
    offsets.text = " ".join(str(int(x)) for x in np.arange(1, len(cells) + 1) * cells.shape[1])
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_pvd(path, entries):
    root = ET.Element("VTKFile", type="Collection", version="0.1", byte_order="LittleEndian")
    collection = ET.SubElement(root, "Collection")
    for time, part, filename in entries:
        ET.SubElement(
            collection,
            "DataSet",
            timestep=f"{time:.10g}",
            group="",
            part=str(part),
            file=str(filename),
        )
    ET.ElementTree(root).write(Path(path), encoding="utf-8", xml_declaration=True)
