"""Multimodal AI Vision Engine for Technical Drawing & Blueprint Interpretation.
Uses Google Gemini API to analyze orthographic views, dimension callouts (cotas),
and reconstruct the parametric CAD Feature Tree.
"""

import os
import json
from typing import Optional, Tuple
from PIL import Image
from core.schema import (
    CadModelSpecification, PartMetadata, BaseFeature, CutFeature, HoleFeature,
    ChamferFeature, FilletFeature, ProfileType, SketchPlane
)
from core.ingestion import BlueprintIngestor
from core.geometry_validator import GeometryValidator

# Specialized prompt designed for Brazilian University Technical Drawing 2 (ABNT / ISO)
CAD_VISION_SYSTEM_INSTRUCTION = """
Você é um Engenheiro Mecânico Especialista em Desenho Técnico Mecânico (ABNT NBR 10067, NBR 10126, NBR 8403, 1º Diedro) e Modelagem Paramétrica CAD no Autodesk Inventor.
Sua missão é analisar uma imagem ou prancha técnica de croqui/desenho de aula (croquis à mão livre, desenhos com vistas ortográficas, cortes e cotas) e reconstruir a Árvore de Features 3D para modelagem no Inventor.

Regras de Interpretação:
1. **Unidade**: Todas as medidas de Desenho Técnico Mecânico são estritamente em MILÍMETROS (mm), a menos que explicitado o contrário.
2. **Vistas e Diedro**: No 1º diedro (padrão brasileiro/ABNT):
   - A Vista Frontal é a vista principal.
   - A Vista Superior fica ABAIXO da vista frontal.
   - A Vista Lateral Esquerda fica À DIREITA da vista frontal.
   - Se houver corte (ex: Corte A-A), as hachuras indicam material sólido cortado e linhas cheias indicam contornos visíveis internos (furos, rebaixos).
3. **Simbologia de Cotagem**:
   - 'Ø' ou 'diam': Diâmetro de cilindro ou furo.
   - 'R': Raio de curvatura/concordância.
   - 'x 45°': Chanfro (ex: 2x45° significa chanfro de 2mm a 45 graus).
   - 'passante' ou furo sem indicação de profundidade em vista de corte: through_all = True.
4. **Decomposição em Operações CAD**:
   - **base_feature**: O corpo sólido primordial da peça (ex: bloco retangular ou cilindro principal).
     - length: comprimento (X)
     - width: largura (Y)
     - extrude_depth: altura ou espessura (Z)
   - **cuts**: Rebaixos, rasgos, degraus, encaixes ou bolsões (subtração de material).
     - pos_x, pos_y: centro ou posição relativa na face superior/face correspondente.
     - length, width, depth: dimensões do rasgo.
   - **holes**: Furos cilíndricos, passantes ou cegos.
     - diameter: diâmetro Ø
     - pos_x, pos_y: coordenadas do centro do furo em relação ao centro da face (0,0 no centro da peça).
     - through_all: booleano (True para furo passante).
   - **chamfers**: Chanfros nas bordas externas ou cantos.
   - **fillets**: Raios de arredondamento / concordâncias.

IMPORTANTE: Você deve responder EXCLUSIVAMENTE um objeto JSON válido, sem texto explicativo antes ou depois, sem crases de markdown além do bloco JSON se necessário.
"""

CAD_JSON_SCHEMA_DESCRIPTION = {
    "metadata": {
        "title": "Nome da peça extraído da legenda ou descrição (ex: Suporte Guia)",
        "material": "Aço 1020 ou material indicado",
        "standard": "ABNT_NBR",
        "overall_bbox": {"length": 100.0, "width": 60.0, "height": 30.0}
    },
    "base_feature": {
        "name": "Base_Prismatica",
        "profile_type": "RECTANGLE",
        "length": 100.0,
        "width": 60.0,
        "extrude_depth": 25.0
    },
    "cuts": [
        {
            "name": "Rebaixo_Central",
            "face": "TOP",
            "pos_x": 0.0,
            "pos_y": 0.0,
            "length": 40.0,
            "width": 30.0,
            "depth": 10.0,
            "through_all": False
        }
    ],
    "holes": [
        {
            "name": "Furo_Passante_1",
            "face": "TOP",
            "pos_x": -30.0,
            "pos_y": 0.0,
            "diameter": 12.0,
            "depth": 25.0,
            "through_all": True
        }
    ],
    "chamfers": [
        {
            "name": "Chanfro_Bordas",
            "distance": 2.0,
            "angle": 45.0
        }
    ],
    "fillets": [
        {
            "name": "Raio_Cantos",
            "radius": 5.0
        }
    ]
}


