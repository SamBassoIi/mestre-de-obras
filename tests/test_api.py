"""Integration tests for FastAPI endpoints."""

import io
from fastapi.testclient import TestClient
from PIL import Image
from server.app import app

client = TestClient(app)

def test_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "AutoCroqui3D" in response.text

def test_upload_image_route():
    # Create simple image in memory
    img = Image.new("RGB", (100, 100), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/upload",
        files={"file": ("exercicio_dt2.jpg", buf, "image/jpeg")},
        data={"notes": "Mancal teste", "api_key": ""}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "spec" in data
    assert "threejs_data" in data
    assert "ilogic_script" in data
    assert "Sub Main()" in data["ilogic_script"]

def test_update_model_route():
    sample_spec = {
        "metadata": {"title": "Bloco_Teste", "material": "Aço 1020", "units": "mm", "standard": "ABNT_NBR", "overall_bbox": {}},
        "base_feature": {"name": "Base", "profile_type": "RECTANGLE", "length": 80.0, "width": 50.0, "extrude_depth": 15.0},
        "cuts": [],
        "holes": []
    }
    response = client.post("/api/update_model", json=sample_spec)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["spec"]["base_feature"]["length"] == 80.0
