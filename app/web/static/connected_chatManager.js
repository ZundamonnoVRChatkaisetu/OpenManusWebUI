// connected_chatManager.js - 处理聊天界面和消息

export class ChatManager {
    constructor(sendMessageCallback) {
        this.chatContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-btn');
        this.sendMessageCallback = sendMessageCallback;
    }

    // 初始化聊天管理器
    init() {
        // 绑定发送按钮点击事件
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // 绑定输入框回车键事件
        this.userInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });

        // 自动调整输入框高度
        this.userInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
        });
    }

    // 发送消息
    sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;

        // 调用回调函数发送消息
        if (this.sendMessageCallback) {
            this.sendMessageCallback(message);
        }

        // 清空输入框
        this.userInput.value = '';
        this.adjustTextareaHeight();
    }

    // 添加用户消息
    addUserMessage(message, scrollToBottom = true) {
        const messageElement = this.createMessageElement('user-message', message);
        this.chatContainer.appendChild(messageElement);
        if (scrollToBottom) {
            this.scrollToBottom();
        }
    }

    // 添加AI消息
    addAIMessage(message, scrollToBottom = true) {
        const messageElement = this.createMessageElement('ai-message', message);
        this.chatContainer.appendChild(messageElement);
        if (scrollToBottom) {
            this.scrollToBottom();
        }
    }

    // 添加系统消息
    addSystemMessage(message, scrollToBottom = true) {
        const messageElement = this.createMessageElement('system-message', message);
        this.chatContainer.appendChild(messageElement);
        if (scrollToBottom) {
            this.scrollToBottom();
        }
    }

    // 创建消息元素
    createMessageElement(className, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;

        // メッセージヘッダーを追加（Claudeライク）
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        // アバターとユーザー名
        const avatar = document.createElement('span');
        avatar.className = 'avatar';
        
        const sender = document.createElement('span');
        sender.className = 'sender';
        
        if (className === 'user-message') {
            avatar.textContent = '👤';
            sender.textContent = 'You';
        } else if (className === 'ai-message') {
            avatar.textContent = '🤖';
            sender.textContent = 'Assistant';
        } else {
            avatar.textContent = '🔔';
            sender.textContent = 'System';
        }
        
        headerDiv.appendChild(avatar);
        headerDiv.appendChild(sender);
        messageDiv.appendChild(headerDiv);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // 处理Markdown格式
        const formattedContent = this.formatMessage(content);
        contentDiv.innerHTML = formattedContent;

        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }

    // 格式化消息内容（处理简单的Markdown）
    formatMessage(content) {
        if (!content) return '';

        // 转义HTML特殊字符
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // 处理代码块
        formatted = formatted.replace(/\`\`\`([^\`]+)\`\`\`/g, '<pre><code>$1</code></pre>');

        // 处理行内代码
        formatted = formatted.replace(/\`([^\`]+)\`/g, '<code>$1</code>');

        // 处理粗体
        formatted = formatted.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

        // 处理斜体
        formatted = formatted.replace(/\*([^\*]+)\*/g, '<em>$1</em>');

        // 处理换行
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    // 清除所有消息
    clearMessages() {
        this.chatContainer.innerHTML = '';
    }

    // 滚动到底部
    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    // 调整输入框高度
    adjustTextareaHeight() {
        this.userInput.style.height = 'auto';
        this.userInput.style.height = (this.userInput.scrollHeight) + 'px';
    }
    
    // チャット履歴の表示
    displayChatHistory(messages) {
        // チャットコンテナをクリア
        this.clearMessages();
        
        // メッセージを時系列順にソート
        const sortedMessages = [...messages].sort((a, b) => {
            return new Date(a.created_at) - new Date(b.created_at);
        });
        
        // 各メッセージを表示
        sortedMessages.forEach(message => {
            if (message.role === 'user') {
                this.addUserMessage(message.content, false);
            } else if (message.role === 'assistant') {
                this.addAIMessage(message.content, false);
            } else if (message.role === 'system') {
                this.addSystemMessage(message.content, false);
            }
        });
        
        // 最後までスクロール
        this.scrollToBottom();
    }
}
