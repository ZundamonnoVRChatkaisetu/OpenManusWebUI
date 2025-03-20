/**
 * tool_usage_visualizer.js
 * ツール使用状況を視覚的に表示するためのモジュール
 */

// ToolUsageVisualizer クラス
class ToolUsageVisualizer {
    constructor(containerId = 'tool-usage-items') {
        this.container = document.getElementById(containerId);
        this.tools = [];
        this.maxTools = 5; // 表示する最大ツール数
        this.currentLanguage = 'ja-JP'; // デフォルト言語
        
        // ツールアイコンマッピング
        this.toolIcons = {
            'github': '📂',
            'search': '🔍',
            'web': '🌐',
            'file': '📄',
            'database': '💾',
            'api': '🔌',
            'default': '🔧'
        };
    }

    /**
     * ツール実行を追加する
     * @param {string} toolName - ツール名
     * @param {object} params - パラメータ
     * @param {string|object} result - 実行結果
     * @param {boolean} isError - エラーフラグ
     */
    addToolExecution(toolName, params, result, isError = false) {
        // ツール実行情報を配列に追加
        this.tools.push({
            name: toolName,
            params: params,
            result: result,
            isError: isError,
            timestamp: new Date()
        });

        // 最大数を超えた場合は古いツールを削除
        if (this.tools.length > this.maxTools) {
            this.tools.shift();
        }

        // UI更新
        this.updateUI();
    }

    /**
     * 全てのツールをクリアする
     */
    clearTools() {
        this.tools = [];
        this.updateUI();
    }

    /**
     * UIを更新する
     */
    updateUI() {
        if (!this.container) {
            this.checkContainer();
            if (!this.container) return;
        }

        // コンテナをクリア
        this.container.innerHTML = '';

        // ツール実行がない場合
        if (this.tools.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'visualizer-empty';
            emptyMessage.textContent = this.getTranslation('tools_empty', 'ツールは使用されていません');
            this.container.appendChild(emptyMessage);
            return;
        }

        // 各ツール実行を表示
        this.tools.forEach(tool => {
            const toolElement = document.createElement('div');
            toolElement.className = 'tool-execution';
            
            // ヘッダー
            const header = document.createElement('div');
            header.className = 'tool-execution-header';
            
            const nameElement = document.createElement('div');
            nameElement.className = 'tool-name';
            
            // ツール名からアイコンを決定
            const icon = this.getToolIcon(tool.name);
            nameElement.innerHTML = `<span class="tool-name-icon">${icon}</span> ${tool.name}`;
            
            const timestamp = document.createElement('div');
            timestamp.className = 'tool-timestamp';
            timestamp.textContent = tool.timestamp.toLocaleTimeString();
            
            header.appendChild(nameElement);
            header.appendChild(timestamp);
            
            // パラメータ
            const paramsElement = document.createElement('pre');
            paramsElement.className = 'tool-params';
            paramsElement.textContent = typeof tool.params === 'object' 
                ? JSON.stringify(tool.params, null, 2) 
                : tool.params;
            
            // 結果
            const resultElement = document.createElement('div');
            resultElement.className = tool.isError ? 'tool-error' : 'tool-result';
            
            // 結果テキストの整形
            let resultText = '';
            if (typeof tool.result === 'object') {
                try {
                    resultText = JSON.stringify(tool.result, null, 2);
                } catch (e) {
                    resultText = String(tool.result);
                }
            } else {
                resultText = String(tool.result);
            }
            
            // 結果が長すぎる場合は省略
            if (resultText.length > 500) {
                resultText = resultText.substring(0, 497) + '...';
            }
            
            resultElement.textContent = resultText;
            
            // 全て組み立て
            toolElement.appendChild(header);
            toolElement.appendChild(paramsElement);
            toolElement.appendChild(resultElement);
            
            // コンテナに追加
            this.container.appendChild(toolElement);
        });
        
        // 最新のツールにスクロール
        this.container.scrollTop = this.container.scrollHeight;
    }
    
    /**
     * ツール名からアイコンを取得する
     * @param {string} toolName - ツール名
     * @returns {string} - アイコン文字列
     */
    getToolIcon(toolName) {
        const lowerName = toolName.toLowerCase();
        
        for (const [key, icon] of Object.entries(this.toolIcons)) {
            if (lowerName.includes(key)) {
                return icon;
            }
        }
        
        return this.toolIcons.default;
    }

    /**
     * 言語設定を変更する
     * @param {string} language - 言語コード（'ja-JP', 'en-US', 'zh-CN'など）
     */
    setLanguage(language) {
        this.currentLanguage = language;
        this.updateUI();
    }

    /**
     * 翻訳テキストを取得する
     * @param {string} key - 翻訳キー
     * @param {string} defaultText - デフォルトテキスト
     * @returns {string} 翻訳されたテキスト
     */
    getTranslation(key, defaultText) {
        // i18n.jsがロードされている場合はそれを使用
        if (typeof t === 'function') {
            return t(key) || defaultText;
        }
        return defaultText;
    }

    /**
     * コンテナ要素が存在するかチェックし、必要に応じて再取得する
     */
    checkContainer() {
        if (!this.container) {
            this.container = document.getElementById('tool-usage-items');
        }
    }
}

// グローバルインスタンスを作成
window.toolUsageVisualizer = new ToolUsageVisualizer();

// DOMのロード完了時のイベントリスナー
document.addEventListener('DOMContentLoaded', () => {
    // コンテナの存在チェック
    window.toolUsageVisualizer.checkContainer();
});
