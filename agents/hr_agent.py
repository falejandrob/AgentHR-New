"""
Main HR agent enhanced with LangChain
Integrates vector search, memory and intelligent processing
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage

from config.langchain_config import (
    get_azure_llm, 
    get_translation_llm, 
    SYSTEM_PROMPT,
    LANGUAGE_DETECTION_PROMPT,
    TRANSLATION_PROMPT
)
from tools.vector_search import document_search
try:
    from tools.azure_search import azure_search
except Exception:
    azure_search = None  # Fallback si no está disponible
from memory.conversation_memory import memory_manager

logger = logging.getLogger(__name__)

class HRAgent:
    def __init__(self):
        import os
        self.main_llm = get_azure_llm()
        self.translation_disabled = os.getenv("DISABLE_TRANSLATION", "false").lower() == "true" or \
            os.getenv("AZURE_SEARCH_VECTOR", "false").lower() == "true"
        # Only initialize translation LLM if it's enabled
        if not self.translation_disabled:
            self.translation_llm = get_translation_llm()
        else:
            self.translation_llm = None
        # Main chains
        self.qa_chain = self._create_qa_chain()
        if not self.translation_disabled:
            self.language_detection_chain = self._create_language_detection_chain()
            self.translation_chain = self._create_translation_chain()
        else:
            self.language_detection_chain = None
            self.translation_chain = None
        logger.info("🤖 HRAgent initialized with LangChain (translation_disabled=%s)" % self.translation_disabled)
    
    def _create_qa_chain(self) -> LLMChain:
        """
        Create main chain for Q&A responses
        """
        prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=SYSTEM_PROMPT
        )
        
        return LLMChain(
            llm=self.main_llm,
            prompt=prompt,
            verbose=False
        )
    
    def _create_language_detection_chain(self) -> LLMChain:
        """
        Create chain for language detection
        """
        prompt = PromptTemplate(
            input_variables=["text"],
            template=LANGUAGE_DETECTION_PROMPT
        )
        
        return LLMChain(
            llm=self.translation_llm,
            prompt=prompt,
            verbose=False
        )
    
    def _create_translation_chain(self) -> LLMChain:
        """
        Create chain for translation
        """
        prompt = PromptTemplate(
            input_variables=["text", "source_lang", "target_lang"],
            template=TRANSLATION_PROMPT
        )
        
        return LLMChain(
            llm=self.translation_llm,
            prompt=prompt,
            verbose=False
        )
    
    def detect_language(self, message: str) -> str:
        """
        Detect message language
        """
        try:
            if self.translation_disabled or not self.language_detection_chain:
                return 'unknown'
            result = self.language_detection_chain.invoke({"text": message})
            detected_lang = result["text"].strip().lower()
            logger.info(f"🌐 Language detected: {detected_lang}")
            return detected_lang
        except Exception as e:
            logger.error(f"❌ Error detecting language: {e}")
            return 'fr'  # Default to French
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Translate text using LangChain
        """
        try:
            if self.translation_disabled or not self.translation_chain:
                return text
            result = self.translation_chain.invoke({
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            })
            return result["text"].strip()
        except Exception as e:
            logger.error(f"❌ Error translating text: {e}")
            return text  # Return original text if fails
    
    def process_message(self, message: str, session_id: str = "default") -> Dict:
        """
        Process complete message with enhanced pipeline
        """
        start_time = datetime.now()
        
        try:
            if self.translation_disabled:
                detected_language = 'original'
                search_query = message  # Process directly
                logger.info("📩 Processing message without translation (vector/disabled)")
            else:
                detected_language = self.detect_language(message)
                logger.info(f"📩 Processing message in {detected_language}")
                # Use original message for search - no need to translate for search
                search_query = message
            
            # 3. Document retrieval (Azure AI Search preferred)
            use_azure = bool(azure_search and getattr(azure_search, 'enabled', False))
            search_results = []
            context = ""
            if use_azure:
                search_results = azure_search.search(search_query, k=5)
                context = azure_search.get_context(search_results, max_length=3000)
                logger.info(f"📦 Context source: Azure AI Search ({len(search_results)} docs)")
            # Fallback if Azure returned no results
            if not search_results and not (use_azure and getattr(azure_search, 'only_mode', False)):
                search_results = document_search.search(search_query, k=5)
                context = document_search.get_context(search_results, max_length=3000)
                logger.info(f"📦 Context source: Local vectorstore ({len(search_results)} docs)")
            logger.info(f"🔍 Found {len(search_results)} relevant documents")
            
            # 4. Get conversation history
            chat_history = memory_manager.get_conversation_history(session_id)
            
            # 5. Generate response using Q&A chain - let the model respond in the original language
            final_response = self.qa_chain.invoke({
                "context": context or "No specific information found in the knowledge base.",
                "chat_history": chat_history,
                "question": message  # Use original message so the model responds in the same language
            })["text"]
            
            
            # 6. Save in memory
            memory_manager.add_message(session_id, message, final_response)
            
            # Processing metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'response': final_response,
                'documentsFound': len(search_results),
                'hasContext': bool(context),
                'language': {
                    'detected': None if self.translation_disabled else detected_language,
                    'processed_directly': True,  # No translation needed
                    'original_message': message
                },
                'session_info': memory_manager.get_session_info(session_id),
                'processing_time': round(processing_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Message processed successfully in {processing_time:.2f}s - Response in {detected_language}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {
                'error': 'Internal server error',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def start_new_conversation(self, session_id: str = "default"):
        """
        Start new conversation by clearing memory
        """
        memory_manager.clear_session(session_id)
        logger.info(f"🔄 New conversation started for session: {session_id}")
    
    def get_conversation_stats(self, session_id: str = "default") -> Dict:
        """
        Get conversation statistics
        """
        return memory_manager.get_session_info(session_id)
    
    def rebuild_knowledge_base(self) -> bool:
        """
        Rebuild knowledge base
        """
        logger.info("🔄 Rebuilding knowledge base...")
        return document_search.rebuild_index()

# Global agent instance
hr_agent = HRAgent()
