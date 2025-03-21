/**
 * connected_chatManager.js
 * チャットインターフェイスとメッセージ管理を担当するクラス
 * ChatGPT風UI対応およびファイル表示機能との連携強化
 */

export class ChatManager {
    constructor(sendCallback) {
        this.sendCallback = sendCallback; // メッセージ送信時のコールバック関数
        this.chatMessages = null; // チャットメッセージコンテナ
        this.userInput = null; // ユーザー入力フィールド
        this.sendButton = null; // 送信ボタン
        this.clearButton = null; // クリアボタン
        this.autoScrollEnabled = true; // 自動スクロールフラグ
        this.messageTemplate = null; // メッセージテンプレート
        
        // コードハイライト設定
        this.enableCodeHighlight = true;
        this.highlightLanguages = ['python', 'javascript', 'typescript', 'bash', 'json', 'html', 'css', 'java', 'c', 'cpp'];
    }

    // 初期化処理
    init() {
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-btn');
        this.clearButton = document.getElementById('clear-btn');
        this.messageTemplate = document.getElementById('message-template');
        
        // メッセージの送信イベント
        this.sendButton.addEventListener('click', () => {
            const message = this.userInput.value.trim();
            if (message) {
                this.sendCallback(message);
                this.userInput.value = '';
                this.userInput.style.height = 'auto'; // テキストエリアの高さをリセット
            }
        });

        // Enterキーでの送信（Shift+Enterは改行）
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendButton.click();
            }
        });

        // テキストエリアの高さ自動調整
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = (this.userInput.scrollHeight) + 'px';
        });
        
        // メッセージのクリア
        this.clearButton.addEventListener('click', () => {
            this.clearMessages();
        });
        
        // スクロールイベントでのオートスクロール制御
        this.chatMessages.addEventListener('scroll', () => {
            const { scrollTop, scrollHeight, clientHeight } = this.chatMessages;
            const isNearBottom = scrollHeight - scrollTop - clientHeight < 50;
            document.getElementById('auto-scroll').checked = isNearBottom;
            this.autoScrollEnabled = isNearBottom;
        });
        
        // オートスクロールチェックボックスの変更イベント
        document.getElementById('auto-scroll').addEventListener('change', (e) => {
            this.autoScrollEnabled = e.target.checked;
            if (this.autoScrollEnabled) {
                this.scrollToBottom();
            }
        });
        
        // チャットメッセージコンテナのクリック処理
        this.chatMessages.addEventListener('click', this.handleMessageClick.bind(this));
    }

    // ユーザーメッセージを追加
    addUserMessage(message, scroll = true) {
        this.createMessageElement('user', message, scroll);
    }

    // AIメッセージを追加
    addAIMessage(message, scroll = true) {
        this.createMessageElement('assistant', message, scroll);
    }

    // システムメッセージを追加
    addSystemMessage(message, scroll = true) {
        const element = document.createElement('div');
        element.className = 'message system-message';
        element.textContent = message;
        
        this.chatMessages.appendChild(element);
        
        if (scroll && this.autoScrollEnabled) {
            this.scrollToBottom();
        }
    }

    // メッセージ要素を作成
    createMessageElement(role, content, scroll = true) {
        let messageElement;
        
        // テンプレートが利用可能ならそれを使用
        if (this.messageTemplate && 'content' in document.createElement('template')) {
            messageElement = this.messageTemplate.content.cloneNode(true).firstElementChild;
        } else {
            // テンプレートが利用できない場合は手動でDOM要素を作成
            messageElement = document.createElement('div');
            messageElement.className = 'message';
            
            const messageHeader = document.createElement('div');
            messageHeader.className = 'message-header';
            
            const messageAvatar = document.createElement('div');
            messageAvatar.className = 'message-avatar';
            
            const messageRole = document.createElement('div');
            messageRole.className = 'message-role';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            messageHeader.appendChild(messageAvatar);
            messageHeader.appendChild(messageRole);
            messageElement.appendChild(messageHeader);
            messageElement.appendChild(messageContent);
        }
        
        // ロールに基づいたスタイル設定
        messageElement.classList.add(`${role}-message`);
        
        // アバターの設定
        const avatar = messageElement.querySelector('.message-avatar');
        if (avatar) {
            if (role === 'user') {
                avatar.textContent = 'U';
            } else if (role === 'assistant') {
                avatar.textContent = 'AI';
            }
        }
        
        // ロール名の設定
        const roleDisplay = messageElement.querySelector('.message-role');
        if (roleDisplay) {
            roleDisplay.textContent = role === 'user' ? this.getTranslation('user', 'ユーザー') : this.getTranslation('assistant', 'アシスタント');
        }
        
        // メッセージ内容を設定
        const contentElement = messageElement.querySelector('.message-content');
        if (contentElement) {
            // マークダウン処理とコードブロックのハイライト
            contentElement.innerHTML = this.processMessageContent(content);
            
            // コードブロックのハイライト処理
            if (this.enableCodeHighlight && window.hljs) {
                const codeBlocks = contentElement.querySelectorAll('pre code');
                codeBlocks.forEach(block => {
                    window.hljs.highlightElement(block);
                });
            }
        }
        
        // メッセージリストに追加
        this.chatMessages.appendChild(messageElement);
        
        // 自動スクロールが有効な場合は最下部にスクロール
        if (scroll && this.autoScrollEnabled) {
            this.scrollToBottom();
        }
        
        // 生成ファイル情報を抽出して処理
        this.processGeneratedFiles(content);
        
        return messageElement;
    }
    
    // メッセージからファイル生成情報を抽出して処理
    processGeneratedFiles(content) {
        // ファイルパスの抽出（`ファイル名が生成されました`、`ファイルが作成されました`などのパターン）
        const filePatterns = [
            /`([^`]+\.[a-z]{1,5})`\s*(を|が)(生成|作成)(されました|しました)/g,
            /新しいファイル: `([^`]+\.[a-z]{1,5})`/g,
            /ファイル `([^`]+\.[a-z]{1,5})` を作成しました/g,
            /Created file `([^`]+\.[a-z]{1,5})`/g,
            /Generated file `([^`]+\.[a-z]{1,5})`/g
        ];
        
        let matches = [];
        filePatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                matches.push(match[1]); // マッチしたファイル名
            }
        });
        
        // ファイルが見つかった場合、ファイルビューワーに通知
        if (matches.length > 0 && window.enhancedFilesViewer) {
            matches.forEach(filename => {
                // ファイル生成情報をビューワーに追加
                window.enhancedFilesViewer.addFile({
                    filename: filename,
                    content_preview: `AIによって生成されたファイル`,
                    timestamp: new Date().toISOString()
                });
            });
            
            // 通知
            if (matches.length === 1) {
                this.showNotification(`ファイル ${matches[0]} が生成されました`);
            } else {
                this.showNotification(`${matches.length}個のファイルが生成されました`);
            }
        }
    }
    
    // 通知を表示
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'chat-notification';
        notification.textContent = message;
        
        // スタイル設定
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '80px',
            right: '20px',
            backgroundColor: 'rgba(16, 163, 127, 0.9)',
            color: 'white',
            padding: '10px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '1000',
            transition: 'opacity 0.3s ease',
            fontSize: '14px',
            fontWeight: '500'
        });
        
        // bodyに追加
        document.body.appendChild(notification);
        
        // 3秒後に消える
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentElement) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // マークダウンとコードブロックを処理
    processMessageContent(content) {
        if (!content) return '';
        
        // コードブロックを処理
        const codeBlockRegex = /```([\w]+)?\n([\s\S]*?)```/g;
        let processedContent = content.replace(codeBlockRegex, (match, language, code) => {
            const langClass = language ? ` class="language-${language}"` : '';
            return `<pre><code${langClass}>${this.escapeHTML(code)}</code></pre>`;
        });
        
        // インラインコードを処理
        const inlineCodeRegex = /`([^`]+)`/g;
        processedContent = processedContent.replace(inlineCodeRegex, '<code>$1</code>');
        
        // 改行を<br>に変換
        processedContent = processedContent.replace(/\n/g, '<br>');
        
        return processedContent;
    }
    
    // HTML特殊文字をエスケープ
    escapeHTML(text) {
        const escapeMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return text.replace(/[&<>"']/g, char => escapeMap[char]);
    }

    // メッセージをすべてクリア
    clearMessages() {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = '';
        }
    }

    // 最下部にスクロール
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    // メッセージクリックイベント処理
    handleMessageClick(e) {
        // コードブロッククリックでコピー
        if (e.target.tagName === 'CODE' || e.target.tagName === 'PRE' || 
            e.target.parentElement.tagName === 'CODE' || e.target.parentElement.tagName === 'PRE') {
            
            // クリックされた要素またはその親からコードを取得
            let codeElement = e.target;
            if (e.target.tagName !== 'CODE' && e.target.tagName !== 'PRE') {
                codeElement = e.target.closest('code') || e.target.closest('pre');
            }
            
            if (codeElement) {
                // ダブルクリックでコピー
                if (e.detail === 2) {
                    const code = codeElement.textContent;
                    navigator.clipboard.writeText(code)
                        .then(() => this.showCodeCopiedStatus(codeElement))
                        .catch(err => console.error('コードのコピーに失敗:', err));
                }
            }
        }
        
        // ファイルリンクのクリック処理
        const fileLink = e.target.closest('[data-file-path]');
        if (fileLink) {
            const filePath = fileLink.dataset.filePath;
            if (filePath && window.app && typeof window.app.handleFileClick === 'function') {
                window.app.handleFileClick(filePath);
            }
        }
    }
    
    // コードコピー成功表示
    showCodeCopiedStatus(element) {
        // 一時的な通知要素を作成
        const notification = document.createElement('div');
        notification.textContent = this.getTranslation('code_copied', 'コードをコピーしました');
        notification.className = 'code-copied-notification';
        
        // スタイル設定
        Object.assign(notification.style, {
            position: 'absolute',
            top: '0',
            right: '0',
            backgroundColor: 'rgba(16, 163, 127, 0.9)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            zIndex: '10',
            opacity: '0',
            transition: 'opacity 0.3s ease'
        });
        
        // コード要素に追加
        const container = element.parentElement;
        if (container) {
            // 位置調整のために相対位置指定
            if (getComputedStyle(container).position === 'static') {
                container.style.position = 'relative';
            }
            
            container.appendChild(notification);
            
            // フェードイン
            setTimeout(() => {
                notification.style.opacity = '1';
                
                // 2秒後にフェードアウト
                setTimeout(() => {
                    notification.style.opacity = '0';
                    
                    // アニメーション後に削除
                    setTimeout(() => {
                        if (notification.parentElement) {
                            notification.parentElement.removeChild(notification);
                        }
                    }, 300);
                }, 2000);
            }, 10);
        }
    }
    
    // 翻訳テキストを取得
    getTranslation(key, defaultText) {
        // グローバルな翻訳関数が利用可能なら使用
        if (typeof t === 'function') {
            return t(key) || defaultText;
        }
        return defaultText;
    }
}
