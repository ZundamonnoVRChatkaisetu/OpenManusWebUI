/**
 * 多言語対応モジュール
 */

// 翻訳データ
const translations = {
    // 中国語（簡体字）
    'zh-CN': {
        'app_title': 'OpenManus',
        'app_subtitle': 'AI智能助手 - 网页版',
        'processing_progress': '处理进度',
        'ai_thinking_process': 'AI思考过程',
        'records_count': '0 条记录',
        'auto_scroll': '自动滚动',
        'clear': '清空',
        'workspace_files': '工作区文件',
        'refresh_countdown': '5秒后刷新',
        'refresh': '刷新',
        'conversation': '对话',
        'file_name': '文件名',
        'close': '关闭',
        'input_placeholder': '输入您的问题或指令...（可使用工具命令）',
        'send': '发送',
        'stop': '停止',
        'ui_made_by': 'Web界面制作:',
        'powered_by': 'Powered by OpenManus -',

        // プロジェクト管理関連
        'projects': '项目',
        'new_project': '新建',
        'rename_project': '重命名',
        'delete_project': '删除',
        'sessions': '对话',
        'new_session': '新建',
        'rename_session': '重命名',
        'delete_session': '删除',
        'project_details': '项目详情',
        'save_project': '保存',
        'project_name_placeholder': '项目名称',
        'project_instructions': '项目指示',
        'project_instructions_placeholder': '输入项目指示 - 这些指示将应用于所有对话',
        'confirm_delete_project': '确定要删除这个项目吗？所有相关对话也会被删除。',
        'confirm_delete_session': '确定要删除这个对话吗？',
        'rename_project_prompt': '请输入新的项目名称：',
        'rename_session_prompt': '请输入新的对话名称：',
        'project_saved': '项目已保存',
        'no_project_selected': '未选择项目',

        // ツール関連
        'tool_settings': '工具设置',
    },

    // 英語
    'en-US': {
        'app_title': 'OpenManus',
        'app_subtitle': 'AI Assistant - Web Version',
        'processing_progress': 'Processing Progress',
        'ai_thinking_process': 'AI Thinking Process',
        'records_count': '0 records',
        'auto_scroll': 'Auto-scroll',
        'clear': 'Clear',
        'workspace_files': 'Workspace Files',
        'refresh_countdown': 'Refresh in 5s',
        'refresh': 'Refresh',
        'conversation': 'Conversation',
        'file_name': 'File Name',
        'close': 'Close',
        'input_placeholder': 'Enter your question or instruction... (Tool commands are available)',
        'send': 'Send',
        'stop': 'Stop',
        'ui_made_by': 'Web UI by:',
        'powered_by': 'Powered by OpenManus -',

        // Project management
        'projects': 'Projects',
        'new_project': 'New',
        'rename_project': 'Rename',
        'delete_project': 'Delete',
        'sessions': 'Sessions',
        'new_session': 'New',
        'rename_session': 'Rename',
        'delete_session': 'Delete',
        'project_details': 'Project Details',
        'save_project': 'Save',
        'project_name_placeholder': 'Project Name',
        'project_instructions': 'Project Instructions',
        'project_instructions_placeholder': 'Enter project instructions - these will apply to all sessions',
        'confirm_delete_project': 'Are you sure you want to delete this project? All related sessions will also be deleted.',
        'confirm_delete_session': 'Are you sure you want to delete this session?',
        'rename_project_prompt': 'Please enter a new project name:',
        'rename_session_prompt': 'Please enter a new session name:',
        'project_saved': 'Project saved',
        'no_project_selected': 'No project selected',

        // Tools related
        'tool_settings': 'Tool Settings',
    },

    // 日本語
    'ja-JP': {
        'app_title': 'OpenManus',
        'app_subtitle': 'AI アシスタント - Web版',
        'processing_progress': '処理の進捗',
        'ai_thinking_process': 'AI思考プロセス',
        'records_count': '0 件',
        'auto_scroll': '自動スクロール',
        'clear': 'クリア',
        'workspace_files': 'ワークスペースファイル',
        'refresh_countdown': '5秒後に更新',
        'refresh': '更新',
        'conversation': '会話',
        'file_name': 'ファイル名',
        'close': '閉じる',
        'input_placeholder': '質問や指示を入力してください...（ツールコマンドも使用可能）',
        'send': '送信',
        'stop': '停止',
        'ui_made_by': 'Web UI 制作:',
        'powered_by': 'Powered by OpenManus -',

        // プロジェクト管理関連
        'projects': 'プロジェクト',
        'new_project': '新規',
        'rename_project': '名前変更',
        'delete_project': '削除',
        'sessions': 'セッション',
        'new_session': '新規',
        'rename_session': '名前変更',
        'delete_session': '削除',
        'project_details': 'プロジェクト詳細',
        'save_project': '保存',
        'project_name_placeholder': 'プロジェクト名',
        'project_instructions': 'プロジェクト指示',
        'project_instructions_placeholder': 'プロジェクト指示を入力 - これはすべてのセッションに適用されます',
        'confirm_delete_project': 'このプロジェクトを削除してもよろしいですか？関連するすべてのセッションも削除されます。',
        'confirm_delete_session': 'このセッションを削除してもよろしいですか？',
        'rename_project_prompt': '新しいプロジェクト名を入力してください：',
        'rename_session_prompt': '新しいセッション名を入力してください：',
        'project_saved': 'プロジェクトを保存しました',
        'no_project_selected': 'プロジェクトが選択されていません',

        // ツール関連
        'tool_settings': 'ツール設定',
    }
};

