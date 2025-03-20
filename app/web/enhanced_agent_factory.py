"""
強化エージェントファクトリー - Webアプリケーション用
"""

import os
from typing import Optional

from app.agent.enhanced_manus import EnhancedManus
from app.utils.language_utils import Language


def create_enhanced_agent(prompt: str = "") -> EnhancedManus:
    """
    適切に設定されたEnhancedManusエージェントを作成する
    
    Args:
        prompt: オプションの初期プロンプト（言語検出に使用される）
        
    Returns:
        設定されたEnhancedManusインスタンス
    """
    # 環境変数から設定を取得
    show_thoughts = os.environ.get("ENHANCED_MANUS_SHOW_THOUGHTS") == "1"
    disable_auto_files = os.environ.get("ENHANCED_MANUS_DISABLE_AUTO_FILES") == "1"
    language_str = os.environ.get("ENHANCED_MANUS_LANGUAGE", "auto")
    
    # 言語設定
    language: Optional[Language] = None
    if language_str != "auto":
        if language_str in ["en", "ja", "zh"]:
            language = language_str
    
    # エージェントの作成と設定
    agent = EnhancedManus()
    
    # 思考プロセスの表示設定
    agent.hide_thought_process = not show_thoughts
    
    # ファイル自動生成の設定
    agent.auto_generate_files = not disable_auto_files
    
    # 言語設定
    agent.language = language
    
    return agent
