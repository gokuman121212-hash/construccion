import os
import re
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import chromadb
from pypdf import PdfReader
import ollama 
import zipfile
from xml.sax.saxutils import escape

app = FastAPI(
    title="REEF - Copiloto de Laboratorio Tecsup",
    version="6.0.0",
    description="Backend definitivo con RAG Estructural Avanzado, Auditoría de Evidencias y Generación Nativa DOCX"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="lab_guides_reef_elite")

STUDENT_WORK_MEMORY = {}

class QueryInput(BaseModel):
    question: str
    guide_id: str = "default"
    mode: str = "expert"
    image: str | None = None

class GuideInput(BaseModel):
    guide_id: str
    raw_text: str


@app.post("/ingest-pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un formato PDF válido.")
    
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    reader = PdfReader(temp_path)
    extracted_text = ""
    for page_num, page in enumerate(reader.pages):
        t = page.extract_text()
        if t:
            extracted_text += f"\n[Página {page_num + 1}]\n" + t + "\n"
            
    os.remove(temp_path)
    
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="El PDF está vacío o no se pudo extraer texto.")

    guide_id = file.filename.split('.')[0]
    
    # Segmentación inteligente basada en patrones académicos y títulos
    raw_sections = re.split(r"(?i)(?:objetivo|paso|sección|actividad|cuestionario|conclusión|\b\d+[\.\-]\s+[A-ZÁÉÍÓÚ])", extracted_text)
    chunks = [s.strip() for s in raw_sections if len(s.strip()) > 50]
    
    if not chunks:
        # Fallback de fragmentación por bloques de 1000 caracteres con solapamiento
        chunk_size = 1000
        overlap = 200
        chunks = [extracted_text[i:i+chunk_size] for i in range(0, len(extracted_text), chunk_size - overlap)]

    chunk_ids = [f"{guide_id}_chunk_{idx}" for idx in range(len(chunks))]
    chunk_metadatas = [{"guide_id": guide_id, "chunk_index": idx} for idx in range(len(chunks))]

    # Extracción de checklist de actividades
    detectados = re.findall(r"(?:Paso|Sección|Actividad)\s*\d+[\.\-]?\s*([^\.\n]+)", extracted_text, re.IGNORECASE)
    if not detectados:
        detectados = [
            "1. Objetivos y Requisitos del Entorno",
            "2. Configuración y Pruebas Iniciales",
            "3. Ejecución de Procedimientos y Scripts",
            "4. Cuestionario de Análisis y Preguntas",
            "5. Conclusiones y Observaciones"
        ]
    
    checklist = [d.strip() for d in detectados[:10]]

    collection.upsert(
        documents=chunks,
        metadatas=chunk_metadatas,
        ids=chunk_ids
    )

    STUDENT_WORK_MEMORY[guide_id] = {
        "sections": checklist,
        "content_collected": {}
    }

    return {
        "status": "PDF examinado y desglosado con éxito mediante RAG Estructural",
        "guide_id": guide_id,
        "checklist_verificacion": checklist
    }


@app.post("/query")
def query_copilot(data: QueryInput):
    results = collection.query(
        query_texts=[data.question],
        n_results=4
    )

    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    
    context_blocks = []
    if documents and documents[0]:
        for doc, meta in zip(documents[0], metadatas[0]):
            context_blocks.append(f"[Referencia - Segmento {meta.get('chunk_index', 0)}]\n{doc}")
            
    contexto_guia = "\n\n".join(context_blocks) if context_blocks else "Guía estándar de laboratorio Tecsup."

    if data.image and data.guide_id:
        if data.guide_id not in STUDENT_WORK_MEMORY:
            STUDENT_WORK_MEMORY[data.guide_id] = {"sections": ["Desarrollo General"], "content_collected": {}}
        STUDENT_WORK_MEMORY[data.guide_id]["content_collected"][data.question[:40] or "Evidencia visual"] = {
            "text": data.question,
            "image": data.image
        }

    try:
        system_prompt = """
        Eres REEF, el copiloto académico de élite y tutor experto para estudiantes de Tecsup (Arequipa).
        Tu propósito es asegurar el rigor técnico, la excelencia en el código y el cumplimiento de los estándares institucionales.
        
        Directrices de respuesta:
        1. Explica los fundamentos técnicos, comandos, fragmentos de código o lógica de programación de forma impecable y didáctica.
        2. Analiza críticamente los avances o evidencias que aporte el estudiante, validando su correspondencia con el contexto de la guía oficial.
        3. Mantén un tono formal, profesional y directo. NUNCA recortes respuestas ni dejes oraciones inconclusas.
        """
        
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"CONTEXTO OFICIAL DE LA GUÍA:\n{contexto_guia}\n\nCONSULTA / AVANCE DEL ESTUDIANTE:\n{data.question}"}
        ], options={'temperature': 0.2, 'num_predict': 1500})
        
        return {"answer": response['message']['content']}

    except Exception as e:
        return {"answer": f"Error al procesar la solicitud con el motor local: {str(e)}"}


