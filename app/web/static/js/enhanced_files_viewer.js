/**
 * enhanced_files_viewer.js
 * 
 * 強化版ファイルビューワーコンポーネント
 * ChatGPT風UIに適した生成ファイル表示とファイル操作機能を提供する
 */

class EnhancedFilesViewer {
    constructor(containerId = 'generated-files-container') {
        // コンテナ要素
        this.container = document.getElementById(containerId);
        
        // 生成されたファイルのリスト
        this.files = [];
        
        // フィルター状態
        this.currentFilter = 'all';
        
        // 現在選択されているファイルのインデックス
        this.selectedFileIndex = -1;
        
        // ファイルプレビューモード（'inline', 'popup'）
        this.previewMode = 'inline';
        
        // ポップアップオーバーレイ
        this.overlay = null;
        
        // 検索テキスト
        this.searchText = '';
        
        // UIコンポーネント
        this.headerElement = null;
        this.searchInput = null;
        this.filterButtons = null;
        this.listElement = null;
        this.previewElement = null;
        this.actionBar = null;
        
        // 初期化
        this.initializeContainer();
    }
    
    /**
     * コンテナ要素を初期化
     */
    initializeContainer() {
        // コンテナがなければ作成
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'generated-files-container';
            this.container.className = 'generated-files-container';
            
            // 適切な位置に追加
            const leftPanel = document.querySelector('.left-panel');
            if (leftPanel) {
                // 思考プロセスの次に配置
                const thinkingSection = leftPanel.querySelector('.thinking-section');
                if (thinkingSection) {
                    thinkingSection.after(this.container);
                } else {
                    leftPanel.appendChild(this.container);
                }
            }
        }
        
        // コンテナをクリア
        this.container.innerHTML = '';
        
        // コンテナにChatGPTテーマクラスを追加
        const body = document.body;
        if (body.classList.contains('chatgpt-theme')) {
            this.container.classList.add('chatgpt-theme');
        }
        
