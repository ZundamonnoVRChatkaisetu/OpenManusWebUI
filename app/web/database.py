"""
データベース接続および初期化モジュール
SQLiteを使用してプロジェクト、セッション、指示を保存する
"""
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# データベースファイルのパス
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "openmanus.db"

def get_db_connection():
    """データベース接続を取得する"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 結果を辞書形式で取得
    return conn

def init_db():
    """データベースを初期化する"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # プロジェクトテーブル
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        instructions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # セッションテーブル
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_path TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')

    # メッセージテーブル
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions (id)
    )
    ''')

    conn.commit()
    conn.close()

# プロジェクト関連の操作
def create_project(project_id: str, name: str, instructions: Optional[str] = None) -> bool:
    """新しいプロジェクトを作成する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO projects (id, name, instructions) VALUES (?, ?, ?)",
            (project_id, name, instructions)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"プロジェクト作成エラー: {str(e)}")
        return False
    finally:
        conn.close()

def get_project(project_id: str) -> Optional[Dict]:
    """プロジェクトを取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    
    if project:
        return dict(project)
    return None

def update_project(project_id: str, name: Optional[str] = None, instructions: Optional[str] = None) -> bool:
    """プロジェクトを更新する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = []
    params = []
    
    if name is not None:
        update_fields.append("name = ?")
        params.append(name)
    
    if instructions is not None:
        update_fields.append("instructions = ?")
        params.append(instructions)
    
    if not update_fields:
        return True  # 更新するフィールドがない場合は成功とみなす
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    query = f"UPDATE projects SET {', '.join(update_fields)} WHERE id = ?"
    params.append(project_id)
    
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"プロジェクト更新エラー: {str(e)}")
        return False
    finally:
        conn.close()

def delete_project(project_id: str) -> bool:
    """プロジェクトを削除する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 関連するセッションとメッセージも削除
        cursor.execute("SELECT id FROM sessions WHERE project_id = ?", (project_id,))
        session_ids = [row['id'] for row in cursor.fetchall()]
        
        for session_id in session_ids:
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        
        cursor.execute("DELETE FROM sessions WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"プロジェクト削除エラー: {str(e)}")
        return False
    finally:
        conn.close()

def get_all_projects() -> List[Dict]:
    """すべてのプロジェクトを取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects

# セッション関連の操作
def create_session(session_id: str, project_id: str, title: Optional[str] = None, workspace_path: Optional[str] = None) -> bool:
    """新しいセッションを作成する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO sessions (id, project_id, title, workspace_path) VALUES (?, ?, ?, ?)",
            (session_id, project_id, title, workspace_path)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"セッション作成エラー: {str(e)}")
        return False
    finally:
        conn.close()

def get_session(session_id: str) -> Optional[Dict]:
    """セッションを取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return dict(session)
    return None

def update_session(session_id: str, title: Optional[str] = None, workspace_path: Optional[str] = None) -> bool:
    """セッションを更新する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = []
    params = []
    
    if title is not None:
        update_fields.append("title = ?")
        params.append(title)
    
    if workspace_path is not None:
        update_fields.append("workspace_path = ?")
        params.append(workspace_path)
    
    if not update_fields:
        return True
    
    query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE id = ?"
    params.append(session_id)
    
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"セッション更新エラー: {str(e)}")
        return False
    finally:
        conn.close()

def delete_session(session_id: str) -> bool:
    """セッションを削除する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 関連するメッセージを先に削除
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        
        # セッション自体を削除
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"セッション削除エラー: {str(e)}")
        return False
    finally:
        conn.close()

def get_project_sessions(project_id: str) -> List[Dict]:
    """プロジェクトに属するすべてのセッションを取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

# メッセージ関連の操作
def create_message(message_id: str, session_id: str, role: str, content: str) -> bool:
    """新しいメッセージを作成する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, role, content)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"メッセージ作成エラー: {str(e)}")
        return False
    finally:
        conn.close()

def get_session_messages(session_id: str) -> List[Dict]:
    """セッションに属するすべてのメッセージを取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

# 起動時にデータベースを初期化
init_db()
