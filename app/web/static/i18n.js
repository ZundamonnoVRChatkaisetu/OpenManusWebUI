// i18n.js - 国际化模块，管理中英文翻译

// 支持的语言
export const SUPPORTED_LANGUAGES = {
    'zh-CN': '中文',
    'en-US': 'English',
    'ja-JP': '日本語'
};

// 翻译文本
export const translations = {
    // 中文翻译
    'zh-CN': {
        // 页面标题和头部
        'page_title': 'OpenManus Web - 网页版',
        'app_title': 'OpenManus',
        'app_subtitle': 'AI智能助手 - 网页版',
        
        // 主要区域标题
        'processing_progress': '处理进度',
        'ai_thinking_process': 'AI思考过程',
        'workspace_files': '工作区文件',
        'conversation': '对话',
        
        // 按钮和控件
        'auto_scroll': '自动滚动',
        'clear': '清空',
        'refresh': '刷新',
        'send': '发送',
        'stop': '停止',
        'close': '关闭',
        
        // 状态和提示
        'records_count': '{count} 条记录',
        'refresh_countdown': '{seconds}秒后刷新',
        'processing_request': '正在处理您的请求...',
        'processing_stopped': '处理已停止',
        'file_name': '文件名',
        
        // 输入框占位符
        'input_placeholder': '输入您的问题或指令...',
        
        // 页脚
        'ui_made_by': 'Web界面制作:',
        'powered_by': 'Powered by OpenManus -',
        
        // 错误消息
        'api_error': 'API错误: {status}',
        'send_message_error': '发送消息错误: {message}',
        'stop_processing_error': '停止处理错误: {message}',
        'load_workspace_error': '加载工作区文件错误: {message}',
        'load_file_error': '加载文件内容错误: {message}',
        
        // 系统消息
        'error_occurred': '发生错误: {message}',
        'processing_in_progress': '正在处理中，请等待...',
        
        // 语言切换
        'language': '语言',
        'switch_language': '切换语言'
    },
    
    // 英文翻译
    'en-US': {
        // 页面标题和头部
        'page_title': 'OpenManus Web - Web Version',
        'app_title': 'OpenManus',
        'app_subtitle': 'AI Assistant - Web Version',
        
        // 主要区域标题
        'processing_progress': 'Processing Progress',
        'ai_thinking_process': 'AI Thinking Process',
        'workspace_files': 'Workspace Files',
        'conversation': 'Conversation',
        
        // 按钮和控件
        'auto_scroll': 'Auto Scroll',
        'clear': 'Clear',
        'refresh': 'Refresh',
        'send': 'Send',
        'stop': 'Stop',
        'close': 'Close',
        
        // 状态和提示
        'records_count': '{count} Records',
        'refresh_countdown': 'Refresh in {seconds}s',
        'processing_request': 'Processing your request...',
        'processing_stopped': 'Processing stopped',
        'file_name': 'File Name',
        
        // 输入框占位符
        'input_placeholder': 'Enter your question or instruction...',
        
        // 页脚
        'ui_made_by': 'UI Made by:',
        'powered_by': 'Powered by OpenManus -',
        
        // 错误消息
        'api_error': 'API Error: {status}',
        'send_message_error': 'Send message error: {message}',
        'stop_processing_error': 'Stop processing error: {message}',
        'load_workspace_error': 'Load workspace files error: {message}',
        'load_file_error': 'Load file content error: {message}',
        
        // 系统消息
        'error_occurred': 'Error occurred: {message}',
        'processing_in_progress': 'Processing in progress, please wait...',
        
        // 语言切换
        'language': 'Language',
        'switch_language': 'Switch Language'
    },

    // 日本語翻訳
    'ja-JP': {
        // ページタイトルとヘッダー
        'page_title': 'OpenManus Web - ウェブ版',
        'app_title': 'OpenManus',
        'app_subtitle': 'AIアシスタント - ウェブ版',
        
        // 主要エリアタイトル
        'processing_progress': '処理の進捗',
        'ai_thinking_process': 'AI思考プロセス',
        'workspace_files': 'ワークスペースファイル',
        'conversation': '会話',
        
        // ボタンとコントロール
        'auto_scroll': '自動スクロール',
        'clear': 'クリア',
        'refresh': '更新',
        'send': '送信',
        'stop': '停止',
        'close': '閉じる',
        
        // ステータスとヒント
        'records_count': '{count} 件',
        'refresh_countdown': '{seconds}秒後に更新',
        'processing_request': 'リクエストを処理中...',
        'processing_stopped': '処理が停止しました',
        'file_name': 'ファイル名',
        
        // 入力欄プレースホルダー
        'input_placeholder': '質問や指示を入力してください...',
        
        // フッター
        'ui_made_by': 'UI制作:',
        'powered_by': 'Powered by OpenManus -',
        
        // エラーメッセージ
        'api_error': 'APIエラー: {status}',
        'send_message_error': 'メッセージ送信エラー: {message}',
        'stop_processing_error': '処理停止エラー: {message}',
        'load_workspace_error': 'ワークスペースファイル読み込みエラー: {message}',
        'load_file_error': 'ファイル内容読み込みエラー: {message}',
        
        // システムメッセージ
        'error_occurred': 'エラーが発生しました: {message}',
        'processing_in_progress': '処理中です。お待ちください...',
        
        // 言語切り替え
        'language': '言語',
        'switch_language': '言語を切り替える'
    }
};

// 当前语言
let currentLanguage = 'zh-CN';

// 获取浏览器语言
export function getBrowserLanguage() {
    const browserLang = navigator.language || navigator.userLanguage;
    // 根据浏览器语言返回合适的界面语言
    if (browserLang.startsWith('zh')) {
        return 'zh-CN';
    } else if (browserLang.startsWith('ja')) {
        return 'ja-JP';
    } else {
        return 'en-US';
    }
}

// 设置当前语言
export function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        // 保存语言设置到localStorage
        localStorage.setItem('openmanus_language', lang);
        return true;
    }
    return false;
}

// 获取当前语言
export function getCurrentLanguage() {
    return currentLanguage;
}

// 初始化语言设置
export function initLanguage() {
    // 首先尝试从localStorage获取语言设置
    const savedLang = localStorage.getItem('openmanus_language');
    if (savedLang && translations[savedLang]) {
        currentLanguage = savedLang;
    } else {
        // 如果没有保存的语言设置，使用浏览器语言
        currentLanguage = getBrowserLanguage();
    }
    return currentLanguage;
}

// 获取翻译文本
export function t(key, params = {}) {
    // 获取当前语言的翻译
    const translation = translations[currentLanguage];
    
    // 如果找不到翻译，尝试使用英文，如果英文也没有，返回键名
    let text = translation[key] || translations['en-US'][key] || key;
    
    // 替换参数
    Object.keys(params).forEach(param => {
        text = text.replace(`{${param}}`, params[param]);
    });
    
    return text;
}

// 更新页面上所有带有data-i18n属性的元素的文本
export function updatePageTexts() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        
        // 如果元素是输入框或文本区域，更新placeholder
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.getAttribute('placeholder')) {
                element.setAttribute('placeholder', t(key));
            }
        } else {
            // 否则更新内部文本
            element.textContent = t(key);
        }
    });
    
    // 更新页面标题
    document.title = t('page_title');
}
