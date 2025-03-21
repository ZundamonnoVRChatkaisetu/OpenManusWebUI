/**
 * generated_files_viewer.js
 * 
 * モデルが作成したファイルを表示するためのコンポーネント
 * 生成ファイルのリスト表示、プレビュー、クリップボードへのコピー機能を提供
 */

class GeneratedFilesViewer {
    constructor(containerId = 'generated-files-container') {
        // コンテナ要素
        this.container = document.getElementById(containerId);
        
        // 生成されたファイルのリスト
        this.files = [];
        
        // プレビュー要素
        this.previewElement = null;
        
        // 現在プレビュー中のファイルインデックス
        this.currentPreviewIndex = -1;
        
        // ヘッダー、リスト、プレビューエリア要素
        this.headerElement = null;
        this.listElement = null;
        this.previewElement = null;
        
        // 要素が見つからない場合は作成
        this.initializeContainer();
    }
    
    /**
     * コンテナ要素を初期化
     */
    initializeContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'generated-files-container';
            this.container.className = 'generated-files-container';
            
            // 適切な場所に挿入（思考プロセスの下、ツール使用状況の下）
            const toolUsageContainer = document.getElementById('tool-usage-container');
            if (toolUsageContainer) {
                toolUsageContainer.after(this.container);
            } else {
                const thinkingContainer = document.getElementById('thinking-process-container');
                if (thinkingContainer) {
                    thinkingContainer.after(this.container);
                } else {
                    // 左パネルの最初の要素として挿入
                    const leftPanel = document.querySelector('.left-panel');
                    if (leftPanel) {
                        leftPanel.insertBefore(this.container, leftPanel.firstChild);
                    }
                }
            }
        }
        
        // コンテナ内の要素を作成
        this.createContainerElements();
    }
    
    /**
     * コンテナ内の要素（ヘッダー、リスト、プレビュー）を作成
     */
    createContainerElements() {
        // コンテナをクリア
        this.container.innerHTML = '';
        
        // ヘッダー
        this.headerElement = document.createElement('div');
        this.headerElement.className = 'generated-files-header';
        
        const title = document.createElement('div');
        title.className = 'generated-files-title';
        title.innerHTML = `<span class="generated-files-title-icon">🗄️</span> ${this.getTranslation('generated_files', 'モデル作成ファイル')}`;
        
        const controls = document.createElement('div');
        controls.className = 'generated-files-controls';
        
        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = this.getTranslation('refresh', '更新');
        refreshBtn.addEventListener('click', () => this.refreshFilesList());
        controls.appendChild(refreshBtn);
        
        const clearBtn = document.createElement('button');
        clearBtn.textContent = this.getTranslation('clear', 'クリア');
        clearBtn.addEventListener('click', () => this.clearFiles());
        controls.appendChild(clearBtn);
        
        this.headerElement.appendChild(title);
        this.headerElement.appendChild(controls);
        
        // ファイルリスト
        this.listElement = document.createElement('ul');
        this.listElement.className = 'generated-files-list';
        
        // プレビューエリア
        this.previewElement = document.createElement('div');
        this.previewElement.className = 'generated-file-preview';
        
        // 全ての要素をコンテナに追加
        this.container.appendChild(this.headerElement);
        this.container.appendChild(this.listElement);
        this.container.appendChild(this.previewElement);
        
        // 空の状態を表示
        this.updateEmptyState();
    }
    
    /**
     * 生成されたファイルを追加
     * @param {Object} fileInfo - ファイル情報オブジェクト
     * @param {string} fileInfo.filename - ファイル名
     * @param {string} fileInfo.content_preview - 内容プレビュー
     * @param {string} fileInfo.project - プロジェクト名
     * @param {string} fileInfo.timestamp - タイムスタンプ（省略可）
     */
    addFile(fileInfo) {
        // タイムスタンプがない場合は現在時刻を設定
        if (!fileInfo.timestamp) {
            fileInfo.timestamp = new Date().toISOString();
        }
        
        // 同名ファイルがあれば上書き、なければ追加
        const existingIndex = this.files.findIndex(file => 
            file.filename === fileInfo.filename && file.project === fileInfo.project
        );
        
        if (existingIndex !== -1) {
            this.files[existingIndex] = fileInfo;
        } else {
            this.files.push(fileInfo);
        }
        
        // UI更新
        this.updateUI();
        
        // 新しいファイルの場合はハイライト
        if (existingIndex === -1) {
            const newIndex = this.files.length - 1;
            setTimeout(() => {
                const fileElement = this.listElement.children[newIndex];
                if (fileElement) {
                    fileElement.classList.add('file-highlight-animation');
                    setTimeout(() => {
                        fileElement.classList.remove('file-highlight-animation');
                    }, 1000);
                }
            }, 100);
        }
    }
    
    /**
     * 複数のファイルを一度に追加
     * @param {Array} filesInfo - ファイル情報オブジェクトの配列
     */
    addFiles(filesInfo) {
        if (!filesInfo || !filesInfo.length) return;
        
        // 各ファイルを追加
        filesInfo.forEach(fileInfo => {
            // タイムスタンプがない場合は現在時刻を設定
            if (!fileInfo.timestamp) {
                fileInfo.timestamp = new Date().toISOString();
            }
            
            // 同名ファイルがあれば上書き、なければ追加
            const existingIndex = this.files.findIndex(file => 
                file.filename === fileInfo.filename && file.project === fileInfo.project
            );
            
            if (existingIndex !== -1) {
                this.files[existingIndex] = fileInfo;
            } else {
                this.files.push(fileInfo);
            }
        });
        
        // UI更新
        this.updateUI();
    }
    
    /**
     * 全てのファイルをクリア
     */
    clearFiles() {
        this.files = [];
        this.currentPreviewIndex = -1;
        this.updateUI();
    }
    
    /**
     * ファイルリストを更新（最新の状態を取得）
     */
    async refreshFilesList() {
        try {
            // サーバーからファイル一覧を取得（実装予定）
            // 現在のプロジェクトIDを取得
            const projectId = this.getCurrentProjectId();
            
            // API呼び出し
            let url = '/api/generated_files';
            if (projectId) {
                url += `?project_id=${projectId}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.files) {
                // ファイルリストをリセットして新しいリストを設定
                this.files = data.files;
                this.updateUI();
            }
        } catch (error) {
            console.error('Failed to refresh files list:', error);
            // エラーメッセージを表示
            this.showErrorMessage(error.message);
        }
    }
    
    /**
     * エラーメッセージを表示
     * @param {string} message - エラーメッセージ
     */
    showErrorMessage(message) {
        // エラーメッセージを表示するための要素を作成
        const errorElement = document.createElement('div');
        errorElement.className = 'generated-files-error';
        errorElement.textContent = message;
        
        // リスト要素を一時的にクリアしてエラーメッセージを表示
        this.listElement.innerHTML = '';
        this.listElement.appendChild(errorElement);
        
        // 数秒後に消える
        setTimeout(() => {
            this.updateUI();
        }, 3000);
    }
    
    /**
     * 現在のプロジェクトIDを取得
     * @return {string|null} プロジェクトID
     */
    getCurrentProjectId() {
        // グローバルアプリインスタンスからプロジェクトIDを取得
        if (window.app && window.app.currentProjectId) {
            return window.app.currentProjectId;
        }
        return null;
    }
    
    /**
     * UIを更新
     */
    updateUI() {
        if (!this.container || !this.listElement) {
            this.initializeContainer();
        }
        
        // リストをクリア
        this.listElement.innerHTML = '';
        
        // 空の状態をチェック
        if (this.files.length === 0) {
            this.updateEmptyState();
            return;
        }
        
        // ファイルを日付の新しい順にソート
        const sortedFiles = [...this.files].sort((a, b) => {
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        // ファイルリストを作成
        sortedFiles.forEach((file, index) => {
            const fileItem = document.createElement('li');
            fileItem.className = 'generated-file-item';
            fileItem.dataset.index = index;
            
            // ファイルタイプに基づいてアイコンを決定
            const icon = this.getFileTypeIcon(file.filename);
            
            // ファイル情報の構築
            fileItem.innerHTML = `
                <span class="generated-file-icon">${icon}</span>
                <div class="generated-file-info">
                    <div class="generated-file-name">${file.filename}</div>
                    <div class="generated-file-meta">
                        ${file.project ? `<span class="generated-file-project">${file.project}</span>` : ''}
                        <span class="generated-file-timestamp">${this.formatTimestamp(file.timestamp)}</span>
                    </div>
                </div>
                <div class="generated-file-actions">
                    <button class="generated-file-action-btn copy-btn" title="${this.getTranslation('copy', 'コピー')}">📋</button>
                    <button class="generated-file-action-btn view-btn" title="${this.getTranslation('view', '表示')}">👁️</button>
                </div>
            `;
            
            // アクションボタン
            const copyBtn = fileItem.querySelector('.copy-btn');
            const viewBtn = fileItem.querySelector('.view-btn');
            
            // コピーボタンのクリックイベント
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyFileContentToClipboard(file);
            });
            
            // 表示ボタンのクリックイベント
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePreview(index);
            });
            
            // 項目クリックでファイル詳細表示
            fileItem.addEventListener('click', () => {
                this.togglePreview(index);
            });
            
            this.listElement.appendChild(fileItem);
        });
    }
    
    /**
     * 空の状態を表示
     */
    updateEmptyState() {
        // リストが空の場合のメッセージ
        this.listElement.innerHTML = `
            <div class="generated-files-empty">
                ${this.getTranslation('no_generated_files', 'モデルが作成したファイルはありません')}
            </div>
        `;
        
        // プレビューを非表示
        this.previewElement.classList.remove('active');
        this.previewElement.innerHTML = '';
    }
    
    /**
     * プレビューの表示/非表示を切り替え
     * @param {number} index - ファイルインデックス
     */
    async togglePreview(index) {
        // インデックスがファイル配列の範囲外の場合は処理しない
        if (index < 0 || index >= this.files.length) return;
        
        // 同じファイルを再度クリックした場合はプレビューを閉じる
        if (this.currentPreviewIndex === index && this.previewElement.classList.contains('active')) {
            this.previewElement.classList.remove('active');
            this.currentPreviewIndex = -1;
            return;
        }
        
        // ファイル情報を取得
        const file = this.files[index];
        
        // プレビュー要素を更新
        this.currentPreviewIndex = index;
        
        try {
            // サーバーからファイル内容を取得
            const response = await fetch(`/api/files/${encodeURIComponent(file.filename)}?project=${encodeURIComponent(file.project || '')}`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // プレビュー内容を設定
            let content = data.content || file.content_preview || '';
            
            // プレビュー要素にコードハイライト用のクラスを追加
            this.previewElement.className = 'generated-file-preview active';
            
            // ファイルタイプに基づいてハイライトクラスを追加
            const fileExt = file.filename.split('.').pop();
            if (fileExt) {
                this.previewElement.classList.add(`language-${fileExt}`);
            }
            
            // プレビュー内容をセット
            this.previewElement.textContent = content;
            
            // コードハイライト適用（highlight.jsがあれば）
            if (window.hljs) {
                window.hljs.highlightElement(this.previewElement);
            }
        } catch (error) {
            console.error('Failed to load file content:', error);
            
            // エラーメッセージをプレビューに表示
            this.previewElement.className = 'generated-file-preview active error';
            this.previewElement.textContent = `Error: ${error.message}`;
        }
    }
    
    /**
     * ファイル内容をクリップボードにコピー
     * @param {Object} file - ファイル情報
     */
    async copyFileContentToClipboard(file) {
        try {
            // サーバーからファイル内容を取得
            const response = await fetch(`/api/files/${encodeURIComponent(file.filename)}?project=${encodeURIComponent(file.project || '')}`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // クリップボードにコピー
            await navigator.clipboard.writeText(data.content || file.content_preview || '');
            
            // 成功通知
            this.showCopySuccess();
        } catch (error) {
            console.error('Failed to copy file content:', error);
            
            // エラーメッセージを表示
            this.showErrorMessage(`${this.getTranslation('copy_error', 'コピーエラー')}: ${error.message}`);
        }
    }
    
    /**
     * コピー成功通知を表示
     */
    showCopySuccess() {
        // 成功通知要素
        const notification = document.createElement('div');
        notification.className = 'copy-success-notification';
        notification.textContent = this.getTranslation('copied', 'コピーしました');
        
        // スタイル設定
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: 'rgba(0, 200, 0, 0.8)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: '4px',
            zIndex: '1000',
            transition: 'opacity 0.3s ease'
        });
        
        // bodyに追加
        document.body.appendChild(notification);
        
        // 3秒後に消える
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 2000);
    }
    
    /**
     * ファイル種類に基づいてアイコンを取得
     * @param {string} filename - ファイル名
     * @return {string} アイコン文字列
     */
    getFileTypeIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        
        const icons = {
            'py': '🐍',   // Python
            'js': '📜',   // JavaScript
            'ts': '📜',   // TypeScript
            'html': '🌐', // HTML
            'css': '🎨',  // CSS
            'json': '📋', // JSON
            'md': '📝',   // Markdown
            'txt': '📄',  // テキスト
            'csv': '📊',  // CSV
            'pdf': '📑',  // PDF
            'jpg': '🖼️',  // 画像
            'jpeg': '🖼️', // 画像
            'png': '🖼️',  // 画像
            'gif': '🖼️',  // 画像
            'svg': '🖼️',  // 画像
            'zip': '📦',  // ZIP
            'exe': '⚙️',  // 実行ファイル
            'sh': '⚙️',   // シェルスクリプト
        };
        
        return icons[ext] || '📄'; // デフォルトはテキストファイル
    }
    
    /**
     * タイムスタンプをフォーマット
     * @param {string} timestamp - ISO形式のタイムスタンプ
     * @return {string} フォーマットされた日時
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (error) {
            return timestamp;
        }
    }
    
    /**
     * 翻訳テキストを取得
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
     * WebSocketメッセージからファイル生成情報を処理
     * @param {Object} data - WebSocketから受信したデータ
     */
    processWebSocketMessage(data) {
        // 生成されたファイル情報があれば追加
        if (data.generated_files && Array.isArray(data.generated_files) && data.generated_files.length > 0) {
            this.addFiles(data.generated_files);
        }
        
        // ファイル生成イベントがあれば個別に追加
        if (data.file_generation_event && data.file_generation_event.filename) {
            this.addFile(data.file_generation_event);
        }
    }
}

// グローバルインスタンスを作成
window.generatedFilesViewer = new GeneratedFilesViewer();

// DOMのロード完了時のイベントリスナー
document.addEventListener('DOMContentLoaded', () => {
    // 既存のコンテナがあるかチェック
    const container = document.getElementById('generated-files-container');
    
    // コンテナがない場合は作成
    if (!container) {
        window.generatedFilesViewer = new GeneratedFilesViewer();
    }
});
