import requests

BASE_URL = "http://127.0.0.1:8000"

def probar_generacion_documentacion():
    print("[1] Inyectando datos de prueba y evidencias simuladas en REEF...")
    
    # 1. Registrar secciones y preguntas/respuestas simuladas con imágenes de prueba (base64)
    # Usaremos una imagen diminuta en base64 válida para la prueba
    imagen_base64_falsa = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    preguntas_prueba = [
        ("Sección A: Configuración y despliegue del entorno con variables inventadas XYZ.", "Resultado analítico: Se configuró el entorno con parámetros alfa y beta satisfactoriamente."),
        ("Sección B: Ejecución de scripts y pruebas de conectividad de red con código simulado.", "Resultado analítico: El script devolvió código de estado 200 OK en todas las pruebas ejecutadas."),
        ("Sección C: Auditoría de seguridad y análisis de rendimiento técnico.", "Resultado analítico: Sin pérdida de paquetes y latencia óptima en el servidor local.")
    ]

    for pregunta, respuesta in preguntas_prueba:
        payload = {
            "question": pregunta,
            "guide_id": "Prueba_Documentacion_Elite",
            "mode": "expert",
            "image": imagen_base64_falsa  # Adjuntamos la imagen falsa para probar el marcador visual
        }
        res = requests.post(f"{BASE_URL}/query", json=payload)
        if res.status_code == 200:
            print(f" -> Enunciado procesado: {pregunta[:35]}...")
        else:
            print(f" -> Error al procesar: {res.status_code}")

    print("\n[2] Solicitando descarga del documento .docx de prueba...")
    
    # 2. Descargar el archivo `.docx` generado
    export_url = f"{BASE_URL}/export-docx?guide_id=Prueba_Documentacion_Elite"
    doc_res = requests.get(export_url)
    
    if doc_res.status_code == 200:
        nombre_archivo = "Informe_Prueba_Documentacion.docx"
        with open(nombre_archivo, "wb") as f:
            f.write(doc_res.content)
        print(f"\n¡ÉXITO TOTAL! Documento generado y guardado en tu equipo como: '{nombre_archivo}'")
    else:
        print(f"\nError al exportar: {doc_res.status_code} - {doc_res.text}")

if __name__ == "__main__":
    probar_generacion_documentacion()