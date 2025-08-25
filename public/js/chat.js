// Chat functionality con soporte para Markdown
class HavasChat {
    constructor() {
        this.messagesArea = document.getElementById('messagesArea');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.statusText = document.getElementById('statusText');
        this.docsCounter = document.getElementById('docsCounter');
        this.docsCount = document.getElementById('docsCount');
        
        this.initializeEventListeners();
        this.loadMarkdownRenderer();
        this.checkHealth();
    }
    
    // Cargar la librería de Markdown
    async loadMarkdownRenderer() {
        try {
            // Cargar marked.js desde CDN
            if (!window.marked) {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js';
                script.onload = () => {
                    console.log('✅ Markdown renderer loaded');
                    // Configurar marked para ser más seguro
                    if (window.marked) {
                        marked.setOptions({
                            breaks: true,
                            gfm: true,
                            sanitize: false // Lo manejaremos manualmente
                        });
                    }
                };
                document.head.appendChild(script);
            }
        } catch (error) {
            console.error('Error loading markdown renderer:', error);
        }
    }
    
    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize del textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + 'px';
        });
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('Azure AI Connected', true);
                if (data.services) {
                    console.log('Services status:', data.services);
                }
            } else {
                this.updateStatus('Connection issue', false);
                console.error('Health check failed:', data);
            }
        } catch (error) {
            this.updateStatus('Disconnected', false);
            console.error('Health check failed:', error);
        }
    }
    
    updateStatus(text, isConnected) {
        this.statusText.textContent = text;
        const statusDot = document.querySelector('.status-dot');
        statusDot.style.background = isConnected ? '#00ff00' : '#ff0000';
        statusDot.style.boxShadow = `0 0 10px ${isConnected ? '#00ff00' : '#ff0000'}`;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Clear welcome message if exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Add user message
        this.addMessage(message, 'user');
        
        // Clear input and disable send button
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.sendButton.disabled = true;
        this.messageInput.disabled = true;
        
        // Show typing indicator
        this.showTyping();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.hideTyping();
                this.addMessage(data.response, 'assistant', true); // true para markdown
                
                // Update documents counter if applicable
                if (data.documentsFound > 0) {
                    this.docsCounter.style.display = 'flex';
                    this.docsCount.textContent = data.documentsFound;
                    
                    // Show context indicator
                    if (data.hasContext) {
                        const contextIndicator = document.createElement('div');
                        contextIndicator.className = 'context-indicator';
                        contextIndicator.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14,2 14,8 20,8"/>
                            </svg>
                            Respuesta basada en documentos encontrados
                        `;
                        
                        const lastMessage = this.messagesArea.lastElementChild;
                        if (lastMessage && lastMessage.classList.contains('assistant')) {
                            const messageContent = lastMessage.querySelector('.message-content');
                            if (messageContent) {
                                messageContent.appendChild(contextIndicator);
                            }
                        }
                    }
                    
                    // Hide counter after 5 seconds
                    setTimeout(() => {
                        this.docsCounter.style.display = 'none';
                    }, 5000);
                }
            } else {
                throw new Error(data.error || 'Error en el servidor');
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage(
                '❌ Lo siento, ocurrió un error al procesar tu mensaje. Por favor, **intenta de nuevo** en unos momentos.\n\n*Si el problema persiste, contacta con el soporte técnico.*',
                'assistant',
                true
            );
            console.error('Error:', error);
            
            // Show reconnection status
            this.updateStatus('Error - Reconnecting...', false);
            setTimeout(() => this.checkHealth(), 2000);
            
        } finally {
            this.sendButton.disabled = false;
            this.messageInput.disabled = false;
            this.messageInput.focus();
        }
    }
    
    // Función para sanitizar HTML básico
    sanitizeHtml(html) {
        const temp = document.createElement('div');
        temp.textContent = html;
        return temp.innerHTML
            .replace(/&lt;(\/?(?:b|strong|i|em|u|code|pre|h[1-6]|p|br|ul|ol|li|blockquote|mark))&gt;/g, '<$1>')
            .replace(/&lt;\/(\w+)&gt;/g, '</$1>');
    }
    
    // Función mejorada para renderizar Markdown
    renderMarkdown(text) {
        if (!window.marked) {
            // Fallback: renderizado básico si marked no está disponible
            return this.basicMarkdownRender(text);
        }
        
        try {
            let html = marked.parse(text);
            
            // Sanitización básica (permitir solo tags seguros)
            const allowedTags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'mark'];
            
            // Remover scripts y eventos peligrosos
            html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            html = html.replace(/on\w+="[^"]*"/gi, '');
            html = html.replace(/javascript:/gi, '');
            
            return html;
        } catch (error) {
            console.error('Error rendering markdown:', error);
            return this.basicMarkdownRender(text);
        }
    }
    
    // Renderizado básico de Markdown como fallback
    basicMarkdownRender(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n/g, '<br>');
    }
    
    addMessage(text, sender, useMarkdown = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} fade-in`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (useMarkdown && sender === 'assistant') {
            contentDiv.innerHTML = this.renderMarkdown(text);
            // Enhance tables after rendering
            this.enhanceTablesInMessage(contentDiv);
        } else {
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(contentDiv);
        this.messagesArea.appendChild(messageDiv);
        
        // Scroll to bottom con animación suave
        setTimeout(() => {
            this.messagesArea.scrollTo({
                top: this.messagesArea.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
        
        // Animar la entrada del mensaje
        setTimeout(() => {
            messageDiv.classList.add('visible');
        }, 50);
    }
    
    showTyping() {
        this.typingIndicator.classList.add('active');
        setTimeout(() => {
            this.messagesArea.scrollTo({
                top: this.messagesArea.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }
    
    hideTyping() {
        this.typingIndicator.classList.remove('active');
    }
    
    // Función para debug del índice
    async debugIndex() {
        try {
            const response = await fetch('/api/debug/index');
            const data = await response.json();
            console.log('🔍 Index Debug Info:', data);
            return data;
        } catch (error) {
            console.error('Error getting index debug info:', error);
        }
    }
    
    // Adaptive table enhancement similar to ChatGPT
    enhanceTablesInMessage(messageDiv) {
        const tables = messageDiv.querySelectorAll('table');

        tables.forEach(table => {
            // Remove inline styles from previous passes
            table.removeAttribute('style');

            // Count rows for compact class
            const bodyRows = table.querySelectorAll('tbody tr').length || table.querySelectorAll('tr').length;
            if (bodyRows > 0 && bodyRows <= 4) {
                table.classList.add('compact');
            }

            // Wrap table only if scrollable (defer until next frame to ensure dimensions)
            requestAnimationFrame(() => {
                const needsHorizontal = table.scrollWidth > table.clientWidth;
                const needsVertical = table.scrollHeight > 400; // threshold like CSS max-height

                const alreadyWrapped = table.parentElement.classList.contains('table-wrapper');
                if (!alreadyWrapped && (needsHorizontal || needsVertical)) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-wrapper scrollable';
                    table.parentNode.insertBefore(wrapper, table);
                    wrapper.appendChild(table);
                } else if (!alreadyWrapped) {
                    // Still wrap for consistent radius/shadow, but without scroll class
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-wrapper';
                    table.parentNode.insertBefore(wrapper, table);
                    wrapper.appendChild(table);
                } else if (alreadyWrapped) {
                    // Toggle scrollable class depending on need
                    table.parentElement.classList.toggle('scrollable', (needsHorizontal || needsVertical));
                }
            });
        });
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const chat = new HavasChat();
    
    // Add connection check every 30 seconds
    setInterval(() => {
        chat.checkHealth();
    }, 30000);
    
    // Add debug command in console
    window.debugHavasIndex = () => chat.debugIndex();
    
    console.log('🚀 HAVAS Chat initialized');
    console.log('💡 Use debugHavasIndex() in console to see index structure');
});