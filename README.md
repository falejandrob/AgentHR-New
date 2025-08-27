# 🏢 HAVAS Chatbot - Versión Python

Asistente de IA inteligente para HAVAS, integrado con Azure OpenAI y Azure AI Search.

## 🚀 Características Principales

- **🤖 IA Conversacional**: Azure OpenAI (GPT-4.1-mini) para respuestas naturales
- **🔍 Búsqueda Vectorial**: Azure AI Search con embeddings (text-embedding-3-small)
- **🌍 Multiidioma**: Responde automáticamente en el idioma de la pregunta (español, francés, inglés)
- **⚡ Búsqueda Inteligente**: Vector search con fallback a búsqueda local (FAISS)
- **� Memoria Conversacional**: Mantiene contexto de conversaciones por sesión
- **🖥️ Interfaz Web**: Frontend moderno con soporte Markdown y tiempo real
- **🔒 Rate Limiting**: Protección contra abuso (30 requests/min)
- **📊 Diagnóstico**: Sistema completo de monitoreo y health checks

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.9+ 
- Azure OpenAI Service
- Azure AI Search Service

### 1. Clonar el repositorio
```bash
git clone [repository-url]
cd AgenteHR-v2
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crear archivo `.env` con:
```env
# Azure OpenAI Principal (para respuestas del chat)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Azure OpenAI para Traducciones (GPT-4.1 nano)
AZURE_OPENAI_TRANSLATION_ENDPOINT=https://your-translation-resource.cognitiveservices.azure.com/
AZURE_OPENAI_TRANSLATION_KEY=your-translation-api-key
AZURE_OPENAI_TRANSLATION_DEPLOYMENT=gpt-4.1-nano
AZURE_OPENAI_TRANSLATION_API_VERSION=2025-01-01-preview

# Azure AI Search (fuente primaria de conocimiento)
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name
# (Opcional) Config semántica y modo only
# AZURE_SEARCH_SEMANTIC_CONFIG=default
# AZURE_SEARCH_ONLY=true

# Configuración de la aplicación
PORT=3000
FLASK_ENV=development
```
### 4. Ejecutar la aplicación
```bash
python app_langchain.py
```

## � Estructura del Proyecto

```
AgenteHR-v2/
├── app_langchain.py          # 🚀 Aplicación principal Flask
├── .env                      # 🔧 Variables de entorno (configurar)
├── .env.example             # 📋 Plantilla de configuración
├── requirements.txt         # 📦 Dependencias Python
├── README.md               # 📖 Documentación
├── 
├── agents/                 # 🤖 Agentes IA
│   └── hr_agent.py        # Agente principal HR con LangChain
├── 
├── config/                 # ⚙️ Configuraciones
│   └── langchain_config.py # Configuración LangChain, prompts y LLM
├── 
├── tools/                  # 🔧 Herramientas de búsqueda
│   ├── azure_search.py    # Azure AI Search con vector search
│   ├── vector_search.py   # Búsqueda vectorial local (FAISS)
│   └── document_search.py # Utilidades de documentos
├── 
├── memory/                 # 💾 Sistema de memoria
│   └── conversation_memory.py # Memoria conversacional por sesión
├── 
├── public/                 # 🌐 Frontend web
│   ├── index.html         # Interfaz principal
│   ├── css/styles.css     # Estilos
│   └── js/chat.js         # JavaScript del chat
├── 
├── tests/                  # 🧪 Pruebas y diagnósticos
│   ├── test_chat.py       # Test de chat completo
│   ├── test_vector_search.py # Test búsqueda vectorial
│   └── diagnostic.py      # Diagnóstico de servicios
├── 
├── alternatives/           # 🗂️ Versiones alternativas
│   ├── app.py            # Versión legacy Flask
│   ├── main.py           # Punto entrada alternativo
│   └── start.py          # Script de inicio alternativo
└── 
└── data/                   # 📊 Datos y vectorstore local
    └── vectorstore/       # Base de datos vectorial FAISS
```

## 🚀 Uso

### Iniciar el Servidor
```bash
python app_langchain.py
```

La aplicación estará disponible en: `http://localhost:3000`

### Endpoints Disponibles

- **Chat**: `POST /api/chat` - Endpoint principal de conversación
- **Health**: `GET /api/health` - Health check del sistema
- **Debug**: `GET /api/debug/sessions` - Información de sesiones activas

# Diagnóstico
python diagnostic.py

# Script de inicio
python start.py
```

### Opción 3: Usando el batch file (Windows)
```cmd
# Simplifica el comando en Windows
python.bat main.py help
python.bat app.py
```

## 🌐 Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Página principal del chatbot |
| `/api/chat` | POST | Enviar mensaje al chatbot (con traducción automática) |
| `/api/health` | GET | Estado de salud del sistema |
| `/api/debug/index` | GET | Información del índice de búsqueda |
| `/api/debug/translate` | POST | Test de traducción manual |

### 🌐 Sistema de Traducción Automática

El chatbot ahora incluye **traducción automática inteligente**:

1. **Detección automática** del idioma del mensaje
2. **Traducción a francés** para el procesamiento interno
3. **Búsqueda en francés** en la base de conocimientos
4. **Respuesta en francés** generada por la IA
5. **Traducción de vuelta** al idioma original del usuario

#### Idiomas Soportados
- 🇪🇸 Español
- 🇬🇧 Inglés  
- 🇫🇷 Francés (idioma base)
- 🇩🇪 Alemán
- 🇮🇹 Italiano
- 🇵🇹 Portugués
- Y muchos más...

### Ejemplo de uso de API
```bash
# Mensaje en español
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué servicios ofrece HAVAS?"}'

