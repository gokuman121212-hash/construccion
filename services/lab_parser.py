"""
Parser de Guías de Laboratorio y Generador de Checklist - CAFQ
"""
import re
from typing import Dict, Any

def parse_and_generate_checklist(raw_text: str) -> Dict[str, Any]:
    patterns = {
        "objetivos": r"(?i)(?:objetivos?|prop[oó]sito)\s*[:\-]?\s*(.*?)(?=(?:equipos?|materiales?|reactivos?|fundamento|marco\s+te[oó]rico|procedimiento|cuestionario|\Z))",
        "materiales": r"(?i)(?:equipos?|materiales?|reactivos?|hardware|software)\s*[:\-]?\s*(.*?)(?=(?:fundamento|marco\s+te[oó]rico|procedimiento|cuestionario|\Z))",
        "teoria": r"(?i)(?:fundamento\s+te[oó]rico|marco\s+te[oó]rico|introducci[oó]n)\s*[:\-]?\s*(.*?)(?=(?:procedimiento|experimento|pasos|cuestionario|\Z))",
        "procedimiento": r"(?i)(?:procedimiento|metodolog[ií]a|desarrollo|experimento)\s*[:\-]?\s*(.*?)(?=(?:cuestionario|evaluaci[oó]n|preguntas|\Z))",
        "cuestionario": r"(?i)(?:cuestionario|evaluaci[oó]n|preguntas\s+de\s+control)\s*[:\-]?\s*(?=\Z)"
    }
    
    sections = {}
    for section, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.DOTALL)
        sections[section] = match.group(1).strip() if match else "No detectada"

    procedure_lines = [line.strip() for line in sections["procedimiento"].split('\n') if line.strip()]
    checklist = [f"[ ] {line}" for line in procedure_lines if line[0].isdigit() or line.startswith("-")]
    if not checklist:
        checklist = ["[ ] Verificar equipos y materiales", "[ ] Ejecutar pasos del procedimiento", "[ ] Resolver cuestionario"]

    return {"sections": sections, "checklist": checklist}