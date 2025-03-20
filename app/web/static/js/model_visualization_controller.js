/**
 * model_visualization_controller.js
 * WebUIとWebSocketを介して、モデルの思考プロセスとツール使用状況の可視化を制御するコントローラー
 */

class ModelVisualizationController {
    constructor(options = {}) {
        this.options = Object.assign({
            thinkingContainerId: 'thinking-process-container',
            toolUsageContainerId: 'tool-usage-container',
            language: 'ja-JP',
            webSocketEnabled: true,
            debug: false
        }, options);
        
        this.websocket = null;
        this.sessionId = null;
        this.thinkingVisualizer = null;
        this.toolUsageVisualizer = null;
        this.isInitialized = false;
        
        // ツール使用パターン検出用の正規表現
        this.toolPatterns = {
            terminal: /実行(?:中|します).*?`([^`]+)`|command[:\s]+["|']?([^"|']+)["|']?/i,
            browser: /URL[:\s]+["|']?(https?:\/\/[^\s"']+)["|']?|ブラウザで.*?開(?:きます|いています).*?["|']?(https?:\/\/[^\s"']+)["|']?/i,
            file: /ファイル[:\s]+["|']?([^"']+\.[a-zA-Z0-9]+)["|']?|reading\sfile[:\s]+["|']?([^"']+\.[a-zA-Z0-9]+)["|']?/i,
            api: /API[:\s]+["|']?([^"']+)["|']?|endpoint[:\s]+["|']?([^"']+)["|']?/i,
            github: /GitHub.*?リポジトリ[:\s]+["|']?([^"']+)["|']?|clone.*?["|']?(https:\/\/github\.com\/[^"']+)["|']?/i
        };
        
        // 初期化
        this.initialize();
    }
    
    /**
     * コントローラーの初期化
     */
    initialize() {
        if (this.isInitialized) return;
        
        // コンテナ要素の確認
        if (!document.getElementById(this.options.thinkingContainerId)) {
            const container = document.createElement('div');
            container.id = this.options.thinkingContainerId;
            container.className = 'thinking-process-container';
            
            // 適切な場所に挿入
            const workspaceElement = document.querySelector('.left-panel');
            if (workspaceElement) {
                workspaceElement.appendChild(container);
            } else {
                document.body.appendChild(container);
                console.warn('Left panel not found, appending to body');
            }
        }
        
        if (!document.getElementById(this.options.toolUsageContainerId)) {
            const container = document.createElement('div');
            container.id = this.options.toolUsageContainerId;
            container.className = 'tool-usage-container';
            
            // 適切な場所に挿入
            const workspaceElement = document.querySelector('.left-panel');
            if (workspaceElement) {
                workspaceElement.appendChild(container);
            } else {
                document.body.appendChild(container);
                console.warn('Left panel not found, appending to body');
            }
        }
        
        // スタイルシートの読み込み
        this.loadStylesheet('/static/css/visualizers.css');
        
        // ビジュアライザーの初期化
        this.thinkingVisualizer = new ThinkingProcessVisualizer(
            this.options.thinkingContainerId,
            { 
                language: this.options.language,
                translationEnabled: true
            }
        );
        
        this.toolUsageVisualizer = new ToolUsageVisualizer(
            this.options.toolUsageContainerId,
            { 
                language: this.options.language
            }
        );
        
        // イベントリスナーの追加
        this.attachEventListeners();
        
        this.isInitialized = true;
        this.log('ModelVisualizationController initialized');
    }
    
    /**
     * イベントリスナーの追加
     */
    attachEventListeners() {
        // 言語変更リスナー
        const languageSelector = document.getElementById('language-selector');
        if (languageSelector) {
            languageSelector.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
            });
        }
        
        // チャットメッセージ送信イベント
        const sendButton = document.getElementById('send-btn');
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.onMessageSent();
            });
        }
        
        // WebSockt接続イベントをモンキーパッチする
        if (window.connectWebSocket && this.options.webSocketEnabled) {
            const originalConnectWebSocket = window.connectWebSocket;
            
            window.connectWebSocket = (sessionId) => {
                this.sessionId = sessionId;
                
                // 元の処理を呼び出す
                const result = originalConnectWebSocket(sessionId);
                
                // WebSocketオブジェクトを取得
                setTimeout(() => {
                    this.patchWebSocketHandlers();
                }, 100);
                
                return result;
            };
        }
    }
    
    /**
     * WebSocketハンドラのパッチ適用
     */
    patchWebSocketHandlers() {
        // WebSocketオブジェクトを探す
        if (!window.socket) {
            console.warn('WebSocket object not found');
            return;
        }
        
        this.websocket = window.socket;
        
        // 元のonmessageハンドラを保存
        const originalOnMessage = this.websocket.onmessage;
        
        // onmessageハンドラをオーバーライド
        this.websocket.onmessage = (event) => {
            // データの解析
            const data = JSON.parse(event.data);
            
            // 思考ステップの処理
            if (data.thinking_steps && data.thinking_steps.length > 0) {
                data.thinking_steps.forEach(step => {
                    this.processThinkingStep(step);
                });
            }
            
            // ログの処理
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    this.processLog(log);
                });
            }
            
            // 元のハンドラを呼び出す
            if (originalOnMessage) {
                originalOnMessage.call(this.websocket, event);
            }
        };
    }
    
    /**
     * 思考ステップの処理
     * @param {Object} step 思考ステップデータ
     */
    processThinkingStep(step) {
        // 思考ステップを視覚化コンポーネントに追加
        this.thinkingVisualizer.addThinkingStep(step);
        
        // ツール使用の検出
        this.detectAndVisualizeToolUsage(step);
        
        this.log('Process thinking step:', step);
    }
    
    /**
     * ログの処理
     * @param {Object} log ログデータ
     */
    processLog(log) {
        // ログから必要な情報を抽出
        const { level, message, timestamp } = log;
        
        // レベルに応じたログタイプの設定
        let stepType = 'thinking';
        if (level === 'ERROR') stepType = 'error';
        else if (level === 'WARNING') stepType = 'warning';
        
        // 思考ステップとして追加
        const step = {
            message: message,
            type: stepType,
            timestamp: timestamp
        };
        
        this.thinkingVisualizer.addThinkingStep(step);
        
        // ツール使用の検出
        this.detectAndVisualizeToolUsage(step);
        
        this.log('Process log:', log);
    }
    
    /**
     * ツール使用の検出と視覚化
     * @param {Object} step 思考ステップデータ
     */
    detectAndVisualizeToolUsage(step) {
        const message = step.message;
        
        // ツールタイプの判定
        const toolData = this.extractToolData(message);
        if (toolData) {
            this.toolUsageVisualizer.showToolUsage(toolData);
        }
    }
    
    /**
     * メッセージからツール使用データを抽出
     * @param {string} message メッセージ
     * @returns {Object|null} ツールデータ
     */
    extractToolData(message) {
        // ターミナルコマンドの検出
        let match = this.toolPatterns.terminal.exec(message);
        if (match) {
            const command = match[1] || match[2];
            return {
                type: 'terminal',
                data: {
                    command: command,
                    directory: '~',
                    status: 'running'
                }
            };
        }
        
        // ブラウザアクセスの検出
        match = this.toolPatterns.browser.exec(message);
        if (match) {
            const url = match[1] || match[2];
            return {
                type: 'browser',
                data: {
                    url: url,
                    action: 'navigation'
                }
            };
        }
        
        // ファイル操作の検出
        match = this.toolPatterns.file.exec(message);
        if (match) {
            const filename = match[1] || match[2];
            let action = 'read';
            
            if (message.includes('作成') || message.includes('create')) {
                action = 'create';
            } else if (message.includes('書き込み') || message.includes('write')) {
                action = 'write';
            } else if (message.includes('更新') || message.includes('update')) {
                action = 'update';
            } else if (message.includes('削除') || message.includes('delete')) {
                action = 'delete';
            }
            
            return {
                type: 'file',
                data: {
                    filename: filename,
                    action: action
                }
            };
        }
        
        // API操作の検出
        match = this.toolPatterns.api.exec(message);
        if (match) {
            const endpoint = match[1] || match[2];
            let method = 'GET';
            
            if (message.includes('POST') || message.includes('作成') || message.includes('create')) {
                method = 'POST';
            } else if (message.includes('PUT') || message.includes('更新') || message.includes('update')) {
                method = 'PUT';
            } else if (message.includes('DELETE') || message.includes('削除') || message.includes('delete')) {
                method = 'DELETE';
            }
            
            return {
                type: 'api',
                data: {
                    endpoint: endpoint,
                    method: method,
                    status: 'pending'
                }
            };
        }
        
        // GitHub操作の検出
        match = this.toolPatterns.github.exec(message);
        if (match) {
            const repository = match[1] || match[2];
            return {
                type: 'github',
                data: {
                    repository: repository,
                    description: `GitHub: ${repository}`
                }
            };
        }
        
        // 他のツール操作パターンをここに追加...
        
        // 検出できなかった場合
        if (message.includes('ツール') || message.includes('tool') || 
            message.includes('実行') || message.includes('execute')) {
            return {
                type: 'default',
                data: {
                    description: message
                }
            };
        }
        
        return null;
    }
    
    /**
     * 言語設定の変更
     * @param {string} language 言語コード
     */
    setLanguage(language) {
        this.options.language = language;
        
        // 各ビジュアライザーの言語設定を更新
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.setLanguage(language);
        }
        
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.setLanguage(language);
        }
        
        this.log('Language set to:', language);
    }
    
    /**
     * メッセージ送信時の処理
     */
    onMessageSent() {
        // 実行に必要ないため、このメソッドは空でよい
        // ここにカスタムロジックを追加可能
    }
    
    /**
     * ツール操作の完了状態設定
     * @param {string} toolType ツールタイプ
     * @param {string} status 状態 ('success'|'error')
     * @param {Object} resultData 結果データ
     */
    setToolComplete(toolType, status, resultData = {}) {
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.setComplete(toolType, status, resultData);
        }
    }
    
    /**
     * スタイルシートの読み込み
     * @param {string} href スタイルシートのパス
     */
    loadStylesheet(href) {
        // すでに読み込まれているか確認
        const links = document.getElementsByTagName('link');
        for (let i = 0; i < links.length; i++) {
            if (links[i].rel === 'stylesheet' && links[i].href.includes(href)) {
                return;
            }
        }
        
        // 新しいスタイルシートを読み込む
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = href;
        document.head.appendChild(link);
    }
    
    /**
     * ログ出力（デバッグモードの場合のみ）
     * @param  {...any} args ログ引数
     */
    log(...args) {
        if (this.options.debug) {
            console.log('[ModelVisualizationController]', ...args);
        }
    }
}

// グローバルスコープでエクスポート
window.ModelVisualizationController = ModelVisualizationController;

// DOMの読み込み完了時に自動初期化
document.addEventListener('DOMContentLoaded', () => {
    // すでに初期化済みでなければ初期化
    if (!window.modelVisualizationController) {
        window.modelVisualizationController = new ModelVisualizationController();
    }
});
