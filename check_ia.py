import sys
import httpx
import chromadb
import ollama

print("=" * 60)
print("🔍 INICIANDO DIAGNÓSTICO DE MOTORES DE IA LOCALES - LABGUARD AI")
print("=" * 60)

# 1. Verificar Ollama
print("\n[1] Verificando Ollama...")
try:
    models_response = ollama.list()
    # Compatibilidad con distintas versiones de la librería de ollama
    models = models_response.get('models', []) if isinstance(models_response, dict) else getattr(models_response, 'models', [])
    
    print("✅ ¡Ollama está activo y respondiendo!")
    print("   Modelos instalados en tu PC:")
    if models:
        for m in models:
            name = m.get('model') or getattr(m, 'model', 'Desconocido')
            print(f"     • {name}")
    else:
        print("     ⚠️ Hay conexión con Ollama, pero no se detectaron modelos descargados.")
except Exception as e:
    print(f"❌ Ollama NO está activo o no responde: {str(e)}")
    print("   👉 Sugerencia: Asegúrate de tener Ollama abierto en segundo plano.")

# 2. Verificar ChromaDB
print("\n[2] Verificando Base Vectorial (ChromaDB)...")
try:
    CHROMA_PATH = "./chroma_db"
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col = client.get_or_create_collection(name="lab_guides_cafq")
    count = col.count()
    print(f"✅ ChromaDB está funcionando correctamente en '{CHROMA_PATH}'.")
    print(f"   📊 Documentos/Guías indexados actualmente: {count}")
except Exception as e:
    print(f"❌ Error al conectar con ChromaDB: {str(e)}")

# 3. Verificar LM Studio (Puerto 1234)
print("\n[3] Verificando LM Studio (Puerto 1234)...")
try:
    response = httpx.get("http://localhost:1234/v1/models", timeout=2.0)
    if response.status_code == 200:
        print("✅ ¡LM Studio está abierto y su servidor local está activo!")
    else:
        print("⚠️ LM Studio respondió, pero con código inesperado.")
except Exception:
    print("💤 LM Studio está apagado o no se está ejecutando en el puerto 1234 (Esto es normal si no lo usas).")

print("\n" + "=" * 60)
print("🏁 DIAGNÓSTICO FINALIZADO")
print("=" * 60)