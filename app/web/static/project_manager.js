// project_manager.js - プロジェクト管理モジュール
import { t } from '/static/i18n.js';

export class ProjectManager {
    constructor(handleSessionSelect) {
        this.projects = [];
        this.currentProjectId = null;
        this.currentSessionId = null;
        this.handleSessionSelect = handleSessionSelect;
        
        // Claudeライクなプロジェクト管理のためにプロジェクト選択ハンドラーを保持
        this.handleProjectSelect = null;
        
        // 現在のプロジェクトとセッションデータを保持
        this.currentProjectData = null;
        this.currentSessionData = null;
    }

    init() {
        console.log('プロジェクト管理を初期化中...');
        
        // プロジェクトリスト要素
        this.projectListElement = document.getElementById('project-list');
        
        // セッションリスト要素
        this.sessionListElement = document.getElementById('session-list');
        
        // プロジェクト詳細要素
        this.projectDetailsElement = document.getElementById('project-details');
        
        // プロジェクト指示エリア
        this.projectInstructionsElement = document.getElementById('project-instructions');
        
        // プロジェクト関連ボタン
        this.newProjectBtn = document.getElementById('new-project-btn');
        this.saveProjectBtn = document.getElementById('save-project-btn');
        this.newSessionBtn = document.getElementById('new-session-btn');
        
        // 削除・名前変更ボタン
        this.deleteProjectBtn = document.getElementById('delete-project-btn');
        this.renameProjectBtn = document.getElementById('rename-project-btn');
        this.deleteSessionBtn = document.getElementById('delete-session-btn');
        this.renameSessionBtn = document.getElementById('rename-session-btn');
        
        // イベントハンドラ登録
        this.bindEvents();
        
        // プロジェクト一覧を読み込み
        this.loadProjects();
    }

    // プロジェクト選択ハンドラーを設定（外部から呼び出し用）
    setProjectSelectHandler(handler) {
        this.handleProjectSelect = handler;
    }

    bindEvents() {
        console.log('プロジェクト管理のイベントハンドラを登録...');
        
        // 新規プロジェクト作成ボタン
        if (this.newProjectBtn) {
            this.newProjectBtn.addEventListener('click', () => this.createNewProject());
        } else {
            console.warn('新規プロジェクトボタンが見つかりません');
        }
        
        // プロジェクト保存ボタン
        if (this.saveProjectBtn) {
            this.saveProjectBtn.addEventListener('click', () => this.saveCurrentProject());
        } else {
            console.warn('プロジェクト保存ボタンが見つかりません');
        }
        
        // 新規セッション作成ボタン
        if (this.newSessionBtn) {
            this.newSessionBtn.addEventListener('click', () => this.createNewSession());
        } else {
            console.warn('新規セッションボタンが見つかりません');
        }
        
        // プロジェクト削除ボタン
        if (this.deleteProjectBtn) {
            this.deleteProjectBtn.addEventListener('click', () => this.deleteCurrentProject());
        }
        
        // プロジェクト名前変更ボタン
        if (this.renameProjectBtn) {
            this.renameProjectBtn.addEventListener('click', () => this.renameCurrentProject());
        }
        
        // セッション削除ボタン
        if (this.deleteSessionBtn) {
            this.deleteSessionBtn.addEventListener('click', () => this.deleteCurrentSession());
        }
        
        // セッション名前変更ボタン
        if (this.renameSessionBtn) {
            this.renameSessionBtn.addEventListener('click', () => this.renameCurrentSession());
        }
    }

    // プロジェクト一覧を読み込む
    async loadProjects() {
        try {
            console.log('プロジェクト一覧を読み込み中...');
            const response = await fetch('/api/projects');
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            this.projects = await response.json();
            this.updateProjectList();
            
            // 最近のプロジェクトを選択
            if (this.projects.length > 0) {
                this.selectProject(this.projects[0].id);
            }
        } catch (error) {
            console.error('プロジェクト一覧の読み込みに失敗しました:', error);
        }
    }

    // プロジェクトリストを更新
    updateProjectList() {
        if (!this.projectListElement) {
            console.warn('プロジェクトリスト要素が見つかりません');
            return;
        }
        
        // リストを空にする
        this.projectListElement.innerHTML = '';
        
        // プロジェクトが空の場合のメッセージ
        if (this.projects.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'project-item empty';
            emptyItem.textContent = t('no_projects');
            this.projectListElement.appendChild(emptyItem);
            return;
        }
        
        // プロジェクトアイテムを追加
        this.projects.forEach(project => {
            const projectItem = document.createElement('div');
            projectItem.className = 'project-item';
            if (project.id === this.currentProjectId) {
                projectItem.classList.add('selected');
            }
            
            projectItem.addEventListener('click', () => this.selectProject(project.id));
            
            // プロジェクト名
            const nameElement = document.createElement('div');
            nameElement.className = 'project-name';
            nameElement.textContent = project.name;
            projectItem.appendChild(nameElement);
            
            // 更新日時
            const dateElement = document.createElement('div');
            dateElement.className = 'project-date';
            const updatedDate = new Date(project.updated_at);
            dateElement.textContent = updatedDate.toLocaleString();
            projectItem.appendChild(dateElement);
            
            this.projectListElement.appendChild(projectItem);
        });
    }

