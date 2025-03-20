// connected_chatManager.js - 处理聊天界面和消息

export class ChatManager {
    constructor(sendMessageCallback) {
        this.chatContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-btn');
        this.sendMessageCallback = sendMessageCallback;
        this.isWaitingForUserInput = false; // 追加: ユーザー入力待機状態の管理
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
        
        // 追加: フォーカス時にテキストエリアを強調
        this.userInput.addEventListener('focus', () => {
            this.userInput.classList.add('focused');
        });
        
        // 追加: フォーカスが外れたときにテキストエリアの強調を解除
        this.userInput.addEventListener('blur', () => {
            this.userInput.classList.remove('focused');
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
        
        // 追加: ユーザー入力待機状態を解除
        this.isWaitingForUserInput = false;
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
        
        // 追加: モデルが応答したら、入力フィールドにフォーカスして入力を促す
        this.userInput.focus();
        this.isWaitingForUserInput = true; // 追加: ユーザー入力待機状態に設定
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
        this.isWaitingForUserInput = false; // 追加: ユーザー入力待機状態をリセット
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
        
        // 追加: メッセージ履歴の最後がAIからの応答なら、ユーザー入力待機状態に設定
        if (sortedMessages.length > 0 && sortedMessages[sortedMessages.length - 1].role === 'assistant') {
            this.isWaitingForUserInput = true;
            this.userInput.focus();
        }
    }
    
    // 追加: ユーザー入力待機状態を取得
    isWaitingForInput() {
        return this.isWaitingForUserInput;
    }
    
    // 追加: ユーザー入力を促す視覚的な合図を表示
    showInputPrompt() {
        // 入力フィールドの周りに点滅するボーダーを表示するなど
        if (this.isWaitingForUserInput) {
            this.userInput.classList.add('waiting-input');
            // フォーカスを入力フィールドに設定
            this.userInput.focus();
            // プレースホルダーテキストを変更
            this.userInput.placeholder = '続けて指示できます...';
        } else {
            this.userInput.classList.remove('waiting-input');
            this.userInput.placeholder = 'メッセージを入力してください...';
        }
    }
}
