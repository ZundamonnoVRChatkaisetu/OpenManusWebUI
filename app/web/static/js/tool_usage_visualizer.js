/**
 * tool_usage_visualizer.js
 * AIモデルのツール使用状況を視覚的に表示するためのモジュール
 */

// ToolUsageVisualizer クラス
class ToolUsageVisualizer {
    constructor(containerId = 'tool-usage-content') {
        this.container = document.getElementById(containerId);
        this.activeTools = new Map(); // 現在アクティブなツール
        this.toolHistory = []; // ツール使用履歴
        this.maxHistoryItems = 5; // 表示する最大履歴数
        this.currentLanguage = 'ja-JP'; // デフォルト言語
        
        // ツールタイプに関連するアイコン
        this.toolIcons = {
            'github': 'fab fa-github',
            'web_search': 'fas fa-search',
            'file_analysis': 'fas fa-file-alt',
            'code_execution': 'fas fa-code',
            'database': 'fas fa-database',
            'default': 'fas fa-tools'
        };
    }

    /**
     * ツールの使用開始を記録する
     * @param {string} toolName - ツール名
     * @param {string} toolType - ツールタイプ（'github', 'web_search'など）
     * @param {string} description - ツール使用の説明
     */
    startToolUsage(toolName, toolType = 'default', description = '') {
        const startTime = new Date();
        
        // アクティブなツールリストに追加
        this.activeTools.set(toolName, {
            type: toolType,
            description: description,
            startTime: startTime
        });
        
        // UI更新
        this.updateUI();
    }

    /**
     * ツールの使用終了を記録する
     * @param {string} toolName - ツール名
     * @param {string} result - ツール実行結果の概要（成功/失敗など）
     */
    endToolUsage(toolName, result = 'completed') {
        // アクティブなツールが存在するか確認
        if (this.activeTools.has(toolName)) {
            const tool = this.activeTools.get(toolName);
            const endTime = new Date();
            const duration = endTime - tool.startTime;
            
            // 履歴に追加
            this.toolHistory.unshift({
                name: toolName,
                type: tool.type,
                description: tool.description,
                startTime: tool.startTime,
                endTime: endTime,
                duration: duration,
                result: result
            });
            
            // 履歴が最大数を超えた場合は古い項目を削除
            if (this.toolHistory.length > this.maxHistoryItems) {
                this.toolHistory.pop();
            }
            
            // アクティブリストから削除
            this.activeTools.delete(toolName);
            
            // UI更新
            this.updateUI();
        }
    }

    /**
     * 全てのツール使用状況をリセットする
     */
    resetAllTools() {
        this.activeTools.clear();
        this.toolHistory = [];
        this.updateUI();
    }

    /**
     * UIを更新する
     */
    updateUI() {
        if (!this.container) return;

        // コンテナをクリア
        this.container.innerHTML = '';

        // アクティブなツールを表示
        if (this.activeTools.size > 0) {
            const activeSection = document.createElement('div');
            activeSection.className = 'active-tools-section';
            
            this.activeTools.forEach((tool, toolName) => {
                const toolElement = this.createToolElement(toolName, tool, true);
                activeSection.appendChild(toolElement);
            });
            
            this.container.appendChild(activeSection);
        }

        // 履歴を表示
        if (this.toolHistory.length > 0) {
            const historySection = document.createElement('div');
            historySection.className = 'tool-history-section';
            
            // セクションヘッダー（履歴がある場合のみ）
            if (this.activeTools.size > 0 && this.toolHistory.length > 0) {
                const historyHeader = document.createElement('h5');
                historyHeader.className = 'tool-history-header';
                historyHeader.textContent = this.getTranslation('recent_tool_usage', '最近のツール使用');
                historySection.appendChild(historyHeader);
            }
            
            // 各履歴項目
            this.toolHistory.forEach(historyItem => {
                const historyElement = this.createHistoryElement(historyItem);
                historySection.appendChild(historyElement);
            });
            
            this.container.appendChild(historySection);
        }

        // ツール使用がない場合
        if (this.activeTools.size === 0 && this.toolHistory.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'tool-usage-empty';
            emptyMessage.textContent = this.getTranslation('no_tool_usage', 'ツール使用はまだありません');
            this.container.appendChild(emptyMessage);
        }
    }

    /**
     * ツール要素を作成する
     * @param {string} toolName - ツール名
     * @param {Object} tool - ツール情報
     * @param {boolean} isActive - アクティブなツールかどうか
     * @returns {HTMLElement} ツール要素
     */
    createToolElement(toolName, tool, isActive) {
        const toolElement = document.createElement('div');
        toolElement.className = `tool-item ${isActive ? 'active' : ''}`;
        
        // アイコン
        const iconClass = this.toolIcons[tool.type] || this.toolIcons.default;
        const iconElement = document.createElement('i');
        iconElement.className = `tool-icon ${iconClass} ${isActive ? 'fa-spin' : ''}`;
        toolElement.appendChild(iconElement);
        
        // ツール情報
        const infoElement = document.createElement('div');
        infoElement.className = 'tool-info';
        
        // ツール名
        const nameElement = document.createElement('div');
        nameElement.className = 'tool-name';
        nameElement.textContent = toolName;
        infoElement.appendChild(nameElement);
        
        // 説明（あれば）
        if (tool.description) {
            const descElement = document.createElement('div');
            descElement.className = 'tool-description';
            descElement.textContent = tool.description;
            infoElement.appendChild(descElement);
        }
        
        // 経過時間（アクティブな場合）
        if (isActive) {
            const elapsed = document.createElement('div');
            elapsed.className = 'tool-elapsed';
            const now = new Date();
            const seconds = Math.floor((now - tool.startTime) / 1000);
            elapsed.textContent = `${seconds}秒経過`;
            infoElement.appendChild(elapsed);
        }
        
        toolElement.appendChild(infoElement);
        return toolElement;
    }

    /**
     * 履歴要素を作成する
     * @param {Object} historyItem - 履歴項目
     * @returns {HTMLElement} 履歴要素
     */
    createHistoryElement(historyItem) {
        const historyElement = document.createElement('div');
        historyElement.className = `tool-history-item result-${historyItem.result}`;
        
        // アイコン
        const iconClass = this.toolIcons[historyItem.type] || this.toolIcons.default;
        const iconElement = document.createElement('i');
        iconElement.className = `tool-icon ${iconClass}`;
        historyElement.appendChild(iconElement);
        
        // 情報
        const infoElement = document.createElement('div');
        infoElement.className = 'tool-info';
        
        // 名前
        const nameElement = document.createElement('div');
        nameElement.className = 'tool-name';
        nameElement.textContent = historyItem.name;
        infoElement.appendChild(nameElement);
        
        // 説明（あれば）
        if (historyItem.description) {
            const descElement = document.createElement('div');
            descElement.className = 'tool-description';
            descElement.textContent = historyItem.description;
            infoElement.appendChild(descElement);
        }
        
        // 所要時間
        const durationElement = document.createElement('div');
        durationElement.className = 'tool-duration';
        const seconds = Math.floor(historyItem.duration / 1000);
        durationElement.textContent = `${seconds}秒`;
        infoElement.appendChild(durationElement);
        
        historyElement.appendChild(infoElement);
        return historyElement;
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
        if (typeof getLocalizedString === 'function') {
            return getLocalizedString(key) || defaultText;
        }
        return defaultText;
    }

    /**
     * コンテナ要素が存在するかチェックし、必要に応じて再取得する
     */
    checkContainer() {
        if (!this.container) {
            this.container = document.getElementById('tool-usage-content');
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
