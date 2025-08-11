from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
documents = [
    "Paris is the capital of France.",
    "Berlin is the capital of Germany.",
    "Madrid is the capital of Spain.",
    "Ottawa is the capital of Canada."
]
model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = model.encode(documents)
print(" Document Embeddings Shape:", doc_embeddings.shape)
#print(" Embedding of doc 0:\n", doc_embeddings[0])
dimension = doc_embeddings.shape[1]  # should be 384
index = faiss.IndexFlatL2(dimension)
index.add(doc_embeddings)
query = "Paris is the capital of France."
query_vector = model.encode([query])
#print(" First vector in index:")
#print(np.array(index.reconstruct(0)))
#print("Query Vector:\n", query_vector[0])
top_k = 1
distances, indices = index.search(query_vector, top_k)
retrieved_doc = documents[indices[0][0]]
print(" Distance Score:", distances[0][0])
print(" Retrieved Document:", retrieved_doc)