    // 特定のプロジェクトを選択
    async selectProject(projectId) {
        try {
            console.log(`プロジェクトを選択: ${projectId}`);
            const response = await fetch(`/api/projects/${projectId}`);
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const projectData = await response.json();
            this.currentProjectId = projectId;
            this.currentProjectData = projectData;
            
            // プロジェクトリストの選択状態を更新
            this.updateProjectList();
            
            // プロジェクト詳細を表示
            this.updateProjectDetails(projectData);
            
            // セッションリストを更新
            this.updateSessionList(projectData.sessions);
            
            // 最初のセッションを選択（存在する場合）
            if (projectData.sessions && projectData.sessions.length > 0) {
                this.selectSession(projectData.sessions[0].id);
            } else {
                this.currentSessionId = null;
                this.currentSessionData = null;
            }
            
            // 外部のプロジェクト選択ハンドラを呼び出し
            if (this.handleProjectSelect) {
                this.handleProjectSelect(projectId);
            }
        } catch (error) {
            console.error('プロジェクト詳細の読み込みに失敗しました:', error);
        }
    }
    
    // 現在のプロジェクトを再読み込み（セッションを更新するため）
    async refreshCurrentProject() {
        if (this.currentProjectId) {
            await this.selectProject(this.currentProjectId);
        }
    }

    // プロジェクト詳細表示を更新
    updateProjectDetails(project) {
        if (!this.projectDetailsElement) {
            console.warn('プロジェクト詳細要素が見つかりません');
            return;
        }
        
        // プロジェクト名入力欄
        const nameInput = this.projectDetailsElement.querySelector('#project-name');
        if (nameInput) {
            nameInput.value = project.name;
        } else {
            console.warn('プロジェクト名入力欄が見つかりません');
        }
        
        // プロジェクト指示入力欄
        if (this.projectInstructionsElement) {
            this.projectInstructionsElement.value = project.instructions || '';
        } else {
            console.warn('プロジェクト指示入力欄が見つかりません');
        }
        
        // 削除・名前変更ボタンの表示状態を更新
        if (this.deleteProjectBtn) {
            this.deleteProjectBtn.disabled = false;
        }
        
        if (this.renameProjectBtn) {
            this.renameProjectBtn.disabled = false;
        }
    }

