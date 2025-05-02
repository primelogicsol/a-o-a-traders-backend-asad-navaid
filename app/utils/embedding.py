from sentence_transformers import SentenceTransformer
import numpy as np
from app.models.product import Product

_model = None
_schema_embeddings = None

def init_embedding_model():
    global _model, _schema_embeddings
    if _model is None:
        _model = SentenceTransformer('all-mpnet-base-v2')
        db_columns = [column.name for column in Product.__table__.columns]
        _schema_embeddings = {col: _model.encode(col) for col in db_columns}

def get_embedding(text: str) -> np.ndarray:
    if _model is None:
        raise RuntimeError("Embedding model not initialized. Call init_embedding_model() first.")
    return _model.encode(text)

def get_schema_embeddings() -> dict:
    if _schema_embeddings is None:
        raise RuntimeError("Schema embeddings not initialized. Call init_embedding_model() first.")
    return _schema_embeddings

def compute_similarity(query: str, target_column: str) -> float:
    if _model is None or _schema_embeddings is None:
        raise RuntimeError("Model not initialized. Call init_embedding_model() first.")
        
    query_embed = get_embedding(query)
    target_embed = _schema_embeddings[target_column]
    
    return float(np.dot(query_embed, target_embed) / (
        np.linalg.norm(query_embed) * np.linalg.norm(target_embed)
    ))