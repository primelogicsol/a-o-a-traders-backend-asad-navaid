import numpy as np
from app.utils.embedding import get_embedding, get_schema_embeddings

def vectorized_column_mapping(uploaded_columns: list[str]) -> dict:

    schema_data = get_schema_embeddings()
    db_columns = np.array(list(schema_data.keys()))
    db_embeddings = np.array(list(schema_data.values()))
    uploaded_embeddings = get_embedding(uploaded_columns)
    
    uploaded_norm = uploaded_embeddings / np.linalg.norm(uploaded_embeddings, axis=1, keepdims=True)
    db_norm = db_embeddings / np.linalg.norm(db_embeddings, axis=1, keepdims=True)

    similarity_matrix = np.dot(uploaded_norm, db_norm.T)
    
    top5_indices = np.argpartition(-similarity_matrix, 5, axis=1)[:, :5]
    top5_scores = np.take_along_axis(similarity_matrix, top5_indices, axis=1)
    
    sort_order = np.argsort(-top5_scores, axis=1)
    sorted_indices = np.take_along_axis(top5_indices, sort_order, axis=1)
    sorted_scores = np.take_along_axis(top5_scores, sort_order, axis=1)
    
    results = {}
    for idx, col in enumerate(uploaded_columns):
        best_score = sorted_scores[idx, 0]
        suggestions = []
        
        if best_score < 0.5:
            suggestions = [{
                "column": db_columns[sorted_indices[idx, i]],
                "confidence": float(sorted_scores[idx, i])
            } for i in range(5)]
        
        results[col] = {
            "auto_mapped": db_columns[sorted_indices[idx, 0]] if best_score >= 0.5 else None,
            "suggestions": suggestions
        }
    
    return {
        "mapping_suggestions": results,
        "requires_attention": [col for col, data in results.items() if data["auto_mapped"] is None]
    }