import os
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.embeddings import get_embeddings
from app.config import settings

def get_qdrant_client() -> QdrantClient:
    if settings.qdrant_host == ":memory:":
        print("[Qdrant] Initializing in-memory Qdrant Client...")
        return QdrantClient(":memory:")

    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            timeout=3.0
        )
        client.get_collections()
        return client
    except Exception as e:
        print(f"[Qdrant] Failed to connect to server at {settings.qdrant_host}:{settings.qdrant_port} ({e}). Falling back to in-memory Qdrant Client...")
        return QdrantClient(":memory:")

def get_vector_store() -> QdrantVectorStore:
    embeddings = get_embeddings()
    client = get_qdrant_client()

    if not client.collection_exists(collection_name=settings.qdrant_collection_name):
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config={"size": 1536, "distance": "Cosine"}
        )

    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=embeddings
    )

def ingest_datasheet(pdf_path: str) -> int:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)

def query_datasheets(query_text: str, limit: int = 5):
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query_text, k=limit)
    return docs
