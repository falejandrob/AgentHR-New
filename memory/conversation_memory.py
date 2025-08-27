"""
Conversation memory system with LangChain
Maintains intelligent conversation context
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage
from config.langchain_config import get_azure_llm

logger = logging.getLogger(__name__)

class ConversationMemoryManager:
    def __init__(self):
        self.llm = get_azure_llm()
        self.active_memories: Dict[str, ConversationSummaryBufferMemory] = {}
        self.session_timestamps: Dict[str, datetime] = {}
        self.max_sessions = 100
        self.session_timeout = timedelta(hours=24)
    
    def get_memory(self, session_id: str) -> ConversationSummaryBufferMemory:
        """
        Get or create memory for a specific session
        """
        # Clean expired sessions
        self._cleanup_expired_sessions()
        
        if session_id not in self.active_memories:
            self.active_memories[session_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000,
                return_messages=True,
                memory_key="chat_history"
            )
            logger.info(f"📝 New memory created for session: {session_id}")
        
        # Update timestamp
        self.session_timestamps[session_id] = datetime.now()
        return self.active_memories[session_id]
    
    def add_message(self, session_id: str, human_message: str, ai_message: str):
        """
        Add message exchange to memory
        """
        memory = self.get_memory(session_id)
        memory.save_context(
            {"input": human_message}, 
            {"output": ai_message}
        )
        logger.debug(f"💭 Message added to session memory: {session_id}")
    
    def get_conversation_history(self, session_id: str) -> str:
        """
        Get formatted conversation history
        """
        if session_id not in self.active_memories:
            return ""
        
        memory = self.active_memories[session_id]
        history = memory.load_memory_variables({})
        
        # Formatear mensajes para el prompt
        if "chat_history" in history and history["chat_history"]:
            messages = []
            for message in history["chat_history"]:
                if hasattr(message, 'content'):
                    role = "Usuario" if message.__class__.__name__ == "HumanMessage" else "Asistente"
                    messages.append(f"{role}: {message.content}")
            return "\n".join(messages[-10:])  # Last 10 exchanges
        
        return ""
    
    def clear_session(self, session_id: str):
        """
        Clear memory for a specific session
        """
        if session_id in self.active_memories:
            del self.active_memories[session_id]
        if session_id in self.session_timestamps:
            del self.session_timestamps[session_id]
        logger.info(f"🧹 Memory cleared for session: {session_id}")
    
    def _cleanup_expired_sessions(self):
        """
        Clean expired sessions automatically
        """
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, timestamp in self.session_timestamps.items():
            if current_time - timestamp > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.clear_session(session_id)
            logger.info(f"🕐 Sesión expirada limpiada: {session_id}")
        
        # Limpiar sesiones excedentes (mantener solo las más recientes)
        if len(self.active_memories) > self.max_sessions:
            sorted_sessions = sorted(
                self.session_timestamps.items(),
                key=lambda x: x[1]
            )
            sessions_to_remove = len(sorted_sessions) - self.max_sessions
            
            for session_id, _ in sorted_sessions[:sessions_to_remove]:
                self.clear_session(session_id)
                logger.info(f"📊 Session removed due to limit: {session_id}")
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        Get information about a session
        """
        if session_id not in self.active_memories:
            return {"exists": False}
        
        memory = self.active_memories[session_id]
        history = memory.load_memory_variables({})
        
        return {
            "exists": True,
            "last_activity": self.session_timestamps[session_id],
            "message_count": len(history.get("chat_history", [])),
            "has_summary": bool(memory.moving_summary_buffer)
        }
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get information about all active sessions
        """
        sessions = []
        for session_id in self.active_memories.keys():
            info = self.get_session_info(session_id)
            info["session_id"] = session_id
            sessions.append(info)
        
        return sorted(sessions, key=lambda x: x["last_activity"], reverse=True)

# Global instance for memory management
memory_manager = ConversationMemoryManager()
