"""
データベースアクセスユーティリティモジュール
app.web.database をラップし、依存性注入パターンを使ってデータベース接続を提供する
"""
from typing import Dict, List, Optional, Any, Callable
import app.web.database as web_db

class Database:
    """データベース操作クラス - app.web.database モジュールの関数をラップ"""
    
    def __init__(self):
        """データベース操作のインスタンスを初期化"""
        pass
    
    def get_all_projects(self) -> List[Dict]:
        """すべてのプロジェクトを取得する"""
        return web_db.get_all_projects()
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """プロジェクトを取得する"""
        return web_db.get_project(project_id)
    
    def create_project(self, project_id: str, name: str, instructions: Optional[str] = None) -> bool:
        """新しいプロジェクトを作成する"""
        return web_db.create_project(project_id, name, instructions)
    
    def update_project(self, project_id: str, name: Optional[str] = None, instructions: Optional[str] = None) -> bool:
        """プロジェクトを更新する"""
        return web_db.update_project(project_id, name, instructions)
    
    def delete_project(self, project_id: str) -> bool:
        """プロジェクトを削除する"""
        return web_db.delete_project(project_id)
    
    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """プロジェクトに属するすべてのセッションを取得する"""
        return web_db.get_project_sessions(project_id)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """セッションを取得する"""
        return web_db.get_session(session_id)
    
    def create_session(self, session_id: str, project_id: str, title: Optional[str] = None, workspace_path: Optional[str] = None) -> bool:
        """新しいセッションを作成する"""
        return web_db.create_session(session_id, project_id, title, workspace_path)
    
    def update_session(self, session_id: str, title: Optional[str] = None, workspace_path: Optional[str] = None) -> bool:
        """セッションを更新する"""
        return web_db.update_session(session_id, title, workspace_path)
    
    def delete_session(self, session_id: str) -> bool:
        """セッションを削除する"""
        return web_db.delete_session(session_id)
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """セッションに属するすべてのメッセージを取得する"""
        return web_db.get_session_messages(session_id)
    
    def create_message(self, message_id: str, session_id: str, role: str, content: str) -> bool:
        """新しいメッセージを作成する"""
        return web_db.create_message(message_id, session_id, role, content)

# データベースのグローバルインスタンス
_db = Database()

def get_db() -> Database:
    """データベース接続を取得する（依存性注入に使用）"""
    return _db
