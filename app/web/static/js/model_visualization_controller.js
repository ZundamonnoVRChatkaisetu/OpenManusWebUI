/**
 * model_visualization_controller.js
 * 
 * AIモデルの操作と思考プロセスを視覚化するためのコントローラー
 * ThinkingProcessVisualizerとToolUsageVisualizerを統合して管理するモジュール
 */

class ModelVisualizationController {
    constructor() {
        // コンテナ要素の取得
        this.thinkingContainer = document.getElementById('thinking-process-container');
        this.toolUsageContainer = document.getElementById('tool-usage-container');
        
        // 視覚化コンポーネントのインスタンス化（存在する場合）
        this.thinkingVisualizer = window.thinkingProcessVisualizer || null;
        this.toolUsageVisualizer = window.toolUsageVisualizer || null;
        
        // コンテナが見つからない場合は作成
        this.initializeContainers();
    }
    
    /**
     * 必要なコンテナを初期化する
     */
    initializeContainers() {
        if (!this.thinkingContainer) {
            this.thinkingContainer = document.createElement('div');
            this.thinkingContainer.id = 'thinking-process-container';
            this.thinkingContainer.className = 'visualizer-container';
            
            // タイトル要素
            const title = document.createElement('div');
            title.className = 'visualizer-title thinking-process-title';
            title.textContent = this.getTranslation('thinking_process', 'AI思考プロセス');
            
            // コンテンツエリア
            const content = document.createElement('div');
            content.id = 'thinking-process-steps';
            content.className = 'thinking-process-steps';
            
            this.thinkingContainer.appendChild(title);
            this.thinkingContainer.appendChild(content);
            
            // 適切な場所に挿入
            const leftPanel = document.querySelector('.left-panel');
            if (leftPanel) {
                leftPanel.insertBefore(this.thinkingContainer, leftPanel.firstChild);
            }
        }
        
        if (!this.toolUsageContainer) {
            this.toolUsageContainer = document.createElement('div');
            this.toolUsageContainer.id = 'tool-usage-container';
            this.toolUsageContainer.className = 'visualizer-container';
            
            // タイトル要素
            const title = document.createElement('div');
            title.className = 'visualizer-title tool-usage-title';
            title.textContent = this.getTranslation('tool_usage', 'ツール使用状況');
            
            // コンテンツエリア
            const content = document.createElement('div');
            content.id = 'tool-usage-items';
            content.className = 'tool-usage-items';
            
            this.toolUsageContainer.appendChild(title);
            this.toolUsageContainer.appendChild(content);
            
            // 適切な場所に挿入（思考プロセスの下）
            if (this.thinkingContainer) {
                this.thinkingContainer.after(this.toolUsageContainer);
            } else {
                const leftPanel = document.querySelector('.left-panel');
                if (leftPanel) {
                    leftPanel.insertBefore(this.toolUsageContainer, leftPanel.firstChild);
                }
            }
        }
    }
    
