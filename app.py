"""
HAVAS Chatbot - Aplicación Flask Simplificada
Optimizada para o3-mini reasoning model
"""
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Imports locales
from config.langchain_config import validate_config
from agents.hr_agent import hr_agent_simple

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar Flask
app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour", "10 per minute"]
)

@app.route('/')
def index():
    """Servir página principal"""
    return app.send_static_file('index.html')

@app.route('/api/health')
@limiter.exempt
def health():
    """Health check endpoint"""
    try:
        logger.info("✅ Health check: healthy")
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0-simplified'
        })
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat():
    """Endpoint principal de chat"""
    try:
        # Obtener datos de la petición
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensaje requerido'}), 400
            
        message = data.get('message', '').strip()
        session_id = data.get('sessionId', 'default')
        
        
        if not message:
            return jsonify({'error': 'Mensaje no puede estar vacío'}), 400
            
        logger.info(f"📩 Nuevo mensaje recibido: {message[:50]}...")
        logger.info(f"🆔 Session ID: {session_id}")
        
        
        # Procesar mensaje con el agente simplificado y modelo especificado
        result = hr_agent_simple.process_message(message, session_id)
        
        # Verificar si hubo error
        if 'error' in result:
            logger.error(f"❌ Error procesando mensaje: {result.get('details', 'Unknown error')}")
            return jsonify({
                'error': 'Error interno del servidor',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        logger.info("✅ Mensaje procesado exitosamente")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint de chat: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/new-conversation', methods=['POST'])
@limiter.limit("10 per minute")
def new_conversation():
    """Iniciar nueva conversación"""
    try:
        data = request.get_json() or {}
        session_id = data.get('sessionId', 'default')
        
        hr_agent_simple.start_new_conversation(session_id)
        
        return jsonify({
            'success': True,
            'message': 'Nueva conversación iniciada',
            'sessionId': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error iniciando nueva conversación: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/debug/sessions')
@limiter.exempt
def debug_sessions():
    """Debug endpoint para ver sesiones activas"""
    try:
        sessions_info = {}
        
        # Obtener info de todas las sesiones (simplificado)
        for session_id in ['default']:  # Por ahora solo default
            try:
                info = hr_agent_simple.get_conversation_stats(session_id)
                sessions_info[session_id] = info
            except:
                sessions_info[session_id] = {'status': 'inactive'}
        
        return jsonify({
            'active_sessions': sessions_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error en debug endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Manejar rate limit exceeded"""
    return jsonify({
        'error': 'Demasiadas peticiones. Por favor espera antes de intentar de nuevo.',
        'retry_after': str(e.retry_after) if hasattr(e, 'retry_after') else '60'
    }), 429

@app.errorhandler(500)
def internal_error_handler(e):
    """Manejar errores internos"""
    logger.error(f"❌ Error interno: {e}")
    return jsonify({
        'error': 'Error interno del servidor',
        'timestamp': datetime.now().isoformat()
    }), 500

def initialize_app():
    """Inicializar aplicación"""
    try:
        # Validar configuración
        if not validate_config():
            raise ValueError("Configuración de Azure OpenAI inválida")
        
        logger.info("✅ Configuración validada exitosamente")
        logger.info("✅ Agente HR Simplificado inicializado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando aplicación: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando HAVAS Chatbot Simplificado...")
    
    if not initialize_app():
        print("❌ Error en la inicialización. Revisa la configuración.")
        exit(1)
    
    # Configuración del servidor
    port = int(os.getenv('PORT', 3000))
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 HAVAS Chatbot Simplificado ejecutándose en http://localhost:{port}")
    logger.info(f"📊 Modo debug: {debug_mode}")
    logger.info("🔧 Endpoints disponibles:")
    logger.info(f"   - Chat: http://localhost:{port}/api/chat")
    logger.info(f"   - Health: http://localhost:{port}/api/health")
    logger.info(f"   - Debug: http://localhost:{port}/api/debug/sessions")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
