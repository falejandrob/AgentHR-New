// Script de diagnóstico para Azure AI Search
const axios = require('axios');
require('dotenv').config();

async function runDiagnostics() {
    console.log('🔍 HAVAS Chatbot - Diagnóstico de Azure AI Search');
    console.log('='.repeat(60));
    
    // Verificar variables de entorno
    console.log('\n1. ✅ Verificando variables de entorno...');
    const requiredVars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY', 
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_KEY',
        'AZURE_SEARCH_INDEX'
    ];
    
    let missingVars = [];
    requiredVars.forEach(varName => {
        if (process.env[varName]) {
            console.log(`   ✅ ${varName}: ${process.env[varName].substring(0, 20)}...`);
        } else {
            console.log(`   ❌ ${varName}: NO CONFIGURADA`);
            missingVars.push(varName);
        }
    });
    
    if (missingVars.length > 0) {
        console.log(`\n❌ Faltan ${missingVars.length} variables de entorno requeridas.`);
        process.exit(1);
    }
    
    // Test Azure Search Index
    console.log('\n2. 🔍 Verificando índice de Azure AI Search...');
    try {
        const indexUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}?api-version=2023-11-01`;
        const response = await axios.get(indexUrl, {
            headers: {
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        console.log(`   ✅ Índice encontrado: ${response.data.name}`);
        console.log(`   📄 Total de campos: ${response.data.fields.length}`);
        
        // Mostrar campos importantes
        console.log('\n   📋 Campos del índice:');
        response.data.fields.forEach(field => {
            const searchable = field.searchable ? '🔍' : '  ';
            const key = field.key ? '🔑' : '  ';
            console.log(`   ${key}${searchable} ${field.name} (${field.type})`);
        });
        
    } catch (error) {
        console.log('   ❌ Error al acceder al índice:');
        console.log(`      Status: ${error.response?.status}`);
        console.log(`      Message: ${error.response?.data?.error?.message || error.message}`);
        return;
    }
    
    // Test búsqueda simple
    console.log('\n3. 🔍 Probando búsqueda simple...');
    try {
        const searchUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01`;
        const searchResponse = await axios.post(searchUrl, {
            search: '*',
            top: 3,
            select: '*'
        }, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        const results = searchResponse.data.value || [];
        console.log(`   ✅ Búsqueda exitosa: ${results.length} documentos encontrados`);
        
        if (results.length > 0) {
            console.log('\n   📄 Muestra del primer documento:');
            const doc = results[0];
            Object.keys(doc).slice(0, 5).forEach(key => {
                let value = doc[key];
                if (typeof value === 'string' && value.length > 50) {
                    value = value.substring(0, 50) + '...';
                }
                console.log(`      ${key}: ${value}`);
            });
        } else {
            console.log('   ⚠️  No se encontraron documentos en el índice');
        }
        
    } catch (error) {
        console.log('   ❌ Error en la búsqueda:');
        console.log(`      Status: ${error.response?.status}`);
        console.log(`      Message: ${error.response?.data?.error?.message || error.message}`);
    }
    
    // Test búsqueda con query específico
    console.log('\n4. 🔍 Probando búsqueda específica...');
    try {
        const testQueries = ['HAVAS', 'información', 'empresa', 'servicio'];
        
        for (const query of testQueries) {
            const searchUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01`;
            const searchResponse = await axios.post(searchUrl, {
                search: query,
                top: 2,
                select: '*'
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'api-key': process.env.AZURE_SEARCH_KEY
                }
            });
            
            const results = searchResponse.data.value || [];
            console.log(`   📝 Query "${query}": ${results.length} resultados`);
        }
        
    } catch (error) {
        console.log('   ❌ Error en búsqueda específica:', error.response?.data?.error?.message || error.message);
    }
    
    // Test Azure OpenAI
    console.log('\n5. 🤖 Verificando Azure OpenAI...');
    try {
        const deploymentUrl = `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments?api-version=2023-05-15`;
        const openaiResponse = await axios.get(deploymentUrl, {
            headers: {
                'api-key': process.env.AZURE_OPENAI_KEY
            }
        });
        
        console.log('   ✅ Conexión a OpenAI exitosa');
        
        const deployments = openaiResponse.data.data || [];
        const targetDeployment = deployments.find(d => d.id === process.env.AZURE_OPENAI_DEPLOYMENT);
        
        if (targetDeployment) {
            console.log(`   ✅ Deployment encontrado: ${targetDeployment.id}`);
            console.log(`   📊 Modelo: ${targetDeployment.model}`);
        } else {
            console.log(`   ⚠️  Deployment "${process.env.AZURE_OPENAI_DEPLOYMENT}" no encontrado`);
            console.log('   📋 Deployments disponibles:');
            deployments.forEach(d => console.log(`      - ${d.id} (${d.model})`));
        }
        
    } catch (error) {
        console.log('   ❌ Error al conectar con OpenAI:');
        console.log(`      Status: ${error.response?.status}`);
        console.log(`      Message: ${error.response?.data?.error?.message || error.message}`);
    }
    
    // Test integración completa
    console.log('\n6. 🎯 Test de integración completa...');
    try {
        // Simular una consulta real
        const testMessage = 'Hola, ¿qué servicios ofrece HAVAS?';
        console.log(`   📝 Query de prueba: "${testMessage}"`);
        
        // Búsqueda
        const searchUrl = `${process.env.AZURE_SEARCH_ENDPOINT}/indexes/${process.env.AZURE_SEARCH_INDEX}/docs/search?api-version=2023-11-01`;
        const searchResponse = await axios.post(searchUrl, {
            search: testMessage,
            top: 2,
            select: '*'
        }, {
            headers: {
                'Content-Type': 'application/json',
                'api-key': process.env.AZURE_SEARCH_KEY
            }
        });
        
        const searchResults = searchResponse.data.value || [];
        console.log(`   🔍 Documentos encontrados: ${searchResults.length}`);
        
        // Generar contexto
        let context = '';
        if (searchResults.length > 0) {
            context = searchResults.map(doc => {
                const fields = Object.keys(doc);
                const textField = fields.find(f => 
                    ['content', 'text', 'description', 'body'].includes(f.toLowerCase())
                ) || fields[0];
                
                return doc[textField] || JSON.stringify(doc).substring(0, 200);
            }).join('\n\n');
        }
        
        // Test OpenAI con contexto
        if (context) {
            const apiUrl = `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments/${process.env.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2024-02-15-preview`;
            
            const openaiResponse = await axios.post(apiUrl, {
                messages: [
                    { 
                        role: 'system', 
                        content: `Eres un asistente de HAVAS. Contexto: ${context.substring(0, 500)}` 
                    },
                    { role: 'user', content: testMessage }
                ],
                max_tokens: 150,
                temperature: 0.7
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'api-key': process.env.AZURE_OPENAI_KEY
                }
            });
            
            const aiResponse = openaiResponse.data.choices[0].message.content;
            console.log('   🤖 Respuesta de IA generada exitosamente');
            console.log(`   💬 Preview: "${aiResponse.substring(0, 100)}..."`);
            console.log('\n   ✅ ¡Integración completa funcionando correctamente!');
        } else {
            console.log('   ⚠️  Sin contexto disponible, pero OpenAI funciona');
        }
        
    } catch (error) {
        console.log('   ❌ Error en test de integración:', error.response?.data?.error?.message || error.message);
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('🎉 Diagnóstico completado');
    console.log('\n💡 Sugerencias:');
    console.log('   - Si no hay documentos, revisa el proceso de indexación');
    console.log('   - Verifica que los campos de búsqueda estén marcados como "searchable"');  
    console.log('   - Considera usar búsqueda semántica para mejores resultados');
    console.log('   - Revisa los logs del servidor para más detalles durante las consultas');
}

// Ejecutar diagnósticos
runDiagnostics().catch(error => {
    console.error('❌ Error durante el diagnóstico:', error.message);
    process.exit(1);
});