        // 要素構造を作成
        this.createContainerElements();
    }
    
    /**
     * UI要素を作成
     */
    createContainerElements() {
        // ヘッダー
        this.headerElement = document.createElement('div');
        this.headerElement.className = 'generated-files-header';
        
        const title = document.createElement('div');
        title.className = 'generated-files-title';
        title.innerHTML = `<span class="generated-files-title-icon">📁</span> ${this.getTranslation('generated_files', 'モデル生成ファイル')}`;
        
        const controls = document.createElement('div');
        controls.className = 'generated-files-controls';
        
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'refresh-btn';
        refreshBtn.innerHTML = '<span>🔄</span>';
        refreshBtn.title = this.getTranslation('refresh', '更新');
        refreshBtn.addEventListener('click', () => this.refreshFilesList());
        
        const collapseBtn = document.createElement('button');
        collapseBtn.className = 'collapse-btn';
        collapseBtn.innerHTML = '<span>▼</span>';
        collapseBtn.title = this.getTranslation('collapse', '折りたたむ');
        collapseBtn.addEventListener('click', () => this.toggleCollapse());
        
        controls.appendChild(refreshBtn);
        controls.appendChild(collapseBtn);
        
        this.headerElement.appendChild(title);
        this.headerElement.appendChild(controls);
        
        // 検索・フィルターバー
        const searchBar = document.createElement('div');
        searchBar.className = 'generated-files-search-bar';
        
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.className = 'generated-files-search-input';
        this.searchInput.placeholder = this.getTranslation('search_files', 'ファイルを検索...');
        this.searchInput.addEventListener('input', (e) => {
            this.searchText = e.target.value.toLowerCase();
            this.updateUI();
        });
        
        searchBar.appendChild(this.searchInput);
        
        // フィルターボタン
        this.filterButtons = document.createElement('div');
        this.filterButtons.className = 'generated-files-filter-buttons';
        
        const filters = [
            { id: 'all', label: this.getTranslation('all_files', '全て') },
            { id: 'code', label: this.getTranslation('code_files', 'コード') },
            { id: 'document', label: this.getTranslation('document_files', '文書') },
            { id: 'image', label: this.getTranslation('image_files', '画像') }
        ];
        
        filters.forEach(filter => {
            const button = document.createElement('button');
            button.className = `filter-btn ${filter.id === this.currentFilter ? 'active' : ''}`;
            button.textContent = filter.label;
            button.dataset.filter = filter.id;
            button.addEventListener('click', () => {
                this.currentFilter = filter.id;
                this.updateFilters();
                this.updateUI();
            });
            
            this.filterButtons.appendChild(button);
        });
        
        searchBar.appendChild(this.filterButtons);
        
        // ファイルリスト
        this.listElement = document.createElement('ul');
        this.listElement.className = 'generated-files-list';
        
        // プレビューエリア
        this.previewElement = document.createElement('div');
        this.previewElement.className = 'generated-file-preview';
        
        // アクションバー
        this.actionBar = document.createElement('div');
        this.actionBar.className = 'generated-files-action-bar';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn copy-btn';
        copyBtn.innerHTML = '<span>📋</span> ' + this.getTranslation('copy', 'コピー');
        copyBtn.addEventListener('click', () => this.copySelectedFileContent());
        
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'action-btn download-btn';
        downloadBtn.innerHTML = '<span>💾</span> ' + this.getTranslation('download', 'ダウンロード');
        downloadBtn.addEventListener('click', () => this.downloadSelectedFile());
        
        const expandBtn = document.createElement('button');
        expandBtn.className = 'action-btn expand-btn';
        expandBtn.innerHTML = '<span>🔍</span> ' + this.getTranslation('expand', '拡大表示');
        expandBtn.addEventListener('click', () => this.togglePreviewMode());
        
        this.actionBar.appendChild(copyBtn);
        this.actionBar.appendChild(downloadBtn);
        this.actionBar.appendChild(expandBtn);
        
        // 全てをコンテナに追加
        this.container.appendChild(this.headerElement);
        this.container.appendChild(searchBar);
        this.container.appendChild(this.listElement);
        this.container.appendChild(this.previewElement);
        this.container.appendChild(this.actionBar);
        
        // 初期状態ではアクションバーを非表示
        this.actionBar.style.display = 'none';
        
        // 空の状態を表示
        this.updateEmptyState();
    }
    
    /**
     * フィルターボタンの状態を更新
     */
    updateFilters() {
        if (!this.filterButtons) return;
        
        // 全てのボタンからアクティブクラスを削除
        const buttons = this.filterButtons.querySelectorAll('.filter-btn');
        buttons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.filter === this.currentFilter) {
                button.classList.add('active');
            }
        });
    }
    
    /**
     * コンテナの折りたたみ/展開を切り替え
     */
    toggleCollapse() {
        const collapseBtn = this.headerElement.querySelector('.collapse-btn span');
        const content = [this.listElement, this.previewElement, this.actionBar];
        
        // 現在の状態を切り替え
        const isCollapsed = collapseBtn.textContent === '▲';
        
        if (isCollapsed) {
            // 展開
            content.forEach(el => el.style.display = '');
            collapseBtn.textContent = '▼';
            collapseBtn.parentElement.title = this.getTranslation('collapse', '折りたたむ');
        } else {
            // 折りたたむ
            content.forEach(el => el.style.display = 'none');
            collapseBtn.textContent = '▲';
            collapseBtn.parentElement.title = this.getTranslation('expand', '展開');
        }
    }
    
    /**
     * プレビューモードを切り替え
     */
    togglePreviewMode() {
        if (this.selectedFileIndex === -1) return;
        
        if (this.previewMode === 'inline') {
            // インラインからポップアップへ
            this.previewMode = 'popup';
            this.showPopupPreview();
        } else {
            // ポップアップからインラインへ
            this.previewMode = 'inline';
            this.closePopupPreview();
        }
    }
    
    /**
     * ポップアップでファイルプレビューを表示
     */
    showPopupPreview() {
        if (this.selectedFileIndex === -1) return;
        
        const file = this.files[this.selectedFileIndex];
        
        // ポップアップオーバーレイを作成
        this.overlay = document.createElement('div');
        this.overlay.className = 'enhanced-files-overlay';
        
        const popup = document.createElement('div');
        popup.className = 'enhanced-files-popup';
        
        // ポップアップヘッダー
        const header = document.createElement('div');
        header.className = 'enhanced-files-popup-header';
        
        const title = document.createElement('div');
        title.className = 'enhanced-files-popup-title';
        title.textContent = file.filename;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'enhanced-files-popup-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => this.closePopupPreview());
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        // ポップアップコンテンツ
        const content = document.createElement('div');
        content.className = 'enhanced-files-popup-content';
        
        // ファイル内容をロード
        this.loadFileContent(file).then(fileContent => {
            content.innerHTML = `<pre>${this.escapeHtml(fileContent)}</pre>`;
            
            // コードハイライト適用（highlight.jsがあれば）
            if (window.hljs) {
                const codeBlock = content.querySelector('pre');
                window.hljs.highlightElement(codeBlock);
            }
        }).catch(error => {
            content.innerHTML = `<div class="enhanced-files-error">${error.message}</div>`;
        });
        
        // ポップアップアクション
        const actions = document.createElement('div');
        actions.className = 'enhanced-files-popup-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.innerHTML = '<span>📋</span> ' + this.getTranslation('copy', 'コピー');
        copyBtn.addEventListener('click', () => this.copySelectedFileContent());
        
        const downloadBtn = document.createElement('button');
        downloadBtn.innerHTML = '<span>💾</span> ' + this.getTranslation('download', 'ダウンロード');
        downloadBtn.addEventListener('click', () => this.downloadSelectedFile());
        
        actions.appendChild(copyBtn);
        actions.appendChild(downloadBtn);
        
        // ポップアップを組み立てる
        popup.appendChild(header);
        popup.appendChild(content);
        popup.appendChild(actions);
        
        this.overlay.appendChild(popup);
        document.body.appendChild(this.overlay);
        
        // ESCキーでポップアップを閉じる
        document.addEventListener('keydown', this.handleEscKey);
        
        // オーバーレイクリックで閉じる
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.closePopupPreview();
            }
        });
    }
    
    /**
     * ポップアッププレビューを閉じる
     */
    closePopupPreview() {
        if (this.overlay) {
            document.body.removeChild(this.overlay);
            this.overlay = null;
            this.previewMode = 'inline';
            
            // ESCキーイベントリスナーを削除
            document.removeEventListener('keydown', this.handleEscKey);
        }
    }
    
    /**
     * ESCキーハンドラー
     */
    handleEscKey = (e) => {
        if (e.key === 'Escape') {
            this.closePopupPreview();
        }
    }
    
    /**
     * HTMLエスケープ
     * @param {string} html - エスケープするHTML文字列
     * @returns {string} エスケープされた文字列
     */
    escapeHtml(html) {
        return html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    /**
     * ファイルを追加
     * @param {Object} fileInfo - ファイル情報オブジェクト
     */
    addFile(fileInfo) {
        // タイムスタンプがない場合は現在時刻を使用
        if (!fileInfo.timestamp) {
            fileInfo.timestamp = new Date().toISOString();
        }
        
        // ファイルタイプを推定
        if (!fileInfo.fileType) {
            fileInfo.fileType = this.getFileType(fileInfo.filename);
        }
        
        // 同じファイルが既にあるかチェック
        const existingIndex = this.files.findIndex(file => 
            file.filename === fileInfo.filename && 
            (file.project === fileInfo.project || (!file.project && !fileInfo.project))
        );
        
        if (existingIndex !== -1) {
            // 更新
            this.files[existingIndex] = fileInfo;
        } else {
            // 追加
            this.files.push(fileInfo);
        }
        
        // UI更新
        this.updateUI();
        
        // 新しいファイルをハイライト
        if (existingIndex === -1) {
            setTimeout(() => {
                const newIndex = this.files.length - 1;
                const fileItem = this.listElement.querySelector(`[data-index="${newIndex}"]`);
                if (fileItem) {
                    fileItem.classList.add('file-highlight-animation');
                    setTimeout(() => {
                        fileItem.classList.remove('file-highlight-animation');
                    }, 2000);
                }
            }, 100);
        }
    }
    
    /**
     * 複数のファイルを追加
     * @param {Array} filesInfo - ファイル情報の配列
     */
    addFiles(filesInfo) {
        if (!filesInfo || !Array.isArray(filesInfo) || filesInfo.length === 0) return;
        
        let hasNewFiles = false;
        
        filesInfo.forEach(fileInfo => {
            // タイムスタンプがない場合は現在時刻を使用
            if (!fileInfo.timestamp) {
                fileInfo.timestamp = new Date().toISOString();
            }
            
            // ファイルタイプを推定
            if (!fileInfo.fileType) {
                fileInfo.fileType = this.getFileType(fileInfo.filename);
            }
            
            // 同じファイルが既にあるかチェック
            const existingIndex = this.files.findIndex(file => 
                file.filename === fileInfo.filename && 
                (file.project === fileInfo.project || (!file.project && !fileInfo.project))
            );
            
            if (existingIndex !== -1) {
                // 更新
                this.files[existingIndex] = fileInfo;
            } else {
                // 追加
                this.files.push(fileInfo);
                hasNewFiles = true;
            }
        });
        
        // UI更新
        this.updateUI();
        
        // 新しいファイルがある場合は通知
        if (hasNewFiles) {
            this.notifyNewFiles(filesInfo.length);
        }
    }
    
    /**
     * 新しいファイルの通知を表示
     * @param {number} count - 追加されたファイル数
     */
    notifyNewFiles(count) {
        // 通知要素
        const notification = document.createElement('div');
        notification.className = 'enhanced-files-notification';
        notification.textContent = this.getTranslation('new_files_added', `${count}個の新しいファイルが追加されました`);
        
        // スタイル
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: 'rgba(16, 163, 127, 0.9)',
            color: 'white',
            padding: '10px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '1000',
            transition: 'opacity 0.3s ease',
            fontSize: '14px',
            fontWeight: '500'
        });
        
        // bodyに追加
        document.body.appendChild(notification);
        
        // 3秒後に消える
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentElement) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * 全てのファイルをクリア
     */
    clearFiles() {
        this.files = [];
        this.selectedFileIndex = -1;
        this.updateUI();
    }
    
    /**
     * ファイルリストを更新
     */
    async refreshFilesList() {
        try {
            // 現在のプロジェクトIDを取得
            const projectId = this.getCurrentProjectId();
            
            // APIからファイル一覧を取得
            let url = '/api/generated_files';
            if (projectId) {
                url += `?project_id=${encodeURIComponent(projectId)}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // 既存のファイルリストを更新
            if (data.files) {
                const oldCount = this.files.length;
                this.addFiles(data.files);
                
                // 新しいファイルがあれば通知
                const newCount = this.files.length - oldCount;
                if (newCount > 0) {
                    this.notifyNewFiles(newCount);
                }
            }
        } catch (error) {
            console.error('Failed to refresh files list:', error);
            this.showError(error.message);
        }
    }
    
    /**
     * UIを更新
     */
    updateUI() {
        if (!this.container || !this.listElement) {
            this.initializeContainer();
            return;
        }
        
        // リストをクリア
        this.listElement.innerHTML = '';
        
        // 空の状態をチェック
        if (this.files.length === 0) {
            this.updateEmptyState();
            this.actionBar.style.display = 'none';
            return;
        }
        
        // フィルターとソートを適用
        const filteredFiles = this.getFilteredFiles();
        
        // ファイルリストを生成
        filteredFiles.forEach((file, index) => {
            const fileItem = document.createElement('li');
            fileItem.className = 'generated-file-item';
            fileItem.dataset.index = this.files.indexOf(file); // 元のインデックスを保持
            
            if (this.files.indexOf(file) === this.selectedFileIndex) {
                fileItem.classList.add('selected');
            }
            
            // ファイルアイコン
            const fileIcon = this.getFileTypeIcon(file.filename);
            
            // ファイル情報の構築
            fileItem.innerHTML = `
                <span class="generated-file-icon">${fileIcon}</span>
                <div class="generated-file-info">
                    <div class="generated-file-name">${this.highlightSearchText(file.filename)}</div>
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
            
            // コピーボタン
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyFileContentToClipboard(file);
            });
            
            // 表示ボタン
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectFile(this.files.indexOf(file));
            });
            
            // 項目全体をクリックしたときの処理
            fileItem.addEventListener('click', () => {
                this.selectFile(this.files.indexOf(file));
            });
            
            this.listElement.appendChild(fileItem);
        });
        
        // 結果がなければその旨を表示
        if (filteredFiles.length === 0) {
            const noResults = document.createElement('li');
            noResults.className = 'generated-files-no-results';
            noResults.textContent = this.getTranslation('no_matching_files', '条件に一致するファイルがありません');
            this.listElement.appendChild(noResults);
        }
        
        // 現在選択されているファイルがある場合、プレビューを更新
        if (this.selectedFileIndex !== -1) {
            this.updatePreview();
            this.actionBar.style.display = 'flex';
        } else {
            this.previewElement.innerHTML = '';
            this.previewElement.classList.remove('active');
            this.actionBar.style.display = 'none';
        }
    }
    
    /**
     * 検索テキストのハイライト
     * @param {string} text - ハイライト対象のテキスト
     * @returns {string} ハイライト適用後のテキスト
     */
    highlightSearchText(text) {
        if (!this.searchText) return text;
        
        const searchRegex = new RegExp(`(${this.escapeRegExp(this.searchText)})`, 'gi');
        return text.replace(searchRegex, '<span class="search-highlight">$1</span>');
    }
    
    /**
     * 正規表現のためのエスケープ
     * @param {string} string - エスケープする文字列
     * @returns {string} エスケープされた文字列
     */
    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    /**
     * フィルター適用済みのファイルリストを取得
     * @returns {Array} フィルター済みファイル配列
     */
    getFilteredFiles() {
        // 検索テキストとフィルターを適用
        let filtered = [...this.files];
        
        // 検索テキストでフィルター
        if (this.searchText) {
            filtered = filtered.filter(file => 
                file.filename.toLowerCase().includes(this.searchText)
            );
        }
        
        // ファイルタイプでフィルター
        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(file => {
                const fileType = file.fileType || this.getFileType(file.filename);
                
                switch (this.currentFilter) {
                    case 'code':
                        return ['code', 'script'].includes(fileType);
                    case 'document':
                        return ['document', 'text'].includes(fileType);
                    case 'image':
                        return fileType === 'image';
                    default:
                        return true;
                }
            });
        }
        
        // 日付の新しい順にソート
        return filtered.sort((a, b) => {
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
    }
    
    /**
     * ファイル種類を取得
     * @param {string} filename - ファイル名
     * @returns {string} ファイル種類
     */
    getFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        
        // コード・スクリプト
        if (['py', 'js', 'ts', 'java', 'c', 'cpp', 'cs', 'go', 'rb', 'php', 'sh', 'bash', 'sql', 'html', 'css', 'jsx', 'tsx'].includes(ext)) {
            return 'code';
        }
        
        // ドキュメント
        if (['md', 'txt', 'doc', 'docx', 'pdf', 'rtf', 'tex', 'csv', 'json', 'xml', 'yaml', 'yml'].includes(ext)) {
            return 'document';
        }
        
        // 画像
        if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'].includes(ext)) {
            return 'image';
        }
        
        // その他
        return 'other';
    }
    
    /**
     * ファイルを選択
     * @param {number} index - ファイルインデックス
     */
    selectFile(index) {
        if (index < 0 || index >= this.files.length) return;
        
        // インデックスを保存
        this.selectedFileIndex = index;
        
        // UI更新
        this.updateUI();
        
        // プレビュー更新
        this.updatePreview();
    }
    
    /**
     * プレビューを更新
     */
    async updatePreview() {
        if (this.selectedFileIndex === -1) {
            this.previewElement.classList.remove('active');
            return;
        }
        
        const file = this.files[this.selectedFileIndex];
        
        // プレビュー要素をアクティブ化
        this.previewElement.classList.add('active');
        
        // ローディング表示
        this.previewElement.innerHTML = '<div class="preview-loading">Loading...</div>';
        
        try {
            // ファイル内容を取得
            const content = await this.loadFileContent(file);
            
            // ファイルタイプに基づいてプレビューを作成
            const fileType = file.fileType || this.getFileType(file.filename);
            const ext = file.filename.split('.').pop().toLowerCase();
            
            if (fileType === 'image') {
                // 画像プレビュー
                this.previewElement.innerHTML = `<img src="/api/files/${encodeURIComponent(file.filename)}?project=${encodeURIComponent(file.project || '')}" alt="${file.filename}" class="preview-image">`;
            } else {
                // テキストプレビュー
                const preEl = document.createElement('pre');
                preEl.className = `preview-code language-${ext}`;
                preEl.textContent = content;
                
                this.previewElement.innerHTML = '';
                this.previewElement.appendChild(preEl);
                
                // コードハイライト適用（highlight.jsがあれば）
                if (window.hljs) {
                    window.hljs.highlightElement(preEl);
                }
            }
            
            // アクションバーを表示
            this.actionBar.style.display = 'flex';
        } catch (error) {
            console.error('Failed to load file content:', error);
            this.previewElement.innerHTML = `<div class="preview-error">${error.message}</div>`;
        }
    }
    
    /**
     * ファイル内容を読み込む
     * @param {Object} file - ファイル情報
     * @returns {Promise<string>} ファイル内容
     */
    async loadFileContent(file) {
        // APIからファイル内容を取得
        const url = `/api/files/${encodeURIComponent(file.filename)}?project=${encodeURIComponent(file.project || '')}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load file: ${response.status}`);
        }
        
        const data = await response.json();
        return data.content || '';
    }
    
    /**
     * 選択されたファイルの内容をコピー
     */
    async copySelectedFileContent() {
        if (this.selectedFileIndex === -1) return;
        
        const file = this.files[this.selectedFileIndex];
        
        try {
            const content = await this.loadFileContent(file);
            await navigator.clipboard.writeText(content);
            this.showCopySuccess();
        } catch (error) {
            console.error('Failed to copy file content:', error);
            this.showError(this.getTranslation('copy_failed', 'コピーに失敗しました'));
        }
    }
    
    /**
     * 選択されたファイルをダウンロード
     */
    async downloadSelectedFile() {
        if (this.selectedFileIndex === -1) return;
        
        const file = this.files[this.selectedFileIndex];
        
        try {
            const content = await this.loadFileContent(file);
            
            // ダウンロード用の一時リンクを作成
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename.split('/').pop(); // パスからファイル名のみを抽出
            document.body.appendChild(a);
            a.click();
            
            // クリーンアップ
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);
        } catch (error) {
            console.error('Failed to download file:', error);
            this.showError(this.getTranslation('download_failed', 'ダウンロードに失敗しました'));
        }
    }
    
    /**
     * コピー成功通知を表示
     */
    showCopySuccess() {
        const notification = document.createElement('div');
        notification.className = 'enhanced-files-notification success';
        notification.textContent = this.getTranslation('copied_to_clipboard', 'クリップボードにコピーしました');
        
        // スタイル
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: 'rgba(16, 163, 127, 0.9)',
            color: 'white',
            padding: '10px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '1000',
            transition: 'opacity 0.3s ease',
            fontSize: '14px',
            fontWeight: '500'
        });
        
        // bodyに追加
        document.body.appendChild(notification);
        
        // 2秒後に消える
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentElement) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }
    
    /**
     * エラーメッセージを表示
     * @param {string} message - エラーメッセージ
     */
    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'enhanced-files-notification error';
        notification.textContent = message;
        
        // スタイル
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: 'rgba(239, 65, 70, 0.9)',
            color: 'white',
            padding: '10px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '1000',
            transition: 'opacity 0.3s ease',
            fontSize: '14px',
            fontWeight: '500'
        });
        
        // bodyに追加
        document.body.appendChild(notification);
        
        // 3秒後に消える
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentElement) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * 空の状態を表示
     */
    updateEmptyState() {
        this.listElement.innerHTML = `
            <div class="generated-files-empty">
                <div class="empty-icon">📄</div>
                <div class="empty-message">${this.getTranslation('no_generated_files', 'モデルが作成したファイルはありません')}</div>
            </div>
        `;
        
        this.previewElement.classList.remove('active');
        this.previewElement.innerHTML = '';
    }
    
    /**
     * ファイル種類に基づいてアイコンを取得
     * @param {string} filename - ファイル名
     * @returns {string} アイコン文字列
     */
    getFileTypeIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        
        const icons = {
            // コード
            'py': '🐍',
            'js': '📜',
            'ts': '📜',
            'java': '☕',
            'c': '🔧',
            'cpp': '🔧',
            'cs': '🔧',
            'go': '🔵',
            'rb': '💎',
            'php': '🐘',
            'sh': '⚙️',
            'bash': '⚙️',
            'sql': '🗃️',
            
            // マークアップ
            'html': '🌐',
            'css': '🎨',
            'jsx': '⚛️',
            'tsx': '⚛️',
            
            // ドキュメント
            'md': '📝',
            'txt': '📄',
            'doc': '📄',
            'docx': '📄',
            'pdf': '📑',
            'rtf': '📄',
            'tex': '📑',
            
            // データ
            'csv': '📊',
            'json': '📋',
            'xml': '📋',
            'yaml': '📋',
            'yml': '📋',
            
            // 画像
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'png': '🖼️',
            'gif': '🖼️',
            'bmp': '🖼️',
            'svg': '🖼️',
            'webp': '🖼️',
            'ico': '🖼️',
            
            // その他
            'zip': '📦',
            'exe': '⚙️',
        };
        
        return icons[ext] || '📄';
    }
    
    /**
     * タイムスタンプをフォーマット
     * @param {string} timestamp - ISOフォーマットのタイムスタンプ
     * @returns {string} フォーマットされた日時
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            
            // 24時間以内なら相対時間表示
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60 * 1000) {
                return this.getTranslation('just_now', '今');
            } else if (diff < 60 * 60 * 1000) {
                const minutes = Math.floor(diff / (60 * 1000));
                return this.getTranslation('minutes_ago', `${minutes}分前`);
            } else if (diff < 24 * 60 * 60 * 1000) {
                const hours = Math.floor(diff / (60 * 60 * 1000));
                return this.getTranslation('hours_ago', `${hours}時間前`);
            } else {
                // 日付表示
                return date.toLocaleString(undefined, {
                    month: 'numeric',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: 'numeric'
                });
            }
        } catch (error) {
            return timestamp;
        }
    }
    
    /**
     * 現在のプロジェクトIDを取得
     * @returns {string|null} プロジェクトID
     */
    getCurrentProjectId() {
        if (window.app && window.app.currentProjectId) {
            return window.app.currentProjectId;
        }
        return null;
    }
    
    /**
     * 翻訳テキストを取得
     * @param {string} key - 翻訳キー
     * @param {string} defaultText - デフォルトテキスト
     * @returns {string} 翻訳テキスト
     */
    getTranslation(key, defaultText) {
        // i18n.jsがロードされている場合はそれを使用
        if (typeof t === 'function') {
            return t(key) || defaultText;
        }
        return defaultText;
    }
    
    /**
     * WebSocketメッセージを処理
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
window.enhancedFilesViewer = null;

// DOMのロード完了時に初期化
document.addEventListener('DOMContentLoaded', () => {
    // 既存の旧バージョンのビューワーをチェック
    const oldViewer = window.generatedFilesViewer;
    
    // 強化版ビューワーを作成
    window.enhancedFilesViewer = new EnhancedFilesViewer();
    
    // 以前のビューワーへの互換性のためのプロキシを設定
    window.generatedFilesViewer = new Proxy({}, {
        get(target, prop) {
            // 新しいビューワーの同名メソッドがあればそれを返す
            if (typeof window.enhancedFilesViewer[prop] === 'function') {
                return window.enhancedFilesViewer[prop].bind(window.enhancedFilesViewer);
            }
            
            // 既存のビューワーがあればそれを使用
            if (oldViewer && typeof oldViewer[prop] === 'function') {
                return oldViewer[prop].bind(oldViewer);
            }
            
            return undefined;
        }
    });
    
    // CSSを追加
    const style = document.createElement('style');
    style.textContent = `
        /* 強化版ファイルビューワースタイル */
        .enhanced-files-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 16px;
            border-radius: 8px;
            background-color: rgba(16, 163, 127, 0.9);
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            transition: opacity 0.3s ease;
            font-size: 14px;
            font-weight: 500;
        }
        
        .enhanced-files-notification.error {
            background-color: rgba(239, 65, 70, 0.9);
        }
        
        .enhanced-files-search-bar {
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .enhanced-files-search-input {
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 13px;
            width: 100%;
        }
        
        .enhanced-files-filter-buttons {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 4px;
        }
        
        .filter-btn {
            padding: 4px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 12px;
            background: none;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
        }
        
        .filter-btn.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .generated-files-action-bar {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 8px 12px;
            border-top: 1px solid var(--border-color);
        }
        
        .action-btn {
            padding: 6px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 13px;
            background-color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }
        
        .action-btn:hover {
            background-color: var(--background-color);
        }
        
        .generated-files-no-results {
            padding: 20px 16px;
            text-align: center;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .generated-files-empty {
            padding: 30px 16px;
            text-align: center;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        
        .empty-icon {
            font-size: 32px;
            color: var(--border-color);
        }
        
        .empty-message {
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .search-highlight {
            background-color: rgba(255, 255, 0, 0.3);
            font-weight: bold;
        }
        
        .preview-loading {
            padding: 20px;
            text-align: center;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .preview-error {
            padding: 20px;
            text-align: center;
            color: var(--error-color);
        }
        
        .preview-image {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
        
        .enhanced-files-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .enhanced-files-popup {
            width: 80%;
            max-width: 900px;
            max-height: 80vh;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .enhanced-files-popup-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background-color: var(--primary-color);
            color: white;
        }
        
        .enhanced-files-popup-title {
            font-size: 16px;
            font-weight: 500;
        }
        
        .enhanced-files-popup-close {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0 6px;
        }
        
        .enhanced-files-popup-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .enhanced-files-popup-content pre {
            margin: 0;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .enhanced-files-popup-actions {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 12px 16px;
            border-top: 1px solid var(--border-color);
        }
        
        .enhanced-files-popup-actions button {
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background-color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }
        
        .enhanced-files-popup-actions button:hover {
            background-color: var(--background-color);
        }
        
        /* ChatGPTテーマ対応 */
        .chatgpt-theme .enhanced-files-notification {
            background-color: rgba(16, 163, 127, 0.9);
        }
        
        .chatgpt-theme .enhanced-files-notification.error {
            background-color: rgba(239, 65, 70, 0.9);
        }
        
        .chatgpt-theme .filter-btn.active {
            background-color: #10a37f;
            border-color: #10a37f;
        }
        
        .chatgpt-theme .enhanced-files-popup-header {
            background-color: #10a37f;
        }
    `;
    
    document.head.appendChild(style);
});
