/**
 * tool_usage_visualizer.js
 * AIモデルのツール使用状況を視覚的に表示するコンポーネント
 */

class ToolUsageVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container element with ID "${containerId}" not found.`);
            return;
        }
        
        this.options = Object.assign({
            animationDuration: 500,
            maxHistoryItems: 10,
            language: 'ja-JP'
        }, options);
        
        // 言語設定
        this.currentLanguage = this.options.language;
        
        // ツール使用履歴
        this.toolHistory = [];
        
        // 初期化
        this.initialize();
    }
    
    /**
     * コンポーネントの初期化
     */
    initialize() {
        // コンテナクラスの追加
        this.container.classList.add('tool-usage-visualizer');
        
        // UI要素の作成
        this.container.innerHTML = `
            <div class="tool-usage-header">
                <h3>${this.translate('tool_usage_visualization')}</h3>
            </div>
            <div class="tool-usage-content">
                <div class="tool-current-container">
                    <h4>${this.translate('current_operation')}</h4>
                    <div class="tool-current-operation"></div>
                </div>
                <div class="tool-history-container">
                    <h4>${this.translate('operation_history')}</h4>
                    <div class="tool-history-list"></div>
                </div>
            </div>
        `;
        
        // 要素の参照を保持
        this.currentOperationElement = this.container.querySelector('.tool-current-operation');
        this.historyListElement = this.container.querySelector('.tool-history-list');
    }
    
    /**
     * ツール使用の表示
     * @param {Object} toolData ツールデータ
     */
    showToolUsage(toolData) {
        // データの検証
        if (!toolData || !toolData.type) {
            console.error('Invalid tool data provided:', toolData);
            return;
        }
        
        // 現在の操作を表示
        this.renderCurrentOperation(toolData);
        
        // 履歴に追加
        this.addToHistory(toolData);
    }
    
    /**
     * 現在の操作を表示
     * @param {Object} toolData ツールデータ
     */
    renderCurrentOperation(toolData) {
        // ツールタイプに応じたテンプレートの取得
        const template = this.getToolTemplate(toolData);
        
        // 現在の操作要素に設定
        this.currentOperationElement.innerHTML = template;
        
        // アニメーション効果
        this.currentOperationElement.style.opacity = '0';
        this.currentOperationElement.style.transform = 'translateY(-10px)';
        
        // アニメーション
        setTimeout(() => {
            this.currentOperationElement.style.opacity = '1';
            this.currentOperationElement.style.transform = 'translateY(0)';
        }, 10);
        
        // ツール固有のアニメーション
        this.applyToolSpecificAnimations(toolData);
    }
    
    /**
     * 履歴に操作を追加
     * @param {Object} toolData ツールデータ
     */
    addToHistory(toolData) {
        // 履歴データに追加
        this.toolHistory.unshift({
            ...toolData,
            timestamp: new Date()
        });
        
        // 最大履歴数を超えた場合、古いものを削除
        if (this.toolHistory.length > this.options.maxHistoryItems) {
            this.toolHistory.pop();
        }
        
        // 履歴表示を更新
        this.updateHistoryDisplay();
    }
    
    /**
     * 履歴表示の更新
     */
    updateHistoryDisplay() {
        // 履歴リストをクリア
        this.historyListElement.innerHTML = '';
        
        // 履歴アイテムを追加
        this.toolHistory.forEach((historyItem, index) => {
            const historyElement = document.createElement('div');
            historyElement.className = 'tool-history-item';
            
            // タイムスタンプ
            const timestamp = historyItem.timestamp.toLocaleTimeString();
            
            // ツールアイコンとタイプ
            const toolIcon = this.getToolIcon(historyItem.type);
            const toolType = this.translate(historyItem.type);
            
            // 履歴アイテムの内容
            historyElement.innerHTML = `
                <div class="tool-history-time">${timestamp}</div>
                <div class="tool-history-info">
                    <div class="tool-history-type">
                        <span class="tool-icon">${toolIcon}</span>
                        <span>${toolType}</span>
                    </div>
                    <div class="tool-history-detail">${this.getHistoryDetail(historyItem)}</div>
                </div>
            `;
            
            // 追加時のアニメーション
            historyElement.style.opacity = '0';
            historyElement.style.transform = 'translateX(-10px)';
            
            // 履歴リストに追加
            this.historyListElement.appendChild(historyElement);
            
            // アニメーション
            setTimeout(() => {
                historyElement.style.opacity = '1';
                historyElement.style.transform = 'translateX(0)';
            }, 10 + (index * 50));
        });
        
        // 履歴がない場合
        if (this.toolHistory.length === 0) {
            const emptyElement = document.createElement('div');
            emptyElement.className = 'tool-history-empty';
            emptyElement.textContent = this.translate('no_operations');
            this.historyListElement.appendChild(emptyElement);
        }
    }
    
    /**
     * ツールのテンプレートを取得
     * @param {Object} toolData ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getToolTemplate(toolData) {
        const { type, data } = toolData;
        const toolIcon = this.getToolIcon(type);
        const toolTitle = this.translate(type);
        
        // ベーステンプレート
        let template = `
            <div class="tool-operation tool-${type}">
                <div class="tool-header">
                    <span class="tool-icon">${toolIcon}</span>
                    <h4 class="tool-title">${toolTitle}</h4>
                </div>
                <div class="tool-body">
        `;
        
        // ツールタイプに応じたコンテンツを追加
        switch (type) {
            case 'terminal':
                template += this.getTerminalTemplate(data);
                break;
            case 'browser':
                template += this.getBrowserTemplate(data);
                break;
            case 'file':
                template += this.getFileTemplate(data);
                break;
            case 'api':
                template += this.getApiTemplate(data);
                break;
            case 'database':
                template += this.getDatabaseTemplate(data);
                break;
            default:
                template += this.getDefaultTemplate(data);
        }
        
        // テンプレート終了
        template += `
                </div>
            </div>
        `;
        
        return template;
    }
    
    /**
     * ターミナル操作のテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getTerminalTemplate(data) {
        const { command, directory = '~', status = 'running' } = data;
        const statusText = this.translate(status);
        const statusClass = status === 'success' ? 'success' : 
                           status === 'error' ? 'error' : 'running';
        
        return `
            <div class="terminal-container">
                <div class="terminal-header">
                    <span class="terminal-prompt">$</span>
                    <span class="terminal-directory">${directory}</span>
                </div>
                <div class="terminal-command">${command}</div>
                <div class="terminal-status status-${statusClass}">
                    <span class="status-indicator"></span>
                    <span class="status-text">${statusText}</span>
                </div>
            </div>
        `;
    }
    
    /**
     * ブラウザ操作のテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getBrowserTemplate(data) {
        const { url, title, action = 'navigation' } = data;
        const actionText = this.translate(action);
        
        return `
            <div class="browser-container">
                <div class="browser-header">
                    <span class="browser-action">${actionText}</span>
                </div>
                <div class="browser-address-bar">
                    <span class="browser-url">${url}</span>
                </div>
                ${title ? `<div class="browser-title">${title}</div>` : ''}
            </div>
        `;
    }
    
    /**
     * ファイル操作のテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getFileTemplate(data) {
        const { filename, action = 'read', content = null } = data;
        const actionText = this.translate(action);
        
        return `
            <div class="file-container">
                <div class="file-header">
                    <span class="file-action">${actionText}</span>
                    <span class="file-name">${filename}</span>
                </div>
                ${content ? `
                <div class="file-content">
                    <pre>${content.length > 100 ? content.substring(0, 100) + '...' : content}</pre>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * API操作のテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getApiTemplate(data) {
        const { endpoint, method = 'GET', status = 'pending' } = data;
        const statusText = this.translate(status);
        const statusClass = status === 'success' ? 'success' : 
                           status === 'error' ? 'error' : 'pending';
        
        return `
            <div class="api-container">
                <div class="api-header">
                    <span class="api-method">${method}</span>
                    <span class="api-endpoint">${endpoint}</span>
                </div>
                <div class="api-status status-${statusClass}">
                    <span class="status-indicator"></span>
                    <span class="status-text">${statusText}</span>
                </div>
            </div>
        `;
    }
    
    /**
     * データベース操作のテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getDatabaseTemplate(data) {
        const { query, database = 'DB', action = 'query' } = data;
        const actionText = this.translate(action);
        
        return `
            <div class="database-container">
                <div class="database-header">
                    <span class="database-name">${database}</span>
                    <span class="database-action">${actionText}</span>
                </div>
                <div class="database-query">
                    <pre>${query}</pre>
                </div>
            </div>
        `;
    }
    
    /**
     * デフォルトのテンプレート
     * @param {Object} data ツールデータ
     * @returns {string} HTMLテンプレート
     */
    getDefaultTemplate(data) {
        const description = data.description || this.translate('tool_operation');
        
        return `
            <div class="default-tool-container">
                <div class="tool-description">${description}</div>
                ${data.details ? `<div class="tool-details">${data.details}</div>` : ''}
            </div>
        `;
    }
    
    /**
     * 履歴詳細の取得
     * @param {Object} historyItem 履歴アイテム
     * @returns {string} 履歴詳細テキスト
     */
    getHistoryDetail(historyItem) {
        const { type, data } = historyItem;
        
        switch (type) {
            case 'terminal':
                return data.command || '';
            case 'browser':
                return data.url || '';
            case 'file':
                return `${this.translate(data.action || 'read')} ${data.filename || ''}`;
            case 'api':
                return `${data.method || 'GET'} ${data.endpoint || ''}`;
            case 'database':
                return `${this.translate(data.action || 'query')} ${data.database || 'DB'}`;
            default:
                return data.description || '';
        }
    }
    
    /**
     * ツールアイコンの取得
     * @param {string} toolType ツールタイプ
     * @returns {string} アイコン文字列
     */
    getToolIcon(toolType) {
        const icons = {
            'terminal': '💻',
            'browser': '🌐',
            'file': '📄',
            'api': '🔌',
            'database': '🗃️',
            'search': '🔍',
            'github': '🐙',
            'image': '🖼️',
            'text': '📝',
            'code': '👨‍💻',
            'math': '🧮',
            'default': '🛠️'
        };
        
        return icons[toolType] || icons['default'];
    }
    
    /**
     * ツール固有のアニメーションを適用
     * @param {Object} toolData ツールデータ
     */
    applyToolSpecificAnimations(toolData) {
        const { type, data } = toolData;
        
        // ツールタイプに応じたアニメーション
        switch (type) {
            case 'terminal':
                this.animateTerminal();
                break;
            case 'browser':
                this.animateBrowser();
                break;
            case 'file':
                this.animateFile(data.action);
                break;
            case 'api':
                this.animateApi(data.status);
                break;
        }
    }
    
    /**
     * ターミナルアニメーション
     */
    animateTerminal() {
        const statusIndicator = this.currentOperationElement.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.classList.add('blinking');
        }
    }
    
    /**
     * ブラウザアニメーション
     */
    animateBrowser() {
        const addressBar = this.currentOperationElement.querySelector('.browser-address-bar');
        if (addressBar) {
            addressBar.classList.add('loading');
            
            setTimeout(() => {
                addressBar.classList.remove('loading');
            }, 1500);
        }
    }
    
    /**
     * ファイルアニメーション
     * @param {string} action ファイル操作アクション
     */
    animateFile(action) {
        const fileContainer = this.currentOperationElement.querySelector('.file-container');
        if (fileContainer) {
            fileContainer.classList.add(`file-${action}`);
            
            setTimeout(() => {
                fileContainer.classList.remove(`file-${action}`);
            }, 1500);
        }
    }
    
    /**
     * APIアニメーション
     * @param {string} status API状態
     */
    animateApi(status) {
        const statusIndicator = this.currentOperationElement.querySelector('.status-indicator');
        if (statusIndicator) {
            if (status === 'pending') {
                statusIndicator.classList.add('spinning');
            } else {
                statusIndicator.classList.remove('spinning');
                statusIndicator.classList.add(status === 'success' ? 'success-pulse' : 'error-pulse');
            }
        }
    }
    
    /**
     * 言語設定の変更
     * @param {string} language 言語コード
     */
    setLanguage(language) {
        this.currentLanguage = language;
        
        // ヘッダーのテキストを更新
        const header = this.container.querySelector('.tool-usage-header h3');
        if (header) {
            header.textContent = this.translate('tool_usage_visualization');
        }
        
        // サブヘッダーのテキストを更新
        const currentHeader = this.container.querySelector('.tool-current-container h4');
        if (currentHeader) {
            currentHeader.textContent = this.translate('current_operation');
        }
        
        const historyHeader = this.container.querySelector('.tool-history-container h4');
        if (historyHeader) {
            historyHeader.textContent = this.translate('operation_history');
        }
        
        // 履歴表示を更新
        this.updateHistoryDisplay();
    }
    
    /**
     * 翻訳関数
     * @param {string} key 翻訳キー
     * @returns {string} 翻訳されたテキスト
     */
    translate(key) {
        const translations = {
            'ja-JP': {
                'tool_usage_visualization': 'ツール使用状況',
                'current_operation': '現在の操作',
                'operation_history': '操作履歴',
                'no_operations': '操作履歴はありません',
                'terminal': 'ターミナル',
                'browser': 'ブラウザ',
                'file': 'ファイル',
                'api': 'API',
                'database': 'データベース',
                'search': '検索',
                'github': 'GitHub',
                'image': '画像',
                'text': 'テキスト',
                'code': 'コード',
                'math': '計算',
                'running': '実行中',
                'success': '成功',
                'error': 'エラー',
                'pending': '処理中',
                'navigation': 'ナビゲーション',
                'read': '読み込み',
                'write': '書き込み',
                'create': '作成',
                'update': '更新',
                'delete': '削除',
                'query': 'クエリ',
                'tool_operation': 'ツール操作'
            },
            'en-US': {
                'tool_usage_visualization': 'Tool Usage Status',
                'current_operation': 'Current Operation',
                'operation_history': 'Operation History',
                'no_operations': 'No operation history',
                'terminal': 'Terminal',
                'browser': 'Browser',
                'file': 'File',
                'api': 'API',
                'database': 'Database',
                'search': 'Search',
                'github': 'GitHub',
                'image': 'Image',
                'text': 'Text',
                'code': 'Code',
                'math': 'Math',
                'running': 'Running',
                'success': 'Success',
                'error': 'Error',
                'pending': 'Pending',
                'navigation': 'Navigation',
                'read': 'Read',
                'write': 'Write',
                'create': 'Create',
                'update': 'Update',
                'delete': 'Delete',
                'query': 'Query',
                'tool_operation': 'Tool Operation'
            },
            'zh-CN': {
                'tool_usage_visualization': '工具使用状态',
                'current_operation': '当前操作',
                'operation_history': '操作历史',
                'no_operations': '没有操作历史',
                'terminal': '终端',
                'browser': '浏览器',
                'file': '文件',
                'api': 'API',
                'database': '数据库',
                'search': '搜索',
                'github': 'GitHub',
                'image': '图像',
                'text': '文本',
                'code': '代码',
                'math': '计算',
                'running': '运行中',
                'success': '成功',
                'error': '错误',
                'pending': '处理中',
                'navigation': '导航',
                'read': '读取',
                'write': '写入',
                'create': '创建',
                'update': '更新',
                'delete': '删除',
                'query': '查询',
                'tool_operation': '工具操作'
            }
        };
        
        const language = translations[this.currentLanguage] ? this.currentLanguage : 'en-US';
        return translations[language][key] || key;
    }
    
    /**
     * 履歴のクリア
     */
    clearHistory() {
        this.toolHistory = [];
        this.updateHistoryDisplay();
    }
    
    /**
     * 完了状態の設定
     * @param {string} toolType ツールタイプ
     * @param {string} status 状態 ('success'|'error')
     * @param {Object} resultData 結果データ
     */
    setComplete(toolType, status, resultData = {}) {
        // 現在のツール操作の状態を更新
        const statusElement = this.currentOperationElement.querySelector('.status-indicator');
        const statusTextElement = this.currentOperationElement.querySelector('.status-text');
        
        if (statusElement && statusTextElement) {
            // 状態クラスを更新
            statusElement.classList.remove('blinking', 'spinning');
            statusElement.classList.add(status === 'success' ? 'success-pulse' : 'error-pulse');
            
            // 状態テキストを更新
            statusTextElement.textContent = this.translate(status);
            statusTextElement.parentElement.className = 
                `terminal-status status-${status === 'success' ? 'success' : 'error'}`;
        }
        
        // ツールタイプ固有の完了処理
        switch (toolType) {
            case 'api':
                // APIレスポンスを表示
                if (resultData.response) {
                    const apiContainer = this.currentOperationElement.querySelector('.api-container');
                    if (apiContainer) {
                        const responseElement = document.createElement('div');
                        responseElement.className = 'api-response';
                        responseElement.innerHTML = `
                            <div class="response-header">${this.translate('response')}</div>
                            <pre>${resultData.response}</pre>
                        `;
                        apiContainer.appendChild(responseElement);
                    }
                }
                break;
                
            case 'file':
                // ファイル操作結果を表示
                if (resultData.details) {
                    const fileContainer = this.currentOperationElement.querySelector('.file-container');
                    if (fileContainer) {
                        const detailsElement = document.createElement('div');
                        detailsElement.className = 'file-operation-result';
                        detailsElement.innerHTML = `
                            <div class="result-header">${this.translate('result')}</div>
                            <div class="result-details">${resultData.details}</div>
                        `;
                        fileContainer.appendChild(detailsElement);
                    }
                }
                break;
        }
        
        // 履歴の最新アイテムを更新
        if (this.toolHistory.length > 0) {
            this.toolHistory[0].status = status;
            this.toolHistory[0].resultData = resultData;
            this.updateHistoryDisplay();
        }
    }
}

// グローバルスコープでエクスポート
window.ToolUsageVisualizer = ToolUsageVisualizer;
