const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware de seguridad
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
}));

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Rate limiting
const limiter = rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minuto
    max: 30 // límite de 30 requests por minuto
});

app.use('/api/', limiter);

// Validar configuración al inicio
const validateConfig = () => {
    const required = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_KEY',
        'AZURE_SEARCH_INDEX'
    ];
    
    const missing = required.filter(key => !process.env[key]);
    
    if (missing.length > 0) {
        console.error('❌ Faltan variables de entorno:', missing.join(', '));
        console.log('Por favor, configura estas variables en Azure App Service o en tu archivo .env local');
        process.exit(1);
    }
    
    console.log('✅ Configuración validada correctamente');
};

validateConfig();

// Función mejorada para buscar en Azure AI Search
async function searchDocuments(query) {
    const searchUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01`;
    
    try {
        console.log(`🔍 Buscando: "${query}" en índice: ${process.env.AZURE_SEARCH_INDEX}`);
        
        // Búsqueda básica primero, sin dependencias semánticas
        const searchPayload = {
            search: query,
            top: 5,
            select: '*',
            searchMode: 'any',
            queryType: 'simple',
            highlight: 'content_text,document_title,content_id',
            highlightPreTag: '<mark>',
            highlightPostTag: '</mark>'
        };

        // Solo agregar configuración semántica si está disponible
        if (process.env.AZURE_SEARCH_SEMANTIC_CONFIG) {
            searchPayload.queryType = 'semantic';
            searchPayload.semanticConfiguration = process.env.AZURE_SEARCH_SEMANTIC_CONFIG || 'default';
            searchPayload.captions = 'extractive';
            searchPayload.answers = 'extractive';
        }
        
        const response = await axios.post(searchUrl, searchPayload, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        const results = response.data.value || [];
        console.log(`📄 Encontrados ${results.length} documentos`);
        
        // Log de la estructura del primer documento para debug
        if (results.length > 0) {
            console.log('📋 Estructura del primer documento:', Object.keys(results[0]));
        }
        
        return results;
        
    } catch (error) {
        console.error('❌ Error en Azure Search:', {
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data,
            url: searchUrl
        });
        
        // Si falla la búsqueda semántica, intentar búsqueda simple
        if (error.response?.status === 400) {
            console.log('🔄 Reintentando con búsqueda simple...');
            try {
                const simpleResponse = await axios.post(searchUrl, {
                    search: query,
                    top: 20,
                    select: '*',
                    searchMode: 'any'
                }, {
                    headers: {
                        'Content-Type': 'application/json',
                        'api-key': process.env.AZURE_SEARCH_KEY
                    }
                });
                
                console.log(`📄 Búsqueda simple exitosa: ${simpleResponse.data.value?.length || 0} documentos`);
                return simpleResponse.data.value || [];
            } catch (simpleError) {
                console.error('❌ Error en búsqueda simple:', simpleError.response?.data || simpleError.message);
                return [];
            }
        }
        
        return [];
    }
}

// Función mejorada para extraer contexto de documentos
function extractContext(searchResults) {
    if (!searchResults || searchResults.length === 0) {
        return null;
    }
    
    const context = searchResults.map((doc, index) => {
        let content = '';
        let title = '';
        let summary = '';
        
        // Intentar diferentes nombres de campos comunes
        const possibleContentFields = ['content', 'text', 'description', 'body', 'document_content', 'chunk'];
        const possibleTitleFields = ['title', 'name', 'filename', 'document_title', 'heading'];
        
        // Extraer contenido
        for (const field of possibleContentFields) {
            if (doc[field]) {
                content = doc[field];
                break;
            }
        }
        
        // Extraer título
        for (const field of possibleTitleFields) {
            if (doc[field]) {
                title = doc[field];
                break;
            }
        }
        
        // Extraer resumen de captions si existe
        if (doc['@search.captions']) {
            summary = doc['@search.captions'].map(c => c.text).join(' ');
        } else if (doc['@search.highlights']) {
            const highlights = Object.values(doc['@search.highlights']).flat();
            summary = highlights.slice(0, 2).join(' ');
        }
        
        // Si no hay contenido específico, usar todo el documento
        if (!content && !title) {
            const docStr = JSON.stringify(doc);
            content = docStr.length > 500 ? docStr.substring(0, 500) + '...' : docStr;
            title = `Documento ${index + 1}`;
        }
        
        const docText = [
            title ? `**Título:** ${title}` : '',
            content ? `**Contenido:** ${content.substring(0, 800)}${content.length > 800 ? '...' : ''}` : '',
            summary ? `**Resumen:** ${summary}` : ''
        ].filter(Boolean).join('\n\n');
        
        return docText;
    }).filter(text => text.length > 0);
    
    return context.join('\n\n---\n\n');
}

// Función mejorada para llamar a Azure OpenAI
async function getAIResponse(message, context) {
    const apiUrl = `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments/${process.env.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-12-01-preview`;
    
    let systemMessage = `Eres un asistente AI profesional de HAVAS, una de las agencias de publicidad y comunicación más grandes del mundo. 

**INSTRUCCIONES IMPORTANTES:**
- Responde en el idioma que te hable de manera profesional y útil
- Usa formato Markdown cuando sea apropiado (## títulos, **negrita**, *cursiva*, listas, etc.)
- Si tienes contexto relevante de documentos, úsalo para dar respuestas precisas
- Si no tienes información específica sobre lo que se pregunta, indícalo claramente
- Mantén un tono profesional pero cercano, representando los valores de HAVAS

`;

    if (context && context.trim()) {
        systemMessage += `**Contexto de documentos encontrados:**\n\n${context}`;
    } else {
        systemMessage += `**Nota:** No se encontraron documentos específicos para esta consulta en la base de conocimientos.`;
    }
    
    try {
        console.log('🤖 Enviando mensaje a Azure OpenAI...');
        
        const response = await axios.post(apiUrl, {
            messages: [
                { role: 'system', content: systemMessage },
                { role: 'user', content: message }
            ],
            max_completion_tokens: 10000,
            model: process.env.AZURE_OPENAI_DEPLOYMENT
        }, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_OPENAI_KEY
            }
        });
        
        console.log('✅ Respuesta de OpenAI recibida');
        return response.data.choices[0].message.content;
        
    } catch (error) {
        console.error('❌ Error en Azure OpenAI:', {
            status: error.response?.status,
            data: error.response?.data || error.message
        });
        throw error;
    }
}

// Endpoint principal del chat mejorado
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'El mensaje es requerido' });
        }
        
        console.log('📩 Mensaje recibido:', message);
        console.log('⏰ Timestamp:', new Date().toISOString());
        
        // Buscar documentos relevantes
        const searchResults = await searchDocuments(message);
        console.log(`🔍 Resultado de búsqueda: ${searchResults.length} documentos`);
        
        // Extraer contexto de forma más robusta
        const context = extractContext(searchResults);
        
        if (context) {
            console.log(`📄 Contexto extraído: ${context.length} caracteres`);
        } else {
            console.log('ℹ️ No se encontró contexto relevante');
        }
        
        // Obtener respuesta de AI
        const aiResponse = await getAIResponse(message, context);
        console.log('✅ Respuesta generada exitosamente');
        
        res.json({ 
            response: aiResponse,
            documentsFound: searchResults.length,
            hasContext: !!context,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('❌ Error en /api/chat:', error);
        res.status(500).json({ 
            error: 'Error al procesar tu mensaje. Por favor, intenta de nuevo.',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

// Endpoint para debug del índice
app.get('/api/debug/index', async (req, res) => {
    try {
        const indexUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}?api-version=2023-11-01`;
        
        const response = await axios.get(indexUrl, {
            headers: {
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        res.json({
            indexName: process.env.AZURE_SEARCH_INDEX,
            fields: response.data.fields,
            totalFields: response.data.fields.length
        });
    } catch (error) {
        res.status(500).json({
            error: 'Error al obtener información del índice',
            details: error.response?.data || error.message
        });
    }
});

// Endpoint de health check simplificado
app.get('/api/health', async (req, res) => {
    try {
        // Verificar solo que las variables de entorno estén configuradas
        const requiredVars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_KEY',
            'AZURE_OPENAI_DEPLOYMENT',
            'AZURE_SEARCH_ENDPOINT',
            'AZURE_SEARCH_KEY',
            'AZURE_SEARCH_INDEX'
        ];
        
        const missing = requiredVars.filter(key => !process.env[key]);
        
        if (missing.length > 0) {
            return res.status(500).json({
                status: 'unhealthy',
                timestamp: new Date().toISOString(),
                error: `Missing environment variables: ${missing.join(', ')}`
            });
        }
        
        // Health check básico - solo verificar que el servidor esté funcionando
        res.json({ 
            status: 'healthy',
            timestamp: new Date().toISOString(),
            environment: process.env.NODE_ENV || 'production',
            services: {
                server: 'running',
                config: 'loaded'
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'unhealthy',
            timestamp: new Date().toISOString(),
            error: error.message
        });
    }
});

// Servir la aplicación
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`🚀 HAVAS Chatbot corriendo en http://localhost:${PORT}`);
    console.log('📊 Environment:', process.env.NODE_ENV || 'production');
    console.log('🔧 Debug endpoint disponible en: http://localhost:${PORT}/api/debug/index');
});