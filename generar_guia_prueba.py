import zipfile
import os

def crear_guia_laboratorio_nativo():
    nombre_archivo = "Guia_Laboratorio_Tecsup.docx"
    
    # Contenido XML básico estructurado para un documento Word válido
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

    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p><w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr><w:t>TECSUP - GUÍA DE PRÁCTICA DE LABORATORIO N° 01</w:t></w:r></w:p>
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Programa: Diseño y Desarrollo de Software</w:t></w:r></w:p>
            <w:p><w:r><w:t>------------------------------------------------------------------------------------------------</w:t></w:r></w:p>
            
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>1. Objetivos de la Práctica</w:t></w:r></w:p>
            <w:p><w:r><w:t>- Implementar un sistema RAG local con FastAPI y Ollama.</w:t></w:r></w:p>
            <w:p><w:r><w:t>- Gestionar flujos de trabajo guiados y exportación de informes técnicos.</w:t></w:r></w:p>
            
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>2. Procedimiento y Tareas</w:t></w:r></w:p>
            <w:p><w:r><w:t>Paso 1: Ejecute el servidor local de Uvicorn y compruebe los endpoints.</w:t></w:r></w:p>
            <w:p><w:r><w:t>Paso 2: Ingrese las mediciones de latencia obtenidas en las pruebas.</w:t></w:r></w:p>
            
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>3. Espacio para Evidencias y Capturas</w:t></w:r></w:p>
            <w:p><w:r><w:t>[ INSERTE AQUÍ LA CAPTURA DE PANTALLA DE LA TERMINAL FUNCIONANDO ]</w:t></w:r></w:p>
            
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>4. Cuestionario de Análisis</w:t></w:r></w:p>
            <w:p><w:r><w:t>Pregunta 1: ¿Cómo evita REEF las alucinaciones frente a ChatGPT convencional?</w:t></w:r></w:p>
            <w:p><w:r><w:t>Respuesta del alumno: __________________________________________________________________</w:t></w:r></w:p>
            
            <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>5. Conclusiones y Observaciones</w:t></w:r></w:p>
            <w:p><w:r><w:t>- Conclusión 1: ________________________________________________________________________</w:t></w:r></w:p>
        </w:body>
    </w:document>"""

    # Crear el archivo comprimido ZIP con extensión .docx
    with zipfile.ZipFile(nombre_archivo, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types)
        docx.writestr('_rels/.rels', rels)
        docx.writestr('word/document.xml', document_xml)

    print(f"¡Documento '{nombre_archivo}' generado con éxito sin errores de lxml!")

if __name__ == "__main__":
    crear_guia_laboratorio_nativo()