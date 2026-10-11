import os
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from pypdf import PdfReader
import ollama   

app = FastAPI(
    title="LabGuard AI - Sistema Multiagente CAFQ",
    version="3.1.0",
    description="Backend avanzado con RAG, Modo Dual (Flash/Deep), Agente Generador, Agente Auditor y Evaluador."
)

# Configurar CORS para la interfaz web (index.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar ChromaDB en disco local
CHROMA_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="lab_guides_cafq")

# Modelos de Pydantic con soporte para el parámetro 'mode'
class QueryInput(BaseModel):
    question: str
    guide_id: str = "default"
    mode: str = "fast"  # "fast" (modo rápido) o "deep" (modo profundo/auditoría)

class GuideInput(BaseModel):
    guide_id: str
    raw_text: str

class PostLabInput(BaseModel):
    guide_id: str
    report_text: str


# 1. Endpoint para ingerir texto plano
@app.post("/ingest")
def ingest_guide(data: GuideInput):
    text = data.raw_text
    pasos = re.findall(r"\d+[\.\-]\s*([^\.\n]+(?:\.|$))", text)
    if not pasos:
        pasos = [text[:150] + "..."]
    checklist = [f"[ ] {paso.strip()}" for paso in pasos]

    collection.upsert(
        documents=[text],
        metadatas=[{"guide_id": data.guide_id}],
        ids=[data.guide_id]
    )

    return {
        "status": "Ingestado con éxito por el sistema multiagente",
        "guide_id": data.guide_id,
        "checklist_verificacion": checklist
    }


# 2. Endpoint para ingerir archivos PDF optimizado con fragmentación (Chunks)
@app.post("/ingest-pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un formato PDF válido.")
    
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    reader = PdfReader(temp_path)
    extracted_text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            extracted_text += t + "\n"
            
    os.remove(temp_path)
    
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="El PDF está vacío o no se pudo extraer texto.")

    guide_id = file.filename.split('.')[0]
    
    # Fragmentar el texto en bloques de ~1000 caracteres para que ChromaDB busque con precisión
    chunk_size = 1000
    chunks = [extracted_text[i:i+chunk_size] for i in range(0, len(extracted_text), chunk_size)]
    chunk_ids = [f"{guide_id}_chunk_{idx}" for idx in range(len(chunks))]
    chunk_metadatas = [{"guide_id": guide_id, "chunk_index": idx} for idx in range(len(chunks))]

    pasos = re.findall(r"\d+[\.\-]\s*([^\.\n]+(?:\.|$))", extracted_text)
    if not pasos:
        pasos = ["Revisar la guía completa en la interfaz."]
    checklist = [f"[ ] {paso.strip()}" for paso in pasos[:10]]

    # Guardar los fragmentos en ChromaDB
    collection.upsert(
        documents=chunks,
        metadatas=chunk_metadatas,
        ids=chunk_ids
    )

    return {
        "status": "PDF procesado, fragmentado e indexado con éxito",
        "guide_id": guide_id,
        "checklist_verificacion": checklist
    }

# 3. Endpoint de Consulta Inteligente con Soporte de Modo Dual (Flash vs Deep)
@app.post("/query")
def query_multi_agent(data: QueryInput):
    results = collection.query(
        query_texts=[data.question],
        n_results=3  # <-- Recuperamos los 3 mejores fragmentos relacionados
    )

    documents = results.get("documents", [[]])
    if not documents or not documents[0]:
        return {"answer": "No se encontró ninguna guía de laboratorio cargada. Sube un documento primero."}

    contexto_guia = "\n\n".join(results.get("documents", [[]])[0])

    try:
        # --- MODO RÁPIDO (FLASH): Respuesta directa, fluida y ágil ---
        if data.mode == "fast":
            fast_system_prompt = "Eres LabGuard AI en Modo Flash. Responde a la consulta de forma rápida, clara y directa usando la guía."
            response_fast = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': fast_system_prompt},
                {'role': 'user', 'content': f"GUÍA:\n{contexto_guia}\n\nPREGUNTA:\n{data.question}"}
            ], options={'temperature': 0.1, 'num_predict': 350})
            
            return {"answer": response_fast['message']['content']}

        # --- MODO PROFUNDO (DEEP): Sistema Multiagente Estricto (Generador + Auditor) ---
        else:
            # Agente 1: Generador Académico
            gen_system_prompt = "Eres el Agente Generador de LabGuard AI. Redacta una explicación detallada y estructurada basada en la guía."
            response_gen = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': gen_system_prompt},
                {'role': 'user', 'content': f"GUÍA:\n{contexto_guia}\n\nPREGUNTA:\n{data.question}"}
            ])
            respuesta_borrador = response_gen['message']['content']

            # Agente 2: Auditor / Validador de Seguridad (Anti-Alucinaciones)
            auditor_system_prompt = """
            Eres el Agente Auditor de Seguridad de LabGuard AI. Verifica si la respuesta contiene información inventada o ajena al texto de la guía.
            - Si es fiel al texto, devuélvela con formato claro.
            - Si detectas datos falsos, responde: 'Esa información no se encuentra en la guía de este laboratorio. Consulta con tu docente.'
            """
            response_auditor = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': auditor_system_prompt},
                {'role': 'user', 'content': f"TEXTO ORIGINAL DE LA GUÍA:\n{contexto_guia}\n\nRESPUESTA A AUDITAR:\n{respuesta_borrador}"}
            ])
            
            return {"answer": response_auditor['message']['content']}

    except Exception as e:
        return {
            "answer": f"Error de comunicación con el motor local de Ollama. Asegúrate de ejecutar 'ollama run llama3.2'. Detalle: {str(e)}"
        }


# 4. Endpoint para el Agente Evaluador de Informes Post-Laboratorio
@app.post("/post-lab-report")
def evaluate_post_lab(data: PostLabInput):
    results = collection.get(ids=[data.guide_id])
    if not results or not results.get("documents"):
        all_docs = collection.get()
        if all_docs and all_docs.get("documents"):
            contexto_guia = all_docs["documents"][0]
        else:
            raise HTTPException(status_code=404, detail="No se encontró la guía de referencia para evaluar el informe.")
    else:
        contexto_guia = results["documents"][0]

    eval_system_prompt = """
    Eres el Agente Evaluador Pedagógico de LabGuard AI. Califica y da retroalimentación constructiva sobre el informe post-laboratorio.
    Proporciona:
    1. Valoración general (Logrado / En proceso).
    2. Retroalimentación sobre aciertos y errores en cálculos o conclusiones.
    """
    eval_user_prompt = f"GUÍA DE REFERENCIA:\n{contexto_guia}\n\nINFORME DEL ESTUDIANTE:\n{data.report_text}"

    try:
        response_eval = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': eval_system_prompt},
            {'role': 'user', 'content': eval_user_prompt}
        ])
        return {"evaluation": response_eval['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la evaluación con Ollama: {str(e)}")