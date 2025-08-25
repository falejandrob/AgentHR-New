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
            scriptSrc: ["'self'", "'unsafe-inline'"],
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

// Función para buscar en Azure AI Search
async function searchDocuments(query) {
    const searchUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01`;
    
    try {
        const response = await axios.post(searchUrl, {
            search: query,
            top: 5,
            select: '*',
            queryType: 'semantic',
            semanticConfiguration: 'default',
            captions: 'extractive',
            answers: 'extractive'
        }, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        return response.data.value || [];
    } catch (error) {
        console.error('Error en Azure Search:', error.response?.data || error.message);
        return [];
    }
}

// Función para llamar a Azure OpenAI
async function getAIResponse(message, context) {
    const apiUrl = `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments/${process.env.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview`;
    
    const systemMessage = `Eres un asistente AI profesional de HAVAS, una de las agencias de publicidad y comunicación más grandes del mundo. 
    Tu objetivo es ayudar con información precisa y relevante basada en el conocimiento de la empresa.
    
    IMPORTANTE: Si tienes contexto relevante, úsalo para responder. Si no hay contexto o no es relevante, indica que no tienes esa información específica en la base de conocimientos.
    
    Contexto disponible:
    ${context || 'No hay contexto específico disponible para esta consulta.'}`;
    
    try {
        const response = await axios.post(apiUrl, {
            messages: [
                { role: 'system', content: systemMessage },
                { role: 'user', content: message }
            ],
            max_tokens: 1000,
            temperature: 0.7,
            top_p: 0.95,
            frequency_penalty: 0,
            presence_penalty: 0,
            stop: null
        }, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_OPENAI_KEY
            }
        });
        
        return response.data.choices[0].message.content;
    } catch (error) {
        console.error('Error en Azure OpenAI:', error.response?.data || error.message);
        throw error;
    }
}

// Endpoint principal del chat
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'El mensaje es requerido' });
        }
        
        console.log('📩 Mensaje recibido:', message);
        
        // Buscar documentos relevantes
        const searchResults = await searchDocuments(message);
        console.log(`🔍 Se encontraron ${searchResults.length} documentos relevantes`);
        
        // Preparar contexto
        const context = searchResults.map(doc => {
            // Adaptar según la estructura de tus documentos
            const content = doc.content || doc.text || doc.description || '';
            const title = doc.title || doc.name || '';
            const caption = doc['@search.captions']?.[0]?.text || '';
            
            return `Título: ${title}\nContenido: ${content}\nResumen: ${caption}`;
        }).filter(text => text.length > 0).join('\n\n---\n\n');
        
        // Obtener respuesta de AI
        const aiResponse = await getAIResponse(message, context);
        console.log('✅ Respuesta generada exitosamente');
        
        res.json({ 
            response: aiResponse,
            documentsFound: searchResults.length
        });
        
    } catch (error) {
        console.error('Error en /api/chat:', error);
        res.status(500).json({ 
            error: 'Error al procesar tu mensaje. Por favor, intenta de nuevo.',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

// Endpoint de health check
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'production'
    });
});

// Servir la aplicación
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`🚀 HAVAS Chatbot corriendo en http://localhost:${PORT}`);
    console.log('📊 Environment:', process.env.NODE_ENV || 'production');
});