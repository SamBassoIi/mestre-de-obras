"""Unit tests for Blueprint Ingestor."""

import io
from PIL import Image
from core.ingestion import BlueprintIngestor

def test_image_bytes_processing():
    # Create simple RGB test image in memory
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    result_imgs = BlueprintIngestor.load_document(png_bytes, "croqui_teste.png")
    assert len(result_imgs) == 1
    assert result_imgs[0].size == (200, 200)

def test_supported_extensions():
    assert BlueprintIngestor.is_supported("croqui.pdf")
    assert BlueprintIngestor.is_supported("foto.jpg")
    assert BlueprintIngestor.is_supported("scan.png")
    assert BlueprintIngestor.is_supported("desenho.webp")
    assert not BlueprintIngestor.is_supported("croqui.docx")
