"""Azure AI Search integration as retrieval source.

Provides direct HTTP search against Azure AI Search and returns
results in the same format used by local vector search
to allow transparent fallback.

Strategy:
 - Uses environment variables AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX
 - Supports optional semantic configuration AZURE_SEARCH_SEMANTIC_CONFIG
 - Returns list of dicts with keys: content, title, score, metadata, source, type, category
 - Dynamically selects content field from various candidates.
"""
from __future__ import annotations
import os
import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

CONTENT_FIELD_CANDIDATES = [
    "content", "content_text", "chunk", "text", "body", "page_content"
]
TITLE_FIELD_CANDIDATES = [
    "title", "document_title", "name", "heading"
]
TYPE_FIELD_CANDIDATES = [
    "type", "category", "doc_type"
]


class AzureSearchClient:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index = os.getenv("AZURE_SEARCH_INDEX")
        self.semantic_config = os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG")
        self.api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2024-07-01")
        self.only_mode = os.getenv("AZURE_SEARCH_ONLY", "false").lower() == "true"
        self.vector_mode = os.getenv("AZURE_SEARCH_VECTOR", "false").lower() == "true"
        self.vector_field = os.getenv("AZURE_SEARCH_VECTOR_FIELD", "content_embedding")
        self.vector_k = int(os.getenv("AZURE_SEARCH_VECTOR_K", "15"))
        self.enabled = all([self.endpoint, self.key, self.index])
        self.embeddings = None
        if self.enabled:
            mode = "ONLY" if self.only_mode else "mixed"
            vec = "vector" if self.vector_mode else "text"
            logger.info(f"🔗 Azure AI Search enabled (mode={mode}, retrieval={vec})")
            if self.vector_mode:
                try:
                    from config.langchain_config import get_azure_embeddings
                    self.embeddings = get_azure_embeddings()
                except Exception as e:
                    logger.error(f"❌ Could not initialize embeddings for vector search: {e}")
                    self.vector_mode = False
        else:
            logger.info("ℹ️ Azure AI Search not fully configured; local vectorstore will be used")

    def _choose_field(self, doc: Dict[str, Any], candidates: List[str]) -> str:
        for field in candidates:
            if field in doc and isinstance(doc[field], str) and doc[field].strip():
                return doc[field]
        return ""

    def _embed_query(self, query: str) -> Optional[List[float]]:
        try:
            if not self.embeddings:
                return None
            vec = self.embeddings.embed_query(query)
            # Asegurar tipo list de floats (serializable)
            return list(map(float, vec))
        except Exception as e:
            logger.error(f"❌ Error generating query embedding: {e}")
            return None

    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for documents using vector or text search"""
        if not self.enabled:
            return []
        
        # Use environment variable or default
        if k is None:
            k = int(os.getenv("SEARCH_RESULTS_COUNT", "15"))
            
        search_url = f"{self.endpoint}/indexes/{self.index}/docs/search?api-version={self.api_version}"
        payload: Dict[str, Any]
        if self.vector_mode:
            embedding = self._embed_query(query)
            if not embedding:
                logger.warning("⚠️ Fallback to text search because embedding not available")
                self.vector_mode = False
            else:
                payload = {
                    "vectorQueries": [
                        {
                            "kind": "vector",
                            "vector": embedding,
                            "fields": self.vector_field,
                            "k": k if k else self.vector_k
                        }
                    ],
                    "top": k,
                    "select": "*"
                }
                # Hybrid optional: if AZURE_SEARCH_HYBRID=true is defined we add text
                if os.getenv("AZURE_SEARCH_HYBRID", "false").lower() == "true":
                    payload["search"] = query
                    payload["searchMode"] = "any"
                    payload["queryType"] = "simple"
                # Note: semantic and vector together not always compatible; semantic is omitted here.
        if not self.vector_mode:
            payload = {
                "search": query,
                "top": k,
                "select": "*",
                "searchMode": "any",
                "queryType": "simple"
            }
            if self.semantic_config:
                payload.update({
                    "queryType": "semantic",
                    "semanticConfiguration": self.semantic_config,
                    "captions": "extractive",
                    "answers": "extractive"
                })
        headers = {
            "Content-Type": "application/json",
            "api-key": self.key
        }
        try:
            resp = requests.post(search_url, json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                logger.error(f"❌ Azure Search status {resp.status_code}: {resp.text[:200]}")
                return []
            raw_results = resp.json().get("value", [])
            results: List[Dict[str, Any]] = []
            for r in raw_results:
                content = self._choose_field(r, CONTENT_FIELD_CANDIDATES)
                title = self._choose_field(r, TITLE_FIELD_CANDIDATES)
                doc_type = self._choose_field(r, TYPE_FIELD_CANDIDATES)
                score = r.get("@search.score") or r.get("searchScore") or 0.0
                results.append({
                    "content": content,
                    "title": title,
                    "score": float(score) if isinstance(score, (int, float)) else 0.0,
                    "metadata": r,
                    "source": r.get("source") or r.get("id") or self.index,
                    "type": doc_type,
                    "category": r.get("category", "")
                })
            logger.info(f"🔍 Azure Search returned {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"❌ Error querying Azure Search: {e}")
            return []

    def get_context(self, results: List[Dict[str, Any]], max_length: int = 3000) -> str:
        if not results:
            return ""
        parts = []
        length = 0
        for r in results:
            content = (r.get("content") or "").strip()
            title = r.get("title") or ""
            if not content:
                continue
            chunk = f"**{title}**\n{content}\n" if title else f"{content}\n"
            if length + len(chunk) <= max_length:
                parts.append(chunk)
                length += len(chunk)
            else:
                remaining = max_length - length
                if remaining > 100:
                    parts.append(chunk[:remaining-3] + "...")
                break
        return "\n".join(parts)


# Instancia global
azure_search = AzureSearchClient()
