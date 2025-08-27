#!/usr/bin/env python3
"""Script de diagnóstico para Azure AI Search"""

import requests
import os
import json
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def run_diagnostics():
    print('🔍 HAVAS Chatbot - Diagnóstico de Azure AI Search')
    print('=' * 60)
    
    # Verificar variables de entorno
    print('\n1. ✅ Verificando variables de entorno...')
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY', 
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_TRANSLATION_DEPLOYMENT',
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_KEY',
        'AZURE_SEARCH_INDEX'
    ]
    
    missing_vars = []
    for var_name in required_vars:
        value = os.getenv(var_name)
        if value:
            print(f'   ✅ {var_name}: {value[:20]}...')
        else:
            print(f'   ❌ {var_name}: NO CONFIGURADA')
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f'\n❌ Faltan {len(missing_vars)} variables de entorno requeridas.')
        sys.exit(1)
    
    # Test Azure Search Index
    print('\n2. 🔍 Verificando índice de Azure AI Search...')
    try:
        index_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}?api-version=2023-11-01"
        headers = {
            'api-key': os.getenv('AZURE_SEARCH_KEY')
        }
        
        response = requests.get(index_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ Índice encontrado: {data["name"]}')
            print(f'   📄 Total de campos: {len(data["fields"])}')
            
            # Mostrar campos importantes
            print('\n   📋 Campos del índice:')
            for field in data['fields']:
                searchable = '🔍' if field.get('searchable', False) else '  '
                key = '🔑' if field.get('key', False) else '  '
                print(f'   {key}{searchable} {field["name"]} ({field["type"]})')
        else:
            print(f'   ❌ Error al acceder al índice:')
            print(f'      Status: {response.status_code}')
            print(f'      Message: {response.text}')
            return
        
    except Exception as error:
        print('   ❌ Error al acceder al índice:')
        print(f'      Message: {str(error)}')
        return
    
    # Test búsqueda simple
    print('\n3. 🔍 Probando búsqueda simple...')
    try:
        search_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}/docs/search?api-version=2023-11-01"
        
        payload = {
            "search": "*",
            "top": 3,
            "select": "*"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'api-key': os.getenv('AZURE_SEARCH_KEY')
        }
        
        search_response = requests.post(search_url, json=payload, headers=headers)
        
        if search_response.status_code == 200:
            results = search_response.json().get('value', [])
            print(f'   ✅ Búsqueda exitosa: {len(results)} documentos encontrados')
            
            if results:
                print('\n   📄 Muestra del primer documento:')
                doc = results[0]
                for i, (key, value) in enumerate(doc.items()):
                    if i >= 5:  # Solo mostrar los primeros 5 campos
                        break
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + '...'
                    print(f'      {key}: {value}')
            else:
                print('   ⚠️  No se encontraron documentos en el índice')
        else:
            print('   ❌ Error en la búsqueda:')
            print(f'      Status: {search_response.status_code}')
            print(f'      Message: {search_response.text}')
        
    except Exception as error:
        print('   ❌ Error en la búsqueda:')
        print(f'      Message: {str(error)}')
    
    # Test búsqueda con query específico
    print('\n4. 🔍 Probando búsqueda específica...')
    try:
        test_queries = ['HAVAS', 'información', 'empresa', 'servicio']
        
        for query in test_queries:
            search_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}/docs/search?api-version=2023-11-01"
            
            payload = {
                "search": query,
                "top": 2,
                "select": "*"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': os.getenv('AZURE_SEARCH_KEY')
            }
            
            search_response = requests.post(search_url, json=payload, headers=headers)
            
            if search_response.status_code == 200:
                results = search_response.json().get('value', [])
                print(f'   📝 Query "{query}": {len(results)} resultados')
            else:
                print(f'   ❌ Error en query "{query}": {search_response.text}')
        
    except Exception as error:
        print(f'   ❌ Error en búsqueda específica: {str(error)}')
    
    # Test Azure OpenAI
    print('\n5. 🤖 Verificando Azure OpenAI...')
    try:
        deployment_url = f"{os.getenv('AZURE_OPENAI_ENDPOINT')}/openai/deployments?api-version=2023-05-15"
        headers = {
            'api-key': os.getenv('AZURE_OPENAI_KEY')
        }
        
        openai_response = requests.get(deployment_url, headers=headers)
        
        if openai_response.status_code == 200:
            print('   ✅ Conexión a OpenAI exitosa')
            
            deployments = openai_response.json().get('data', [])
            target_deployment = next((d for d in deployments if d.get('id') == os.getenv('AZURE_OPENAI_DEPLOYMENT')), None)
            
            if target_deployment:
                print(f'   ✅ Deployment encontrado: {target_deployment["id"]}')
                print(f'   📊 Modelo: {target_deployment.get("model", "N/A")}')
            else:
                print(f'   ⚠️  Deployment "{os.getenv("AZURE_OPENAI_DEPLOYMENT")}" no encontrado')
                print('   📋 Deployments disponibles:')
                for d in deployments:
                    print(f'      - {d.get("id", "N/A")} ({d.get("model", "N/A")})')
        else:
            print('   ❌ Error al conectar con OpenAI:')
            print(f'      Status: {openai_response.status_code}')
            print(f'      Message: {openai_response.text}')
        
    except Exception as error:
        print('   ❌ Error al conectar con OpenAI:')
        print(f'      Message: {str(error)}')
    
    # Test integración completa
    print('\n6. 🎯 Test de integración completa...')
    try:
        # Simular una consulta real
        test_message = 'Hola, ¿qué servicios ofrece HAVAS?'
        print(f'   📝 Query de prueba: "{test_message}"')
        
        # Búsqueda
        search_url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}/docs/search?api-version=2023-11-01"
        
        payload = {
            "search": test_message,
            "top": 2,
            "select": "*"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'api-key': os.getenv('AZURE_SEARCH_KEY')
        }
        
        search_response = requests.post(search_url, json=payload, headers=headers)
        
        if search_response.status_code == 200:
            search_results = search_response.json().get('value', [])
            print(f'   🔍 Documentos encontrados: {len(search_results)}')
            
            # Generar contexto
            context = ''
            if search_results:
                context_parts = []
                for doc in search_results:
                    fields = list(doc.keys())
                    text_field = next((f for f in fields if f.lower() in ['content', 'text', 'description', 'body']), fields[0])
                    
                    doc_content = doc.get(text_field, json.dumps(doc)[:200])
                    context_parts.append(str(doc_content))
                
                context = '\n\n'.join(context_parts)
            
            # Test OpenAI con contexto
            if context:
                api_url = f"{os.getenv('AZURE_OPENAI_ENDPOINT')}/openai/deployments/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}/chat/completions?api-version=2024-12-01-preview"
                
                openai_payload = {
                    "messages": [
                        { 
                            "role": "system", 
                            "content": f"Eres un asistente de HAVAS. Contexto: {context[:500]}" 
                        },
                        { "role": "user", "content": test_message }
                    ],
                    "max_completion_tokens": 150,
                    "temperature": 0.7
                }
                
                openai_headers = {
                    'Content-Type': 'application/json',
                    'api-key': os.getenv('AZURE_OPENAI_KEY')
                }
                
                openai_response = requests.post(api_url, json=openai_payload, headers=openai_headers)
                
                if openai_response.status_code == 200:
                    ai_response = openai_response.json()['choices'][0]['message']['content']
                    print('   🤖 Respuesta de IA generada exitosamente')
                    print(f'   💬 Preview: "{ai_response[:100]}..."')
                    print('\n   ✅ ¡Integración completa funcionando correctamente!')
                else:
                    print(f'   ❌ Error en OpenAI: {openai_response.text}')
            else:
                print('   ⚠️  Sin contexto disponible, pero OpenAI funciona')
        else:
            print(f'   ❌ Error en búsqueda de integración: {search_response.text}')
        
    except Exception as error:
        print(f'   ❌ Error en test de integración: {str(error)}')
    
    print('\n' + '=' * 60)
    print('🎉 Diagnóstico completado')
    print('\n💡 Sugerencias:')
    print('   - Si no hay documentos, revisa el proceso de indexación')
    print('   - Verifica que los campos de búsqueda estén marcados como "searchable"')  
    print('   - Considera usar búsqueda semántica para mejores resultados')
    print('   - Revisa los logs del servidor para más detalles durante las consultas')

if __name__ == '__main__':
    # Ejecutar diagnósticos
    try:
        run_diagnostics()
    except Exception as error:
        print(f'❌ Error durante el diagnóstico: {str(error)}')
        sys.exit(1)
