/**
 * thinking_process_visualizer.js
 * AIの思考プロセスを視覚的に表示するためのモジュール
 */

// ThinkingProcessVisualizer クラス
class ThinkingProcessVisualizer {
    constructor(containerId = 'thinking-process-steps') {
        this.container = document.getElementById(containerId);
        this.steps = [];
        this.maxSteps = 5; // 表示する最大ステップ数
        this.currentLanguage = 'ja-JP'; // デフォルト言語
    }

    /**
     * 思考ステップを追加する
     * @param {string} step - 思考ステップの内容
     * @param {string} type - ステップのタイプ（例：'reasoning', 'planning', 'execution'）
     */
    addStep(step, type = 'reasoning') {
        // ステップを配列に追加
        this.steps.push({
            content: step,
            type: type,
            timestamp: new Date()
        });

        // 最大数を超えた場合は古いステップを削除
        if (this.steps.length > this.maxSteps) {
            this.steps.shift();
        }

        // UI更新
        this.updateUI();
    }

    /**
     * 全てのステップをクリアする
     */
    clearSteps() {
        this.steps = [];
        this.updateUI();
    }

    /**
     * UIを更新する
     */
    updateUI() {
        if (!this.container) return;

        // コンテナをクリア
        this.container.innerHTML = '';

        // 思考ステップがない場合
        if (this.steps.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'thinking-process-empty';
            emptyMessage.textContent = this.getTranslation('thinking_empty', '思考プロセスはまだありません');
            this.container.appendChild(emptyMessage);
            return;
        }

        // 各ステップを表示
        this.steps.forEach((step, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = `thinking-process-step ${step.type}`;
            
            // ステップ番号
            const number = this.steps.length - index;
            stepElement.textContent = `${number}. ${step.content}`;
            
            // コンテナに追加
            this.container.appendChild(stepElement);
        });
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
            this.container = document.getElementById('thinking-process-steps');
        }
    }
}

// グローバルインスタンスを作成
window.thinkingProcessVisualizer = new ThinkingProcessVisualizer();

// DOMのロード完了時のイベントリスナー
document.addEventListener('DOMContentLoaded', () => {
    // コンテナの存在チェック
    window.thinkingProcessVisualizer.checkContainer();
});
