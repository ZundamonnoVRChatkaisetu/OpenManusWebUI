/**
 * thinking_process_visualizer.js
 * AIモデルの思考プロセスを視覚化するコンポーネント
 */

class ThinkingProcessVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container element with ID "${containerId}" not found.`);
            return;
        }
        
        this.options = Object.assign({
            autoScroll: true,
            maxEntries: 100,
            animationDuration: 300,
            translationEnabled: true,
            language: 'ja-JP'
        }, options);
        
        this.thinking_steps = [];
        this.initialized = false;
        
        // 言語設定
        this.currentLanguage = this.options.language;
        
        // 初期化
        this.initialize();
    }
    
    /**
     * コンポーネントの初期化
     */
    initialize() {
        if (this.initialized) return;
        
        // ヘッダー要素の作成
        const header = document.createElement('div');
        header.className = 'thinking-header';
        header.innerHTML = `
            <h3>${this.translate('ai_thinking_process')}</h3>
            <div class="controls">
                <label class="auto-scroll">
                    <input type="checkbox" id="auto-scroll" ${this.options.autoScroll ? 'checked' : ''}>
                    <span>${this.translate('auto_scroll')}</span>
                </label>
                <button id="clear-thinking" class="btn-clear">${this.translate('clear')}</button>
            </div>
        `;
        this.container.appendChild(header);
        
        // 思考ステップ表示エリアの作成
        this.timeline = document.createElement('div');
        this.timeline.className = 'thinking-timeline';
        this.container.appendChild(this.timeline);
        
        // イベントリスナーの設定
        document.getElementById('auto-scroll').addEventListener('change', (e) => {
            this.options.autoScroll = e.target.checked;
        });
        
        document.getElementById('clear-thinking').addEventListener('click', () => {
            this.clearThinkingSteps();
        });
        
        this.initialized = true;
    }
    
    /**
     * 思考ステップの追加
     * @param {Object} step 思考ステップデータ
     */
    addThinkingStep(step) {
        if (!this.initialized) {
            console.warn('ThinkingProcessVisualizer is not initialized yet.');
            return;
        }
        
        // 思考ステップの保存
        this.thinking_steps.push(step);
        
        // 最大表示数を超えた場合、古いものを削除
        if (this.thinking_steps.length > this.options.maxEntries) {
            this.thinking_steps.shift();
            // 最初の要素を画面から削除
            if (this.timeline.firstChild) {
                this.timeline.removeChild(this.timeline.firstChild);
            }
        }
        
        // 思考ステップの表示
        this.renderStep(step);
        
        // 自動スクロール
        if (this.options.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    /**
     * 思考ステップを画面に描画
     * @param {Object} step 思考ステップデータ
     */
    renderStep(step) {
        const stepElement = document.createElement('div');
        stepElement.className = 'timeline-item';
        stepElement.style.opacity = '0';
        
        // ステップの種類に応じたクラスを追加
        if (step.type) {
            stepElement.classList.add(`timeline-item-${step.type}`);
        }
        
        // 完了ステップか特別なステップの場合、completed クラスを追加
        if (step.type === 'conclusion' || step.message.includes(this.translate('completed'))) {
            stepElement.classList.add('completed');
        }
        
        // ツール使用ステップの場合、tool-usage クラスを追加
        if (step.message.includes('ツール') || step.message.includes('Tool') || 
            step.message.includes('tool') || step.message.includes('通信') || 
            step.message.includes('communication')) {
            stepElement.classList.add('tool-usage');
        }
        
        // 思考ステップの内容
        let message = step.message;
        if (this.options.translationEnabled && this.currentLanguage !== 'en-US') {
            // 英語の思考ステップを現在の言語に翻訳
            message = this.translateThinkingStep(message);
        }
        
        // タイムスタンプをフォーマット
        const timestamp = new Date(step.timestamp * 1000).toLocaleTimeString();
        
        stepElement.innerHTML = `
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <div class="timeline-header">
                    <span class="timeline-time">${timestamp}</span>
                    <span class="timeline-message">${message}</span>
                </div>
                ${step.details ? `
                <button class="btn-details">${this.translate('show_details')}</button>
                <div class="timeline-details">${step.details}</div>
                ` : ''}
            </div>
        `;
        
        // 詳細の表示/非表示切り替え
        const detailsButton = stepElement.querySelector('.btn-details');
        const detailsContent = stepElement.querySelector('.timeline-details');
        
        if (detailsButton && detailsContent) {
            detailsButton.addEventListener('click', () => {
                if (detailsContent.style.display === 'block') {
                    detailsContent.style.display = 'none';
                    detailsButton.textContent = this.translate('show_details');
                } else {
                    detailsContent.style.display = 'block';
                    detailsButton.textContent = this.translate('hide_details');
                }
            });
        }
        
        // タイムラインに追加
        this.timeline.appendChild(stepElement);
        
        // アニメーション
        setTimeout(() => {
            stepElement.style.opacity = '1';
        }, 10);
    }
    
    /**
     * タイムラインの最下部にスクロール
     */
    scrollToBottom() {
        this.timeline.scrollTop = this.timeline.scrollHeight;
    }
    
    /**
     * 思考ステップの全クリア
     */
    clearThinkingSteps() {
        this.thinking_steps = [];
        this.timeline.innerHTML = '';
    }
    
    /**
     * 言語設定の変更
     * @param {string} language 言語コード
     */
    setLanguage(language) {
        this.currentLanguage = language;
        
        // 既存の表示を更新
        const header = this.container.querySelector('.thinking-header h3');
        if (header) {
            header.textContent = this.translate('ai_thinking_process');
        }
        
        const autoScrollLabel = this.container.querySelector('.auto-scroll span');
        if (autoScrollLabel) {
            autoScrollLabel.textContent = this.translate('auto_scroll');
        }
        
        const clearButton = this.container.querySelector('#clear-thinking');
        if (clearButton) {
            clearButton.textContent = this.translate('clear');
        }
        
        // 詳細ボタンのテキストを更新
        const detailsButtons = this.container.querySelectorAll('.btn-details');
        detailsButtons.forEach(button => {
            const detailsContent = button.nextElementSibling;
            button.textContent = detailsContent && detailsContent.style.display === 'block' 
                ? this.translate('hide_details') 
                : this.translate('show_details');
        });
    }
    
    /**
     * 表示中の思考ステップ数の取得
     * @returns {number} 思考ステップ数
     */
    getStepsCount() {
        return this.thinking_steps.length;
    }
    
    /**
     * 翻訳関数
     * @param {string} key 翻訳キー
     * @returns {string} 翻訳されたテキスト
     */
    translate(key) {
        const translations = {
            'ja-JP': {
                'ai_thinking_process': 'AI思考プロセス',
                'auto_scroll': '自動スクロール',
                'clear': 'クリア',
                'show_details': '詳細を表示',
                'hide_details': '詳細を隠す',
                'completed': '完了',
                'error': 'エラー',
                'warning': '警告',
                'info': '情報',
                'communication': '通信',
                'executing': '実行中',
                'tool_usage': 'ツール使用'
            },
            'en-US': {
                'ai_thinking_process': 'AI Thinking Process',
                'auto_scroll': 'Auto Scroll',
                'clear': 'Clear',
                'show_details': 'Show Details',
                'hide_details': 'Hide Details',
                'completed': 'Completed',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Info',
                'communication': 'Communication',
                'executing': 'Executing',
                'tool_usage': 'Tool Usage'
            },
            'zh-CN': {
                'ai_thinking_process': 'AI思考过程',
                'auto_scroll': '自动滚动',
                'clear': '清空',
                'show_details': '显示详情',
                'hide_details': '隐藏详情',
                'completed': '已完成',
                'error': '错误',
                'warning': '警告',
                'info': '信息',
                'communication': '通信',
                'executing': '执行中',
                'tool_usage': '工具使用'
            }
        };
        
        const language = translations[this.currentLanguage] ? this.currentLanguage : 'en-US';
        return translations[language][key] || key;
    }
    
    /**
     * 思考ステップメッセージの翻訳
     * 英語の思考ステップを現在の言語に翻訳
     * @param {string} message 思考ステップメッセージ
     * @returns {string} 翻訳されたメッセージ
     */
    translateThinkingStep(message) {
        // 英語の定型フレーズを翻訳
        const patterns = {
            'ja-JP': {
                'Start processing': '処理を開始',
                'Analyzing user request': 'ユーザーリクエストを分析中',
                'Creating task plan': 'タスク計画を作成中',
                'Executing step': 'ステップを実行中',
                'Completed': '完了',
                'Error': 'エラー',
                'Warning': '警告',
                'Info': '情報',
                'Communication': '通信',
                'Executing': '実行中',
                'Using tool': 'ツールを使用中',
                'Workspace directory': 'ワークスペースディレクトリ',
                'Task completed': 'タスク完了'
            },
            'zh-CN': {
                'Start processing': '开始处理',
                'Analyzing user request': '分析用户请求',
                'Creating task plan': '创建任务计划',
                'Executing step': '执行步骤',
                'Completed': '已完成',
                'Error': '错误',
                'Warning': '警告',
                'Info': '信息',
                'Communication': '通信',
                'Executing': '执行中',
                'Using tool': '使用工具',
                'Workspace directory': '工作区目录',
                'Task completed': '任务完成'
            }
        };
        
        // 現在の言語の変換パターン
        const currentPatterns = patterns[this.currentLanguage];
        if (!currentPatterns) return message;
        
        // パターンに基づいて変換
        let translatedMessage = message;
        
        for (const [english, translated] of Object.entries(currentPatterns)) {
            translatedMessage = translatedMessage.replace(
                new RegExp(english, 'gi'), 
                translated
            );
        }
        
        return translatedMessage;
    }
}

// グローバルスコープでエクスポート
window.ThinkingProcessVisualizer = ThinkingProcessVisualizer;
