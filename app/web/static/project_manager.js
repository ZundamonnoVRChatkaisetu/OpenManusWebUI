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
            }
            
            // 外部のプロジェクト選択ハンドラを呼び出し
            if (this.handleProjectSelect) {
                this.handleProjectSelect(projectId);
            }
        } catch (error) {
            console.error('プロジェクト詳細の読み込みに失敗しました:', error);
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
            return;
        }
        
        // セッションアイテムを追加
        sessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
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
        });
        
        // 選択されたセッションにselectedクラスを追加
        // セッションIDの比較は複雑になる可能性がある
        // ここではtitleで検索する方法から、
        // セッションIDを明示的に保存するアプローチに変更
        const selectedItems = this.sessionListElement.querySelectorAll(`.session-item`);
        selectedItems.forEach(item => {
            if (item.querySelector && item.querySelector('.session-title')) {
                const title = item.querySelector('.session-title').textContent;
                const session = this.findSessionByTitle(title);
                if (session && session.id === sessionId) {
                    item.classList.add('selected');
                }
            }
        });
        
        // 親コンポーネントにセッション選択を通知
        if (this.handleSessionSelect) {
            this.handleSessionSelect(sessionId);
        } else {
            console.warn('セッション選択ハンドラが設定されていません');
        }
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            if (!response.ok) {
                throw new Error(t('api_error', { status: response.status }));
            }
            
            const sessionData = await response.json();
            // メッセージ表示などの処理
            
            // チャット履歴を表示する場合、ここでメッセージを取得して表示
            // if (sessionData.messages && sessionData.messages.length > 0) {
            //     this.displayChatHistory(sessionData.messages);
            // }
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
            
            // 保存成功メッセージ
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
            
            // プロジェクト一覧を再読み込み
            await this.loadProjects();
        } catch (error) {
            console.error('プロジェクト保存に失敗しました:', error);
            alert(t('project_save_failed'));
        }
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

    // 現在のセッション情報取得
    getCurrentSession() {
        return {
            projectId: this.currentProjectId,
            sessionId: this.currentSessionId
        };
    }
}
