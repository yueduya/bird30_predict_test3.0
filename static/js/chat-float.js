class ChatFloat {
    constructor() {
        this.isOpen = false;
        this.sessionId = null;
        this.token = localStorage.getItem('access_token');
        this.init();
    }

    init() {
        this.createElements();
        this.bindEvents();
    }

    createElements() {
        const btnHtml = `
            <button class="chat-float-btn" id="chatFloatBtn" title="AI 助手">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
            </button>
        `;

        const windowHtml = `
            <div class="chat-float-window" id="chatFloatWindow">
                <div class="chat-header">
                    <span class="chat-header-title">🤖 AI 助手</span>
                    <div class="chat-header-actions">
                        <button class="chat-header-btn" id="chatNewBtn" title="新对话">+</button>
                        <button class="chat-header-btn" id="chatCloseBtn" title="关闭">×</button>
                    </div>
                </div>
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chatInput" placeholder="输入消息..." />
                    <button class="chat-send-btn" id="chatSendBtn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="#0a192f">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', btnHtml);
        document.body.insertAdjacentHTML('beforeend', windowHtml);

        this.btn = document.getElementById('chatFloatBtn');
        this.window = document.getElementById('chatFloatWindow');
        this.messages = document.getElementById('chatMessages');
        this.input = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('chatSendBtn');
        this.closeBtn = document.getElementById('chatCloseBtn');
        this.newBtn = document.getElementById('chatNewBtn');
    }

    bindEvents() {
        this.btn.addEventListener('click', () => this.toggle());
        this.closeBtn.addEventListener('click', () => this.close());
        this.newBtn.addEventListener('click', () => this.newChat());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        this.makeDraggable();
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.window.classList.add('active');
        this.btn.style.display = 'none';
        
        if (!this.token) {
            this.showLoginPrompt();
        } else if (this.messages.children.length === 0) {
            this.addMessage('assistant', '你好！我是 AI 助手，有什么可以帮助你的吗？');
        }
    }

    close() {
        this.isOpen = false;
        this.window.classList.remove('active');
        this.btn.style.display = 'flex';
    }

    newChat() {
        this.sessionId = null;
        this.messages.innerHTML = '';
        this.addMessage('assistant', '你好！我是 AI 助手，有什么可以帮助你的吗？');
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        if (!this.token) {
            this.showLoginPrompt();
            return;
        }

        this.addMessage('user', message);
        this.input.value = '';
        this.sendBtn.disabled = true;

        const assistantDiv = this.createStreamingMessage();

        try {
            const response = await fetch('/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.error) {
                                assistantDiv.textContent = '抱歉，出现了错误：' + data.error;
                                break;
                            }
                            
                            if (data.content) {
                                fullContent += data.content;
                                assistantDiv.textContent = fullContent;
                                this.scrollToBottom();
                            }
                            
                            if (data.done) {
                                this.sessionId = data.session_id;
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                }
            }

            if (!fullContent) {
                assistantDiv.textContent = '抱歉，没有收到回复。';
            }
        } catch (error) {
            assistantDiv.textContent = '网络错误，请检查连接。';
        }

        this.sendBtn.disabled = false;
    }

    createStreamingMessage() {
        const div = document.createElement('div');
        div.className = 'chat-message assistant streaming';
        div.innerHTML = '<span class="cursor-blink">▊</span>';
        this.messages.appendChild(div);
        this.scrollToBottom();
        return div;
    }

    addMessage(role, content) {
        const div = document.createElement('div');
        div.className = `chat-message ${role}`;
        div.textContent = content;
        this.messages.appendChild(div);
        this.scrollToBottom();
    }

    showTyping() {
        const div = document.createElement('div');
        div.className = 'chat-message assistant typing';
        div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        this.messages.appendChild(div);
        this.scrollToBottom();
    }

    hideTyping() {
        const typing = this.messages.querySelector('.typing');
        if (typing) typing.remove();
    }

    showLoginPrompt() {
        this.messages.innerHTML = `
            <div class="chat-login-prompt">
                <p>请先登录以使用 AI 助手</p>
                <a href="/user/login">点击登录</a>
            </div>
        `;
    }

    scrollToBottom() {
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    makeDraggable() {
        const header = this.window.querySelector('.chat-header');
        let isDragging = false;
        let startX, startY, startLeft, startTop;

        header.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            const rect = this.window.getBoundingClientRect();
            startLeft = rect.left;
            startTop = rect.top;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            this.window.style.left = `${startLeft + dx}px`;
            this.window.style.top = `${startTop + dy}px`;
            this.window.style.right = 'auto';
            this.window.style.bottom = 'auto';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatFloat = new ChatFloat();
});
