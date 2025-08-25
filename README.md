# HAVAS Chatbot - Azure Web App

## 🚀 Descripción
Aplicación de chatbot empresarial para HAVAS que integra Azure OpenAI y Azure AI Search para proporcionar respuestas basadas en RAG (Retrieval-Augmented Generation).

## 📋 Prerrequisitos

### Recursos de Azure necesarios:
1. **Azure OpenAI Service**
   - Un deployment de GPT-4 o GPT-3.5
   - Endpoint y API Key

2. **Azure AI Search**
   - Un índice configurado con tus documentos
   - Endpoint y API Key
   - Configuración semántica (opcional pero recomendada)

3. **Azure App Service** (para deployment)
   - Plan de App Service (B1 o superior recomendado)

## 🛠️ Instalación Local

### 1. Crear la estructura del proyecto:

```bash
# Crear carpeta principal
mkdir havas-chatbot
cd havas-chatbot

# Crear estructura de carpetas
mkdir -p public/css public/js
```

### 2. Crear los archivos:

Copia cada archivo de los artifacts anteriores en su ubicación correspondiente:
- `package.json` en la raíz
- `app.js` en la raíz
- `.env.example` en la raíz
- `index.html` en `public/`
- `styles.css` en `public/css/`
- `chat.js` en `public/js/`

### 3. Instalar dependencias:

```bash
npm install
```

### 4. Configurar variables de entorno:

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales reales
# Usar tu editor favorito (nano, vim, code, etc.)
nano .env
```

### 5. Ejecutar en modo desarrollo:

```bash
npm run dev
```

La aplicación estará disponible en http://localhost:3000

## 🚀 Despliegue en Azure App Service

### Opción 1: Usando Azure CLI

#### Instalar Azure CLI (si no lo tienes):

```bash
# Windows
winget install Microsoft.AzureCLI

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### Desplegar la aplicación:

```bash
# 1. Login en Azure
az login

# 2. Definir variables
RESOURCE_GROUP="rg-havas-chatbot"
APP_NAME="havas-chatbot-$(date +%s)"  # Nombre único
LOCATION="westeurope"

# 3. Crear grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION

# 4. Crear App Service Plan
az appservice plan create \
  --name "$APP_NAME-plan" \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# 5. Crear Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan "$APP_NAME-plan" \
  --name $APP_NAME \
  --runtime "node|18-lts"

# 6. Configurar variables de entorno
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    AZURE_OPENAI_ENDPOINT="tu-endpoint-aqui" \
    AZURE_OPENAI_KEY="tu-key-aqui" \
    AZURE_OPENAI_DEPLOYMENT="tu-deployment-aqui" \
    AZURE_SEARCH_ENDPOINT="tu-search-endpoint-aqui" \
    AZURE_SEARCH_KEY="tu-search-key-aqui" \
    AZURE_SEARCH_INDEX="tu-index-aqui"

# 7. Crear archivo ZIP para deployment
zip -r deploy.zip . -x "*.git*" -x "*.env" -x "node_modules/*"

# 8. Desplegar el ZIP
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src deploy.zip

# 9. Ver la URL de tu app
echo "Tu app está en: https://$APP_NAME.azurewebsites.net"
```

### Opción 2: Usando Azure Portal

