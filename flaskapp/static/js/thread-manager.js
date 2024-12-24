class ThreadManager {
    constructor() {
        this.messages = [];
        this.loadMessages();
    }

    loadMessages() {
        fetch('/companion/history')
            .then(response => response.json())
            .then(data => {
                if (data.messages) {
                    this.messages = data.messages;
                    this.renderMessages();
                }
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                this.showError('Error loading messages');
            });
    }

    renderMessages() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        chatMessages.innerHTML = '';
        
        if (this.messages.length > 0) {
            this.messages.forEach(message => {
                this.addMessage(message);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            chatMessages.innerHTML = `
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="h-10 w-10 rounded-full bg-primary-500 flex items-center justify-center">
                            <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                        </div>
                    </div>
                    <div class="ml-3">
                        <div class="bg-white rounded-lg shadow-sm p-4 max-w-lg">
                            <p class="text-gray-900">Hello! I'm your AI companion. How can I help you today?</p>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    addMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start ' + (message.type === 'user' ? 'justify-end' : '');
        
        const content = `
            ${message.type === 'user' ? '' : `
            <div class="flex-shrink-0">
                <div class="h-10 w-10 rounded-full bg-primary-500 flex items-center justify-center">
                    <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </div>
            </div>
            `}
            <div class="${message.type === 'user' ? 'mr-3' : 'ml-3'}">
                <div class="${message.type === 'user' ? 'bg-primary-600 text-white' : 'bg-white'} rounded-lg shadow-sm p-4 max-w-lg">
                    <p class="${message.type === 'user' ? 'text-white' : 'text-gray-900'}">${message.content}</p>
                </div>
                ${message.audio_url ? `
                <div class="mt-2">
                    <audio controls src="${message.audio_url}" class="w-full"></audio>
                </div>
                ` : ''}
            </div>
        `;
        
        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async sendMessage(message) {
        if (!message.trim()) return;

        const requestId = crypto.randomUUID();
        const timestamp = Date.now();

        this.addMessage({
            content: message,
            type: 'user',
            timestamp: new Date()
        });

        try {
            const response = await fetch('/companion/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    request_id: requestId
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            this.addMessage({
                content: 'Processing your message...',
                type: 'ai',
                timestamp: new Date()
            });

        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Error sending message');
        }
    }

    showError(message) {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;

        const alert = document.createElement('div');
        alert.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4';
        alert.role = 'alert';
        
        alert.innerHTML = `
            <span class="block sm:inline">${message}</span>
            <span class="absolute top-0 bottom-0 right-0 px-4 py-3">
                <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                    <title>Close</title>
                    <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
                </svg>
            </span>
        `;
        
        alertContainer.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }
}
