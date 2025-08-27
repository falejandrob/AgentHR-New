"""
LangChain configuration for HAVAS chatbot
"""
import os
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.memory import ConversationSummaryBufferMemory
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_azure_llm():
    """
    Configure Azure OpenAI model for LangChain
    """
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')

    # Some models (e.g. o3-mini / reasoning) don't accept the temperature parameter.
    # LangChain wrapper always includes a default value if we don't specify it,
    # so we apply a fallback to a standard model if we detect that case.
    if deployment and deployment.lower() in {"o3-mini", "o4-mini", "o3"}:
        import logging
        logger = logging.getLogger(__name__)
        fallback = os.getenv('AZURE_OPENAI_FALLBACK_DEPLOYMENT', 'gpt-4.1-nano')
        logger.warning(
            f"⚠️ The deployment '{deployment}' is a reasoning model that rejects 'temperature'. "
            f"Applying fallback to '{fallback}'. Define AZURE_OPENAI_FALLBACK_DEPLOYMENT to change it."
        )
        deployment = fallback

    # We force empty model_kwargs to minimize parameters sent.
    # We use max_tokens (standard param) instead of max_completion_tokens to avoid warnings.
    llm = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment,
        max_tokens=1500,
        # NOTE: We don't pass temperature so it won't be sent (avoid error in some models)
        model_kwargs={},
    )

    try:
        import logging
        logging.getLogger(__name__).info(
            f"🧪 LLM initialized deployment={deployment} api_version={api_version} model_kwargs={getattr(llm, 'model_kwargs', {})}"
        )
    except Exception:
        pass

    return llm

def get_azure_embeddings():
    """
    Configure Azure OpenAI embeddings for vector search
    """
    return AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview'),
        azure_deployment=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small')
    )

def get_translation_llm():
    """
    Configure translation model for LangChain
    """
    # For translation we reuse AzureChatOpenAI wrapper. We remove model_name (deployment_name is enough)
    # and use max_tokens for consistency.
    return AzureChatOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_TRANSLATION_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_TRANSLATION_KEY'),
        api_version=os.getenv('AZURE_OPENAI_TRANSLATION_API_VERSION', '2025-01-01-preview'),
        deployment_name=os.getenv('AZURE_OPENAI_TRANSLATION_DEPLOYMENT'),
        max_tokens=1500,
        model_kwargs={},
    )

def create_conversation_memory(llm):
    """
    Create conversation memory with intelligent summary
    """
    return ConversationSummaryBufferMemory(
        llm=llm,
        max_token_limit=2000,
        return_messages=True,
        memory_key="chat_history"
    )

# Constants for prompts
SYSTEM_PROMPT = """You are the AI Assistant for HAVAS, a leading global communications company. 

Your role is to help employees with their HR, administrative and professional questions using the company's knowledge base.

IMPORTANT: Always respond in the same language as the user's question. If the user asks in Spanish, respond in Spanish. If they ask in French, respond in French. If they ask in English, respond in English.

Important guidelines:
1. Always respond professionally and kindly
2. Use the information provided in the context to give accurate answers
3. If you don't find information in the context, say so clearly
4. Adapt your tone according to the nature of the question (formal for procedures, more relaxed for general questions)
5. Always offer additional help if necessary
6. RESPOND IN THE SAME LANGUAGE AS THE USER'S QUESTION

Company context: {context}

Conversation history: {chat_history}

Question: {question}
"""

LANGUAGE_DETECTION_PROMPT = """You are a language detector. Respond ONLY with the ISO 639-1 language code (2 letters). 
Examples: 'es' for Spanish, 'en' for English, 'fr' for French, 'de' for German, 'it' for Italian, etc. 
Respond only with the code, nothing else.

Text to analyze: {text}
"""

TRANSLATION_PROMPT = """Translate the following text from {source_lang} to {target_lang}. 
Maintain the original tone and meaning. Do not add explanations or additional text.

Text to translate: {text}
"""