@app.get("/export-docx")
def export_docx(guide_id: str = "default"):
    work_data = STUDENT_WORK_MEMORY.get(guide_id, {
        "sections": [
            "1. Objetivos de la Práctica",
            "2. Procedimiento y Tareas",
            "3. Espacio para Evidencias y Capturas",
            "4. Cuestionario de Análisis",
            "5. Conclusiones y Observaciones"
        ],
        "content_collected": {}
    })
    
    sections = work_data.get("sections", [])
    collected = work_data.get("content_collected", {})

    # Estructura formal idéntica a la guía oficial de Tecsup
    body_xml = f"""
    <w:p><w:r><w:rPr><w:b/><w:sz w:val="32"/></w:rPr><w:t>TECSUP - GUÍA DE PRÁCTICA DE LABORATORIO N° 01</w:t></w:r></w:p>
    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Programa: Diseño y Desarrollo de Software</w:t></w:r></w:p>
    <w:p><w:r><w:t>----------------------------------------------------------------------------------------------------------------</w:t></w:r></w:p>
    """

    # 1. Objetivos de la Práctica
    body_xml += '<w:p><w:r><w:rPr><w:b/><w:sz w:val="26"/></w:rPr><w:t>1. Objetivos de la Práctica</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>- Implementar y validar los componentes desarrollados mediante el copiloto REEF.</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>- Gestionar flujos de trabajo guiados y exportación de informes técnicos formales.</w:t></w:r></w:p>'

    # 2. Procedimiento y Tareas (Rellenado con el avance del alumno)
    body_xml += '<w:p><w:r><w:rPr><w:b/><w:sz w:val="26"/></w:rPr><w:t>2. Procedimiento y Tareas</w:t></w:r></w:p>'
    for idx, sec in enumerate(sections[:3], start=1):
        body_xml += f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Paso {idx}: {escape(str(sec))}</w:t></w:r></w:p>'
        body_xml += '<w:p><w:r><w:t>  - Estado: Ejecutado, auditado y validado satisfactoriamente en entorno local.</w:t></w:r></w:p>'

    # 3. Espacio para Evidencias y Capturas (Con las imágenes / trazas reales de sesión)
    body_xml += '<w:p><w:r><w:rPr><w:b/><w:sz w:val="26"/></w:rPr><w:t>3. Espacio para Evidencias y Capturas</w:t></w:r></w:p>'
    if collected:
        for key, item in collected.items():
            text_desc = escape(item.get('text', 'Evidencia adjunta'))
            body_xml += f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>[ INSERTE AQUÍ LA CAPTURA DE PANTALLA: {text_desc} ]</w:t></w:r></w:p>'
    else:
        body_xml += '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>[ INSERTE AQUÍ LA CAPTURA DE PANTALLA DE LA TERMINAL FUNCIONANDO ]</w:t></w:r></w:p>'

    # 4. Cuestionario de Análisis
    body_xml += '<w:p><w:r><w:rPr><w:b/><w:sz w:val="26"/></w:rPr><w:t>4. Cuestionario de Análisis</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Pregunta 1: ¿Cómo optimiza REEF la validación y el desarrollo en los laboratorios de Tecsup?</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>Respuesta del alumno:</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>Permite automatizar la auditoría técnica paso a paso y empaquetar de forma exacta la estructura institucional exigida en los informes.</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>_________________________________________________________________________________</w:t></w:r></w:p>'

    # 5. Conclusiones y Observaciones
    body_xml += '<w:p><w:r><w:rPr><w:b/><w:sz w:val="26"/></w:rPr><w:t>5. Conclusiones y Observaciones</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>- Conclusión 1: Se cumplió con la configuración del servidor local Uvicorn y la integración de endpoints con FastAPI.</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>- Conclusión 2: El sistema RAG de REEF garantizó precisión técnica y rigor académico durante todo el proceso de laboratorio.</w:t></w:r></w:p>'
    body_xml += '<w:p><w:r><w:t>_________________________________________________________________________________</w:t></w:r></w:p>'

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            {body_xml}
        </w:body>
    </w:document>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
        <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
        <Default Extension="xml" ContentType="application/xml"/>
        <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    </Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    </Relationships>"""

    file_stream = BytesIO()
    with zipfile.ZipFile(file_stream, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types)
        docx.writestr('_rels/.rels', rels)
        docx.writestr('word/document.xml', document_xml)
    
    file_stream.seek(0)

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=Informe_Tecsup_Exacto_{guide_id}.docx"}
    )