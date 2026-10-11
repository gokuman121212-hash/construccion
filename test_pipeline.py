import requests

BASE_URL = "http://127.0.0.1:8000"

def test_health_and_query():
    print("🔍 Verificando conexión con el backend de FastAPI...")
    try:
        # 1. Probar una consulta de ejemplo directamente al endpoint /query
        payload = {
            "question": "¿Cuáles son los roles del equipo?",
            "guide_id": "default",
            "mode": "fast"
        }
        response = requests.post(f"{BASE_URL}/query", json=payload)
        
        if response.status_code == 200:
            print("¡Conexión exitosa con el servidor!")
            print("Respuesta de LabGuard AI (Modo Flash):")
            print("-" * 50)
            print(response.json().get("answer"))
            print("-" * 50)
        else:
            print(f"El servidor respondió con error HTTP: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("No se pudo conectar con Uvicorn. Asegúrate de que el servidor esté corriendo en http://127.0.0.1:8000")

if __name__ == "__main__":
    test_health_and_query()