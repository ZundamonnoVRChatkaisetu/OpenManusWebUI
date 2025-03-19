// connected_interface.js - 主要JavaScript文件，负责初始化和协调其他模块

// 导入各个管理器类
import { WebSocketManager } from '/static/connected_websocketManager.js';
import { ChatManager } from '/static/connected_chatManager.js';
import { ThinkingManager } from '/static/connected_thinkingManager.js';
import { WorkspaceManager } from '/static/connected_workspaceManager.js';
import { FileViewerManager } from '/static/connected_fileViewerManager.js';
import { ProjectManager } from '/static/project_manager.js';
import { initLanguage, setLanguage, updatePageTexts, t } from '/static/i18n.js';

// 主应用类
class App {
    constructor() {
        this.sessionId = null;
        this.isProcessing = false;

        // 初始化各个管理器
        this.websocketManager = new WebSocketManager(this.handleWebSocketMessage.bind(this));
        this.chatManager = new ChatManager(this.handleSendMessage.bind(this));
        this.thinkingManager = new ThinkingManager();
        this.workspaceManager = new WorkspaceManager(this.handleFileClick.bind(this));
        this.fileViewerManager = new FileViewerManager();
        this.projectManager = new ProjectManager(this.handleSessionSelect.bind(this));

        // 绑定UI事件
        this.bindEvents();
    }

    // 初始化应用
    init() {
        console.log('OpenManus Web应用初始化...');

        // 初始化语言设置
        const currentLang = initLanguage();
        document.getElementById('language-selector').value = currentLang;
        
        // 更新前端页面文本
        updatePageTexts();
        
        // 更新后端语言设置
        this.updateBackendLanguage(currentLang);

        // 初始化各个管理器
        this.chatManager.init();
        this.thinkingManager.init();
        this.workspaceManager.init();
        this.fileViewerManager.init();
        this.projectManager.init();

        // 加载工作区文件
        this.loadWorkspaceFiles();
    }

