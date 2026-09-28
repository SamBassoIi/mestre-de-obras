"""Unit tests for CAD Feature Tree Schema."""

import pytest
from core.schema import (
    CadModelSpecification, PartMetadata, BaseFeature,
    CutFeature, HoleFeature, ProfileType
)

def test_default_cad_specification():
    spec = CadModelSpecification()
    assert spec.metadata.units == "mm"
    assert spec.base_feature.length == 100.0
    assert spec.base_feature.width == 60.0
    assert spec.base_feature.extrude_depth == 20.0
    assert len(spec.cuts) == 0
    assert len(spec.holes) == 0

def test_custom_cad_specification():
    spec = CadModelSpecification(
        metadata=PartMetadata(title="Mancal_Guia", material="Aço 1045"),
        base_feature=BaseFeature(
            name="Base",
            profile_type=ProfileType.RECTANGLE,
            length=150.0,
            width=90.0,
            extrude_depth=30.0
        ),
        cuts=[
            CutFeature(name="Rasgo", pos_x=0.0, pos_y=0.0, length=40.0, width=20.0, depth=10.0)
        ],
        holes=[
            HoleFeature(name="Furo_M8", pos_x=50.0, pos_y=20.0, diameter=8.5, through_all=True)
        ]
    )
    dumped = spec.model_dump()
    assert dumped["metadata"]["title"] == "Mancal_Guia"
    assert len(dumped["cuts"]) == 1
    assert len(dumped["holes"]) == 1
    assert dumped["holes"][0]["diameter"] == 8.5
