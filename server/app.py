"""FastAPI Application Server for AutoCroqui3D.
Provides REST endpoints for blueprint uploading, AI interpretation,
parametric updates, Three.js 3D visualization, and Autodesk Inventor automation.
"""

import os
import io
import base64
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from core.schema import CadModelSpecification
from core.ingestion import BlueprintIngestor
from core.vision import TechnicalDrawingVisionEngine
from core.geometry_validator import GeometryValidator
from core.inventor.ilogic_generator import generate_ilogic_code
from core.inventor.threejs_exporter import model_to_threejs_data, generate_obj_file
from core.inventor.inventor_com import InventorConnector

app = FastAPI(title="AutoCroqui3D - Desenho Técnico 2 para Autodesk Inventor", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AutoCroqui3D API Running. Front-end loading...</h1>"


@app.post("/api/upload")
async def upload_croqui(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(""),
    api_key: Optional[str] = Form("")
):
    """Processes uploaded blueprint (PDF, PNG, JPG, WEBP, etc.) and runs CAD vision interpretation."""
    if not BlueprintIngestor.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado. Envie arquivos PDF, PNG, JPG, JPEG, WEBP ou TIFF."
        )

    file_bytes = await file.read()
    images = BlueprintIngestor.load_document(file_bytes, file.filename)
    if not images:
        raise HTTPException(status_code=400, detail="Não foi possível extrair imagem do arquivo enviado.")

    primary_image = images[0]

    # Convert primary image to base64 for immediate side-by-side display in UI
    img_buffer = io.BytesIO()
    primary_image.save(img_buffer, format="JPEG", quality=85)
    img_b64 = f"data:image/jpeg;base64,{base64.b64encode(img_buffer.getvalue()).decode('utf-8')}"

    # AI Vision interpretation
    engine = TechnicalDrawingVisionEngine(api_key=api_key or None)
    spec, summary = engine.interpret_drawing(primary_image, additional_notes=notes or "")

    # Generate 3D visualization and iLogic code
    threejs_data = model_to_threejs_data(spec)
    ilogic_script = generate_ilogic_code(spec)

    return {
        "success": True,
        "filename": file.filename,
        "summary": summary,
        "preview_image": img_b64,
        "spec": spec.model_dump(),
        "threejs_data": threejs_data,
        "ilogic_script": ilogic_script,
        "inventor_available": InventorConnector().is_available()
    }


@app.post("/api/update_model")
async def update_model(spec_data: Dict[str, Any]):
    """Receives updated CAD specification from UI editing table and recalculates 3D data and iLogic."""
    try:
        spec = CadModelSpecification(**spec_data)
        GeometryValidator.validate_and_sanitize(spec)
        threejs_data = model_to_threejs_data(spec)
        ilogic_script = generate_ilogic_code(spec)
        return {
            "success": True,
            "spec": spec.model_dump(),
            "threejs_data": threejs_data,
            "ilogic_script": ilogic_script
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar modelo: {str(e)}")


@app.post("/api/model_inventor")
async def model_in_inventor(spec_data: Dict[str, Any]):
    """Triggers live Autodesk Inventor COM modeling on the local Windows machine."""
    try:
        spec = CadModelSpecification(**spec_data)
        GeometryValidator.validate_and_sanitize(spec)
        connector = InventorConnector(visible=True)
        result = connector.model_part(spec)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Falha na comunicação com o Autodesk Inventor: {str(e)}"
        }


@app.post("/api/download_ilogic")
async def download_ilogic(spec_data: Dict[str, Any]):
    """Returns downloadable .iLogicVb rule file."""
    try:
        spec = CadModelSpecification(**spec_data)
        code = generate_ilogic_code(spec)
        return PlainTextResponse(
            content=code,
            headers={"Content-Disposition": f'attachment; filename="{spec.metadata.title}_iLogic.iLogicVb"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download_obj")
async def download_obj(spec_data: Dict[str, Any]):
    """Returns downloadable .OBJ 3D geometry file."""
    try:
        spec = CadModelSpecification(**spec_data)
        obj_content = generate_obj_file(spec)
        return PlainTextResponse(
            content=obj_content,
            headers={"Content-Disposition": f'attachment; filename="{spec.metadata.title}.obj"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Mount static assets directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
