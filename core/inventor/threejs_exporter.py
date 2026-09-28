"""Three.js & 3D Geometry Exporter.
Transforms a CadModelSpecification into lightweight 3D visualization objects
and parametric meshes for browser preview and CAD export (OBJ / JSON).
"""

import math
from typing import Dict, Any, List
from core.schema import CadModelSpecification, ProfileType


def model_to_threejs_data(model: CadModelSpecification) -> Dict[str, Any]:
    """Generates structured mesh and annotation primitives for the frontend Three.js viewport."""
    base = model.base_feature
    meta = model.metadata

    # Bounding dimensions
    length = float(base.length)
    width = float(base.width)
    height = float(base.extrude_depth)

    is_cylindrical = (base.profile_type == ProfileType.CIRCLE or (base.diameter and base.diameter > 0))
    diameter = float(base.diameter or base.length) if is_cylindrical else None

    # Base shape primitive definition
    base_mesh = {
        "type": "cylinder" if is_cylindrical else "box",
        "name": base.name,
        "color": "#4a7ebb", # Engineering CAD steel blue
        "dimensions": {
            "length": length,
            "width": width,
            "height": height,
            "diameter": diameter,
            "radius": (diameter / 2.0) if diameter else None
        },
        "position": {"x": 0.0, "y": height / 2.0, "z": 0.0}
    }

    # Cut features representation
    cuts_data = []
    for cut in model.cuts:
        cuts_data.append({
            "name": cut.name,
            "type": "box",
            "color": "#e74c3c", # Red overlay for subtracted volume
            "dimensions": {
                "length": float(cut.length),
                "width": float(cut.width),
                "height": float(cut.depth)
            },
            # Positioned at the top surface, cutting down
            "position": {
                "x": float(cut.pos_x),
                "y": float(height - (cut.depth / 2.0)),
                "z": float(cut.pos_y)
            }
        })

    # Holes representation
    holes_data = []
    for hole in model.holes:
        hole_depth = float(height if hole.through_all else hole.depth)
        holes_data.append({
            "name": hole.name,
            "type": "cylinder",
            "color": "#2c3e50", # Dark cylinder for hole cavity
            "diameter": float(hole.diameter),
            "radius": float(hole.diameter) / 2.0,
            "height": hole_depth,
            "through_all": hole.through_all,
            "position": {
                "x": float(hole.pos_x),
                "y": float(height / 2.0) if hole.through_all else float(height - (hole_depth / 2.0)),
                "z": float(hole.pos_y)
            }
        })

    # Overall dimension callout lines for 3D overlay
    annotations = [
        {"label": f"L = {length} mm", "axis": "X", "value": length},
        {"label": f"W = {width} mm", "axis": "Z", "value": width},
        {"label": f"H = {height} mm", "axis": "Y", "value": height},
    ]

    return {
        "title": meta.title,
        "material": meta.material,
        "units": meta.units,
        "base_mesh": base_mesh,
        "cuts": cuts_data,
        "holes": holes_data,
        "annotations": annotations,
        "features_count": {
            "cuts": len(model.cuts),
            "holes": len(model.holes),
            "fillets": len(model.fillets),
            "chamfers": len(model.chamfers)
        }
    }


def generate_obj_file(model: CadModelSpecification) -> str:
    """Generates standard Wavefront .OBJ 3D file for direct CAD import."""
    base = model.base_feature
    l = base.length / 2.0
    w = base.width / 2.0
    h = base.extrude_depth

    # 8 vertices of base box
    lines = [
        f"# AutoCroqui3D Wavefront OBJ: {model.metadata.title}",
        f"# Units: millimeters (mm)",
        f"o {model.metadata.title}",
        f"v {-l} 0 {-w}",
        f"v {l} 0 {-w}",
        f"v {l} 0 {w}",
        f"v {-l} 0 {w}",
        f"v {-l} {h} {-w}",
        f"v {l} {h} {-w}",
        f"v {l} {h} {w}",
        f"v {-l} {h} {w}",
        "# Normals",
        "vn 0 0 1",
        "vn 0 0 -1",
        "vn 0 1 0",
        "vn 0 -1 0",
        "vn 1 0 0",
        "vn -1 0 0",
        "# Faces",
        "f 1 2 3 4", # Bottom
        "f 5 8 7 6", # Top
        "f 1 5 6 2", # Front
        "f 2 6 7 3", # Right
        "f 3 7 8 4", # Back
        "f 4 8 5 1", # Left
    ]
    return "\n".join(lines)
