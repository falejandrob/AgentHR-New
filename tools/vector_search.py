"""
Enhanced document search system with LangChain and FAISS
Semantic vector search for better accuracy
"""
import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pickle

from langchain.text_splitter import RecursiveCharacterTextSplitter
"""Vector search helper with graceful fallback.

Recent changes:
 - Use import from langchain_community to avoid deprecation warning.
 - Robust vectorstore loading detecting 'allow_dangerous_deserialization' support.
 - Clearer log messages to distinguish benign warnings from critical errors.
"""

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from config.langchain_config import get_azure_embeddings

logger = logging.getLogger(__name__)

class VectorDocumentSearch:
    def __init__(self, documents_path: str = "data/documents", vector_store_path: str = "data/vectorstore"):
        self.documents_path = Path(documents_path)
        self.vector_store_path = Path(vector_store_path)
        
        # Usar embeddings básicos por ahora hasta configurar Azure correctamente
        try:
            self.embeddings = get_azure_embeddings()
        except Exception as e:
            logger.warning(f"⚠️ Error con Azure embeddings: {e}")
            # Fallback a sistema de búsqueda por palabras clave
            self.embeddings = None
            self.use_keyword_search = True
            logger.info("🔄 Usando búsqueda por palabras clave como fallback")
        else:
            self.use_keyword_search = False
            
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def load_documents(self) -> List[Document]:
        """
        Cargar documentos desde archivos JSON
        """
        documents = []
        
        if not self.documents_path.exists():
            logger.warning(f"📁 Directorio de documentos no encontrado: {self.documents_path}")
            return documents
            
        for file_path in self.documents_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    for item in data:
                        doc = Document(
                            page_content=item.get('content', ''),
                            metadata={
                                'source': str(file_path),
                                'title': item.get('title', ''),
                                'type': item.get('type', ''),
                                'category': item.get('category', '')
                            }
                        )
                        documents.append(doc)
                else:
                    doc = Document(
                        page_content=data.get('content', ''),
                        metadata={
                            'source': str(file_path),
                            'title': data.get('title', ''),
                            'type': data.get('type', ''),
                            'category': data.get('category', '')
                        }
                    )
                    documents.append(doc)
                    
            except Exception as e:
                logger.error(f"❌ Error cargando {file_path}: {e}")
                
        logger.info(f"📚 Cargados {len(documents)} documentos")
        return documents
    
    def create_vectorstore(self) -> bool:
        """
        Crear el almacén vectorial desde los documentos
        """
        if self.use_keyword_search:
            logger.info("✅ Usando búsqueda por palabras clave - no se requiere vectorstore")
            return True
            
        try:
            documents = self.load_documents()
            if not documents:
                logger.error("❌ No hay documentos para procesar")
                return False
                
            # Dividir documentos en chunks
            texts = self.text_splitter.split_documents(documents)
            logger.info(f"📝 Documentos divididos en {len(texts)} chunks")
            
            # Crear vectorstore
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
            
            # Guardar vectorstore
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(self.vector_store_path))
            
            logger.info("✅ Vectorstore creado y guardado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando vectorstore: {e}")
            # Cambiar a búsqueda por palabras clave
            self.use_keyword_search = True
            self.embeddings = None
            logger.info("🔄 Cambiando a búsqueda por palabras clave")
            return True
    
    def load_vectorstore(self) -> bool:
        """
        Cargar el almacén vectorial existente
        """
        if self.use_keyword_search:
            logger.info("✅ Usando búsqueda por palabras clave - no se requiere cargar vectorstore")
            return True
            
        try:
            if not self.vector_store_path.exists():
                logger.warning("📁 Vectorstore no encontrado, creando nuevo...")
                return self.create_vectorstore()
                
            # Intentar carga detectando si la firma soporta el parámetro
            load_kwargs = {}
            try:
                import inspect
                params = inspect.signature(FAISS.load_local).parameters
                if 'allow_dangerous_deserialization' in params:
                    load_kwargs['allow_dangerous_deserialization'] = True
            except Exception:
                pass  # Si falla la inspección, continuamos sin el parámetro

            try:
                self.vectorstore = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    **load_kwargs
                )
            except TypeError as te:
                # Reintentar sin kwargs en caso de versión antigua
                logger.warning(f"⚠️ Reintentando carga de vectorstore sin parámetros extra: {te}")
                self.vectorstore = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings
                )

            logger.info("✅ Vectorstore cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando vectorstore: {e}")
            logger.info("🔄 Attempting to recreate vectorstore...")
            return self.create_vectorstore()
    
    def search(self, query: str, k: int = None) -> List[Dict]:
        """
        Search similar documents using vector search or keyword search
        """
        # Use environment variable or default
        if k is None:
            k = int(os.getenv("SEARCH_RESULTS_COUNT", "15"))
            
        try:
            if self.use_keyword_search:
                return self._keyword_search(query, k)
            
            if not self.vectorstore:
                if not self.load_vectorstore():
                    return self._keyword_search(query, k)
            
            # Similarity search
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs:
                result = {
                    'content': doc.page_content,
                    'score': float(score),
                    'metadata': doc.metadata,
                    'title': doc.metadata.get('title', ''),
                    'source': doc.metadata.get('source', ''),
                    'type': doc.metadata.get('type', ''),
                    'category': doc.metadata.get('category', '')
                }
                results.append(result)
                
            logger.info(f"🔍 Encontrados {len(results)} documentos relevantes")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda vectorial: {e}")
            return self._keyword_search(query, k)
    
    def _keyword_search(self, query: str, k: int = 15) -> List[Dict]:
        """
        Búsqueda por palabras clave como fallback
        """
        try:
            documents = self.load_documents()
            if not documents:
                return []
            
            query_words = set(query.lower().split())
            scored_docs = []
            
            for doc in documents:
                content_words = set(doc.page_content.lower().split())
                title_words = set(doc.metadata.get('title', '').lower().split())
                
                # Calcular puntuación basada en palabras coincidentes
                content_matches = len(query_words.intersection(content_words))
                title_matches = len(query_words.intersection(title_words)) * 2  # Peso mayor para título
                
                score = content_matches + title_matches
                
                if score > 0:
                    result = {
                        'content': doc.page_content,
                        'score': score,
                        'metadata': doc.metadata,
                        'title': doc.metadata.get('title', ''),
                        'source': doc.metadata.get('source', ''),
                        'type': doc.metadata.get('type', ''),
                        'category': doc.metadata.get('category', '')
                    }
                    scored_docs.append(result)
            
            # Ordenar por puntuación descendente
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🔍 Búsqueda por palabras clave: {len(scored_docs[:k])} resultados")
            return scored_docs[:k]
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda por palabras clave: {e}")
            return []
    
    def get_context(self, results: List[Dict], max_length: int = 3000) -> str:
        """
        Extraer contexto optimizado de los resultados
        """
        if not results:
            return ""
            
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content'].strip()
            title = result.get('title', '')
            
            # Formatear el chunk con título si está disponible
            if title:
                chunk = f"**{title}**\n{content}\n"
            else:
                chunk = f"{content}\n"
                
            # Verificar si podemos agregar este chunk
            if current_length + len(chunk) <= max_length:
                context_parts.append(chunk)
                current_length += len(chunk)
            else:
                # Agregar lo que podamos del chunk actual
                remaining = max_length - current_length
                if remaining > 100:  # Solo si queda espacio significativo
                    truncated = chunk[:remaining-3] + "..."
                    context_parts.append(truncated)
                break
        
        return "\n".join(context_parts)
    
    def rebuild_index(self) -> bool:
        """
        Reconstruir completamente el índice vectorial
        """
        logger.info("🔄 Reconstruyendo índice vectorial...")
        
        # Eliminar vectorstore existente
        if self.vector_store_path.exists():
            import shutil
            shutil.rmtree(self.vector_store_path)
            
        return self.create_vectorstore()

# Instancia global para reutilización
document_search = VectorDocumentSearch()
