"""
Gestor de memoria simplificado sin dependencias de LangChain
"""
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SimpleMemoryManager:
    """
    Gestor de memoria simplificado sin LangChain
    """
    
    def __init__(self):
        self.sessions: Dict[str, List[Dict]] = {}
        logger.info("✅ SimpleMemoryManager inicializado")
    
    def add_message(self, session_id: str, human_message: str, ai_response: str):
        """Agregar mensaje a la sesión"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        message_entry = {
            'human': human_message,
            'ai': ai_response,
            'timestamp': datetime.now().isoformat()
        }
        
        self.sessions[session_id].append(message_entry)
        
        # Mantener solo los últimos 10 mensajes para evitar sobrecarga
        if len(self.sessions[session_id]) > 10:
            self.sessions[session_id] = self.sessions[session_id][-10:]
        
        logger.info(f"📝 Mensaje agregado a sesión {session_id}")
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Obtener historial de conversación"""
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str):
        """Limpiar sesión"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        logger.info(f"🗑️ Sesión {session_id} limpiada")
    
    def get_session_info(self, session_id: str) -> Dict:
        """Obtener información de la sesión"""
        history = self.get_conversation_history(session_id)
        return {
            'session_id': session_id,
            'message_count': len(history),
            'last_activity': history[-1]['timestamp'] if history else None,
            'created': history[0]['timestamp'] if history else None
        }
