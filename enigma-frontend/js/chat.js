import { apiCall } from './api.js';

function addChatMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message ${sender === 'user' ? 'chat-user' : 'chat-ai'}`;
    div.innerHTML = `<p class="text-sm">${text.replace(/\n/g, '<br>')}</p>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

export function initChat() {
    document.getElementById('chat-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        addChatMessage(message, 'user');
        input.value = '';

        try {
            const data = await apiCall('/brain/chat', {
                method: 'POST',
                body: { message }
            });
            addChatMessage(data.reply, 'ai');
        } catch (e) {}
    });
}
