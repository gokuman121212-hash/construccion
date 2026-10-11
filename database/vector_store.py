"""
Módulo de Persistencia Vectorial con ChromaDB - CAFQ
"""
import chromadb

# Inicialización del cliente persistente en disco
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="lab_guides_cafq")