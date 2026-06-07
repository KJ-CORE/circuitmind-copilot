from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings
from app.config import settings

def get_embeddings():
    if settings.openai_api_key.startswith("nvapi-"):
        print("[Embeddings] Nvidia API key detected. Using FakeEmbeddings (size 1536) for offline vector database testing.")
        return FakeEmbeddings(size=1536)

    try:
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
    except Exception as e:
        print(f"[Embeddings] OpenAI connection failed: {e}. Falling back to FakeEmbeddings.")
        return FakeEmbeddings(size=1536)
