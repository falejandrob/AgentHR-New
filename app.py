"""
HAVAS Chatbot with LangChain - Enhanced Flask Application
Integrates vector search, conversation memory and intelligent processing
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar componentes de LangChain
from agents.hr_agent import hr_agent
from tools.vector_search import document_search
from memory.conversation_memory import memory_manager

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicialización de Flask
app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('public', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check LangChain components
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'langchain_agent': True,
                'vector_search': document_search.vectorstore is not None,
                'memory_manager': len(memory_manager.active_memories) >= 0,
                'azure_openai': bool(os.getenv('AZURE_OPENAI_ENDPOINT')),
                'embeddings': bool(os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT'))
            }
        }
        
        # Check for critical issues
        critical_issues = []
        if not os.getenv('AZURE_OPENAI_ENDPOINT'):
            critical_issues.append('AZURE_OPENAI_ENDPOINT missing')
        if not os.getenv('AZURE_OPENAI_KEY'):
            critical_issues.append('AZURE_OPENAI_KEY missing')
        
        if critical_issues:
            health_status['status'] = 'degraded'
            health_status['issues'] = critical_issues
        
        logger.info(f"✅ Health check: {health_status['status']}")
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat():
    """Main chat endpoint with LangChain"""
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        logger.info(f'📩 New message received: {message[:50]}...')
        logger.info(f'🆔 Session ID: {session_id}')
        
        # Process message with LangChain agent
        result = hr_agent.process_message(message, session_id)
        
        if 'error' in result:
            logger.error(f'❌ Error processing message: {result["error"]}')
            return jsonify(result), 500
        
        logger.info(f'✅ Response generated successfully')
        return jsonify(result)
        
    except Exception as error:
        logger.error(f'❌ Error in /api/chat: {str(error)}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/new-conversation', methods=['POST'])
def new_conversation():
    """Iniciar nueva conversación"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        
        hr_agent.start_new_conversation(session_id)
        
        return jsonify({
            'message': 'Nueva conversación iniciada',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'❌ Error iniciando nueva conversación: {e}')
        return jsonify({
            'error': 'Error iniciando nueva conversación',
            'details': str(e)
        }), 500

@app.route('/api/conversation-stats', methods=['GET'])
def conversation_stats():
    """Obtener estadísticas de conversación"""
    try:
        session_id = request.args.get('session_id', 'default')
        stats = hr_agent.get_conversation_stats(session_id)
        
        return jsonify({
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'❌ Error obteniendo estadísticas: {e}')
        return jsonify({
            'error': 'Error obteniendo estadísticas',
            'details': str(e)
        }), 500

@app.route('/api/rebuild-knowledge-base', methods=['POST'])
@limiter.limit("1 per hour")
def rebuild_knowledge_base():
    """Reconstruir la base de conocimientos vectorial"""
    try:
        logger.info('🔄 Iniciando reconstrucción de base de conocimientos...')
        
        success = hr_agent.rebuild_knowledge_base()
        
        if success:
            return jsonify({
                'message': 'Base de conocimientos reconstruida exitosamente',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': 'Error reconstruyendo la base de conocimientos'
            }), 500
            
    except Exception as e:
        logger.error(f'❌ Error reconstruyendo base de conocimientos: {e}')
        return jsonify({
            'error': 'Error interno',
            'details': str(e)
        }), 500

@app.route('/api/debug/sessions', methods=['GET'])
def debug_sessions():
    """Debug: Información de todas las sesiones activas"""
    try:
        sessions = memory_manager.get_all_sessions()
        return jsonify({
            'active_sessions': len(sessions),
            'sessions': sessions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'❌ Error obteniendo debug de sesiones: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/vector-search', methods=['POST'])
def debug_vector_search():
    """Debug: Probar búsqueda vectorial directamente"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        k = data.get('k', 3)
        
        if not query:
            return jsonify({'error': 'Query requerido'}), 400
        
        results = document_search.search(query, k)
        context = document_search.get_context(results)
        
        return jsonify({
            'query': query,
            'results_count': len(results),
            'results': results,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'❌ Error en debug vector search: {e}')
        return jsonify({'error': str(e)}), 500

def validate_configuration():
    """Validate configuration before starting"""
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_API_VERSION'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ Configuration validated successfully")
    return True

def initialize_components():
    """Initialize LangChain components"""
    try:
        # Try to load or create vectorstore
        logger.info("🔄 Initializing vector search...")
        success = document_search.load_vectorstore()
        if not success:
            logger.warning("⚠️ Could not initialize vectorstore")
        else:
            logger.info("✅ Vector search initialized")
        
        logger.info("✅ LangChain components initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing components: {e}")
        return False

if __name__ == '__main__':
    # Validate configuration
    if not validate_configuration():
        exit(1)
    
    # Initialize components
    if not initialize_components():
        logger.warning("⚠️ Some components did not initialize correctly")
    
    # Server configuration
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f'🚀 HAVAS Chatbot with LangChain running on http://localhost:{port}')
    logger.info(f'📊 Environment: {"development" if debug else "production"}')
    logger.info(f'🔧 Available endpoints:')
    logger.info(f'   - Chat: http://localhost:{port}/api/chat')
    logger.info(f'   - Health: http://localhost:{port}/api/health')
    logger.info(f'   - Debug: http://localhost:{port}/api/debug/sessions')
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
