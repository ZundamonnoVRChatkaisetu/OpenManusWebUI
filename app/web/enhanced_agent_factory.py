"""エージェント生成ファクトリー

OpenManusエージェントを生成するためのファクトリー関数を提供します。
"""

import os
from typing import List, Optional, Dict, Any, Union

from app.agent.manus import Manus
from app.agent.base import BaseAgent as Agent
from app.agent.enhanced_manus import EnhancedManus
from app.llm.factory import create_llm_client
from app.web.database import get_project


def create_agent(prompt: str, llm_vendor: str = "open-webui") -> Agent:
    """
    プロンプトに基づいてエージェントを生成

    Args:
        prompt: ユーザープロンプト
        llm_vendor: LLMベンダー名

    Returns:
        生成されたエージェント
    """
    llm = create_llm_client(llm_vendor)
    return Manus(llm)


def create_enhanced_agent(
    prompt: str, 
    llm_vendor: str = "open-webui", 
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **kwargs
) -> EnhancedManus:
    """
    強化版エージェントを生成

    Args:
        prompt: ユーザープロンプト
        llm_vendor: LLMベンダー名
        session_id: セッションID（オプション）
        project_id: プロジェクトID（オプション）
        **kwargs: その他の引数

    Returns:
        生成された強化版エージェント
    """
    llm = create_llm_client(llm_vendor)
    agent = EnhancedManus(llm)
    
    # セッションIDを設定
    agent.session_id = session_id
    
    # プロジェクトIDがある場合は設定
    if project_id:
        agent.current_project = project_id
    
    # 環境変数から言語設定を取得
    if "ENHANCED_MANUS_LANGUAGE" in os.environ:
        agent.language = os.environ["ENHANCED_MANUS_LANGUAGE"]
    
    return agent
