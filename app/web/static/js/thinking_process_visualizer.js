/**
 * thinking_process_visualizer.js
 * モデルの思考プロセスをリアルタイムで視覚化するコンポーネント
 * ChatGPT風UIに適合したデザインとアニメーション効果
 */

class ThinkingProcessVisualizer {
    constructor(containerId = 'thinking-process-container') {
        // コンテナ要素
        this.container = document.getElementById(containerId);
        
        // 思考ステップのリスト
        this.steps = [];
        
        // 現在のステータス
        this.status = 'ready'; // ready, thinking, complete, error
        
        // ステータス表示要素
        this.statusIndicator = document.getElementById('thinking-status');
        
        // アニメーション状態
        this.animationInProgress = false;
        
        // 自動スクロールの状態
        this.autoScroll = true;
        
        // 要素が見つからない場合は作成
        this.initializeContainer();
    }
    
    /**
     * コンテナ要素を初期化
     */
    initializeContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'thinking-process-container';
            this.container.className = 'thinking-process-container';
            
            // 適切な場所に挿入
            const thinkingSection = document.querySelector('.thinking-section');
            if (thinkingSection) {
                const header = thinkingSection.querySelector('.thinking-process-header');
                if (header) {
                    header.after(this.container);
                } else {
                    thinkingSection.prepend(this.container);
                }
            }
        }
        
        // ChatGPTテーマ対応
        const body = document.body;
        if (body.classList.contains('chatgpt-theme')) {
            this.container.classList.add('chatgpt-theme');
        }
        
        // ステータスインジケーターがなければ作成
        if (!this.statusIndicator) {
            this.statusIndicator = document.createElement('div');
            this.statusIndicator.id = 'thinking-status';
            this.statusIndicator.className = 'thinking-status';
            this.statusIndicator.textContent = this.getTranslation('status_ready', '準備完了');
            
            const header = document.querySelector('.thinking-process-header');
            if (header) {
                header.appendChild(this.statusIndicator);
            }
        }
        
        // スタイル適用
        this.applyStyles();
    }
    
    /**
     * スタイルを適用
     */
    applyStyles() {
        // 既存のスタイルがあるか確認
        let styleElement = document.getElementById('thinking-visualizer-styles');
        
        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'thinking-visualizer-styles';
            
            styleElement.textContent = `
                .thinking-process-container {
                    margin-bottom: 16px;
                    font-size: 14px;
                    line-height: 1.5;
                    max-height: 300px;
                    overflow-y: auto;
                    padding-right: 8px;
                }
                
                .thinking-step {
                    margin-bottom: 12px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    background-color: rgba(0, 0, 0, 0.02);
                    border-left: 3px solid #4C6FFF;
                    transition: all 0.3s ease;
                    animation: fadeIn 0.3s ease;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                
                .thinking-step.tool-execution {
                    border-left-color: #FFAB2E;
                    background-color: rgba(255, 171, 46, 0.05);
                }
                
                .thinking-step.tool-result {
                    border-left-color: #00C48C;
                    background-color: rgba(0, 196, 140, 0.05);
                }
                
                .thinking-step.error {
                    border-left-color: #FF3B5C;
                    background-color: rgba(255, 59, 92, 0.05);
                }
                
                .thinking-step.conclusion {
                    border-left-color: #00C48C;
                    background-color: rgba(0, 196, 140, 0.05);
                    font-weight: 500;
                }
                
                .thinking-step-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 4px;
                    font-size: 12px;
                }
                
                .thinking-step-type {
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .thinking-step-type-icon {
                    font-size: 14px;
                }
                
                .thinking-step-time {
                    color: var(--text-secondary);
                    font-size: 11px;
                }
                
                .thinking-step-content {
                    font-size: 13px;
                    line-height: 1.5;
                    white-space: pre-wrap;
                }
                
                .thinking-step-content code {
                    background-color: rgba(0, 0, 0, 0.05);
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 0.9em;
                }
                
                .thinking-step-details {
                    margin-top: 6px;
                    padding-top: 6px;
                    border-top: 1px dashed rgba(0, 0, 0, 0.1);
                    font-size: 12px;
                    line-height: 1.4;
                    color: var(--text-secondary);
                }
                
                .thinking-status {
                    font-size: 12px;
                    padding: 3px 10px;
                    border-radius: 12px;
                    background-color: rgba(16, 163, 127, 0.1);
                    color: #10a37f;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .thinking-status.active {
                    background-color: rgba(16, 163, 127, 0.2);
                    animation: pulse 2s infinite;
                }
                
                .thinking-status.error {
                    background-color: rgba(255, 59, 92, 0.1);
                    color: #FF3B5C;
                }
                
                .thinking-status.complete {
                    background-color: rgba(0, 196, 140, 0.1);
                    color: #00C48C;
                }
                
                .thinking-status-icon {
                    font-size: 14px;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 0.7; }
                    50% { opacity: 1; }
                }
                
                /* チャットGPTテーマ対応 */
                .chatgpt-theme .thinking-step {
                    border-left-color: #10a37f;
                }
                
                .chatgpt-theme .thinking-step.tool-execution {
                    border-left-color: #f5a623;
                }
                
                .chatgpt-theme .thinking-step.tool-result {
                    border-left-color: #10a37f;
                }
                
                .chatgpt-theme .thinking-step.error {
                    border-left-color: #ef4146;
                }
                
                .chatgpt-theme .thinking-step.conclusion {
                    border-left-color: #10a37f;
                }
            `;
            
            document.head.appendChild(styleElement);
        }
    }
    
    /**
     * 思考ステップを追加
     * @param {Object} step - 思考ステップ情報
     * @param {string} step.message - ステップメッセージ
     * @param {string} step.type - ステップタイプ（thinking, tool_execution, tool_result, error, conclusion）
     * @param {Object} step.details - 詳細情報（オプション）
     * @param {number} step.timestamp - タイムスタンプ
     */
    addStep(step) {
        // ステップを保存
        this.steps.push(step);
        
        // ステータスを更新
        this.updateStatus('thinking');
        
        // UIを更新
        this.renderStep(step);
        
        // 自動スクロールが有効なら最下部にスクロール
        if (this.autoScroll) {
            this.scrollToBottom();
        }
        
        // 思考タイムラインにも反映
        this.updateThinkingTimeline();
    }
    
    /**
     * 思考ステップをUIにレンダリング
     * @param {Object} step - 思考ステップ情報
     */
    renderStep(step) {
        // ステップ要素を作成
        const stepElement = document.createElement('div');
        stepElement.className = `thinking-step ${step.type || 'thinking'}`;
        
        // ヘッダー（タイプとタイムスタンプ）
        const header = document.createElement('div');
        header.className = 'thinking-step-header';
        
        // タイプとアイコン
        const typeDisplay = document.createElement('div');
        typeDisplay.className = 'thinking-step-type';
        
        // タイプに基づいたアイコンとラベル
        const typeInfo = this.getTypeInfo(step.type);
        typeDisplay.innerHTML = `<span class="thinking-step-type-icon">${typeInfo.icon}</span> ${typeInfo.label}`;
        
        // タイムスタンプ
        const timeDisplay = document.createElement('div');
        timeDisplay.className = 'thinking-step-time';
        timeDisplay.textContent = this.formatTimestamp(step.timestamp);
        
        header.appendChild(typeDisplay);
        header.appendChild(timeDisplay);
        
        // メッセージ内容
        const content = document.createElement('div');
        content.className = 'thinking-step-content';
        content.innerHTML = this.formatMessage(step.message);
        
        // 詳細情報（あれば）
        if (step.details) {
            const details = document.createElement('div');
            details.className = 'thinking-step-details';
            
            if (typeof step.details === 'string') {
                details.innerHTML = this.formatMessage(step.details);
            } else {
                details.innerHTML = this.formatMessage(JSON.stringify(step.details, null, 2));
            }
            
            stepElement.appendChild(header);
            stepElement.appendChild(content);
            stepElement.appendChild(details);
        } else {
            stepElement.appendChild(header);
            stepElement.appendChild(content);
        }
        
        // アニメーション効果
        stepElement.style.opacity = '0';
        stepElement.style.transform = 'translateY(10px)';
        
        // コンテナに追加
        this.container.appendChild(stepElement);
        
        // アニメーション
        setTimeout(() => {
            stepElement.style.opacity = '1';
            stepElement.style.transform = 'translateY(0)';
        }, 10);
    }
    
    /**
     * ステップタイプに基づいた情報を取得
     * @param {string} type - ステップタイプ
     * @returns {Object} タイプ情報（アイコンとラベル）
     */
    getTypeInfo(type) {
        const types = {
            'thinking': {
                icon: '🧠',
                label: this.getTranslation('thinking', '思考')
            },
            'tool_execution': {
                icon: '🔧',
                label: this.getTranslation('tool_execution', 'ツール実行')
            },
            'tool_result': {
                icon: '📊',
                label: this.getTranslation('tool_result', 'ツール結果')
            },
            'error': {
                icon: '⚠️',
                label: this.getTranslation('error', 'エラー')
            },
            'conclusion': {
                icon: '✅',
                label: this.getTranslation('conclusion', '結論')
            },
            'communication': {
                icon: '💬',
                label: this.getTranslation('communication', '通信')
            }
        };
        
        return types[type] || types['thinking'];
    }
    
    /**
     * メッセージをフォーマット
     * @param {string} message - メッセージ
     * @returns {string} フォーマット済みメッセージ
     */
    formatMessage(message) {
        if (!message) return '';
        
        // コードをハイライト
        let formatted = message.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // URLをリンクに変換
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // ファイル参照をリンクに変換（オプショナル）
        const fileRegex = /(?:ファイル|file): ([^\s]+\.[a-z]{1,5})/g;
        formatted = formatted.replace(fileRegex, '📄 <a href="#" data-file-path="$1">$1</a>');
        
        return formatted;
    }
    
    /**
     * タイムスタンプをフォーマット
     * @param {number} timestamp - UNIXタイムスタンプ
     * @returns {string} フォーマット済みタイムスタンプ
     */
    formatTimestamp(timestamp) {
        if (!timestamp) {
            return '';
        }
        
        try {
            const date = new Date(timestamp * 1000);
            return date.toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return '';
        }
    }
    
    /**
     * ステータスを更新
     * @param {string} status - ステータス（ready, thinking, complete, error）
     */
    updateStatus(status) {
        if (this.status === status) return;
        
        this.status = status;
        
        if (this.statusIndicator) {
            // クラスをリセット
            this.statusIndicator.className = 'thinking-status';
            
            // ステータスに基づいたクラスとテキストを設定
            switch (status) {
                case 'ready':
                    this.statusIndicator.innerHTML = `<span class="thinking-status-icon">⚪</span> ${this.getTranslation('status_ready', '準備完了')}`;
                    break;
                case 'thinking':
                    this.statusIndicator.innerHTML = `<span class="thinking-status-icon">🧠</span> ${this.getTranslation('status_thinking', '思考中...')}`;
                    this.statusIndicator.classList.add('active');
                    break;
                case 'complete':
                    this.statusIndicator.innerHTML = `<span class="thinking-status-icon">✅</span> ${this.getTranslation('status_complete', '完了')}`;
                    this.statusIndicator.classList.add('complete');
                    break;
                case 'error':
                    this.statusIndicator.innerHTML = `<span class="thinking-status-icon">⚠️</span> ${this.getTranslation('status_error', 'エラー')}`;
                    this.statusIndicator.classList.add('error');
                    break;
            }
        }
    }
    
    /**
     * エラーステップを追加
     * @param {string} message - エラーメッセージ
     */
    addError(message) {
        this.addStep({
            message: message,
            type: 'error',
            timestamp: Math.floor(Date.now() / 1000)
        });
        
        this.updateStatus('error');
    }
    
    /**
     * 結論ステップを追加
     * @param {string} message - 結論メッセージ
     */
    addConclusion(message) {
        this.addStep({
            message: message,
            type: 'conclusion',
            timestamp: Math.floor(Date.now() / 1000)
        });
        
        this.updateStatus('complete');
    }
    
    /**
     * すべてのステップをクリア
     */
    clearSteps() {
        this.steps = [];
        this.container.innerHTML = '';
        this.updateStatus('ready');
        this.updateThinkingTimeline();
    }
    
    /**
     * 最下部にスクロール
     */
    scrollToBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }
    
    /**
     * 思考タイムラインを更新
     */
    updateThinkingTimeline() {
        const timeline = document.getElementById('thinking-timeline');
        if (!timeline) return;
        
        // 全ステップをタイムラインに表示
        timeline.innerHTML = '';
        
        this.steps.forEach((step, index) => {
            const timelineStep = document.createElement('div');
            timelineStep.className = `thinking-step ${step.type || 'thinking'}`;
            
            // ヘッダー（タイプとタイムスタンプ）
            const header = document.createElement('div');
            header.className = 'thinking-step-time';
            header.textContent = this.formatTimestamp(step.timestamp);
            
            // メッセージ内容
            const content = document.createElement('div');
            content.className = 'thinking-step-message';
            content.innerHTML = this.formatMessage(step.message);
            
            timelineStep.appendChild(header);
            timelineStep.appendChild(content);
            
            timeline.appendChild(timelineStep);
        });
        
        // 思考ステップの数を更新
        const recordCount = document.getElementById('record-count');
        if (recordCount) {
            recordCount.textContent = this.getTranslation('records_count_value', {count: this.steps.length});
        }
        
        // 自動スクロールチェックボックスが有効な場合はスクロール
        const autoScrollCheckbox = document.getElementById('auto-scroll');
        if (autoScrollCheckbox && autoScrollCheckbox.checked) {
            timeline.scrollTop = timeline.scrollHeight;
        }
    }
    
    /**
     * 翻訳テキストを取得
     * @param {string} key - 翻訳キー
     * @param {string|Object} defaultText - デフォルトテキストまたはパラメータを含むオブジェクト
     * @returns {string} 翻訳済みテキスト
     */
    getTranslation(key, defaultText) {
        // グローバルな翻訳関数が利用可能なら使用
        if (typeof t === 'function') {
            if (typeof defaultText === 'object') {
                return t(key, defaultText) || (defaultText.count !== undefined ? `${defaultText.count} 件` : key);
            }
            return t(key) || defaultText;
        }
        
        // デフォルト値
        if (typeof defaultText === 'object') {
            return defaultText.count !== undefined ? `${defaultText.count} 件` : key;
        }
        return defaultText;
    }
    
    /**
     * 思考ステップを取得
     * @returns {Array} 思考ステップの配列
     */
    getSteps() {
        return this.steps;
    }
    
    /**
     * 現在のステータスを取得
     * @returns {string} ステータス
     */
    getStatus() {
        return this.status;
    }
}

// グローバルインスタンスを作成
window.thinkingProcessVisualizer = new ThinkingProcessVisualizer();

// DOMのロード完了時のイベントリスナー
document.addEventListener('DOMContentLoaded', () => {
    // コンテナが存在するかチェック
    const container = document.getElementById('thinking-process-container');
    
    // コンテナがない場合は作成
    if (!container) {
        window.thinkingProcessVisualizer = new ThinkingProcessVisualizer();
    }
});
