// Chat functionality
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
        this.checkHealth();
    }
    
    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('Connected', true);
            } else {
                this.updateStatus('Connection issue', false);
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
        this.sendButton.disabled = true;
        
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
                this.addMessage(data.response, 'assistant');
                
                // Update documents counter if applicable
                if (data.documentsFound > 0) {
                    this.docsCounter.style.display = 'flex';
                    this.docsCount.textContent = data.documentsFound;
                    
                    // Hide counter after 3 seconds
                    setTimeout(() => {
                        this.docsCounter.style.display = 'none';
                    }, 3000);
                }
            } else {
                throw new Error(data.error || 'Error en el servidor');
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage(
                'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo.',
                'assistant'
            );
            console.error('Error:', error);
        } finally {
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} fade-in`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        this.messagesArea.appendChild(messageDiv);
        
        // Scroll to bottom
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }
    
    showTyping() {
        this.typingIndicator.classList.add('active');
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }
    
    hideTyping() {
        this.typingIndicator.classList.remove('active');
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new HavasChat();
    
    // Add connection check every 30 seconds
    setInterval(() => {
        const chat = new HavasChat();
        chat.checkHealth();
    }, 30000);
});