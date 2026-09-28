"""Autodesk Inventor iLogic Rule Generator.
Transforms a CadModelSpecification into standalone, executable VB.NET / iLogic code (.iLogicVb).
Can be executed directly inside Autodesk Inventor with 1 click:
Manage Tab -> Add Rule -> Paste -> Run Rule.
"""

from typing import Optional
from core.schema import CadModelSpecification, BaseFeature, CutFeature, HoleFeature, ChamferFeature, FilletFeature, ProfileType


def generate_ilogic_code(model: CadModelSpecification) -> str:
    """Generates pure Autodesk Inventor iLogic code for the given model specification."""
    meta = model.metadata
    base = model.base_feature
    
    # Internal units in Inventor COM/iLogic API are Centimeters: 1 mm = 0.1 cm
    # We maintain mm for display and convert to cm for Inventor API parameters
    
    code_lines = [
        "' ==============================================================================",
        "' AutoCroqui3D - Regra iLogic Gerada Automaticamente para Autodesk Inventor",
        f"' Projeto: {meta.title}",
        f"' Material: {meta.material} | Norma: {meta.standard} (1º Diedro)",
        f"' Dimensões Gerais Estimadas: {meta.overall_bbox.get('length', 100)} x {meta.overall_bbox.get('width', 60)} x {meta.overall_bbox.get('height', 20)} mm",
        "' ==============================================================================",
        "",
        "Sub Main()",
        "    Dim oDoc As PartDocument",
        "    ",
        "    ' 1. Inicializa ou obtém documento de peça em milímetros",
        "    If ThisApplication.ActiveDocumentType = DocumentTypeEnum.kPartDocumentObject Then",
        "        oDoc = ThisApplication.ActiveDocument",
        "    Else",
        "        Dim sTemplate As String = ThisApplication.FileManager.GetTemplateFile(",
        "            DocumentTypeEnum.kPartDocumentObject, ",
        "            SystemOfMeasureEnum.kMetricSystemOfMeasure)",
        "        oDoc = ThisApplication.Documents.Add(DocumentTypeEnum.kPartDocumentObject, sTemplate, True)",
        "    End If",
        "",
        "    Dim oCompDef As PartComponentDefinition = oDoc.ComponentDefinition",
        "    Dim oTG As TransientGeometry = ThisApplication.TransientGeometry",
        "    oDoc.UnitsOfMeasure.LengthUnits = UnitsTypeEnum.kMillimeterLengthUnits",
        "",
        "    ' ==========================================================================",
        "    ' 2. CRIAÇÃO DO CORPO BASE",
        "    ' ==========================================================================",
    ]
    
    # Base feature generation
    base_len_cm = base.length / 10.0
    base_wid_cm = base.width / 10.0
    base_height_cm = base.extrude_depth / 10.0
    
    if base.profile_type == ProfileType.CIRCLE or (base.diameter is not None and base.diameter > 0):
        dia_cm = (base.diameter or base.length) / 10.0
        rad_cm = dia_cm / 2.0
        code_lines.extend([
            "    ' Esboço Base Cilíndrico no Plano XY",
            "    Dim oBaseSketch As PlanarSketch = oCompDef.Sketches.Add(oCompDef.WorkPlanes.Item(3)) ' XY Plane",
            "    oBaseSketch.Name = \"Esboco_Base_Cilindrica\"",
            f"    Dim oCenterPt As Point2d = oTG.CreatePoint2d({base.center_x / 10.0}, {base.center_y / 10.0})",
            f"    oBaseSketch.SketchCircles.AddByCenterRadius(oCenterPt, {rad_cm})",
            "    Dim oBaseProfile As Profile = oBaseSketch.Profiles.AddForSolid()",
            f"    Dim oBaseExtrude As ExtrudeFeature = oCompDef.Features.ExtrudeFeatures.AddDistanceExtend(",
            f"        oBaseProfile, {base_height_cm}, PartFeatureExtentDirectionEnum.kPositiveExtentDirection, PartFeatureOperationEnum.kJoinOperation)",
            f"    oBaseExtrude.Name = \"{base.name}\"",
            "",
        ])
    else:
        # Default rectangular base centered around origin
        code_lines.extend([
            "    ' Esboço Base Prismático no Plano XY",
            "    Dim oBaseSketch As PlanarSketch = oCompDef.Sketches.Add(oCompDef.WorkPlanes.Item(3)) ' XY Plane",
            "    oBaseSketch.Name = \"Esboco_Base\"",
            f"    Dim p1 As Point2d = oTG.CreatePoint2d({-base_len_cm / 2.0}, {-base_wid_cm / 2.0})",
            f"    Dim p2 As Point2d = oTG.CreatePoint2d({base_len_cm / 2.0}, {base_wid_cm / 2.0})",
            "    oBaseSketch.SketchLines.AddAsTwoPointRectangle(p1, p2)",
            "    Dim oBaseProfile As Profile = oBaseSketch.Profiles.AddForSolid()",
            f"    Dim oBaseExtrude As ExtrudeFeature = oCompDef.Features.ExtrudeFeatures.AddDistanceExtend(",
            f"        oBaseProfile, {base_height_cm}, PartFeatureExtentDirectionEnum.kPositiveExtentDirection, PartFeatureOperationEnum.kJoinOperation)",
            f"    oBaseExtrude.Name = \"{base.name}\"",
            "",
        ])
        
    # Cuts generation
    if model.cuts:
        code_lines.extend([
            "    ' ==========================================================================",
            "    ' 3. REBAIXOS E CORTES (CUTS)",
            "    ' ==========================================================================",
        ])
        for idx, cut in enumerate(model.cuts, 1):
            cut_x_cm = cut.pos_x / 10.0
            cut_y_cm = cut.pos_y / 10.0
            cut_l_cm = cut.length / 10.0
            cut_w_cm = cut.width / 10.0
            cut_d_cm = cut.depth / 10.0
            
            code_lines.extend([
                f"    ' Corte #{idx}: {cut.name}",
                "    ' Localizar a face superior (Z máximo) do corpo base",
                "    Dim oTopFace As Face = Nothing",
                "    Dim dMaxZ As Double = -100000.0",
                "    For Each oFace As Face In oBaseExtrude.Faces",
                "        If oFace.SurfaceType = SurfaceTypeEnum.kPlaneSurface Then",
                "            Dim oPlane As Plane = oFace.Geometry",
                "            If Math.Abs(oPlane.Normal.Z - 1.0) < 0.001 AndAlso oPlane.RootPoint.Z > dMaxZ Then",
                "                dMaxZ = oPlane.RootPoint.Z",
                "                oTopFace = oFace",
                "            End If",
                "        End If",
                "    Next",
                "",
                "    If oTopFace IsNot Nothing Then",
                f"        Dim oCutSketch_{idx} As PlanarSketch = oCompDef.Sketches.Add(oTopFace)",
                f"        oCutSketch_{idx}.Name = \"Esboco_{cut.name}\"",
                f"        Dim cp1_{idx} As Point2d = oTG.CreatePoint2d({cut_x_cm - cut_l_cm / 2.0}, {cut_y_cm - cut_w_cm / 2.0})",
                f"        Dim cp2_{idx} As Point2d = oTG.CreatePoint2d({cut_x_cm + cut_l_cm / 2.0}, {cut_y_cm + cut_w_cm / 2.0})",
                f"        oCutSketch_{idx}.SketchLines.AddAsTwoPointRectangle(cp1_{idx}, cp2_{idx})",
                f"        Dim oCutProfile_{idx} As Profile = oCutSketch_{idx}.Profiles.AddForSolid()",
                f"        Dim oCutExtrude_{idx} As ExtrudeFeature = oCompDef.Features.ExtrudeFeatures.AddDistanceExtend(",
                f"            oCutProfile_{idx}, {cut_d_cm}, PartFeatureExtentDirectionEnum.kNegativeExtentDirection, PartFeatureOperationEnum.kCutOperation)",
                f"        oCutExtrude_{idx}.Name = \"{cut.name}\"",
                "    End If",
                "",
            ])

    # Holes generation
    if model.holes:
        code_lines.extend([
            "    ' ==========================================================================",
            "    ' 4. FUROS MECÂNICOS (HOLES)",
            "    ' ==========================================================================",
            "    ' Localizar face superior de referência para os furos",
            "    Dim oHoleFace As Face = Nothing",
            "    Dim dHoleMaxZ As Double = -100000.0",
            "    For Each oFace As Face In oCompDef.Faces",
            "        If oFace.SurfaceType = SurfaceTypeEnum.kPlaneSurface Then",
            "            Dim oPlane As Plane = oFace.Geometry",
            "            If Math.Abs(oPlane.Normal.Z - 1.0) < 0.001 AndAlso oPlane.RootPoint.Z > dHoleMaxZ Then",
            "                dHoleMaxZ = oPlane.RootPoint.Z",
            "                oHoleFace = oFace",
            "            End If",
            "        End If",
            "    Next",
            "",
            "    If oHoleFace IsNot Nothing Then",
        ])
        
        for idx, hole in enumerate(model.holes, 1):
            h_x_cm = hole.pos_x / 10.0
            h_y_cm = hole.pos_y / 10.0
            h_dia_cm = hole.diameter / 10.0
            h_depth_cm = hole.depth / 10.0
            
            code_lines.extend([
                f"        ' Furo #{idx}: {hole.name} (Ø {hole.diameter} mm)",
                f"        Dim oHoleSketch_{idx} As PlanarSketch = oCompDef.Sketches.Add(oHoleFace)",
                f"        oHoleSketch_{idx}.Name = \"Esboco_{hole.name}\"",
                f"        Dim oHolePt_{idx} As SketchPoint = oHoleSketch_{idx}.SketchPoints.Add(oTG.CreatePoint2d({h_x_cm}, {h_y_cm}))",
                f"        Dim oHoleCollection_{idx} As ObjectCollection = ThisApplication.TransientObjects.CreateObjectCollection()",
                f"        oHoleCollection_{idx}.Add(oHolePt_{idx})",
            ])
            
            if hole.through_all:
                code_lines.extend([
                    f"        Dim oHole_{idx} As HoleFeature = oCompDef.Features.HoleFeatures.AddDrilledByThroughAllExtent(",
                    f"            oHoleCollection_{idx}, {h_dia_cm}, PartFeatureExtentDirectionEnum.kNegativeExtentDirection)",
                    f"        oHole_{idx}.Name = \"{hole.name}\"",
                ])
            else:
                code_lines.extend([
                    f"        Dim oHole_{idx} As HoleFeature = oCompDef.Features.HoleFeatures.AddDrilledByDistanceExtend(",
                    f"            oHoleCollection_{idx}, {h_dia_cm}, {h_depth_cm}, PartFeatureExtentDirectionEnum.kNegativeExtentDirection)",
                    f"        oHole_{idx}.Name = \"{hole.name}\"",
                ])
            code_lines.append("")
            
        code_lines.append("    End If")
        code_lines.append("")

    # Fillets (Arredondamentos)
    if model.fillets:
        code_lines.extend([
            "    ' ==========================================================================",
            "    ' 5. ARREDONDAMENTOS / CONCORDÂNCIAS (FILLETS)",
            "    ' ==========================================================================",
        ])
        for idx, fillet in enumerate(model.fillets, 1):
            r_cm = fillet.radius / 10.0
            code_lines.extend([
                f"    ' Arredondamento #{idx}: Raio {fillet.radius} mm",
                "    Dim oFilletEdges As EdgeCollection = ThisApplication.TransientObjects.CreateEdgeCollection()",
                "    For Each oEdge As Edge In oCompDef.Edges",
                "        If oEdge.GeometryType = CurveTypeEnum.kLineSegmentCurve Then",
                "            Dim oLine As LineSegment = oEdge.Geometry",
                "            ' Arestas verticais paralelas a Z",
                "            If Math.Abs(Math.Abs(oLine.Direction.Z) - 1.0) < 0.05 Then",
                "                oFilletEdges.Add(oEdge)",
                "            End If",
                "        End If",
                "    Next",
                "    If oFilletEdges.Count > 0 Then",
                f"        Dim oFillet_{idx} As FilletFeature = oCompDef.Features.FilletFeatures.AddSimple(oFilletEdges, {r_cm})",
                f"        oFillet_{idx}.Name = \"{fillet.name}\"",
                "    End If",
                "",
            ])

    # Chamfers (Chanfros)
    if model.chamfers:
        code_lines.extend([
            "    ' ==========================================================================",
            "    ' 6. CHANFROS (CHAMFERS)",
            "    ' ==========================================================================",
        ])
        for idx, chamfer in enumerate(model.chamfers, 1):
            ch_cm = chamfer.distance / 10.0
            code_lines.extend([
                f"    ' Chanfro #{idx}: {chamfer.distance} mm x {chamfer.angle}°",
                "    Dim oChamferEdges As EdgeCollection = ThisApplication.TransientObjects.CreateEdgeCollection()",
                "    For Each oEdge As Edge In oCompDef.Edges",
                "        If oEdge.GeometryType = CurveTypeEnum.kLineSegmentCurve OrElse oEdge.GeometryType = CurveTypeEnum.kCircleCurve Then",
                "            Dim ptMid As Point = oEdge.PointOnEdge",
                "            ' Bordas superiores do contorno",
                f"            If ptMid.Z >= ({base_height_cm} - 0.001) Then",
                "                oChamferEdges.Add(oEdge)",
                "            End If",
                "        End If",
                "    Next",
                "    If oChamferEdges.Count > 0 Then",
                f"        Try",
                f"            Dim oChamfer_{idx} As ChamferFeature = oCompDef.Features.ChamferFeatures.AddUsingDistance(oChamferEdges, {ch_cm})",
                f"            oChamfer_{idx}.Name = \"{chamfer.name}\"",
                f"        Catch ex As Exception",
                f"            ' Fallback silencioso se aresta possuir conflito topológico",
                f"        End Try",
                "    End If",
                "",
            ])

    # Finalization and View
    code_lines.extend([
        "    ' ==========================================================================",
        "    ' 7. FINALIZAÇÃO",
        "    ' ==========================================================================",
        "    oDoc.Update()",
        "    ThisApplication.ActiveView.Fit()",
        f"    MsgBox(\"Peça '{meta.title}' modelada com sucesso no Autodesk Inventor!\" & vbCrLf & _",
        f"           \"Dimensões: {base.length}x{base.width}x{base.extrude_depth} mm\", vbInformation, \"AutoCroqui3D\")",
        "End Sub",
    ])
    
    return "\n".join(code_lines)
