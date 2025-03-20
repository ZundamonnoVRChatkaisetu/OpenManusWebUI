// connected_websocketManager.js - WebSocket接続とメッセージ処理

import { t } from '/static/i18n.js';

export class WebSocketManager {
    constructor(messageHandler) {
        this.socket = null;
        this.messageHandler = messageHandler;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 初期再接続遅延1秒
        this.sessionId = null;
        
        // モデル視覚化コントローラー参照
        this.visualizationController = null;
        
        // 接続初期化時にコントローラーを取得
        document.addEventListener('DOMContentLoaded', () => {
            if (window.modelVisualizationController) {
                this.visualizationController = window.modelVisualizationController;
            }
        });
    }

    // WebSocketに接続
    connect(sessionId) {
        // セッションIDを保存
        this.sessionId = sessionId;

        // すでに接続があれば閉じる
        if (this.socket) {
            this.socket.close();
        }

        // 再接続試行回数をリセット
        this.reconnectAttempts = 0;

        // WebSocket接続を作成
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;

        console.log(`WebSocketに接続: ${wsUrl}`);

        this.socket = new WebSocket(wsUrl);

        // イベントハンドラを設定
        this.socket.onopen = this.handleOpen.bind(this);
        this.socket.onmessage = this.handleMessage.bind(this);
        this.socket.onclose = this.handleClose.bind(this);
        this.socket.onerror = this.handleError.bind(this);
    }

    // 接続オープン時の処理
    handleOpen(event) {
        console.log('WebSocket接続が確立されました');
        document.getElementById('status-indicator').textContent = t('connection_established');
        // 再接続試行回数をリセット
        this.reconnectAttempts = 0;
    }

    // メッセージ受信時の処理
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocketメッセージを受信:', data);

            // 思考ステップの処理
            this.processThinkingSteps(data);

            // メッセージハンドラーコールバックを呼び出し
            if (this.messageHandler) {
                this.messageHandler(data);
            }
        } catch (error) {
            console.error('WebSocketメッセージの解析エラー:', error);
        }
    }

    // 思考ステップの処理
    processThinkingSteps(data) {
        // 視覚化コントローラーがない場合は処理しない
        if (!this.visualizationController) {
            if (window.modelVisualizationController) {
                this.visualizationController = window.modelVisualizationController;
            } else {
                return;
            }
        }

        // 思考ステップデータの処理
        if (data.type === 'thinking_step' && data.content) {
            const stepType = data.step_type || 'thinking';
            this.visualizationController.processThinkingStep(data.content, stepType);
        }
        
        // ツール使用開始
        else if (data.type === 'tool_start' && data.tool_name) {
            const toolName = data.tool_name;
            const toolType = data.tool_type || 'default';
            const description = data.description || '';
            
            // ツール使用ビジュアライザーのメソッドを直接呼び出す
            if (window.toolUsageVisualizer) {
                window.toolUsageVisualizer.startToolUsage(toolName, toolType, description);
            }
        }
        
        // ツール使用終了
        else if (data.type === 'tool_end' && data.tool_name) {
            const toolName = data.tool_name;
            const result = data.result || 'completed';
            
            // ツール使用ビジュアライザーのメソッドを直接呼び出す
            if (window.toolUsageVisualizer) {
                window.toolUsageVisualizer.endToolUsage(toolName, result);
            }
        }
    }

    // 接続クローズ時の処理
    handleClose(event) {
        console.log(`WebSocket接続が閉じられました: ${event.code} ${event.reason}`);

        // 再接続を試みる
        this.attemptReconnect();
    }

    // 接続エラー時の処理
    handleError(error) {
        console.error('WebSocketエラー:', error);
    }

    // 再接続を試みる
    attemptReconnect() {
        if (!this.sessionId) {
            console.log('セッションIDがないため、再接続できません');
            return;
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('最大再接続試行回数に達しました、再接続を停止します');
            document.getElementById('status-indicator').textContent = t('connection_failed');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数バックオフ

        console.log(`再接続を試みています (${this.reconnectAttempts}/${this.maxReconnectAttempts})、遅延 ${delay}ms`);
        document.getElementById('status-indicator').textContent = t('reconnecting', {
            current: this.reconnectAttempts,
            max: this.maxReconnectAttempts
        });

        setTimeout(() => {
            if (this.sessionId) {
                this.connect(this.sessionId);
            }
        }, delay);
    }

    // メッセージを送信
    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            console.error('WebSocketが接続されていないため、メッセージを送信できません');
        }
    }

    // 接続を閉じる
    close() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}