// デフォルト言語
let currentLanguage = 'ja-JP';

/**
 * 言語を設定する
 * @param {string} language - 言語コード
 */
function setLanguage(language) {
    if (translations[language]) {
        currentLanguage = language;
        updatePageTranslations();
        saveLanguagePreference(language);
        
        // バックエンドにも言語設定を通知
        fetch('/api/set_language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ language: language })
        }).catch(error => {
            console.error('言語設定の更新中にエラーが発生しました:', error);
        });
    } else {
        console.error('サポートされていない言語:', language);
    }
}

/**
 * 言語設定を保存する
 * @param {string} language - 言語コード
 */
function saveLanguagePreference(language) {
    localStorage.setItem('openmanusLanguage', language);
}

/**
 * 保存された言語設定を読み込む
 * @returns {string} 言語コード
 */
function loadLanguagePreference() {
    return localStorage.getItem('openmanusLanguage') || 'ja-JP';
}

/**
 * ページの翻訳を更新する
 */
function updatePageTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[currentLanguage][key]) {
            // タグの種類に応じて処理を分ける
            if (element.tagName === 'INPUT' && element.type === 'text') {
                element.placeholder = translations[currentLanguage][key];
            } else if (element.tagName === 'TEXTAREA') {
                element.placeholder = translations[currentLanguage][key];
            } else {
                element.textContent = translations[currentLanguage][key];
            }
        }
    });
}

/**
 * 指定したキーに対応する翻訳テキストを取得する
 * @param {string} key - 翻訳キー
 * @returns {string} 翻訳テキスト
 */
function t(key) {
    return translations[currentLanguage][key] || key;
}

/**
 * ブラウザの言語から最適な言語を決定する
 * @returns {string} 言語コード
 */
function detectBrowserLanguage() {
    const browserLang = navigator.language || navigator.userLanguage;
    
    // 言語コードの前半部分だけを取得（例：'ja-JP' -> 'ja'）
    const langPrefix = browserLang.split('-')[0];
    
    // サポートされている言語のうち、ブラウザの言語に最も近いものを選択
    if (langPrefix === 'zh') {
        return 'zh-CN';
    } else if (langPrefix === 'ja') {
        return 'ja-JP';
    } else {
        return 'en-US'; // デフォルト
    }
}

/**
 * 初期化処理
 */
function initI18n() {
    // 保存された言語設定を読み込む、なければブラウザの言語を検出
    const savedLanguage = loadLanguagePreference();
    const detectedLanguage = detectBrowserLanguage();
    
    // 言語設定
    setLanguage(savedLanguage || detectedLanguage);
    
    // 言語セレクターのイベントリスナー
    const languageSelector = document.getElementById('language-selector');
    if (languageSelector) {
        languageSelector.value = currentLanguage;
        languageSelector.addEventListener('change', (e) => {
            setLanguage(e.target.value);
        });
    }
}

// ページロード時に初期化
document.addEventListener('DOMContentLoaded', initI18n);

// エクスポート
export { setLanguage, t, currentLanguage, initI18n };
