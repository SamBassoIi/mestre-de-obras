"""Unit tests for GeometryValidator."""

from core.schema import CadModelSpecification, BaseFeature, HoleFeature, CutFeature
from core.geometry_validator import GeometryValidator

def test_geometry_sanitizer_clamps_overflowing_holes():
    spec = CadModelSpecification(
        base_feature=BaseFeature(length=100.0, width=50.0, extrude_depth=20.0),
        holes=[
            # Hole placed completely outside the base bounds
            HoleFeature(name="Furo_Fora", pos_x=90.0, pos_y=0.0, diameter=10.0)
        ]
    )
    is_valid, warnings = GeometryValidator.validate_and_sanitize(spec)
    assert is_valid
    assert len(warnings) > 0
    # Hole pos_x should be clamped inside base half length (50mm)
    assert abs(spec.holes[0].pos_x) < 50.0

def test_geometry_sanitizer_fixes_negative_base():
    spec = CadModelSpecification(
        base_feature=BaseFeature(length=-10.0, width=0.0, extrude_depth=-5.0)
    )
    is_valid, warnings = GeometryValidator.validate_and_sanitize(spec)
    assert is_valid
    assert spec.base_feature.length > 0
    assert spec.base_feature.width > 0
    assert spec.base_feature.extrude_depth > 0
