/**
 * model_visualization_controller.js
 * モデルの思考プロセス・ツール使用状況・生成ファイル表示を統合制御するコントローラー
 * WebSocket通信とのブリッジとして機能し、UIコンポーネントを連携させる
 */

class ModelVisualizationController {
    constructor() {
        // 各種視覚化コンポーネント
        this.thinkingVisualizer = window.thinkingProcessVisualizer;
        this.toolUsageVisualizer = window.toolUsageVisualizer;
        this.filesViewer = window.enhancedFilesViewer || window.generatedFilesViewer;
        
        // セッションID
        this.sessionId = null;
        
        // WebSocketメッセージのキャッシュ
        this.messageCache = [];
        
        // 初期化状態
        this.initialized = false;
        
        // コンポーネントのロードを待機して初期化
        this.waitForComponents();
    }
    
    /**
     * 視覚化コンポーネントのロードを待機して初期化
     */
    waitForComponents() {
        // すべてのコンポーネントが利用可能かチェック
        if (this.thinkingVisualizer && this.toolUsageVisualizer && this.filesViewer) {
            this.initialized = true;
            
            // キャッシュされたメッセージを処理
            this.processMessageCache();
            
            console.log('Model visualization components loaded and initialized');
        } else {
            // 100ms後に再試行
            setTimeout(() => this.waitForComponents(), 100);
        }
    }
    
    /**
     * セッションIDを設定
     * @param {string} sessionId - セッションID
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
    }
    
    /**
     * WebSocketからのメッセージを処理
     * @param {Object} data - WebSocketから受信したデータ
     */
    processWebSocketMessage(data) {
        // まだ初期化されていなければキャッシュに追加
        if (!this.initialized) {
            this.messageCache.push(data);
            return;
        }
        
        // 思考ステップを処理
        if (data.thinking_steps && Array.isArray(data.thinking_steps) && data.thinking_steps.length > 0) {
            this.processThinkingSteps(data.thinking_steps);
        }
        
        // 生成ファイル情報を処理
        if (data.generated_files || data.file_generation_event) {
            this.processFileGenerationEvents(data);
        }
        
        // ステータス変更を処理
        if (data.status) {
            this.processStatusChange(data.status);
        }
        
        // ツール使用状況を処理（実装予定）
        if (data.tool_executions || data.tool_execution) {
            this.processToolExecutions(data);
        }
    }
    
    /**
     * キャッシュされたメッセージを処理
     */
    processMessageCache() {
        if (this.messageCache.length > 0) {
            console.log(`Processing ${this.messageCache.length} cached messages`);
            
            // すべてのキャッシュメッセージを処理
            this.messageCache.forEach(data => this.processWebSocketMessage(data));
            
            // キャッシュをクリア
            this.messageCache = [];
        }
    }
    
    /**
     * 思考ステップの処理
     * @param {Array} steps - 思考ステップの配列
     */
    processThinkingSteps(steps) {
        if (!this.thinkingVisualizer) return;
        
        steps.forEach(step => {
            // ThinkingProcessVisualizerの期待する形式に変換
            const convertedStep = {
                message: step.message || '',
                type: this.mapStepType(step.type),
                details: step.details || null,
                timestamp: step.timestamp || Math.floor(Date.now() / 1000)
            };
            
            // 思考ステップを追加
            this.thinkingVisualizer.addStep(convertedStep);
            
            // ツール実行に関するステップなら、ツール使用状況ビジュアライザーにも反映
            if (this.toolUsageVisualizer && (step.type === 'tool_start' || step.type === 'tool_end')) {
                this.processToolStep(step);
            }
            
            // ファイル生成ステップならファイルビューワーに反映
            if (this.filesViewer && step.type === 'file_generation') {
                this.processFileStep(step);
            }
        });
    }
    
    /**
     * ステップタイプの変換
     * @param {string} type - 元のステップタイプ
     * @returns {string} 変換後のステップタイプ
     */
    mapStepType(type) {
        const typeMap = {
            'thinking': 'thinking',
            'thought': 'thinking',
            'tool_start': 'tool_execution',
            'tool_execution': 'tool_execution',
            'tool_end': 'tool_result',
            'tool_result': 'tool_result',
            'error': 'error',
            'conclusion': 'conclusion',
            'file_generation': 'tool_result',
            'communication': 'communication'
        };
        
        return typeMap[type] || 'thinking';
    }
    
    /**
     * ツールステップの処理
     * @param {Object} step - ツール関連の思考ステップ
     */
    processToolStep(step) {
        if (!this.toolUsageVisualizer) return;
        
        // ツール開始
        if (step.type === 'tool_start' && step.details) {
            const toolId = step.details.tool_id || `tool_${Date.now()}`;
            const toolName = step.details.tool_name || 'UnknownTool';
            const parameters = step.details.parameters || {};
            
            this.toolUsageVisualizer.startToolExecution(toolId, toolName, parameters);
        } 
        // ツール終了
        else if (step.type === 'tool_end' && step.details) {
            const toolId = step.details.tool_id || `tool_${Date.now()}`;
            const result = step.details.result || step.message;
            const isError = step.details.error || false;
            
            this.toolUsageVisualizer.completeToolExecution(toolId, result, isError);
        }
    }
    