    /**
     * 思考ステップを追加
     * @param {string} step - 思考ステップの内容
     * @param {string} type - 思考のタイプ（reasoning, planning, execution）
     */
    addThinkingStep(step, type = 'reasoning') {
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.addStep(step, type);
        } else {
            // 思考プロセス視覚化がない場合、コンテナに直接表示
            const stepsContainer = document.getElementById('thinking-process-steps');
            if (stepsContainer) {
                const stepElement = document.createElement('div');
                stepElement.className = `thinking-process-step ${type}`;
                
                const timestamp = document.createElement('div');
                timestamp.className = 'thinking-step-timestamp';
                timestamp.textContent = new Date().toLocaleTimeString();
                
                const content = document.createElement('div');
                content.className = 'thinking-step-content';
                content.textContent = step;
                
                stepElement.appendChild(timestamp);
                stepElement.appendChild(content);
                
                stepsContainer.appendChild(stepElement);
                stepsContainer.scrollTop = stepsContainer.scrollHeight;
            }
        }
    }
    
    /**
     * ツール使用状況を追加
     * @param {string} toolName - ツール名
     * @param {object} params - ツールパラメータ
     * @param {string|object} result - ツール実行結果
     * @param {boolean} isError - エラーかどうか
     */
    addToolUsage(toolName, params, result, isError = false) {
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.addToolExecution(toolName, params, result, isError);
        } else {
            // ツール使用状況視覚化がない場合、コンテナに直接表示
            const toolsContainer = document.getElementById('tool-usage-items');
            if (toolsContainer) {
                const toolElement = document.createElement('div');
                toolElement.className = 'tool-execution';
                
                // ヘッダー
                const header = document.createElement('div');
                header.className = 'tool-execution-header';
                
                const nameElement = document.createElement('div');
                nameElement.className = 'tool-name';
                
                // ツールタイプに基づいてアイコンを設定
                const iconClass = this.getToolIconClass(toolName);
                nameElement.innerHTML = `<span class="tool-name-icon ${iconClass}">🔧</span> ${toolName}`;
                
                const timestamp = document.createElement('div');
                timestamp.className = 'tool-timestamp';
                timestamp.textContent = new Date().toLocaleTimeString();
                
                header.appendChild(nameElement);
                header.appendChild(timestamp);
                
                // パラメータ
                const paramsElement = document.createElement('pre');
                paramsElement.className = 'tool-params';
                paramsElement.textContent = typeof params === 'object' 
                    ? JSON.stringify(params, null, 2) 
                    : params;
                
                // 結果
                const resultElement = document.createElement('div');
                resultElement.className = isError ? 'tool-error' : 'tool-result';
                resultElement.textContent = typeof result === 'object' 
                    ? JSON.stringify(result, null, 2) 
                    : result;
                
                toolElement.appendChild(header);
                toolElement.appendChild(paramsElement);
                toolElement.appendChild(resultElement);
                
                toolsContainer.appendChild(toolElement);
                toolsContainer.scrollTop = toolsContainer.scrollHeight;
            }
        }
    }
    
    /**
     * ツール名に基づいてアイコンクラスを取得
     * @param {string} toolName - ツール名
     * @returns {string} アイコンクラス
     */
    getToolIconClass(toolName) {
        const lowerName = toolName.toLowerCase();
        
        if (lowerName.includes('github')) return 'tool-icon-github';
        if (lowerName.includes('web') || lowerName.includes('search')) return 'tool-icon-web';
        if (lowerName.includes('file') || lowerName.includes('document')) return 'tool-icon-file';
        if (lowerName.includes('db') || lowerName.includes('database')) return 'tool-icon-database';
        if (lowerName.includes('api')) return 'tool-icon-api';
        
        return '';
    }
    
    /**
     * 全ての視覚化をクリア
     */
    clearAll() {
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.clearSteps();
        } else {
            const stepsContainer = document.getElementById('thinking-process-steps');
            if (stepsContainer) {
                stepsContainer.innerHTML = '';
            }
        }
        
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.clearTools();
        } else {
            const toolsContainer = document.getElementById('tool-usage-items');
            if (toolsContainer) {
                toolsContainer.innerHTML = '';
            }
        }
    }
    
    /**
     * 言語設定を変更
     * @param {string} language - 言語コード
     */
    setLanguage(language) {
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.setLanguage(language);
        }
        
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.setLanguage(language);
        }
        
        // コンテナのタイトルも更新
        this.updateContainerTitles();
    }
    
    /**
     * コンテナのタイトルを更新
     */
    updateContainerTitles() {
        const thinkingTitle = this.thinkingContainer?.querySelector('.visualizer-title');
        if (thinkingTitle) {
            thinkingTitle.textContent = this.getTranslation('thinking_process', 'AI思考プロセス');
        }
        
        const toolUsageTitle = this.toolUsageContainer?.querySelector('.visualizer-title');
        if (toolUsageTitle) {
            toolUsageTitle.textContent = this.getTranslation('tool_usage', 'ツール使用状況');
        }
    }
    
    /**
     * 翻訳テキストを取得
     * @param {string} key - 翻訳キー
     * @param {string} defaultText - デフォルトテキスト
     * @returns {string} 翻訳されたテキスト
     */
    getTranslation(key, defaultText) {
        // i18n.jsがロードされている場合はそれを使用
        if (typeof t === 'function') {
            return t(key, {}) || defaultText;
        }
        return defaultText;
    }
}

// DOMのロード完了時にコントローラーを初期化
document.addEventListener('DOMContentLoaded', () => {
    window.modelVisualizer = new ModelVisualizationController();
});