    // 绑定UI事件
    bindEvents() {
        // 停止按钮
        document.getElementById('stop-btn').addEventListener('click', () => {
            if (this.sessionId && this.isProcessing) {
                this.stopProcessing();
            }
        });

        // 清除按钮
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.chatManager.clearMessages();
        });

        // 清除思考记录按钮
        document.getElementById('clear-thinking').addEventListener('click', () => {
            this.thinkingManager.clearThinking();
        });

        // 刷新文件按钮
        document.getElementById('refresh-files').addEventListener('click', () => {
            this.loadWorkspaceFiles();
        });

        // 语言选择器
        document.getElementById('language-selector').addEventListener('change', (event) => {
            const selectedLang = event.target.value;
            setLanguage(selectedLang);
            updatePageTexts();
            this.updateDynamicTexts();
            this.updateBackendLanguage(selectedLang); // 更新后端语言设置
        });
    }

    // 处理会话选择
    handleSessionSelect(sessionId) {
        console.log(`选择会话: ${sessionId}`);
        this.sessionId = sessionId;
        
        // 这里可以添加加载会话消息的逻辑
        // 例如: this.loadSessionMessages(sessionId);
    }

    // 更新后端语言设置
    async updateBackendLanguage(language) {
        try {
            const response = await fetch('/api/set_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: language }),
            });

            if (!response.ok) {
                console.error(`更新后端语言设置失败: ${response.status}`);
            }
        } catch (error) {
            console.error('更新后端语言设置出错:', error);
        }
    }

    // 更新动态生成的文本
    updateDynamicTexts() {
        // 更新状态指示器
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator.textContent.includes('正在处理')) {
            statusIndicator.textContent = t('processing_request');
        } else if (statusIndicator.textContent.includes('处理已停止')) {
            statusIndicator.textContent = t('processing_stopped');
        } else if (statusIndicator.textContent.includes('已连接到服务器')) {
            statusIndicator.textContent = t('connection_established');
        } else if (statusIndicator.textContent.includes('已送接到服务器')) {
            statusIndicator.textContent = t('sent_to_server');
        }

        // 更新记录计数
        const recordCount = document.getElementById('record-count');
        const count = parseInt(recordCount.textContent);
        if (!isNaN(count)) {
            recordCount.textContent = t('records_count', { count });
        }

        // 更新刷新倒计时
        const refreshCountdown = document.getElementById('refresh-countdown');
        const seconds = refreshCountdown.textContent.match(/\d+/);
        if (seconds) {
            refreshCountdown.textContent = t('refresh_countdown', { seconds: seconds[0] });
        }
    }

    // 处理发送消息
    async handleSendMessage(message) {
        if (this.isProcessing) {
            console.log(t('processing_in_progress'));
            return;
        }

        this.isProcessing = true;
        document.getElementById('send-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('status-indicator').textContent = t('processing_request');

        try {
            // 获取当前项目和会话信息
            const { projectId, sessionId } = this.projectManager.getCurrentSession();
            
            // 发送API请求创建新会话，如果有项目和会话ID则包含
            const payload = { 
                prompt: message
            };
            
            if (projectId) {
                payload.project_id = projectId;
            }
            
            if (sessionId) {
                payload.session_id = sessionId;
            }
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            // 添加用户消息到聊天
            this.chatManager.addUserMessage(message);

            // 连接WebSocket
            this.websocketManager.connect(this.sessionId);

            // 重置思考记录
            this.thinkingManager.clearThinking();

        } catch (error) {
            console.error(t('send_message_error', { message: error.message }), error);
            this.chatManager.addSystemMessage(t('error_occurred', { message: error.message }));
            this.isProcessing = false;
            document.getElementById('send-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            document.getElementById('status-indicator').textContent = '';
        }
    }

    // 处理WebSocket消息
    handleWebSocketMessage(data) {
        // 处理状态更新
        if (data.status) {
            if (data.status === 'completed' || data.status === 'error' || data.status === 'stopped') {
                this.isProcessing = false;
                document.getElementById('send-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
                document.getElementById('status-indicator').textContent = '';

                // 如果有结果，显示结果
                if (data.result) {
                    this.chatManager.addAIMessage(data.result);
                }
            }
        }

        // 处理思考步骤
        if (data.thinking_steps && data.thinking_steps.length > 0) {
            this.thinkingManager.addThinkingSteps(data.thinking_steps);
        }

        // 处理终端输出
        if (data.terminal_output && data.terminal_output.length > 0) {
            console.log('收到终端输出:', data.terminal_output);
        }

        // 处理系统日志 - 将系统日志转换为思考步骤并显示
        if (data.system_logs && data.system_logs.length > 0) {
            console.log('收到系统日志:', data.system_logs);

            // 将系统日志转换为思考步骤格式并添加到思考时间线
            const logSteps = data.system_logs.map(log => {
                return {
                    message: log,
                    type: "system_log",
                    details: null,
                    timestamp: Date.now() / 1000
                };
            });

            this.thinkingManager.addThinkingSteps(logSteps);
        }

        // 处理聊天日志
        if (data.chat_logs && data.chat_logs.length > 0) {
            console.log('收到聊天日志:', data.chat_logs);
        }

        // 如果处理完成，刷新工作区文件
        if (data.status === 'completed') {
            setTimeout(() => this.loadWorkspaceFiles(), 1000);
        }
    }

    // 停止处理
    async stopProcessing() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/chat/${this.sessionId}/stop`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }

            console.log('处理已停止');
            this.chatManager.addSystemMessage(t('processing_stopped'));
            document.getElementById('status-indicator').textContent = t('processing_stopped');
            document.getElementById('send-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            this.isProcessing = false;

        } catch (error) {
            console.error(t('stop_processing_error', { message: error.message }), error);
            this.chatManager.addSystemMessage(t('error_occurred', { message: error.message }));
        }
    }

    // 加载工作区文件
    async loadWorkspaceFiles() {
        try {
            const response = await fetch('/api/files');
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }

            const data = await response.json();
            this.workspaceManager.updateWorkspaces(data.workspaces);

        } catch (error) {
            console.error(t('load_workspace_error', { message: error.message }), error);
        }
    }

    // 处理文件点击
    async handleFileClick(filePath) {
        try {
            const response = await fetch(`/api/files/${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }

            const data = await response.json();
            this.fileViewerManager.showFile(data.name, data.content);

        } catch (error) {
            console.error(t('load_file_error', { message: error.message }), error);
            this.chatManager.addSystemMessage(t('error_occurred', { message: error.message }));
        }
    }
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();

    // 将app实例暴露到全局，方便调试
    window.app = app;
});
