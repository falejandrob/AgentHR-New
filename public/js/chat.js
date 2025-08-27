// Fonctionnalité de chat avec support Markdown
class HavasChat {
    constructor() {
        this.messagesArea = document.getElementById('messagesArea');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.statusText = document.getElementById('statusText');
        this.docsCounter = document.getElementById('docsCounter');
        this.docsCount = document.getElementById('docsCount');
        this.menuButton = document.getElementById('menuButton');
        this.dropdownMenu = document.getElementById('dropdownMenu');
        this.newChatOption = document.getElementById('newChatOption');
        
        // Pour gérer les requêtes en cours
        this.currentRequest = null;
        this.isTyping = false;
        
        this.initializeEventListeners();
        this.loadMarkdownRenderer();
        this.checkHealth();

    // Gestion de position de l'input
    this.inputSection = document.getElementById('inputSection');
    this.hasStartedConversation = false;
    }
    
    // Charger la bibliothèque Markdown
    async loadMarkdownRenderer() {
        try {
            // Charger marked.js depuis CDN
            if (!window.marked) {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js';
                script.onload = () => {
                    console.log('✅ Rendu Markdown chargé');
                    // Configurer marked pour être plus sûr
                    if (window.marked) {
                        marked.setOptions({
                            breaks: true,
                            gfm: true,
                            sanitize: false // Nous le gérerons manuellement
                        });
                    }
                };
                document.head.appendChild(script);
            }
        } catch (error) {
            console.error('Erreur lors du chargement du rendu markdown:', error);
        }
    }
    
    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Menu button functionality
        this.menuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });
        
        // New chat option
        this.newChatOption.addEventListener('click', () => {
            this.startNewConversation();
            this.hideDropdown();
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdownMenu.contains(e.target) && !this.menuButton.contains(e.target)) {
                this.hideDropdown();
            }
        });
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-redimensionnement du textarea style ChatGPT
        this.messageInput.addEventListener('input', () => {
            // Réinitialiser la hauteur à auto pour obtenir la scrollHeight correcte
            this.messageInput.style.height = 'auto';
            
            // Calculer la nouvelle hauteur basée sur le contenu
            const newHeight = Math.min(this.messageInput.scrollHeight, 200);
            this.messageInput.style.height = newHeight + 'px';
            
            // Mettre à jour l'état du bouton d'envoi
            this.updateSendButtonState();
        });

        // État initial du bouton d'envoi
        this.updateSendButtonState();
    }
    
    // Toggle dropdown menu
    toggleDropdown() {
        const isVisible = this.dropdownMenu.classList.contains('show');
        if (isVisible) {
            this.hideDropdown();
        } else {
            this.showDropdown();
        }
    }
    
    // Show dropdown menu
    showDropdown() {
        this.dropdownMenu.classList.add('show');
        this.menuButton.classList.add('active');
    }
    
    // Hide dropdown menu
    hideDropdown() {
        this.dropdownMenu.classList.remove('show');
        this.menuButton.classList.remove('active');
    }
    
    // Mettre à jour l'état du bouton d'envoi basé sur le contenu de l'input
    updateSendButtonState() {
        const hasContent = this.messageInput.value.trim().length > 0;
        this.sendButton.style.opacity = hasContent ? '1' : '0.5';
        this.sendButton.disabled = !hasContent;
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('Azure AI Connecté', true);
                if (data.services) {
                    console.log('Statut des services:', data.services);
                }
            } else {
                this.updateStatus('Problème de connexion', false);
                console.error('Vérification de santé échouée:', data);
            }
        } catch (error) {
            this.updateStatus('Déconnecté', false);
            console.error('Vérification de santé échouée:', error);
        }
    }
    
    updateStatus(text, isConnected) {
        this.statusText.textContent = text;
        const statusDot = document.querySelector('.status-dot');
        statusDot.style.background = isConnected ? '#00ff00' : '#ff0000';
        statusDot.style.boxShadow = `0 0 10px ${isConnected ? '#00ff00' : '#ff0000'}`;
    }
    
    // Fonction pour initier une nouvelle conversation
    startNewConversation() {
        // Cancelar cualquier request en curso
        if (this.currentRequest) {
            this.currentRequest.abort();
            this.currentRequest = null;
            console.log('🚫 Request cancelada por nueva conversación');
        }

    // Restaurer la position centrée de l'input
    this.restoreCenteredPosition();
        
        // Limpiar estado de typing
        this.hideTyping();
        this.isTyping = false;
        
        // Rehabilitar el input si estaba deshabilitado
        this.messageInput.disabled = false;
        this.updateSendButtonState();
        
        // Nettoyer TOUS les éléments de la zone de messages (y compris welcome-message)
        const allElements = this.messagesArea.querySelectorAll('.message, .welcome-message');
        
        if (allElements.length === 0) {
            // Si aucun élément, ne rien faire (déjà propre)
            return;
        }
        
        allElements.forEach(element => {
            element.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                if (element.parentNode) {
                    element.remove();
                }
            }, 300);
        });
        
        // Restaurer le message de bienvenue après nettoyage
        setTimeout(() => {
            const welcomeMessage = document.createElement('div');
            welcomeMessage.className = 'welcome-message fade-in';
            welcomeMessage.innerHTML = `
                <div class="welcome-icon">👋</div>
                <h3>Bienvenue dans l'Assistant HAVAS!</h3>
                <p>Je suis là pour vous aider avec toute question concernant notre base de connaissances. En quoi puis-je vous assister aujourd'hui ?</p>
            `;
            this.messagesArea.appendChild(welcomeMessage);
            
            // Nettoyer l'input
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
            this.updateSendButtonState();
            this.messageInput.focus();
            
            // Masquer le compteur de documents
            if (this.docsCounter) {
                this.docsCounter.style.display = 'none';
            }
            
            console.log('🔄 Nouvelle conversation démarrée');
        }, 350);
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Si hay una request en curso, cancelarla
        if (this.currentRequest) {
            this.currentRequest.abort();
        }
        
        // Crear nuevo AbortController para esta request
        this.currentRequest = new AbortController();
        
        // Effacer le message de bienvenue s'il existe
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Ajouter le message utilisateur
        this.addMessage(message, 'user');

        // Effacer l'input et désactiver le bouton d'envoi
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateSendButtonState();
        this.messageInput.disabled = true;

        // Afficher l'indicateur de frappe
        this.showTyping();
        this.isTyping = true;

        // Si c'est le premier message, ancrer l'input en bas
        if (!this.hasStartedConversation) {
            this.dockInputSection();
            this.hasStartedConversation = true;
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
                signal: this.currentRequest.signal
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.hideTyping();
                this.isTyping = false;
                this.addMessage(data.response, 'assistant', true); // true pour markdown

                // Mettre à jour le compteur de documents si applicable
                if (data.documentsFound > 0 && this.docsCounter) {
                    this.docsCounter.style.display = 'flex';
                    if (this.docsCount) {
                        this.docsCount.textContent = data.documentsFound;
                    }

                    // Afficher l'indicateur de contexte
                    if (data.hasContext) {
                        const contextIndicator = document.createElement('div');
                        contextIndicator.className = 'context-indicator';
                        contextIndicator.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14,2 14,8 20,8"/>
                            </svg>
                            Réponse basée sur les documents trouvés
                        `;                        const lastMessage = this.messagesArea.lastElementChild;
                        if (lastMessage && lastMessage.classList.contains('assistant')) {
                            const messageContent = lastMessage.querySelector('.message-content');
                            if (messageContent) {
                                messageContent.appendChild(contextIndicator);
                            }
                        }
                    }
                    
                    // Masquer le compteur après 5 secondes
                    if (this.docsCounter) {
                        setTimeout(() => {
                            this.docsCounter.style.display = 'none';
                        }, 5000);
                    }
                }
            } else {
                this.hideTyping();
                this.isTyping = false;
                
                // Mostrar el mensaje de error del servidor si está disponible
                const errorMsg = data.error || data.details || 'Erreur sur le serveur';
                console.error('🚫 Error del servidor:', errorMsg);
                
                this.addMessage(
                    `❌ Erreur du serveur: **${errorMsg}**\n\nVeuillez réessayer dans quelques instants.`,
                    'assistant',
                    true
                );
            }
        } catch (error) {
            // Si la request fue cancelada, no mostrar error
            if (error.name === 'AbortError') {
                console.log('🚫 Request fue cancelada');
                return;
            }
            
            this.hideTyping();
            this.isTyping = false;
            
            console.error('❌ Error en sendMessage:', error);
            
            this.addMessage(
                '❌ Désolé, une erreur s\'est produite lors du traitement de votre message. Veuillez **réessayer** dans quelques instants.\n\n*Si le problème persiste, contactez le support technique.*',
                'assistant',
                true
            );

            // Afficher le statut de reconnexion
            this.updateStatus('Erreur - Reconnexion...', false);
            setTimeout(() => this.checkHealth(), 2000);
        } finally {
            // Solo limpiar el currentRequest si no fue abortado por una nueva conversación
            if (this.currentRequest && !this.currentRequest.signal.aborted) {
                this.currentRequest = null;
            }
            this.messageInput.disabled = false;
            this.updateSendButtonState();
            this.messageInput.focus();
        }
    }
    
    // Ancre l'input en bas (transition centré -> bas)
    dockInputSection() {
        if (!this.inputSection) return;
        this.inputSection.classList.remove('centered');
        void this.inputSection.offsetWidth; // force reflow pour transition
        this.inputSection.classList.add('docked');
    }

    // Restaure la position centrée de l'input (pour nouvelle conversation)
    restoreCenteredPosition() {
        if (!this.inputSection) return;
        this.inputSection.classList.remove('docked');
        void this.inputSection.offsetWidth;
        this.inputSection.classList.add('centered');
        this.hasStartedConversation = false;
    }

    // Fonction pour assainir le HTML de base
    sanitizeHtml(html) {
        const temp = document.createElement('div');
        temp.textContent = html;
        return temp.innerHTML
            .replace(/&lt;(\/?(?:b|strong|i|em|u|code|pre|h[1-6]|p|br|ul|ol|li|blockquote|mark))&gt;/g, '<$1>')
            .replace(/&lt;\/(\w+)&gt;/g, '</$1>');
    }
    
    // Fonction améliorée pour rendre le Markdown
    renderMarkdown(text) {
        if (!window.marked) {
            // Fallback: rendu basique si marked n'est pas disponible
            return this.basicMarkdownRender(text);
        }
        try {
            let html = marked.parse(text);
            // Supprimer les scripts et attributs dangereux
            html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            html = html.replace(/on\w+="[^"]*"/gi, '');
            html = html.replace(/javascript:/gi, '');
            // Filtrer les balises non autorisées (liste blanche simple)
            const allowedTags = ['p','br','strong','b','em','i','u','h1','h2','h3','h4','h5','h6','ul','ol','li','blockquote','code','pre','mark','table','thead','tbody','tr','th','td'];
            html = html.replace(/<(\/)?(\w+)[^>]*>/g, (match, closing, tag) => {
                return allowedTags.includes(tag.toLowerCase()) ? match : '';
            });
            return html;
        } catch (e) {
            console.error('Erreur rendu Markdown:', e);
            return this.basicMarkdownRender(text);
        }
    }
    
    // Rendu basique de Markdown comme fallback
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
        
        // Animer l'entrée du message
        setTimeout(() => {
            messageDiv.classList.add('visible');
        }, 50);
    }
    
    showTyping() {
        this.typingIndicator.classList.add('active');
        this.isTyping = true;
        setTimeout(() => {
            this.messagesArea.scrollTo({
                top: this.messagesArea.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }
    
    hideTyping() {
        this.typingIndicator.classList.remove('active');
        this.isTyping = false;
    }
    
    // Función para debug del índice
    async debugIndex() {
        try {
            const response = await fetch('/api/debug/index');
            const data = await response.json();
            console.log('🔍 Index Debug Info:', data);
            return data;
        } catch (error) {
            console.error('Erreur lors de l\'obtention des informations de débogage de l\'index:', error);
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