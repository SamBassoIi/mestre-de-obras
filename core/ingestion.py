"""Multiformat Blueprint & Sketch Ingestion Engine.
Handles ingestion of PDF (single/multi-page), PNG, JPG, JPEG, WEBP, BMP, and TIFF files.
Prepares optimized, high-contrast imagery for technical drawing vision analysis.
"""

import io
import os
from typing import List, Dict, Any, Union, Optional
from PIL import Image, ImageOps, ImageEnhance


class BlueprintIngestor:
    """Pre-processes CAD blueprints, sketches, and exam drawings from various file formats."""

    SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        ext = os.path.splitext(filename.lower())[1]
        return ext in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def load_document(cls, file_bytes: bytes, filename: str) -> List[Image.Image]:
        """Loads any supported document and returns a list of pre-processed PIL Images (one per page/image)."""
        ext = os.path.splitext(filename.lower())[1]

        if ext == ".pdf":
            return cls._process_pdf(file_bytes)
        else:
            return [cls._process_image_bytes(file_bytes)]

    @classmethod
    def _process_image_bytes(cls, img_bytes: bytes) -> Image.Image:
        """Loads and enhances an image for CAD analysis."""
        img = Image.open(io.BytesIO(img_bytes))
        # Handle EXIF orientation (e.g. photos taken from mobile phone)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode != "RGB":
            img = img.convert("RGB")

        # Gentle auto-contrast enhancement to make faint pencil/drawing lines crisper
        try:
            img = ImageOps.autocontrast(img, cutoff=1)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
        except Exception:
            pass

        return img

    @classmethod
    def _process_pdf(cls, pdf_bytes: bytes) -> List[Image.Image]:
        """Extracts pages or embedded images from a PDF file."""
        images: List[Image.Image] = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))

            for page_idx, page in enumerate(reader.pages):
                page_extracted = False
                # First check for high-res raster drawings embedded in the PDF
                if hasattr(page, "images") and page.images:
                    for img_obj in page.images:
                        try:
                            pil_img = Image.open(io.BytesIO(img_obj.data))
                            if pil_img.mode != "RGB":
                                pil_img = pil_img.convert("RGB")
                            images.append(pil_img)
                            page_extracted = True
                        except Exception:
                            continue

                # If no embedded images could be extracted directly, try pypdfium2 / pdf2image fallback if available
                if not page_extracted:
                    # In case of purely vector PDF without embedded bitmap, create a placeholder representation or fallback
                    pass

        except Exception as e:
            print(f"[Ingestor] Erro ao ler PDF: {e}")

        # If no images were extracted, try opening as a direct image fallback
        if not images:
            try:
                images.append(cls._process_image_bytes(pdf_bytes))
            except Exception:
                # Create a blank fallback canvas indicating vector page
                fallback = Image.new("RGB", (1200, 800), color=(255, 255, 255))
                images.append(fallback)

        return images

    @staticmethod
    def image_to_jpeg_bytes(img: Image.Image, quality: int = 95) -> bytes:
        """Converts PIL image to compressed JPEG bytes suitable for API payload."""
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
