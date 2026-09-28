"""Unit tests for Autodesk Inventor iLogic code generation."""

from core.schema import CadModelSpecification, BaseFeature, HoleFeature, CutFeature
from core.inventor.ilogic_generator import generate_ilogic_code

def test_ilogic_code_structure():
    spec = CadModelSpecification(
        base_feature=BaseFeature(length=120.0, width=80.0, extrude_depth=25.0),
        cuts=[
            CutFeature(name="Rebaixo_Topo", pos_x=0.0, pos_y=0.0, length=40.0, width=20.0, depth=8.0)
        ],
        holes=[
            HoleFeature(name="Furo_Guia", pos_x=30.0, pos_y=0.0, diameter=10.0, through_all=True)
        ]
    )
    code = generate_ilogic_code(spec)
    
    assert "Sub Main()" in code
    assert "End Sub" in code
    assert "PartDocument" in code
    assert "kMillimeterLengthUnits" in code
    assert "AutoCroqui3D" in code
    # Check that conversion to cm is handled (120mm -> 12.0cm, half-length = 6.0cm)
    assert "6.0" in code
    assert "Rebaixo_Topo" in code
    assert "Furo_Guia" in code
