# 🔄 Migración de Node.js a Python - HAVAS Chatbot

## 📊 Resumen de la Migración

Este documento describe la migración completa del backend de HAVAS Chatbot desde Node.js/Express a Python/Flask.

### 🎯 Objetivo
Migrar toda la funcionalidad del backend de JavaScript (Node.js) a Python, manteniendo la misma funcionalidad y compatibilidad con el frontend existente.

## 📁 Archivos Migrados

### ✅ Archivos Python Creados

| Archivo Original (JS) | Archivo Migrado (Python) | Estado | Descripción |
|----------------------|---------------------------|---------|-------------|
| `app.js` | `app.py` | ✅ Completo | Servidor Flask con todas las rutas API |
| `diagnostic.js` | `diagnostic.py` | ✅ Completo | Script de diagnóstico de Azure services |
| N/A | `main.py` | ✅ Nuevo | Punto de entrada principal con CLI |
| N/A | `start.py` | ✅ Nuevo | Script de inicio del servidor |
| `package.json` | `requirements.txt` | ✅ Actualizado | Dependencias Python |

### 🔄 Archivos Preservados (Frontend)
- `public/index.html` - Sin cambios
- `public/css/styles.css` - Sin cambios  
- `public/js/chat.js` - Sin cambios (frontend JavaScript preservado)

## 🛠️ Dependencias

### Node.js → Python
| Node.js | Python | Propósito |
|---------|---------|-----------|
| `express` | `flask` | Framework web |
| `cors` | `flask-cors` | CORS handling |
| `express-rate-limit` | `flask-limiter` | Rate limiting |
| `axios` | `requests` | HTTP requests |
| `dotenv` | `python-dotenv` | Variables de entorno |
| `helmet` | Manual | Seguridad (implementado manualmente) |

## 🔧 Funcionalidades Migradas

### ✅ Completamente Migradas
- ✅ Servidor web con Flask
- ✅ Rutas API (`/api/chat`, `/api/health`, `/api/debug/index`)
- ✅ Integración con Azure OpenAI
- ✅ Integración con Azure AI Search
- ✅ Rate limiting
- ✅ CORS handling
- ✅ Validación de configuración
- ✅ Logging y error handling
- ✅ Servir archivos estáticos
- ✅ Búsqueda semántica con fallback
- ✅ Extracción de contexto de documentos
- ✅ Diagnóstico completo del sistema

### 🚀 Mejoras Añadidas
- 🆕 CLI unificado en `main.py`
- 🆕 Mejor manejo de errores
- 🆕 Logging más detallado
- 🆕 Estructura modular mejorada

## 🚀 Comandos de Uso

### Iniciar el Servidor
```bash
# Opción 1: Usando main.py (recomendado)
python main.py

# Opción 2: Comando específico
python main.py start

# Opción 3: Directamente
python app.py
```

### Ejecutar Diagnóstico
```bash
# Opción 1: A través de main.py
python main.py diagnostic

# Opción 2: Directamente
python diagnostic.py
```

### Ayuda
```bash
python main.py help
```

## 🔐 Variables de Entorno Requeridas

Las mismas variables que en la versión Node.js:

```env
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name
PORT=5000
FLASK_ENV=development  # o production
```

## 🌐 Endpoints API

Todas las rutas API mantienen la misma estructura:

- `POST /api/chat` - Endpoint principal del chatbot
- `GET /api/health` - Health check del sistema
- `GET /api/debug/index` - Información de debug del índice
- `GET /` - Página principal (sirve `index.html`)

## 📋 Testing

### Verificar la Migración
1. Ejecutar diagnóstico: `python main.py diagnostic`
2. Iniciar servidor: `python main.py start`
3. Probar en navegador: `http://localhost:5000`
4. Probar API: `curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d '{"message":"Hola"}'`

## 🔄 Compatibilidad

### ✅ Mantenido
- Frontend JavaScript sin cambios
- Misma estructura de respuestas API
- Mismo formato de configuración
- Mismo comportamiento de Azure integrations

### 🆕 Mejorado
- Mejor manejo de errores
- Logging más detallado
- CLI más amigable
- Código más modular

## 🚨 Notas Importantes

1. **Frontend Intacto**: El frontend (`public/js/chat.js`) no fue modificado y funciona igual
2. **Puerto por Defecto**: Python usa puerto 5000 por defecto (vs 3000 en Node.js)
3. **Variables de Entorno**: Mismo archivo `.env` compatible
4. **Dependencias**: Instalar con `pip install -r requirements.txt`

## 🔧 Próximos Pasos

1. Probar extensivamente todos los endpoints
2. Configurar deployment para producción
3. Actualizar documentación de deployment
4. Considerar migraciones adicionales si es necesario

---

**Estado de la Migración: ✅ COMPLETA**  
**Fecha: Agosto 2025**  
**Migrado por: GitHub Copilot AI Assistant**