# Test de traducción manual
curl -X POST http://localhost:3000/api/debug/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "target": "es"}'
```

#### Respuesta con información de traducción
```json
{
  "response": "HAVAS ofrece servicios de...",
  "documentsFound": 5,
  "hasContext": true,
  "timestamp": "2025-08-26T14:30:00.000Z",
  "language": {
    "detected": "es",
    "original_message": "¿Qué servicios ofrece HAVAS?",
    "french_message": "Quels services HAVAS offre-t-il ?",
    "french_response": "HAVAS offre des services de...",
    "translated_back": true
  }
}
```

## 🔧 Diagnóstico

El sistema incluye un diagnóstico completo que verifica:

1. ✅ Variables de entorno
2. 🔍 Conectividad con Azure AI Search
3. 📄 Estructura del índice de búsqueda
4. 🤖 Conexión con Azure OpenAI
5. 🎯 Test de integración completa

```bash
python main.py diagnostic
```

## 📁 Estructura del Proyecto (Final)

```
├── app.py                    # 🐍 Servidor Flask principal con traducción automática
├── diagnostic.py             # 🔍 Script de diagnóstico completo  
├── main.py                  # 🎛️ CLI unificado y punto de entrada
├── start.py                 # 🚀 Script de inicio alternativo
├── requirements.txt         # 📋 Dependencias Python
├── .env                     # 🔐 Variables de entorno (configuración)
├── .env.example             # 📝 Ejemplo de configuración
├── python.bat              # 🛠️ Helper para Windows (opcional)
├── public/                 # 🌐 Frontend (sin cambios de la versión Node.js)
│   ├── index.html          #   📄 Página principal del chat
│   ├── css/styles.css      #   🎨 Estilos CSS
│   └── js/chat.js          #   ⚙️ Lógica del chat (JavaScript)
├── backup/                 # 📦 Versión original Node.js (respaldo)
│   ├── app.js              #   🟨 Servidor Express original  
│   ├── diagnostic.js       #   🔍 Diagnóstico JavaScript original
│   ├── package.json        #   📋 Dependencias Node.js
│   ├── node_modules/       #   📚 Módulos de Node.js
│   └── README-BACKUP.md    #   📖 Documentación del backup
├── MIGRATION_SUMMARY.md    # 📋 Resumen detallado de la migración
└── README.md               # 📖 Esta documentación
```

## 🔄 Migración desde Node.js

Este proyecto fue migrado completamente desde Node.js/Express a Python/Flask. Detalles completos en [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md).

### Equivalencias
- `app.js` → `app.py` (Flask server)
- `diagnostic.js` → `diagnostic.py` 
- `package.json` → `requirements.txt`
- Express → Flask
- axios → requests
- express-rate-limit → flask-limiter

## 🐞 Resolución de Problemas

### Error: Module 'flask' not found
```bash
pip install -r requirements.txt
```

### Error: Python command not found
Usar el comando específico de tu instalación Python o el archivo `python.bat` incluido.

### Error: Azure API version
Asegúrate de usar la versión correcta de API en las llamadas a Azure OpenAI (2024-12-01-preview).

### Puertos en uso
Por defecto usa puerto 3000. Cambiar con variable de entorno `PORT=5000`.

## 📊 Logging

El sistema incluye logging detallado:
- 📩 Mensajes recibidos
- 🔍 Resultados de búsqueda  
- 🤖 Respuestas de IA
- ❌ Errores y diagnósticos

## 🔒 Seguridad

- Rate limiting: 30 requests/minuto por IP
- CORS configurado
- Validación de entrada
- Variables de entorno para credenciales
- Error handling robusto

## 🌟 Características de la Versión Python

### Mejoras sobre Node.js
- ✅ CLI más intuitivo
- ✅ Mejor manejo de errores
- ✅ Logging más detallado
- ✅ Código más modular
- ✅ Diagnóstico más completo

### Mantenido Compatible
- ✅ Mismo frontend JavaScript
- ✅ Mismas rutas API
- ✅ Mismo formato de respuestas
- ✅ Misma configuración

## 📝 Licencia

Proyecto interno de HAVAS.

## 🤝 Soporte

Para problemas o preguntas, ejecutar diagnóstico y revisar logs:
```bash
python main.py diagnostic
```

---

**🎉 Estado: ✅ MIGRACIÓN COMPLETA Y FUNCIONAL**  
**🌐 Nueva funcionalidad: Sistema de traducción automática con GPT-4.1 nano**  
**🔍 Nueva: Integración Azure AI Search como recuperador primario (variable AZURE_SEARCH_ONLY)**
**🐍 Versión: Python 3.10+ / Flask 3.0**  
**📅 Finalizado: Agosto 2025**

### 🏆 Logros de esta migración:
- ✅ Migración completa de Node.js/Express a Python/Flask
- ✅ Sistema de traducción automática multiidioma implementado
- ✅ Detección automática de idioma con GPT-4.1 nano
- ✅ Procesamiento interno en francés, respuesta en idioma original
- ✅ Frontend JavaScript preservado sin cambios
- ✅ Todas las funcionalidades originales mantenidas
- ✅ Documentación completa y actualizada
- ✅ Scripts de diagnóstico y prueba incluidos
- ✅ Backup completo de la versión original Node.js