class TechnicalDrawingVisionEngine:
    """Processes technical drawings with Gemini Multimodal or heuristic fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def interpret_drawing(
        self, 
        image: Image.Image, 
        additional_notes: str = "",
        model_name: str = "gemini-1.5-pro"
    ) -> Tuple[CadModelSpecification, str]:
        """Interprets a technical drawing image and returns a CadModelSpecification + analysis summary."""
        if not self.api_key:
            # Fallback heuristic / sample model for testing when API key is not configured
            spec = self._generate_heuristic_spec(image, additional_notes)
            summary = "Modo Demonstração / Heurístico (configure GEMINI_API_KEY para interpretação completa por IA multimodal)."
            return spec, summary

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            jpeg_bytes = BlueprintIngestor.image_to_jpeg_bytes(image)

            prompt = (
                f"{CAD_VISION_SYSTEM_INSTRUCTION}\n\n"
                f"Exemplo de Estrutura Esperada (JSON):\n{json.dumps(CAD_JSON_SCHEMA_DESCRIPTION, indent=2)}\n\n"
                f"Notas adicionais do estudante: {additional_notes or 'Nenhuma'}\n"
                "Analise minuciosamente todas as cotas, vistas ortográficas e cortes do desenho em anexo. "
                "Retorne o JSON exato com as operações paramétricas para o Autodesk Inventor."
            )

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            # Clean possible markdown wrap
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            spec = CadModelSpecification(**data)
            
            # Geometric validation and sanitization
            _, warnings = GeometryValidator.validate_and_sanitize(spec)
            summary = f"Croqui interpretado com sucesso pela IA Gemini! ({len(warnings)} avisos geométricos tratados)."

            return spec, summary

        except Exception as e:
            print(f"[Vision Engine] Erro ao chamar API Gemini: {e}. Usando fallback.")
            spec = self._generate_heuristic_spec(image, additional_notes)
            summary = f"Aviso na interpretação por IA: {str(e)}. Modelo de fallback gerado para conferência."
            return spec, summary

    def _generate_heuristic_spec(self, image: Image.Image, notes: str) -> CadModelSpecification:
        """Generates a realistic CAD piece for testing when offline or API is unavailable."""
        title = "Peca_Exercicio_DT2"
        if notes and len(notes.strip()) > 2:
            title = notes.strip().replace(" ", "_")[:30]

        spec = CadModelSpecification(
            metadata=PartMetadata(
                title=title,
                student_notes=notes,
                material="Aço 1020",
                units="mm",
                overall_bbox={"length": 120.0, "width": 80.0, "height": 30.0}
            ),
            base_feature=BaseFeature(
                name="Base_Mecanica",
                profile_type=ProfileType.RECTANGLE,
                length=120.0,
                width=80.0,
                extrude_depth=25.0
            ),
            cuts=[
                CutFeature(
                    name="Rasgo_Central_Superior",
                    face="TOP",
                    pos_x=0.0,
                    pos_y=0.0,
                    length=50.0,
                    width=30.0,
                    depth=10.0
                )
            ],
            holes=[
                HoleFeature(
                    name="Furo_Fixacao_Esq",
                    face="TOP",
                    pos_x=-40.0,
                    pos_y=0.0,
                    diameter=12.0,
                    through_all=True
                ),
                HoleFeature(
                    name="Furo_Fixacao_Dir",
                    face="TOP",
                    pos_x=40.0,
                    pos_y=0.0,
                    diameter=12.0,
                    through_all=True
                )
            ],
            chamfers=[
                ChamferFeature(name="Chanfro_Entrada", distance=2.0, angle=45.0)
            ],
            fillets=[
                FilletFeature(name="Raio_Cantos_Base", radius=6.0)
            ]
        )
        GeometryValidator.validate_and_sanitize(spec)
        return spec