    /**
     * ファイル生成ステップの処理
     * @param {Object} step - ファイル生成関連の思考ステップ
     */
    processFileStep(step) {
        if (!this.filesViewer) return;
        
        // メッセージからファイル名を抽出
        const filePatterns = [
            /`([^`]+\.[a-z]{1,5})`\s*(を|が)(生成|作成)(されました|しました)/g,
            /新しいファイル: `([^`]+\.[a-z]{1,5})`/g,
            /ファイル `([^`]+\.[a-z]{1,5})` を作成しました/g,
            /Created file `([^`]+\.[a-z]{1,5})`/g,
            /Generated file `([^`]+\.[a-z]{1,5})`/g
        ];
        
        let filename = null;
        
        // パターンでマッチを試行
        for (const pattern of filePatterns) {
            const match = pattern.exec(step.message);
            if (match) {
                filename = match[1];
                break;
            }
        }
        
        // 詳細情報からファイル名を取得
        if (!filename && step.details && step.details.filename) {
            filename = step.details.filename;
        }
        
        // ファイル名が見つかった場合
        if (filename) {
            const fileInfo = {
                filename: filename,
                content_preview: step.details && step.details.content 
                    ? step.details.content.substring(0, 200) + (step.details.content.length > 200 ? '...' : '')
                    : 'ファイル内容のプレビューはありません',
                project: step.details && step.details.project_id || null,
                timestamp: step.timestamp ? new Date(step.timestamp * 1000).toISOString() : new Date().toISOString()
            };
            
            this.filesViewer.addFile(fileInfo);
        }
    }
    
    /**
     * 生成ファイル情報イベントの処理
     * @param {Object} data - WebSocketから受信したデータ
     */
    processFileGenerationEvents(data) {
        if (!this.filesViewer) return;
        
        // 複数ファイル情報
        if (data.generated_files && Array.isArray(data.generated_files) && data.generated_files.length > 0) {
            this.filesViewer.addFiles(data.generated_files);
        }
        
        // 単一ファイル情報
        if (data.file_generation_event && data.file_generation_event.filename) {
            this.filesViewer.addFile(data.file_generation_event);
        }
    }
    
    /**
     * ステータス変更の処理
     * @param {string} status - 新しいステータス
     */
    processStatusChange(status) {
        // 思考プロセスのステータスを更新
        if (this.thinkingVisualizer) {
            if (status === 'processing') {
                this.thinkingVisualizer.updateStatus('thinking');
            } else if (status === 'completed') {
                this.thinkingVisualizer.updateStatus('complete');
            } else if (status === 'error' || status === 'stopped') {
                this.thinkingVisualizer.updateStatus('error');
            }
        }
    }
    
    /**
     * ツール実行情報の処理
     * @param {Object} data - WebSocketから受信したデータ
     */
    processToolExecutions(data) {
        if (!this.toolUsageVisualizer) return;
        
        // 複数のツール実行情報
        if (data.tool_executions && Array.isArray(data.tool_executions)) {
            data.tool_executions.forEach(execution => {
                const toolId = execution.id || `tool_${Date.now()}`;
                
                if (execution.status === 'running') {
                    this.toolUsageVisualizer.startToolExecution(
                        toolId,
                        execution.name || 'UnknownTool',
                        execution.parameters || {}
                    );
                } else if (execution.status === 'completed' || execution.status === 'error') {
                    this.toolUsageVisualizer.completeToolExecution(
                        toolId,
                        execution.result || {},
                        execution.status === 'error'
                    );
                }
            });
        }
        
        // 単一のツール実行情報
        if (data.tool_execution) {
            const execution = data.tool_execution;
            const toolId = execution.id || `tool_${Date.now()}`;
            
            if (execution.status === 'running') {
                this.toolUsageVisualizer.startToolExecution(
                    toolId,
                    execution.name || 'UnknownTool',
                    execution.parameters || {}
                );
            } else if (execution.status === 'completed' || execution.status === 'error') {
                this.toolUsageVisualizer.completeToolExecution(
                    toolId,
                    execution.result || {},
                    execution.status === 'error'
                );
            }
        }
    }
    
    /**
     * 表示をクリア
     */
    clearVisualizations() {
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.clearSteps();
        }
        
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.clearHistory();
        }
        
        if (this.filesViewer) {
            this.filesViewer.clearFiles();
        }
    }
}

// グローバルインスタンスを作成
window.modelVizController = new ModelVisualizationController();

// WebSocketマネージャーとの連携設定
document.addEventListener('DOMContentLoaded', () => {
    // メインアプリがロードされた後の初期化
    const initInterval = setInterval(() => {
        if (window.app && window.app.websocketManager) {
            // 元のWebSocketメッセージハンドラを保存
            const originalHandler = window.app.websocketManager.onMessageCallback;
            
            // WebSocketマネージャーにコントローラーを連携
            window.app.websocketManager.onMessageCallback = function(data) {
                // 元のハンドラを呼び出し
                if (originalHandler) {
                    originalHandler(data);
                }
                
                // ビジュアライゼーションコントローラーにも通知
                if (window.modelVizController) {
                    window.modelVizController.processWebSocketMessage(data);
                }
            };
            
            // チャットセッション切り替え時の処理
            const originalSendMessage = window.app.handleSendMessage;
            if (originalSendMessage) {
                window.app.handleSendMessage = async function(message) {
                    // セッション開始前にビジュアライゼーションをクリア
                    if (window.modelVizController) {
                        window.modelVizController.clearVisualizations();
                    }
                    
                    // 元の処理を実行
                    return await originalSendMessage.call(window.app, message);
                };
            }
            
            console.log('Model visualization controller connected to WebSocket manager');
            clearInterval(initInterval);
        }
    }, 100);
    
    // テーマ切り替え時の連携
    const themeButtons = document.querySelectorAll('.theme-btn');
    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const theme = this.dataset.theme;
            // ファイルビューワーのテーマを更新
            if (theme === 'chatgpt' && window.enhancedFilesViewer) {
                window.enhancedFilesViewer.container.classList.add('chatgpt-theme');
            } else if (window.enhancedFilesViewer) {
                window.enhancedFilesViewer.container.classList.remove('chatgpt-theme');
            }
        });
    });
});
