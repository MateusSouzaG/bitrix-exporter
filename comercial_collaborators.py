# -*- coding: utf-8 -*-
"""Colaboradores do departamento COMERCIAL (leitura da planilha existente)."""
from typing import Dict, List, Tuple

from comercial_config import COMERCIAL_DEPT


def filter_comercial_collaborators(
    collaborators_map: Dict[int, Dict[str, str]],
) -> Dict[int, Dict[str, str]]:
    """Retorna apenas colaboradores com departamento COMERCIAL."""
    out = {}
    for uid, info in collaborators_map.items():
        dept = (info.get("dept") or "").strip().upper()
        if dept == COMERCIAL_DEPT.upper():
            out[uid] = info
    return out


def comercial_collaborator_list(
    collaborators_map: Dict[int, Dict[str, str]],
) -> List[Tuple[int, str]]:
    """Lista (user_id, nome) ordenada por nome."""
    filtered = filter_comercial_collaborators(collaborators_map)
    return sorted(
        [(uid, info["name"]) for uid, info in filtered.items() if info.get("name")],
        key=lambda x: x[1].lower(),
    )
