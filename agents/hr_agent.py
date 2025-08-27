"""
Agente HR Simplificado para o3-mini
Eliminando dependencias innecesarias y simplificando la arquitectura
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# Imports optimizados
from tools.azure_search import AzureSearchClient
from memory.simple_memory import SimpleMemoryManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRAgentSimple:
    """
    Agente HR simplificado optimizado para o3-mini
    """
    
    def __init__(self):
        logger.info("🚀 Inicializando HRAgent Simplificado...")
        
        # Inicializar búsqueda de documentos
        self.document_search = AzureSearchClient()
        
        # Inicializar memoria simple
        self.memory_manager = SimpleMemoryManager()
        
        # Configurar LLM simplificado
        self.llm = self._setup_llm()
        
        # Sistema de prompts simplificado
        self.system_prompt = """Eres un asistente de recursos humanos especializado en HAVAS.
Responde SIEMPRE en el idioma en que te pregunten.
Si te preguntan en español, responde en español.
Si te preguntan en francés, responde en francés.

Usa la información proporcionada para dar respuestas precisas y útiles.
Si no tienes información suficiente, dilo claramente."""

        logger.info("✅ HRAgent Simplificado inicializado correctamente")
    
    def _setup_llm(self):
        """Configurar LLM simplificado para o3-mini"""
        try:
            from config.langchain_config import get_azure_llm
            llm = get_azure_llm()
            logger.info("✅ LLM configurado correctamente")
            return llm
        except Exception as e:
            logger.error(f"❌ Error configurando LLM: {e}")
            raise
    
    def process_message(self, message: str, session_id: str = "default") -> Dict:
        """
        Procesar mensaje de forma simplificada
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"📩 Procesando mensaje: {message[:50]}...")
            
            # 1. Buscar documentos relevantes
            search_results = self.document_search.search(message)
            logger.info(f"🔍 Encontrados {len(search_results)} documentos relevantes")
            
            # 2. Preparar contexto
            context = self._prepare_context(search_results)
            
            # 3. Obtener historial de conversación
            conversation_history = self.memory_manager.get_conversation_history(session_id)
            
            # 4. Crear prompt simplificado
            messages = []
            messages.append(SystemMessage(content=self.system_prompt))
            
            # Agregar historial si existe
            for hist_msg in conversation_history[-4:]:  # Solo últimos 4 mensajes
                messages.append(HumanMessage(content=f"Usuario: {hist_msg['human']}"))
                messages.append(SystemMessage(content=f"Asistente: {hist_msg['ai']}"))
            
            # Agregar contexto y pregunta actual
            if context:
                context_msg = f"Información relevante:\n{context}\n\nPregunta del usuario: {message}"
            else:
                context_msg = f"Pregunta del usuario: {message}"
            
            messages.append(HumanMessage(content=context_msg))
            
            # 5. Generar respuesta
            response = self._generate_response(messages)
            
            # 6. Guardar en memoria
            self.memory_manager.add_message(session_id, message, response)
            
            # 7. Preparar resultado
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'response': response,
                'documentsFound': len(search_results),
                'hasContext': bool(context),
                'session_info': self.memory_manager.get_session_info(session_id),
                'processing_time': round(processing_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Mensaje procesado exitosamente en {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return {
                'error': 'Error interno del servidor',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """Preparar contexto de documentos encontrados"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, doc in enumerate(search_results[:3], 1):  # Solo primeros 3
            content = doc.get('content', '').strip()
            if content:
                context_parts.append(f"Documento {i}:\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _generate_response(self, messages: List) -> str:
        """
        Generar respuesta con manejo robusto de errores para o3-mini
        """
        try:
            # Intentar generar respuesta
            result = self.llm.invoke(messages)
            
            # Manejo robusto de diferentes tipos de respuesta
            if result is None:
                logger.warning("⚠️ El modelo devolvió None")
                return "Lo siento, no pude generar una respuesta en este momento. Por favor intenta de nuevo."
            
            # Si es string directamente
            if isinstance(result, str):
                response = result.strip()
                if response:
                    return response
                else:
                    return "No pude generar una respuesta adecuada. Por favor reformula tu pregunta."
            
            # Si tiene atributo content
            if hasattr(result, 'content'):
                response = result.content
                if isinstance(response, str) and response.strip():
                    return response.strip()
                else:
                    return "No pude generar una respuesta adecuada. Por favor reformula tu pregunta."
            
            # Si es dict con 'content'
            if isinstance(result, dict) and 'content' in result:
                response = result['content']
                if isinstance(response, str) and response.strip():
                    return response.strip()
                else:
                    return "No pude generar una respuesta adecuada. Por favor reformula tu pregunta."
            
            # Fallback
            logger.warning(f"⚠️ Formato de respuesta inesperado: {type(result)}")
            return "Lo siento, hubo un problema técnico. Por favor intenta de nuevo."
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return "Lo siento, encontré un problema técnico. Por favor intenta de nuevo en un momento."
    
    def start_new_conversation(self, session_id: str = "default"):
        """Iniciar nueva conversación"""
        self.memory_manager.clear_session(session_id)
        logger.info(f"🔄 Nueva conversación iniciada para sesión: {session_id}")
    
    def get_conversation_stats(self, session_id: str = "default") -> Dict:
        """Obtener estadísticas de conversación"""
        return self.memory_manager.get_session_info(session_id)


# Instancia global del agente
hr_agent_simple = HRAgentSimple()
