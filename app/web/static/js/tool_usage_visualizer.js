/**
 * tool_usage_visualizer.js
 * AIのツール使用状況をリアルタイムで視覚化するコンポーネント
 * ChatGPT風UIに適合したデザイン
 */

class ToolUsageVisualizer {
    constructor(containerId = 'tool-usage-container') {
        // コンテナ要素
        this.container = document.getElementById(containerId);
        
        // ツール使用状況の履歴
        this.usageHistory = [];
        
        // 現在実行中のツール
        this.activeTools = {};
        
        // 要素が見つからない場合は作成
        this.initializeContainer();
    }
    
    /**
     * コンテナ要素を初期化
     */
    initializeContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'tool-usage-container';
            this.container.className = 'tool-usage-container';
            
            // 適切な場所に挿入（思考プロセスの下）
            const thinkingProcessContainer = document.getElementById('thinking-process-container');
            if (thinkingProcessContainer) {
                thinkingProcessContainer.after(this.container);
            } else {
                const thinkingSection = document.querySelector('.thinking-section');
                if (thinkingSection) {
                    thinkingSection.after(this.container);
                }
            }
        }
        
        // ChatGPTテーマ対応
        const body = document.body;
        if (body.classList.contains('chatgpt-theme')) {
            this.container.classList.add('chatgpt-theme');
        }
        
        // 初期表示は非表示
        this.container.style.display = 'none';
        
        // ヘッダー要素を作成
        this.createHeader();
        
        // スタイル適用
        this.applyStyles();
    }
    
    /**
     * ヘッダー要素を作成
     */
    createHeader() {
        // 既存のヘッダーを削除
        const existingHeader = this.container.querySelector('.tool-usage-header');
        if (existingHeader) {
            existingHeader.remove();
        }
        
        // ヘッダー要素を作成
        const header = document.createElement('div');
        header.className = 'tool-usage-header';
        
        // タイトル
        const title = document.createElement('div');
        title.className = 'tool-usage-title';
        title.innerHTML = `<span class="tool-usage-title-icon">🔧</span> ${this.getTranslation('tool_usage', 'ツール使用状況')}`;
        
        // コントロール
        const controls = document.createElement('div');
        controls.className = 'tool-usage-controls';
        
        // クリアボタン
        const clearBtn = document.createElement('button');
        clearBtn.className = 'tool-usage-clear-btn';
        clearBtn.innerHTML = this.getTranslation('clear', 'クリア');
        clearBtn.addEventListener('click', () => this.clearHistory());
        
        controls.appendChild(clearBtn);
        
        header.appendChild(title);
        header.appendChild(controls);
        
        // コンテナの先頭に追加
        this.container.insertBefore(header, this.container.firstChild);
    }
    
    /**
     * スタイルを適用
     */
    applyStyles() {
        // 既存のスタイルがあるか確認
        let styleElement = document.getElementById('tool-usage-visualizer-styles');
        
        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'tool-usage-visualizer-styles';
            
            styleElement.textContent = `
                .tool-usage-container {
                    margin-bottom: 16px;
                    background-color: var(--panel-bg);
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                
                .tool-usage-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background-color: rgba(255, 171, 46, 0.05);
                    border-bottom: 1px solid var(--border-color);
                }
                
                .tool-usage-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #FFAB2E;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .tool-usage-title-icon {
                    font-size: 16px;
                }
                
                .tool-usage-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .tool-usage-clear-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    color: var(--text-secondary);
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 4px;
                    transition: background-color 0.2s ease;
                }
                
                .tool-usage-clear-btn:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    color: var(--text-color);
                }
                
                .tool-usage-content {
                    padding: 16px;
                }
                
                .tool-execution-item {
                    padding: 10px 12px;
                    margin-bottom: 12px;
                    border-radius: 8px;
                    background-color: rgba(255, 171, 46, 0.05);
                    border-left: 3px solid #FFAB2E;
                    animation: fadeIn 0.3s ease;
                }
                
                .tool-execution-item.complete {
                    border-left-color: #00C48C;
                    background-color: rgba(0, 196, 140, 0.05);
                }
                
                .tool-execution-item.error {
                    border-left-color: #FF3B5C;
                    background-color: rgba(255, 59, 92, 0.05);
                }
                
                .tool-execution-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 6px;
                }
                
                .tool-name {
                    font-weight: 500;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .tool-name-icon {
                    font-size: 16px;
                }
                
                .tool-status {
                    font-size: 12px;
                    color: var(--text-secondary);
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .tool-status.running {
                    color: #FFAB2E;
                    animation: pulse 2s infinite;
                }
                
                .tool-status.success {
                    color: #00C48C;
                }
                
                .tool-status.error {
                    color: #FF3B5C;
                }
                
                .tool-duration {
                    font-size: 11px;
                    color: var(--text-secondary);
                }
                
                .tool-parameters {
                    margin: 8px 0;
                    font-size: 13px;
                    line-height: 1.5;
                    background-color: rgba(0, 0, 0, 0.02);
                    padding: 8px 10px;
                    border-radius: 4px;
                    font-family: monospace;
                    white-space: pre-wrap;
                    max-height: 150px;
                    overflow-y: auto;
                }
                
                .tool-result {
                    margin-top: 8px;
                    font-size: 13px;
                    line-height: 1.5;
                    padding: 8px 0;
                    border-top: 1px dashed rgba(0, 0, 0, 0.1);
                }
                
                .tool-result-content {
                    margin-top: 4px;
                    background-color: rgba(0, 0, 0, 0.02);
                    padding: 8px 10px;
                    border-radius: 4px;
                    font-family: monospace;
                    white-space: pre-wrap;
                    max-height: 150px;
                    overflow-y: auto;
                }
                
                .tool-empty {
                    padding: 16px;
                    text-align: center;
                    color: var(--text-secondary);
                    font-style: italic;
                    font-size: 14px;
                }
                
                /* ツールコール生成アニメーション */
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 0.7; }
                    50% { opacity: 1; }
                }
                
                /* ChatGPTテーマ対応 */
                .chatgpt-theme .tool-usage-title {
                    color: #f5a623;
                }
                
                .chatgpt-theme .tool-execution-item {
                    border-left-color: #f5a623;
                }
                
                .chatgpt-theme .tool-execution-item.complete {
                    border-left-color: #10a37f;
                }
                
                .chatgpt-theme .tool-execution-item.error {
                    border-left-color: #ef4146;
                }
                
                .chatgpt-theme .tool-status.running {
                    color: #f5a623;
                }
                
                .chatgpt-theme .tool-status.success {
                    color: #10a37f;
                }
                
                .chatgpt-theme .tool-status.error {
                    color: #ef4146;
                }
            `;
            
            document.head.appendChild(styleElement);
        }
    }
    
    /**
     * ツール実行の開始を登録
     * @param {string} toolId - ツールID
     * @param {string} toolName - ツール名
     * @param {Object} parameters - ツールパラメーター
     */
    startToolExecution(toolId, toolName, parameters) {
        // コンテナを表示
        this.container.style.display = 'block';
        
        // 実行開始時間
        const startTime = Date.now();
        
        // ツール実行情報をアクティブリストに追加
        this.activeTools[toolId] = {
            id: toolId,
            name: toolName,
            parameters: parameters,
            startTime: startTime,
            status: 'running'
        };
        
        // UIを更新
        this.updateUI();
    }
    
    /**
     * ツール実行の完了を登録
     * @param {string} toolId - ツールID
     * @param {Object} result - ツール実行結果
     * @param {boolean} isError - エラーかどうか
     */
    completeToolExecution(toolId, result, isError = false) {
        // アクティブなツールが存在するか確認
        if (!this.activeTools[toolId]) {
            return;
        }
        
        // ツール情報を取得
        const toolInfo = this.activeTools[toolId];
        
        // 完了時間と所要時間
        const endTime = Date.now();
        const duration = endTime - toolInfo.startTime;
        
        // ツール実行情報を更新
        toolInfo.endTime = endTime;
        toolInfo.duration = duration;
        toolInfo.result = result;
        toolInfo.status = isError ? 'error' : 'success';
        
        // 履歴に追加
        this.usageHistory.push({ ...toolInfo });
        
        // アクティブリストから削除
        delete this.activeTools[toolId];
        
        // UIを更新
        this.updateUI();
    }
    
    /**
     * ツール実行履歴をクリア
     */
    clearHistory() {
        this.usageHistory = [];
        this.activeTools = {};
        this.updateUI();
        
        // アクティブなツールがなければコンテナを非表示
        if (Object.keys(this.activeTools).length === 0) {
            this.container.style.display = 'none';
        }
    }
    
    /**
     * UIを更新
     */
    updateUI() {
        // コンテンツ要素を作成
        let contentElement = this.container.querySelector('.tool-usage-content');
        if (!contentElement) {
            contentElement = document.createElement('div');
            contentElement.className = 'tool-usage-content';
            this.container.appendChild(contentElement);
        }
        
        // コンテンツをクリア
        contentElement.innerHTML = '';
        
        // アクティブなツールを表示
        const activeToolIds = Object.keys(this.activeTools);
        
        // 履歴と合わせてアクティブなツールを表示
        const allItems = [
            ...activeToolIds.map(id => this.activeTools[id]),
            ...this.usageHistory
        ].sort((a, b) => (b.startTime || 0) - (a.startTime || 0));
        
        // 表示項目がなければ空メッセージを表示
        if (allItems.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'tool-empty';
            emptyMessage.textContent = this.getTranslation('no_tool_executions', 'ツール実行履歴はありません');
            contentElement.appendChild(emptyMessage);
            
            // コンテナを非表示
            this.container.style.display = 'none';
            
            return;
        }
        
        // 各ツール実行を表示
        allItems.forEach(tool => {
            const toolElement = document.createElement('div');
            toolElement.className = `tool-execution-item ${tool.status === 'running' ? '' : tool.status === 'error' ? 'error' : 'complete'}`;
            toolElement.dataset.toolId = tool.id;
            
            // ヘッダー（ツール名とステータス）
            const header = document.createElement('div');
            header.className = 'tool-execution-header';
            
            // ツール名とアイコン
            const toolNameElement = document.createElement('div');
            toolNameElement.className = 'tool-name';
            
            // ツールアイコンを取得
            const toolIcon = this.getToolIcon(tool.name);
            toolNameElement.innerHTML = `<span class="tool-name-icon">${toolIcon}</span> ${tool.name}`;
            
            // ステータス表示
            const statusElement = document.createElement('div');
            statusElement.className = `tool-status ${tool.status}`;
            
            if (tool.status === 'running') {
                statusElement.innerHTML = `<span>⏳</span> ${this.getTranslation('running', '実行中')}`;
            } else if (tool.status === 'error') {
                statusElement.innerHTML = `<span>❌</span> ${this.getTranslation('error', 'エラー')}`;
            } else {
                statusElement.innerHTML = `<span>✅</span> ${this.getTranslation('success', '成功')}`;
            }
            
            header.appendChild(toolNameElement);
            header.appendChild(statusElement);
            
            // パラメーター表示
            let parametersHtml = '';
            if (tool.parameters) {
                try {
                    const paramsStr = typeof tool.parameters === 'string' 
                        ? tool.parameters 
                        : JSON.stringify(tool.parameters, null, 2);
                    
                    parametersHtml = `
                        <div class="tool-parameters">${this.escapeHTML(paramsStr)}</div>
                    `;
                } catch (e) {
                    parametersHtml = `
                        <div class="tool-parameters">${this.escapeHTML(String(tool.parameters))}</div>
                    `;
                }
            }
            
            // 所要時間（完了している場合）
            let durationHtml = '';
            if (tool.duration) {
                durationHtml = `
                    <div class="tool-duration">${this.formatDuration(tool.duration)}</div>
                `;
            }
            
            // 結果表示（完了している場合）
            let resultHtml = '';
            if (tool.result) {
                try {
                    const resultStr = typeof tool.result === 'string'
                        ? tool.result
                        : JSON.stringify(tool.result, null, 2);
                    
                    resultHtml = `
                        <div class="tool-result">
                            <div>${this.getTranslation('result', '結果')}:</div>
                            <div class="tool-result-content">${this.escapeHTML(resultStr)}</div>
                        </div>
                    `;
                } catch (e) {
                    resultHtml = `
                        <div class="tool-result">
                            <div>${this.getTranslation('result', '結果')}:</div>
                            <div class="tool-result-content">${this.escapeHTML(String(tool.result))}</div>
                        </div>
                    `;
                }
            }
            
            // ツール要素を組み立て
            toolElement.innerHTML = `
                ${header.outerHTML}
                ${parametersHtml}
                ${durationHtml}
                ${resultHtml}
            `;
            
            contentElement.appendChild(toolElement);
        });
    }
    
    /**
     * ツール名に基づいたアイコンを取得
     * @param {string} toolName - ツール名
     * @returns {string} アイコン文字列
     */
    getToolIcon(toolName) {
        const toolIcons = {
            'github': '📊',
            'brave_web_search': '🔍',
            'brave_local_search': '🔍',
            'search': '🔍',
            'browser': '🌐',
            'python': '🐍',
            'execute': '⚙️',
            'file': '📄',
            'database': '🗃️',
            'image': '🖼️',
            'math': '📐',
            'weather': '🌤️',
            'translate': '🌍',
            'calculator': '🧮'
        };
        
        // ツール名の一部にマッチする正規表現
        for (const [pattern, icon] of Object.entries(toolIcons)) {
            if (toolName.toLowerCase().includes(pattern.toLowerCase())) {
                return icon;
            }
        }
        
        return '🔧'; // デフォルトアイコン
    }
    
    /**
     * ミリ秒を読みやすい形式にフォーマット
     * @param {number} ms - ミリ秒
     * @returns {string} フォーマット済み時間
     */
    formatDuration(ms) {
        if (ms < 1000) {
            return `${ms}ms`;
        } else if (ms < 60 * 1000) {
            return `${(ms / 1000).toFixed(1)}s`;
        } else {
            const minutes = Math.floor(ms / (60 * 1000));
            const seconds = ((ms % (60 * 1000)) / 1000).toFixed(1);
            return `${minutes}m ${seconds}s`;
        }
    }
    
    /**
     * HTML特殊文字をエスケープ
     * @param {string} text - エスケープするテキスト
     * @returns {string} エスケープされたテキスト
     */
    escapeHTML(text) {
        const escapeMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return String(text).replace(/[&<>"']/g, char => escapeMap[char]);
    }
    
    /**
     * 翻訳テキストを取得
     * @param {string} key - 翻訳キー
     * @param {string} defaultText - デフォルトテキスト
     * @returns {string} 翻訳テキスト
     */
    getTranslation(key, defaultText) {
        // グローバルな翻訳関数があれば使用
        if (typeof t === 'function') {
            return t(key) || defaultText;
        }
        return defaultText;
    }
}

// グローバルインスタンスを作成
window.toolUsageVisualizer = new ToolUsageVisualizer();

// DOMのロード完了時に初期化
document.addEventListener('DOMContentLoaded', () => {
    // コンテナが存在するかチェック
    const container = document.getElementById('tool-usage-container');
    
    // コンテナがない場合は作成
    if (!container) {
        window.toolUsageVisualizer = new ToolUsageVisualizer();
    }
});
