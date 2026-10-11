"""
Módulo de Seguridad y Filtrado - LabGuard AI (CAFQ)
"""
import re

def sanitize_input(text: str) -> str:
    """Sanitiza las entradas de texto para prevenir inyecciones y asegurar el estándar CAFQ."""
    if not text:
        return ""
    cleaned = re.sub(r'[<>]', '', text)
    return cleaned.strip()

def check_content_safety(query: str) -> bool:
    """Verifica restricciones de seguridad en las consultas de laboratorio."""
    forbidden_terms = ["explosivo casero", "toxico ilegal", "armas"]
    query_lower = query.lower()
    for term in forbidden_terms:
        if term in query_lower:
            return False
    return True