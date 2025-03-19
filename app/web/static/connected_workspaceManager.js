// connected_workspaceManager.js - 工作区文件管理
import { t } from '/static/i18n.js';

export class WorkspaceManager {
    constructor(handleFileClick) {
        this.workspaces = [];
        this.handleFileClick = handleFileClick;
        this.refreshIntervalId = null;
        this.countdownInterval = null;
        this.currentCountdown = 0;
        this.refreshSeconds = 5;
        this.currentProjectId = null; // 現在選択されているプロジェクトID
    }

    init() {
        // 工作区容器
        this.workspaceContainer = document.getElementById('workspace-files');
        
        // 刷新倒计时显示元素
        this.refreshCountdown = document.getElementById('refresh-countdown');
        
        // 自动刷新启动
        this.startRefreshCountdown();
    }

    // プロジェクトIDを設定
    setCurrentProjectId(projectId) {
        this.currentProjectId = projectId;
        // 即座にファイル一覧を更新
        this.loadWorkspaceFiles();
    }

    // プロジェクトIDに基づいてワークスペースファイルを取得
    async loadWorkspaceFiles() {
        try {
            let url = '/api/files';
            if (this.currentProjectId) {
                url += `?project_id=${this.currentProjectId}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const data = await response.json();
            this.updateWorkspaces(data.workspaces);
            
            // リフレッシュカウントダウンをリセット
            this.resetRefreshCountdown();
        } catch (error) {
            console.error(t('load_workspace_error', { message: error.message }), error);
        }
    }

    // 更新工作区文件列表
    updateWorkspaces(workspaces) {
        this.workspaces = workspaces || [];
        this.renderWorkspaces();
    }

    // 渲染工作区文件列表
    renderWorkspaces() {
        if (!this.workspaceContainer) return;
        
        // 清空容器
        this.workspaceContainer.innerHTML = '';
        
        // 如果没有工作区，显示提示信息
        if (this.workspaces.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = t('no_workspace_files');
            this.workspaceContainer.appendChild(emptyMessage);
            return;
        }
        
        // 遍历工作区
        this.workspaces.forEach(workspace => {
            // 创建工作区条目
            const workspaceItem = document.createElement('div');
            workspaceItem.className = 'workspace-item';
            
            // 工作区图标
            const iconSpan = document.createElement('span');
            iconSpan.className = 'workspace-icon';
            iconSpan.textContent = '📁';
            workspaceItem.appendChild(iconSpan);
            
            // 工作区详情
            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'workspace-details';
            
            // 工作区名称
            const nameDiv = document.createElement('div');
            nameDiv.className = 'workspace-name';
            nameDiv.textContent = workspace.name;
            detailsDiv.appendChild(nameDiv);
            
            // 修改日期
            const dateDiv = document.createElement('div');
            dateDiv.className = 'workspace-date';
            const modifiedDate = new Date(workspace.modified * 1000);
            dateDiv.textContent = modifiedDate.toLocaleString();
            detailsDiv.appendChild(dateDiv);
            
            workspaceItem.appendChild(detailsDiv);
            this.workspaceContainer.appendChild(workspaceItem);
            
            // 展开点击事件 - 显示该工作区的文件
            workspaceItem.addEventListener('click', () => {
                workspaceItem.classList.toggle('expanded');
                
                // 如果已经显示文件列表，则移除
                const existingFilesList = workspaceItem.nextElementSibling;
                if (existingFilesList && existingFilesList.classList.contains('files-list')) {
                    this.workspaceContainer.removeChild(existingFilesList);
                    return;
                }
                
                // 创建文件列表容器
                const filesList = document.createElement('div');
                filesList.className = 'files-list';
                
                // 添加文件项
                workspace.files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    
                    // 文件图标
                    const fileIconSpan = document.createElement('span');
                    fileIconSpan.className = 'file-icon';
                    fileIconSpan.textContent = this.getFileIcon(file.type);
                    fileItem.appendChild(fileIconSpan);
                    
                    // 文件详情
                    const fileDetailsDiv = document.createElement('div');
                    fileDetailsDiv.className = 'file-details';
                    
                    // 文件名
                    const fileNameDiv = document.createElement('div');
                    fileNameDiv.className = 'file-name';
                    fileNameDiv.textContent = file.name;
                    fileDetailsDiv.appendChild(fileNameDiv);
                    
                    // 文件元信息（类型和大小）
                    const fileMetaDiv = document.createElement('div');
                    fileMetaDiv.className = 'file-meta';
                    const fileSize = this.formatFileSize(file.size);
                    fileMetaDiv.textContent = `${file.type.toUpperCase()} · ${fileSize}`;
                    fileDetailsDiv.appendChild(fileMetaDiv);
                    
                    fileItem.appendChild(fileDetailsDiv);
                    filesList.appendChild(fileItem);
                    
                    // 添加文件点击事件
                    fileItem.addEventListener('click', (e) => {
                        e.stopPropagation(); // 阻止事件冒泡
                        // 移除之前选中的文件
                        document.querySelectorAll('.file-item.selected').forEach(item => {
                            item.classList.remove('selected');
                        });
                        
                        // 标记当前文件为选中
                        fileItem.classList.add('selected');
                        
                        // 调用回调函数
                        if (this.handleFileClick) {
                            this.handleFileClick(file.path);
                        }
                    });
                });
                
                // 将文件列表添加到工作区后面
                this.workspaceContainer.insertBefore(filesList, workspaceItem.nextSibling);
            });
        });
    }

    // 根据文件类型获取图标
    getFileIcon(fileType) {
        const icons = {
            'txt': '📄',  // 文本文件
            'md': '📝',   // Markdown文件
            'html': '🌐', // HTML文件
            'css': '🎨',  // CSS文件
            'js': '📜',   // JavaScript文件
            'py': '🐍',   // Python文件
            'json': '📋', // JSON文件
            // 可以添加更多文件类型的图标
        };
        
        return icons[fileType.toLowerCase()] || '📄'; // 默认图标
    }

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + ' B';
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(1) + ' KB';
        } else {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
    }

    // 启动刷新倒计时
    startRefreshCountdown() {
        this.currentCountdown = this.refreshSeconds;
        this.updateCountdownDisplay();
        
        // 清除之前的计时器
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // 设置倒计时
        this.countdownInterval = setInterval(() => {
            this.currentCountdown--;
            this.updateCountdownDisplay();
            
            if (this.currentCountdown <= 0) {
                // 到达零时重置并刷新文件
                this.loadWorkspaceFiles();
            }
        }, 1000);
    }

    // 重置刷新倒计时
    resetRefreshCountdown() {
        this.currentCountdown = this.refreshSeconds;
        this.updateCountdownDisplay();
    }

    // 更新倒计时显示
    updateCountdownDisplay() {
        if (this.refreshCountdown) {
            if (this.currentCountdown > 0) {
                this.refreshCountdown.textContent = t('refresh_countdown', { seconds: this.currentCountdown });
            } else {
                this.refreshCountdown.textContent = t('refreshing');
            }
        }
    }

    // 设置刷新间隔
    setRefreshInterval(seconds) {
        this.refreshSeconds = seconds;
        this.resetRefreshCountdown();
    }
}