    // セッションリストを更新
    updateSessionList(sessions) {
        if (!this.sessionListElement) {
            console.warn('セッションリスト要素が見つかりません');
            return;
        }
        
        // リストを空にする
        this.sessionListElement.innerHTML = '';
        
        // セッションが空の場合のメッセージ
        if (!sessions || sessions.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'session-item empty';
            emptyItem.textContent = t('no_sessions');
            this.sessionListElement.appendChild(emptyItem);
            
            // セッション操作ボタンを無効化
            if (this.deleteSessionBtn) {
                this.deleteSessionBtn.disabled = true;
            }
            if (this.renameSessionBtn) {
                this.renameSessionBtn.disabled = true;
            }
            
            return;
        }
        
        // セッションアイテムを追加
        sessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            sessionItem.dataset.sessionId = session.id; // セッションIDをデータ属性として保存
            
            if (session.id === this.currentSessionId) {
                sessionItem.classList.add('selected');
            }
            
            sessionItem.addEventListener('click', () => this.selectSession(session.id));
            
            // セッションタイトル
            const titleElement = document.createElement('div');
            titleElement.className = 'session-title';
            titleElement.textContent = session.title || t('untitled_session');
            sessionItem.appendChild(titleElement);
            
            // 作成日時
            const dateElement = document.createElement('div');
            dateElement.className = 'session-date';
            const createdDate = new Date(session.created_at);
            dateElement.textContent = createdDate.toLocaleString();
            sessionItem.appendChild(dateElement);
            
            this.sessionListElement.appendChild(sessionItem);
        });
    }

    // 特定のセッションを選択
    async selectSession(sessionId) {
        console.log(`セッションを選択: ${sessionId}`);
        this.currentSessionId = sessionId;
        
        // セッションリストの選択状態を更新
        const sessionItems = this.sessionListElement.querySelectorAll('.session-item');
        sessionItems.forEach(item => {
            item.classList.remove('selected');
            if (item.dataset.sessionId === sessionId) {
                item.classList.add('selected');
            }
        });
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const sessionData = await response.json();
            this.currentSessionData = sessionData;
            
            // セッション操作ボタンを有効化
            if (this.deleteSessionBtn) {
                this.deleteSessionBtn.disabled = false;
            }
            if (this.renameSessionBtn) {
                this.renameSessionBtn.disabled = false;
            }
            
            // 親コンポーネントにセッション選択を通知
            if (this.handleSessionSelect) {
                this.handleSessionSelect(sessionId);
            } else {
                console.warn('セッション選択ハンドラが設定されていません');
            }
        } catch (error) {
            console.error('セッション詳細の読み込みに失敗しました:', error);
        }
    }

    // タイトルからセッションを検索するヘルパー関数
    findSessionByTitle(title) {
        if (!this.currentProjectId) return null;
        
        const project = this.projects.find(p => p.id === this.currentProjectId);
        if (!project || !project.sessions) return null;
        
        return project.sessions.find(s => s.title === title);
    }

    // 新規プロジェクト作成
    async createNewProject() {
        const projectName = prompt(t('enter_project_name'), t('new_project'));
        if (!projectName) return;
        
        try {
            console.log(`新規プロジェクトを作成: ${projectName}`);
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: projectName,
                    instructions: '',
                }),
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const newProject = await response.json();
            
            // プロジェクト一覧を再読み込み
            await this.loadProjects();
            
            // 新しいプロジェクトを選択
            this.selectProject(newProject.id);
        } catch (error) {
            console.error('プロジェクト作成に失敗しました:', error);
            alert(t('project_create_failed'));
        }
    }

    // 現在のプロジェクトを保存
    async saveCurrentProject() {
        if (!this.currentProjectId) {
            console.warn('現在のプロジェクトIDがありません');
            return;
        }
        
        const nameInput = this.projectDetailsElement.querySelector('#project-name');
        const name = nameInput ? nameInput.value : '';
        const instructions = this.projectInstructionsElement ? this.projectInstructionsElement.value : '';
        
        try {
            console.log(`プロジェクトを保存: ${this.currentProjectId}`);
            const response = await fetch(`/api/projects/${this.currentProjectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    instructions,
                }),
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            // 保存成功時にプロジェクトデータの内部状態を更新
            this.currentProjectData.name = name;
            this.currentProjectData.instructions = instructions;
            
            // 保存成功メッセージ
            this.showSavedIndicator();
            
            // プロジェクト一覧を再読み込み
            await this.loadProjects();
        } catch (error) {
            console.error('プロジェクト保存に失敗しました:', error);
            alert(t('project_save_failed'));
        }
    }
    
    // 保存成功表示
    showSavedIndicator() {
        const savedIndicator = document.createElement('div');
        savedIndicator.className = 'saved-indicator';
        savedIndicator.textContent = t('project_saved');
        document.body.appendChild(savedIndicator);
        
        // 少し経ったら消す
        setTimeout(() => {
            if (savedIndicator.parentNode === document.body) {
                document.body.removeChild(savedIndicator);
            }
        }, 2000);
    }

    // 新規セッション作成
    async createNewSession() {
        if (!this.currentProjectId) {
            console.warn('プロジェクトが選択されていません');
            return;
        }
        
        try {
            console.log(`新規セッションを作成: プロジェクト ${this.currentProjectId}`);
            const response = await fetch(`/api/projects/${this.currentProjectId}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: this.currentProjectId,
                    title: t('new_session'),
                }),
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const newSession = await response.json();
            
            // プロジェクト詳細を再読み込み（セッションリストの更新のため）
            await this.selectProject(this.currentProjectId);
            
            // 新しいセッションを選択
            this.selectSession(newSession.id);
        } catch (error) {
            console.error('セッション作成に失敗しました:', error);
            alert(t('session_create_failed'));
        }
    }

    // 現在のプロジェクトを削除
    async deleteCurrentProject() {
        if (!this.currentProjectId) {
            console.warn('削除するプロジェクトがありません');
            return;
        }
        
        // 確認ダイアログ
        if (!confirm(t('confirm_delete_project'))) {
            return;
        }
        
        try {
            console.log(`プロジェクトを削除: ${this.currentProjectId}`);
            const response = await fetch(`/api/projects/${this.currentProjectId}`, {
                method: 'DELETE',
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            // プロジェクト一覧を再読み込み
            await this.loadProjects();
            
            // 現在のプロジェクトとセッション情報をクリア
            this.currentProjectId = null;
            this.currentSessionId = null;
            this.currentProjectData = null;
            this.currentSessionData = null;
            
            // 削除成功メッセージ
            const deleteIndicator = document.createElement('div');
            deleteIndicator.className = 'saved-indicator';
            deleteIndicator.textContent = t('project_deleted');
            document.body.appendChild(deleteIndicator);
            
            setTimeout(() => {
                if (deleteIndicator.parentNode === document.body) {
                    document.body.removeChild(deleteIndicator);
                }
            }, 2000);
        } catch (error) {
            console.error('プロジェクト削除に失敗しました:', error);
            alert(t('project_delete_failed'));
        }
    }
    
    // 現在のプロジェクト名を変更
    async renameCurrentProject() {
        if (!this.currentProjectId || !this.currentProjectData) {
            console.warn('名前変更するプロジェクトがありません');
            return;
        }
        
        const newName = prompt(t('enter_new_project_name'), this.currentProjectData.name);
        if (!newName || newName === this.currentProjectData.name) {
            return;
        }
        
        try {
            console.log(`プロジェクト名を変更: ${this.currentProjectId}`);
            const response = await fetch(`/api/projects/${this.currentProjectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: newName,
                    instructions: this.currentProjectData.instructions || '',
                }),
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            // 名前の更新を反映
            const nameInput = this.projectDetailsElement.querySelector('#project-name');
            if (nameInput) {
                nameInput.value = newName;
            }
            
            // プロジェクトデータの内部状態を更新
            this.currentProjectData.name = newName;
            
            // プロジェクト一覧を再読み込み
            await this.loadProjects();
            
            // 名前変更成功メッセージ
            const renameIndicator = document.createElement('div');
            renameIndicator.className = 'saved-indicator';
            renameIndicator.textContent = t('project_renamed');
            document.body.appendChild(renameIndicator);
            
            setTimeout(() => {
                if (renameIndicator.parentNode === document.body) {
                    document.body.removeChild(renameIndicator);
                }
            }, 2000);
        } catch (error) {
            console.error('プロジェクト名変更に失敗しました:', error);
            alert(t('project_rename_failed'));
        }
    }
    
    // 現在のセッションを削除
    async deleteCurrentSession() {
        if (!this.currentSessionId) {
            console.warn('削除するセッションがありません');
            return;
        }
        
        // 確認ダイアログ
        if (!confirm(t('confirm_delete_session'))) {
            return;
        }
        
        try {
            console.log(`セッションを削除: ${this.currentSessionId}`);
            // セッション削除のAPIエンドポイントを呼び出す
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'DELETE',
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            // 現在のプロジェクトを再読み込み（セッションリストの更新のため）
            await this.refreshCurrentProject();
            
            // 現在のセッション情報をクリア
            this.currentSessionId = null;
            this.currentSessionData = null;
            
            // 削除成功メッセージ
            const deleteIndicator = document.createElement('div');
            deleteIndicator.className = 'saved-indicator';
            deleteIndicator.textContent = t('session_deleted');
            document.body.appendChild(deleteIndicator);
            
            setTimeout(() => {
                if (deleteIndicator.parentNode === document.body) {
                    document.body.removeChild(deleteIndicator);
                }
            }, 2000);
        } catch (error) {
            console.error('セッション削除に失敗しました:', error);
            alert(t('session_delete_failed'));
        }
    }
    
    // 現在のセッション名を変更
    async renameCurrentSession() {
        if (!this.currentSessionId || !this.currentSessionData) {
            console.warn('名前変更するセッションがありません');
            return;
        }
        
        const newTitle = prompt(t('enter_new_session_name'), this.currentSessionData.title);
        if (!newTitle || newTitle === this.currentSessionData.title) {
            return;
        }
        
        try {
            console.log(`セッション名を変更: ${this.currentSessionId}`);
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: newTitle,
                }),
            });
            
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            // セッションデータの内部状態を更新
            this.currentSessionData.title = newTitle;
            
            // 現在のプロジェクトを再読み込み（セッションリスト更新のため）
            await this.refreshCurrentProject();
            
            // セッションを再選択して表示を更新
            this.selectSession(this.currentSessionId);
            
            // 名前変更成功メッセージ
            const renameIndicator = document.createElement('div');
            renameIndicator.className = 'saved-indicator';
            renameIndicator.textContent = t('session_renamed');
            document.body.appendChild(renameIndicator);
            
            setTimeout(() => {
                if (renameIndicator.parentNode === document.body) {
                    document.body.removeChild(renameIndicator);
                }
            }, 2000);
        } catch (error) {
            console.error('セッション名変更に失敗しました:', error);
            alert(t('session_rename_failed'));
        }
    }

    // 現在のセッション情報取得
    getCurrentSession() {
        return {
            projectId: this.currentProjectId,
            sessionId: this.currentSessionId
        };
    }
    
    // 現在のプロジェクトデータを取得
    getCurrentProjectData() {
        return this.currentProjectData;
    }
    
    // 現在のセッションデータを取得
    getCurrentSessionData() {
        return this.currentSessionData;
    }
}
