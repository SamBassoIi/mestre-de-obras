"""Geometric validation and sanity checking for CAD models.
Ensures that features extracted by AI or entered by users are physically realizable.
"""

from typing import List, Tuple, Dict, Any
from core.schema import CadModelSpecification


class GeometryValidator:
    """Validates and sanitizes a CadModelSpecification before sending to CAD engines."""

    @staticmethod
    def validate_and_sanitize(model: CadModelSpecification) -> Tuple[bool, List[str]]:
        """Checks model sanity and returns (is_valid, list_of_warnings_or_errors)."""
        warnings = []
        base = model.base_feature

        # 1. Base dimensions check
        if base.length <= 0:
            base.length = 50.0
            warnings.append("Comprimento da base era <= 0; ajustado para 50.0 mm.")
        if base.width <= 0:
            base.width = 30.0
            warnings.append("Largura da base era <= 0; ajustada para 30.0 mm.")
        if base.extrude_depth <= 0:
            base.extrude_depth = 15.0
            warnings.append("Espessura/Altura da base era <= 0; ajustada para 15.0 mm.")

        half_l = base.length / 2.0
        half_w = base.width / 2.0

        # 2. Cuts sanity check
        valid_cuts = []
        for cut in model.cuts:
            if cut.length <= 0 or cut.width <= 0:
                warnings.append(f"Corte '{cut.name}' ignorado: dimensões inválidas ({cut.length}x{cut.width}).")
                continue
            if cut.depth <= 0:
                cut.depth = min(base.extrude_depth, 5.0)
                warnings.append(f"Profundidade do corte '{cut.name}' ajustada para {cut.depth} mm.")

            # Clamp cut boundaries to fit within base bounds with a small margin
            if abs(cut.pos_x) > half_l:
                warnings.append(f"Posição X do corte '{cut.name}' estava fora da base ({cut.pos_x} > {half_l}); ajustada.")
                cut.pos_x = half_l * 0.5 if cut.pos_x > 0 else -half_l * 0.5
            if abs(cut.pos_y) > half_w:
                warnings.append(f"Posição Y do corte '{cut.name}' estava fora da base ({cut.pos_y} > {half_w}); ajustada.")
                cut.pos_y = half_w * 0.5 if cut.pos_y > 0 else -half_w * 0.5

            valid_cuts.append(cut)
        model.cuts = valid_cuts

        # 3. Holes sanity check
        valid_holes = []
        for hole in model.holes:
            if hole.diameter <= 0:
                warnings.append(f"Furo '{hole.name}' ignorado: diâmetro <= 0.")
                continue
            if hole.diameter > min(base.length, base.width) * 0.9:
                hole.diameter = min(base.length, base.width) * 0.5
                warnings.append(f"Diâmetro do furo '{hole.name}' excedia a peça; limitado a {hole.diameter} mm.")

            # Ensure hole center fits inside base
            if abs(hole.pos_x) + (hole.diameter / 2.0) > half_l:
                warnings.append(f"Furo '{hole.name}' reposicionado para ficar contido na face (eixo X).")
                hole.pos_x = max(min(hole.pos_x, half_l - hole.diameter), -half_l + hole.diameter)
            if abs(hole.pos_y) + (hole.diameter / 2.0) > half_w:
                warnings.append(f"Furo '{hole.name}' reposicionado para ficar contido na face (eixo Y).")
                hole.pos_y = max(min(hole.pos_y, half_w - hole.diameter), -half_w + hole.diameter)

            valid_holes.append(hole)
        model.holes = valid_holes

        # 4. Chamfers & Fillets sanity check
        valid_chamfers = []
        for ch in model.chamfers:
            if ch.distance <= 0:
                continue
            max_ch = min(base.length, base.width, base.extrude_depth) * 0.25
            if ch.distance > max_ch:
                ch.distance = round(max_ch, 1)
                warnings.append(f"Chanfro '{ch.name}' limitado a {ch.distance} mm para evitar autointerseção.")
            valid_chamfers.append(ch)
        model.chamfers = valid_chamfers

        valid_fillets = []
        for fil in model.fillets:
            if fil.radius <= 0:
                continue
            max_fil = min(base.length, base.width, base.extrude_depth) * 0.3
            if fil.radius > max_fil:
                fil.radius = round(max_fil, 1)
                warnings.append(f"Raio de concordância '{fil.name}' limitado a {fil.radius} mm.")
            valid_fillets.append(fil)
        model.fillets = valid_fillets

        return True, warnings
