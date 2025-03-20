/**
 * model_visualization_controller.js
 * AIモデルの思考プロセスとツール使用状況の視覚化を統合的に管理するコントローラー
 */

// ModelVisualizationController クラス
class ModelVisualizationController {
    constructor() {
        // 依存するビジュアライザー
        this.thinkingVisualizer = window.thinkingProcessVisualizer;
        this.toolUsageVisualizer = window.toolUsageVisualizer;
        
        // ステップタイプのマッピング
        this.stepTypeMapping = {
            'thinking': 'reasoning',
            'planning': 'planning',
            'action': 'execution',
            'observation': 'observation',
            'tool_use': 'tool_use',
            'reflection': 'reflection'
        };
        
        // ツールタイプのマッピング
        this.toolTypeMapping = {
            'github': 'github',
            'web_search': 'web_search',
            'file': 'file_analysis',
            'code': 'code_execution',
            'database': 'database'
        };
        
        // 言語設定
        this.currentLanguage = 'ja-JP';
        
        // ツール使用状況のステータス追跡
        this.toolStatus = {};
    }

    /**
     * 思考ステップを処理する
     * @param {string} stepContent - 思考ステップの内容
     * @param {string} stepType - ステップのタイプ
     */
    processThinkingStep(stepContent, stepType = 'thinking') {
        // タイプのマッピング
        const mappedType = this.stepTypeMapping[stepType] || 'reasoning';
        
        // ステップ内容をローカライズ
        const localizedStep = this.localizeStepContent(stepContent);
        
        // 思考ビジュアライザーにステップを追加
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.addStep(localizedStep, mappedType);
        }
        
