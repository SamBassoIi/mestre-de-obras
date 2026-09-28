"""Autodesk Inventor COM Automation Driver.
Directly communicates with Autodesk Inventor on Windows using win32com.client.
Models the parametric 3D part live in Inventor.
"""

import sys
import math
from typing import Dict, Any, Optional
from core.schema import CadModelSpecification, BaseFeature, CutFeature, HoleFeature, ChamferFeature, FilletFeature, ProfileType


class InventorConnector:
    """Manages connection and commands to an Autodesk Inventor session."""
    
    def __init__(self, visible: bool = True):
        self.visible = visible
        self.app = None
        self.doc = None
        self.comp_def = None
        self.tg = None
        
    def connect(self) -> bool:
        """Attempts to connect to an open Inventor instance or starts a new one."""
        try:
            import win32com.client
            try:
                # First try active instance
                self.app = win32com.client.GetActiveObject("Inventor.Application")
            except Exception:
                # Otherwise launch or dispatch
                self.app = win32com.client.Dispatch("Inventor.Application")
                
            self.app.Visible = self.visible
            self.tg = self.app.TransientGeometry
            return True
        except Exception as e:
            print(f"[Inventor COM] Não foi possível conectar ao Autodesk Inventor: {e}")
            return False

    def is_available(self) -> bool:
        """Checks if win32com and Autodesk Inventor can be initialized."""
        try:
            import win32com.client
            return True
        except ImportError:
            return False

    def model_part(self, model: CadModelSpecification) -> Dict[str, Any]:
        """Creates the 3D part in Autodesk Inventor from the given CadModelSpecification."""
        if not self.connect():
            return {
                "success": False,
                "error": "Autodesk Inventor não está instalado ou não pôde ser inicializado via COM API no Windows."
            }

        try:
            # DocumentTypeEnum: kPartDocumentObject = 12290
            # SystemOfMeasureEnum: kMetricSystemOfMeasure = 51201
            # UnitsTypeEnum: kMillimeterLengthUnits = 11269
            template_path = self.app.FileManager.GetTemplateFile(12290, 51201)
            self.doc = self.app.Documents.Add(12290, template_path, True)
            self.comp_def = self.doc.ComponentDefinition
            self.doc.UnitsOfMeasure.LengthUnits = 11269 # Millimeter

            base = model.base_feature
            base_len_cm = base.length / 10.0
            base_wid_cm = base.width / 10.0
            base_height_cm = base.extrude_depth / 10.0

            # 1. Base Sketch & Extrusion
            xy_plane = self.comp_def.WorkPlanes.Item(3)
            base_sketch = self.comp_def.Sketches.Add(xy_plane)
            base_sketch.Name = "AutoCroqui_BaseSketch"

            if base.profile_type == ProfileType.CIRCLE or (base.diameter and base.diameter > 0):
                dia_cm = (base.diameter or base.length) / 10.0
                center_pt = self.tg.CreatePoint2d(base.center_x / 10.0, base.center_y / 10.0)
                base_sketch.SketchCircles.AddByCenterRadius(center_pt, dia_cm / 2.0)
            else:
                p1 = self.tg.CreatePoint2d(-base_len_cm / 2.0, -base_wid_cm / 2.0)
                p2 = self.tg.CreatePoint2d(base_len_cm / 2.0, base_wid_cm / 2.0)
                base_sketch.SketchLines.AddAsTwoPointRectangle(p1, p2)

            base_profile = base_sketch.Profiles.AddForSolid()
            # PartFeatureExtentDirectionEnum: kPositiveExtentDirection = 20481
            # PartFeatureOperationEnum: kJoinOperation = 20481
            base_extrude = self.comp_def.Features.ExtrudeFeatures.AddDistanceExtend(
                base_profile, base_height_cm, 20481, 20481
            )
            base_extrude.Name = base.name

            # 2. Cortes / Rebaixos
            for idx, cut in enumerate(model.cuts, 1):
                try:
                    top_face = self._find_top_face(base_extrude)
                    if top_face:
                        cut_sketch = self.comp_def.Sketches.Add(top_face)
                        cut_sketch.Name = f"AutoCroqui_Cut_{idx}"
                        c_x = cut.pos_x / 10.0
                        c_y = cut.pos_y / 10.0
                        c_l = cut.length / 10.0
                        c_w = cut.width / 10.0
                        c_d = cut.depth / 10.0
                        cp1 = self.tg.CreatePoint2d(c_x - c_l / 2.0, c_y - c_w / 2.0)
                        cp2 = self.tg.CreatePoint2d(c_x + c_l / 2.0, c_y + c_w / 2.0)
                        cut_sketch.SketchLines.AddAsTwoPointRectangle(cp1, cp2)
                        cut_profile = cut_sketch.Profiles.AddForSolid()
                        # kNegativeExtentDirection = 20482, kCutOperation = 20482
                        cut_feat = self.comp_def.Features.ExtrudeFeatures.AddDistanceExtend(
                            cut_profile, c_d, 20482, 20482
                        )
                        cut_feat.Name = cut.name
                except Exception as cut_err:
                    print(f"[Inventor COM] Aviso ao criar corte {cut.name}: {cut_err}")

            # 3. Furos
            if model.holes:
                try:
                    top_face = self._find_top_face(base_extrude)
                    if top_face:
                        for idx, hole in enumerate(model.holes, 1):
                            hole_sketch = self.comp_def.Sketches.Add(top_face)
                            hole_sketch.Name = f"AutoCroqui_HoleSketch_{idx}"
                            h_pt = hole_sketch.SketchPoints.Add(
                                self.tg.CreatePoint2d(hole.pos_x / 10.0, hole.pos_y / 10.0)
                            )
                            hole_col = self.app.TransientObjects.CreateObjectCollection()
                            hole_col.Add(h_pt)
                            h_dia_cm = hole.diameter / 10.0
                            h_depth_cm = hole.depth / 10.0

                            if hole.through_all:
                                h_feat = self.comp_def.Features.HoleFeatures.AddDrilledByThroughAllExtent(
                                    hole_col, h_dia_cm, 20482
                                )
                            else:
                                h_feat = self.comp_def.Features.HoleFeatures.AddDrilledByDistanceExtend(
                                    hole_col, h_dia_cm, h_depth_cm, 20482
                                )
                            h_feat.Name = hole.name
                except Exception as hole_err:
                    print(f"[Inventor COM] Aviso ao criar furos: {hole_err}")

            # 4. Finalização da peça
            self.doc.Update()
            self.app.ActiveView.Fit()

            return {
                "success": True,
                "message": f"Peça '{model.metadata.title}' modelada com sucesso no Autodesk Inventor!",
                "document_name": self.doc.DisplayName
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro durante a modelagem no Inventor: {str(e)}"
            }

    def _find_top_face(self, extrude_feat):
        """Finds planar face pointing towards +Z with highest coordinate."""
        top_face = None
        max_z = -100000.0
        try:
            for face in extrude_feat.Faces:
                # SurfaceTypeEnum: kPlaneSurface = 5889
                if face.SurfaceType == 5889:
                    plane = face.Geometry
                    if abs(plane.Normal.Z - 1.0) < 0.01 and plane.RootPoint.Z > max_z:
                        max_z = plane.RootPoint.Z
                        top_face = face
        except Exception:
            pass
        return top_face
