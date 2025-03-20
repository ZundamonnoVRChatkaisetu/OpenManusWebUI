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
        'projects': '项目',
        'sessions': '会话',
        'project_details': '项目详情',
        'project_instructions': '项目指示',
        
        // 按钮和控件
        'auto_scroll': '自动滚动',
        'clear': '清空',
        'refresh': '刷新',
        'send': '发送',
        'stop': '停止',
        'close': '关闭',
        'new_project': '新建',
        'save_project': '保存',
        'new_session': '新建',
        'delete_project': '删除',
        'rename_project': '重命名',
        'delete_session': '删除',
        'rename_session': '重命名',
        
        // 状态和提示
        'records_count': '{count} 条记录',
        'refresh_countdown': '{seconds}秒后刷新',
        'processing_request': '正在处理您的请求...',
        'processing_stopped': '处理已停止',
        'file_name': '文件名',
        'no_projects': '暂无项目',
        'no_sessions': '暂无会话',
        'untitled_project': '未命名项目',
        'untitled_session': '未命名会话',
        'enter_project_name': '请输入项目名称',
        'project_saved': '项目已保存',
        'project_deleted': '项目已删除',
        'project_renamed': '项目已重命名',
        'session_deleted': '会话已删除',
        'session_renamed': '会话已重命名',
        'confirm_delete_project': '确定要删除此项目吗？该操作不可撤销。',
        'confirm_delete_session': '确定要删除此会话吗？该操作不可撤销。',
        'enter_new_project_name': '请输入新的项目名称',
        'enter_new_session_name': '请输入新的会话名称',
        
        // 输入框占位符
        'input_placeholder': '输入您的问题或指令...',
        'project_name_placeholder': '项目名称',
        'project_instructions_placeholder': '输入项目指示...',
        
        // 页脚
        'ui_made_by': 'Web界面制作:',
        'powered_by': 'Powered by OpenManus -',
        
        // 错误消息
        'api_error': 'API错误: {status}',
        'send_message_error': '发送消息错误: {message}',
        'stop_processing_error': '停止处理错误: {message}',
        'load_workspace_error': '加载工作区文件错误: {message}',
        'load_file_error': '加载文件内容错误: {message}',
        'project_create_failed': '创建项目失败',
        'project_save_failed': '保存项目失败',
        'session_create_failed': '创建会话失败',
        'project_delete_failed': '删除项目失败',
        'project_rename_failed': '重命名项目失败',
        'session_delete_failed': '删除会话失败',
        'session_rename_failed': '重命名会话失败',
        'add_instruction_error': '添加指示错误: {message}',
        
        // 系统消息
        'error_occurred': '发生错误: {message}',
        'processing_in_progress': '正在处理中，请等待...',
        
        // 语言切换
        'language': '语言',
        'switch_language': '切换语言',

        // WebSocket状态消息
        'connection_established': '已连接到服务器...',
        'connection_failed': '连接已断开，请刷新页面重试',
        'reconnecting': '连接已断开，正在尝试重连 ({current}/{max})...',

        // 工作区文件消息
        'no_workspace_files': '没有工作区文件',
        'refreshing': '刷新中...',

        // 发送状态
        'sent_to_server': '已送接到服务器...',
        
        // 追加指示関連
        'additional_instructions_enabled': '(可以继续输入指令)',
        'instruction_added': '已添加指示，正在更新执行中的任务...',
        'instruction_queued': '您的指令已加入队列，将在当前处理完成后执行',
        'queued_messages_cleared': '已清除 {count} 条排队消息',
        'tool_settings': '工具设置'
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
        'projects': 'Projects',
        'sessions': 'Sessions',
        'project_details': 'Project Details',
        'project_instructions': 'Project Instructions',
        
        // 按钮和控件
        'auto_scroll': 'Auto Scroll',
        'clear': 'Clear',
        'refresh': 'Refresh',
        'send': 'Send',
        'stop': 'Stop',
        'close': 'Close',
        'new_project': 'New',
        'save_project': 'Save',
        'new_session': 'New',
        'delete_project': 'Delete',
        'rename_project': 'Rename',
        'delete_session': 'Delete',
        'rename_session': 'Rename',
        
        // 状态和提示
        'records_count': '{count} Records',
        'refresh_countdown': 'Refresh in {seconds}s',
        'processing_request': 'Processing your request...',
        'processing_stopped': 'Processing stopped',
        'file_name': 'File Name',
        'no_projects': 'No projects',
        'no_sessions': 'No sessions',
        'untitled_project': 'Untitled Project',
        'untitled_session': 'Untitled Session',
        'enter_project_name': 'Enter project name',
        'project_saved': 'Project saved',
        'project_deleted': 'Project deleted',
        'project_renamed': 'Project renamed',
        'session_deleted': 'Session deleted',
        'session_renamed': 'Session renamed',
        'confirm_delete_project': 'Are you sure you want to delete this project? This action cannot be undone.',
        'confirm_delete_session': 'Are you sure you want to delete this session? This action cannot be undone.',
        'enter_new_project_name': 'Enter new project name',
        'enter_new_session_name': 'Enter new session name',
        
        // 输入框占位符
        'input_placeholder': 'Enter your question or instruction...',
        'project_name_placeholder': 'Project name',
        'project_instructions_placeholder': 'Enter project instructions...',
        
        // 页脚
        'ui_made_by': 'UI Made by:',
        'powered_by': 'Powered by OpenManus -',
        
        // 错误消息
        'api_error': 'API Error: {status}',
        'send_message_error': 'Send message error: {message}',
        'stop_processing_error': 'Stop processing error: {message}',
        'load_workspace_error': 'Load workspace files error: {message}',
        'load_file_error': 'Load file content error: {message}',
        'project_create_failed': 'Failed to create project',
        'project_save_failed': 'Failed to save project',
        'session_create_failed': 'Failed to create session',
        'project_delete_failed': 'Failed to delete project',
        'project_rename_failed': 'Failed to rename project',
        'session_delete_failed': 'Failed to delete session',
        'session_rename_failed': 'Failed to rename session',
        'add_instruction_error': 'Error adding instruction: {message}',
        
        // 系统消息
        'error_occurred': 'Error occurred: {message}',
        'processing_in_progress': 'Processing in progress, please wait...',
        
        // 语言切换
        'language': 'Language',
        'switch_language': 'Switch Language',

        // WebSocket状态消息
        'connection_established': 'Connected to server...',
        'connection_failed': 'Connection lost, please refresh the page',
        'reconnecting': 'Connection lost, trying to reconnect ({current}/{max})...',

        // 工作区文件消息
        'no_workspace_files': 'No workspace files',
        'refreshing': 'Refreshing...',

        // 发送状态
        'sent_to_server': 'Sent to server...',
        
        // 追加指示関連
        'additional_instructions_enabled': '(You can add additional instructions)',
        'instruction_added': 'Instruction added, updating current task...',
        'instruction_queued': 'Your instruction has been queued and will be processed after the current task is completed',
        'queued_messages_cleared': 'Cleared {count} queued messages',
        'tool_settings': 'Tool Settings'
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
        'projects': 'プロジェクト',
        'sessions': 'セッション',
        'project_details': 'プロジェクト詳細',
        'project_instructions': 'プロジェクト指示',
        
        // ボタンとコントロール
        'auto_scroll': '自動スクロール',
        'clear': 'クリア',
        'refresh': '更新',
        'send': '送信',
        'stop': '停止',
        'close': '閉じる',
        'new_project': '新規',
        'save_project': '保存',
        'new_session': '新規',
        'delete_project': '削除',
        'rename_project': '名前変更',
        'delete_session': '削除',
        'rename_session': '名前変更',
        
        // ステータスとヒント
        'records_count': '{count} 件',
        'refresh_countdown': '{seconds}秒後に更新',
        'processing_request': 'リクエストを処理中...',
        'processing_stopped': '処理が停止しました',
        'file_name': 'ファイル名',
        'no_projects': 'プロジェクトがありません',
        'no_sessions': 'セッションがありません',
        'untitled_project': '無題のプロジェクト',
        'untitled_session': '無題のセッション',
        'enter_project_name': 'プロジェクト名を入力',
        'project_saved': '保存しました',
        'project_deleted': 'プロジェクトを削除しました',
        'project_renamed': 'プロジェクト名を変更しました',
        'session_deleted': 'セッションを削除しました',
        'session_renamed': 'セッション名を変更しました',
        'confirm_delete_project': 'このプロジェクトを削除してもよろしいですか？この操作は元に戻せません。',
        'confirm_delete_session': 'このセッションを削除してもよろしいですか？この操作は元に戻せません。',
        'enter_new_project_name': '新しいプロジェクト名を入力してください',
        'enter_new_session_name': '新しいセッション名を入力してください',
        
        // 入力欄プレースホルダー
        'input_placeholder': '質問や指示を入力してください...',
        'project_name_placeholder': 'プロジェクト名',
        'project_instructions_placeholder': 'プロジェクト指示を入力...',
        
        // フッター
        'ui_made_by': 'UI制作:',
        'powered_by': 'Powered by OpenManus -',
        
        // エラーメッセージ
        'api_error': 'APIエラー: {status}',
        'send_message_error': 'メッセージ送信エラー: {message}',
        'stop_processing_error': '処理停止エラー: {message}',
        'load_workspace_error': 'ワークスペースファイル読み込みエラー: {message}',
        'load_file_error': 'ファイル内容読み込みエラー: {message}',
        'project_create_failed': 'プロジェクト作成に失敗しました',
        'project_save_failed': 'プロジェクト保存に失敗しました',
        'session_create_failed': 'セッション作成に失敗しました',
        'project_delete_failed': 'プロジェクト削除に失敗しました',
        'project_rename_failed': 'プロジェクト名変更に失敗しました',
        'session_delete_failed': 'セッション削除に失敗しました',
        'session_rename_failed': 'セッション名変更に失敗しました',
        'add_instruction_error': '追加指示の送信エラー: {message}',
        
        // システムメッセージ
        'error_occurred': 'エラーが発生しました: {message}',
        'processing_in_progress': '処理中です。お待ちください...',
        
        // 言語切り替え
        'language': '言語',
        'switch_language': '言語を切り替える',

        // WebSocketステータスメッセージ
        'connection_established': 'サーバーに接続しました...',
        'connection_failed': '接続が切断されました。ページを更新してください',
        'reconnecting': '接続が切断されました。再接続を試みています ({current}/{max})...',

        // ワークスペースファイルメッセージ
        'no_workspace_files': 'ワークスペースファイルなし',
        'refreshing': '更新中...',

        // 送信状態
        'sent_to_server': 'サーバーに送信済み...',
        
        // 追加指示関連
        'additional_instructions_enabled': '(追加指示の入力が可能です)',
        'instruction_added': '指示を追加しました。現在のタスクを更新しています...',
        'instruction_queued': '指示はキューに追加されました。現在の処理完了後に実行されます',
        'queued_messages_cleared': '{count}件のキュー内メッセージをクリアしました',
        'tool_settings': 'ツール設定'
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