1. **Crear App Service:**
   - Ir a [Azure Portal](https://portal.azure.com)
   - Click en "Crear un recurso"
   - Buscar "Web App"
   - Configurar:
     - **Suscripción**: Tu suscripción
     - **Grupo de recursos**: Crear nuevo o usar existente
     - **Nombre**: Un nombre único para tu app
     - **Publicar**: Código
     - **Pila del runtime**: Node 18 LTS
     - **Sistema operativo**: Linux
     - **Región**: La más cercana a tus usuarios
     - **Plan**: B1 o superior

2. **Configurar variables de entorno:**
   - Ir a tu App Service
   - En el menú lateral: Configuración → Configuración de la aplicación
   - Agregar nueva configuración de aplicación para cada variable:
     - AZURE_OPENAI_ENDPOINT
     - AZURE_OPENAI_KEY
     - AZURE_OPENAI_DEPLOYMENT
     - AZURE_SEARCH_ENDPOINT
     - AZURE_SEARCH_KEY
     - AZURE_SEARCH_INDEX
   - Guardar cambios

3. **Desplegar el código:**
   - En el menú lateral: Centro de implementación
   - Elegir origen: Git local
   - Seguir las instrucciones para configurar Git
   - O usar GitHub Actions si tu código está en GitHub

### Opción 3: Usando VS Code

1. **Instalar extensión:**
   - Abrir VS Code
   - Instalar la extensión "Azure App Service"

2. **Desplegar:**
   - Abrir la carpeta del proyecto en VS Code
   - Click en el icono de Azure en la barra lateral
   - Sign in a tu cuenta de Azure
   - Click derecho en "App Services"
   - "Create New Web App" o "Deploy to Web App"
   - Seguir el asistente

## 🔧 Configuración de Azure AI Search

### Estructura recomendada del índice:

Tu índice debe tener estos campos (ajusta según tus documentos):

```json
{
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "description",
      "type": "Edm.String",
      "searchable": true
    }
  ]
}
```

### Configuración semántica (opcional pero recomendada):

```json
{
  "name": "default",
  "prioritizedFields": {
    "titleField": {
      "fieldName": "title"
    },
    "prioritizedContentFields": [
      {
        "fieldName": "content"
      }
    ],
    "prioritizedKeywordsFields": [
      {
        "fieldName": "description"
      }
    ]
  }
}
```

## 📊 Monitoreo y Logs

### Ver logs en tiempo real:

```bash
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME
```

### Habilitar Application Insights (recomendado):

```bash
# Crear Application Insights
az monitor app-insights component create \
  --app "ai-$APP_NAME" \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Conectar con tu App Service
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>
```

## 🔒 Seguridad

### Configuraciones implementadas:
- ✅ Rate limiting (30 requests/minuto)
- ✅ Helmet.js para headers de seguridad
- ✅ CORS configurado
- ✅ Variables de entorno para secretos
- ✅ No exposición de credenciales al frontend

### Configuraciones adicionales recomendadas:

```bash
# Habilitar HTTPS only
az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --https-only true

# Configurar dominio personalizado (opcional)
az webapp config hostname add \
  --webapp-name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname www.tu-dominio.com
```

## 🧪 Testing

### Probar localmente:

```bash
# Health check
curl http://localhost:3000/api/health

# Enviar mensaje de prueba
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿cómo estás?"}'
```

### Probar en Azure:

```bash
# Reemplazar con tu URL
APP_URL="https://tu-app.azurewebsites.net"

# Health check
curl $APP_URL/api/health

# Test chat
curl -X POST $APP_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

## 📈 Escalamiento

### Escalar verticalmente:

```bash
az appservice plan update \
  --name "$APP_NAME-plan" \
  --resource-group $RESOURCE_GROUP \
  --sku P1V2
```

### Configurar auto-scaling:

```bash
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --resource "$APP_NAME-plan" \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-$APP_NAME \
  --min-count 1 \
  --max-count 5 \
  --count 1

az monitor autoscale rule create \
  --resource-group $RESOURCE_GROUP \
  --autoscale-name autoscale-$APP_NAME \
  --condition "CpuPercentage > 70 avg 5m" \
  --scale out 1
```

## 🐛 Solución de Problemas

### La app no se conecta a Azure OpenAI:
- Verificar que el endpoint incluye el `/` al final
- Confirmar que la API key es correcta
- Verificar que el deployment name existe

### No encuentra documentos:
- Verificar el nombre del índice
- Confirmar que hay documentos indexados
- Revisar los campos del índice

### Error 500:
```bash
# Ver logs detallados
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# Verificar configuración
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME
```

## 📝 Estructura del Proyecto

```
havas-chatbot/
├── package.json          # Dependencias de Node.js
├── app.js               # Servidor Express principal
├── .env                 # Variables de entorno (no subir a Git)
├── .env.example         # Plantilla de variables
├── public/              # Archivos estáticos
│   ├── index.html       # Interfaz principal
│   ├── css/
│   │   └── styles.css   # Estilos
│   └── js/
│       └── chat.js      # Lógica del cliente
└── README.md            # Este archivo
```

## 🆘 Soporte

Para soporte interno, contactar al equipo de IT de HAVAS.

## 📄 Licencia

Proprietary - HAVAS Group

---

**Desarrollado con ❤️ por el equipo de innovación de HAVAS**