        // ツール使用状況の検出
        this.detectToolUsage(localizedStep, stepType);
    }

    /**
     * ステップ内容からツール使用状況を検出する
     * @param {string} stepContent - 思考ステップの内容
     * @param {string} stepType - ステップのタイプ
     */
    detectToolUsage(stepContent, stepType) {
        // ツール使用の開始を検出
        const startToolPattern = /using\s+tool\s+['"]?([a-zA-Z0-9_]+)['"]?|ツール\s*['"]?([a-zA-Z0-9_]+)['"]?\s*を使用|工具\s*['"]?([a-zA-Z0-9_]+)['"]?/i;
        const startMatch = stepContent.match(startToolPattern);
        
        if (startMatch && stepType === 'tool_use') {
            const toolName = startMatch[1] || startMatch[2] || startMatch[3];
            // ツール使用中になっていなければ開始を記録
            if (!this.toolStatus[toolName] || !this.toolStatus[toolName].active) {
                const toolType = this.detectToolType(toolName);
                const description = this.extractToolDescription(stepContent);
                
                this.toolStatus[toolName] = {
                    active: true,
                    type: toolType,
                    description: description,
                    startTime: new Date()
                };
                
                // ツール使用ビジュアライザーを更新
                if (this.toolUsageVisualizer) {
                    this.toolUsageVisualizer.startToolUsage(toolName, toolType, description);
                }
            }
        }
        
        // ツール使用の終了を検出
        const endToolPattern = /tool\s+['"]?([a-zA-Z0-9_]+)['"]?\s+returned|ツール\s*['"]?([a-zA-Z0-9_]+)['"]?\s*の結果|工具\s*['"]?([a-zA-Z0-9_]+)['"]?\s*返回/i;
        const endMatch = stepContent.match(endToolPattern);
        
        if (endMatch && (stepType === 'observation' || stepType === 'reflection')) {
            const toolName = endMatch[1] || endMatch[2] || endMatch[3];
            // ツールがアクティブなら終了を記録
            if (this.toolStatus[toolName] && this.toolStatus[toolName].active) {
                const result = this.detectToolResult(stepContent);
                
                this.toolStatus[toolName] = {
                    active: false,
                    result: result
                };
                
                // ツール使用ビジュアライザーを更新
                if (this.toolUsageVisualizer) {
                    this.toolUsageVisualizer.endToolUsage(toolName, result);
                }
            }
        }
    }

    /**
     * ツール名からツールタイプを推測する
     * @param {string} toolName - ツール名
     * @returns {string} ツールタイプ
     */
    detectToolType(toolName) {
        toolName = toolName.toLowerCase();
        
        if (toolName.includes('github') || toolName.includes('git')) {
            return 'github';
        } else if (toolName.includes('search') || toolName.includes('brave') || toolName.includes('google')) {
            return 'web_search';
        } else if (toolName.includes('file') || toolName.includes('read') || toolName.includes('write')) {
            return 'file_analysis';
        } else if (toolName.includes('code') || toolName.includes('exec') || toolName.includes('run')) {
            return 'code_execution';
        } else if (toolName.includes('db') || toolName.includes('sql') || toolName.includes('database')) {
            return 'database';
        }
        
        return 'default';
    }

    /**
     * ステップ内容からツールの説明を抽出する
     * @param {string} stepContent - 思考ステップの内容
     * @returns {string} ツールの説明
     */
    extractToolDescription(stepContent) {
        // 目的や説明を抽出するパターン
        const purposePattern = /to\s+([^.]+)|\(\s*([^)]+)\)|"([^"]+)"|「([^」]+)」/i;
        const match = stepContent.match(purposePattern);
        
        if (match) {
            return match[1] || match[2] || match[3] || match[4] || '';
        }
        
        // パターンに一致しない場合は短い説明文を生成
        const shortContent = stepContent.split('.')[0];
        if (shortContent.length > 50) {
            return shortContent.substring(0, 47) + '...';
        }
        
        return shortContent;
    }

    /**
     * ステップ内容からツール実行結果を推測する
     * @param {string} stepContent - 思考ステップの内容
     * @returns {string} ツール実行結果
     */
    detectToolResult(stepContent) {
        const lowerContent = stepContent.toLowerCase();
        
        if (lowerContent.includes('error') || lowerContent.includes('failed') || 
            lowerContent.includes('エラー') || lowerContent.includes('失敗') || 
            lowerContent.includes('错误') || lowerContent.includes('失败')) {
            return 'failed';
        } else if (lowerContent.includes('warning') || lowerContent.includes('警告')) {
            return 'warning';
        }
        
        return 'completed';
    }

    /**
     * ステップ内容をローカライズする
     * @param {string} content - ステップ内容
     * @returns {string} ローカライズされたステップ内容
     */
    localizeStepContent(content) {
        // 英語以外の言語の場合は翻訳を試みる
        if (this.currentLanguage !== 'en-US') {
            // ここで翻訳するロジックを実装
            // 単純な例: 頻出フレーズの置換
            if (this.currentLanguage === 'ja-JP') {
                content = content
                    .replace(/I need to/g, '私は〜する必要があります')
                    .replace(/I will/g, '私は〜します')
                    .replace(/Let's/g, '〜しましょう')
                    .replace(/First/g, '最初に')
                    .replace(/Next/g, '次に')
                    .replace(/Finally/g, '最後に');
            } else if (this.currentLanguage === 'zh-CN') {
                content = content
                    .replace(/I need to/g, '我需要')
                    .replace(/I will/g, '我将')
                    .replace(/Let's/g, '让我们')
                    .replace(/First/g, '首先')
                    .replace(/Next/g, '接下来')
                    .replace(/Finally/g, '最后');
            }
        }
        
        return content;
    }

    /**
     * 言語設定を変更する
     * @param {string} language - 言語コード（'ja-JP', 'en-US', 'zh-CN'など）
     */
    setLanguage(language) {
        this.currentLanguage = language;
        
        // 依存するビジュアライザーの言語も更新
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.setLanguage(language);
        }
        
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.setLanguage(language);
        }
    }

    /**
     * 全ての視覚化をリセットする
     */
    resetAllVisualizations() {
        // 思考プロセスをリセット
        if (this.thinkingVisualizer) {
            this.thinkingVisualizer.clearSteps();
        }
        
        // ツール使用状況をリセット
        if (this.toolUsageVisualizer) {
            this.toolUsageVisualizer.resetAllTools();
        }
        
        // ステータス追跡をリセット
        this.toolStatus = {};
    }

    /**
     * すべての依存コンポーネントが存在するかチェックする
     */
    checkDependencies() {
        // 思考プロセスビジュアライザーの確認
        if (!this.thinkingVisualizer) {
            this.thinkingVisualizer = window.thinkingProcessVisualizer;
            if (this.thinkingVisualizer) {
                this.thinkingVisualizer.checkContainer();
            }
        }
        
        // ツール使用ビジュアライザーの確認
        if (!this.toolUsageVisualizer) {
            this.toolUsageVisualizer = window.toolUsageVisualizer;
            if (this.toolUsageVisualizer) {
                this.toolUsageVisualizer.checkContainer();
            }
        }
    }
}

// グローバルインスタンスを作成
window.modelVisualizationController = new ModelVisualizationController();

// DOMのロード完了時のイベントリスナー
document.addEventListener('DOMContentLoaded', () => {
    // 依存関係のチェック
    window.modelVisualizationController.checkDependencies();
    
    // 言語セレクタの変更イベントリスナー
    const languageSelector = document.getElementById('language-selector');
    if (languageSelector) {
        languageSelector.addEventListener('change', (event) => {
            window.modelVisualizationController.setLanguage(event.target.value);
        });
        
        // 初期言語設定
        window.modelVisualizationController.setLanguage(languageSelector.value);
    }
});
