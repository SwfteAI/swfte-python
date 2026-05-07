# RAG

Hybrid retrieval, reranking and BM25 vocabulary management — see [Swfte RAG](https://www.swfte.com/products/rag).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Browse what's available
print(client.rag.embedding_models())
print(client.rag.reranker_models())
print(client.rag.strategies())
print(client.rag.config())

# Hybrid search across one or more datasets
hits = client.rag.search(
    query="How long is the trial?",
    dataset_ids=["ds-faq", "ds-pricing"],  # replace with your own
    strategy="HYBRID",
    top_k=8,
)

# Rerank a candidate list with a cross-encoder
reranked = client.rag.rerank(
    query="How long is the trial?",
    documents=[{"id": h["id"], "text": h["text"]} for h in hits["results"]],
    model="cohere:rerank-english-v3",
    top_k=3,
)

# Build / inspect the BM25 vocabulary
client.rag.build_vocabulary(dataset_id="ds-faq")
print(client.rag.vocabulary_stats(dataset_id="ds-faq"))
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
