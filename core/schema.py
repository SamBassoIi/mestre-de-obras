"""CAD Feature Tree Schema for AutoCroqui3D.
Defines standard geometric and parametric feature structures for CAD modeling.
Compatible with Pydantic v2 and fallback standard classes.
"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Graceful fallback if pydantic is not yet installed during bootstrapping
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def model_dump(self):
            import json
            return json.loads(self.model_dump_json())
        def model_dump_json(self):
            import json
            def _to_dict(obj):
                if hasattr(obj, '__dict__'):
                    return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
                elif isinstance(obj, list):
                    return [_to_dict(x) for x in obj]
                elif isinstance(obj, dict):
                    return {k: _to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, Enum):
                    return obj.value
                return obj
            return json.dumps(_to_dict(self), indent=2)
    def Field(default=None, **kwargs):
        return default


class SketchPlane(str, Enum):
    XY = "XY"
    XZ = "XZ"
    YZ = "YZ"


class ProfileType(str, Enum):
    RECTANGLE = "RECTANGLE"
    CIRCLE = "CIRCLE"
    CYLINDER_STEPPED = "CYLINDER_STEPPED"
    POLYGON = "POLYGON"


class ExtrudeOperation(str, Enum):
    JOIN = "JOIN"
    CUT = "CUT"
    INTERSECT = "INTERSECT"


class BaseFeature(BaseModel):
    name: str = "Base_Feature"
    profile_type: ProfileType = ProfileType.RECTANGLE
    sketch_plane: SketchPlane = SketchPlane.XY
    length: float = 100.0  # Dimensao X (mm)
    width: float = 60.0    # Dimensao Y (mm)
    diameter: Optional[float] = None # Para perfis circulares/cilindricos
    center_x: float = 0.0
    center_y: float = 0.0
    extrude_depth: float = 20.0 # Dimensao Z / Altura (mm)
    comments: Optional[str] = "Corpo principal do croqui"


class CutFeature(BaseModel):
    name: str = "Corte_Rebaixo"
    face: str = "TOP"  # TOP, FRONT, SIDE_LEFT, SIDE_RIGHT, BOTTOM
    profile_type: ProfileType = ProfileType.RECTANGLE
    pos_x: float = 0.0  # Posicao relativa na face (mm)
    pos_y: float = 0.0
    length: float = 30.0 # Comprimento do corte
    width: float = 20.0  # Largura do corte
    depth: float = 10.0  # Profundidade de corte
    through_all: bool = False
    comments: Optional[str] = None


class HoleFeature(BaseModel):
    name: str = "Furo"
    face: str = "TOP"  # Face onde o furo e aplicado
    pos_x: float = 0.0  # Coordenada X na face
    pos_y: float = 0.0  # Coordenada Y na face
    diameter: float = 10.0 # Diametro do furo (mm)
    depth: float = 20.0
    through_all: bool = True
    hole_type: str = "SIMPLE"  # SIMPLE, COUNTERBORE, COUNTERSINK, THREADED
    counterbore_diameter: Optional[float] = None
    counterbore_depth: Optional[float] = None
    countersink_diameter: Optional[float] = None
    countersink_angle: Optional[float] = 90.0
    thread_spec: Optional[str] = None  # Ex: "M8x1.25"
    comments: Optional[str] = None


class ChamferFeature(BaseModel):
    name: str = "Chanfro"
    target: str = "TOP_EDGES"  # TOP_EDGES, ALL_VERTICAL, CORNERS, ALL
    distance: float = 2.0  # Distancia nominal (ex: 2mm em 2x45)
    angle: float = 45.0    # Angulo em graus
    comments: Optional[str] = None


class FilletFeature(BaseModel):
    name: str = "Arredondamento"
    target: str = "VERTICAL_CORNERS"  # VERTICAL_CORNERS, TOP_EDGES, ALL_EDGES
    radius: float = 5.0  # Raio (R) em mm
    comments: Optional[str] = None


class SteppedShaftSegment(BaseModel):
    segment_index: int
    diameter: float  # Diametro do degrau (mm)
    length: float    # Comprimento do degrau (mm)
    has_keyway: bool = False  # Rasgo de chaveta
    keyway_width: Optional[float] = None
    keyway_depth: Optional[float] = None
    keyway_length: Optional[float] = None
    chamfer_start: Optional[float] = None
    fillet_end: Optional[float] = None


class RevolveFeature(BaseModel):
    name: str = "Corpo_Revolucao"
    axis: str = "X"
    total_length: float = 120.0
    max_diameter: float = 50.0
    segments: List[SteppedShaftSegment] = []


class PartMetadata(BaseModel):
    title: str = "Peca_Desenho_Tecnico_2"
    student_notes: Optional[str] = None
    standard: str = "ABNT_NBR"  # ABNT_NBR (1o Diedro) ou ISO
    projection_angle: str = "FIRST_ANGLE"
    units: str = "mm"
    material: str = "Aço 1020"
    overall_bbox: Dict[str, float] = {"length": 100.0, "width": 60.0, "height": 20.0}


class CadModelSpecification(BaseModel):
    metadata: PartMetadata = PartMetadata()
    is_cylindrical: bool = False
    base_feature: BaseFeature = BaseFeature()
    cuts: List[CutFeature] = []
    holes: List[HoleFeature] = []
    chamfers: List[ChamferFeature] = []
    fillets: List[FilletFeature] = []
    revolve_feature: Optional[RevolveFeature] = None
