"""
プロジェクト、セッション、メッセージなどのPydanticモデル定義
API入出力のバリデーションに使用
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    """プロジェクトの基本情報"""
    name: str = Field(..., description="プロジェクト名")
    instructions: Optional[str] = Field(None, description="プロジェクト指示")

class ProjectCreate(ProjectBase):
    """プロジェクト作成時の入力モデル"""
    pass

class ProjectUpdate(BaseModel):
    """プロジェクト更新時の入力モデル"""
    name: Optional[str] = Field(None, description="プロジェクト名")
    instructions: Optional[str] = Field(None, description="プロジェクト指示")

class Project(ProjectBase):
    """プロジェクトの完全なモデル"""
    id: str = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    """セッションの基本情報"""
    project_id: str = Field(..., description="所属プロジェクトID")
    title: Optional[str] = Field(None, description="セッションタイトル")
    workspace_path: Optional[str] = Field(None, description="関連ワークスペースパス")

class SessionCreate(SessionBase):
    """セッション作成時の入力モデル"""
    pass

class SessionUpdate(BaseModel):
    """セッション更新時の入力モデル"""
    title: Optional[str] = Field(None, description="セッションタイトル")

class Session(SessionBase):
    """セッションの完全なモデル"""
    id: str = Field(..., description="セッションID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    """メッセージの基本情報"""
    session_id: str = Field(..., description="所属セッションID")
    role: str = Field(..., description="送信者役割（user/assistant/system）")
    content: str = Field(..., description="メッセージ内容")

class MessageCreate(MessageBase):
    """メッセージ作成時の入力モデル"""
    pass

class Message(MessageBase):
    """メッセージの完全なモデル"""
    id: str = Field(..., description="メッセージID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True

class ProjectWithSessions(Project):
    """セッションリストを含むプロジェクト情報"""
    sessions: List[Session] = Field(default_factory=list, description="プロジェクトに属するセッション")

class SessionWithMessages(Session):
    """メッセージリストを含むセッション情報"""
    messages: List[Message] = Field(default_factory=list, description="セッションに属するメッセージ")

class ChatRequest(BaseModel):
    """チャットリクエスト"""
    prompt: str = Field(..., description="ユーザーの入力メッセージ")
    project_id: Optional[str] = Field(None, description="プロジェクトID")
    session_id: Optional[str] = Field(None, description="セッションID")

class ChatResponse(BaseModel):
    """チャットレスポンス"""
    session_id: str = Field(..., description="セッションID")
    project_id: Optional[str] = Field(None, description="プロジェクトID")
    workspace: Optional[str] = Field(None, description="ワークスペースパス")
