"""
ツール関連のAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json

from .tool_manager import ToolManager
from .config import get_tool_config, update_tool_config

# ルーター
router = APIRouter(prefix="/api/tools", tags=["tools"])

# ツールマネージャーのインスタンス
tool_manager = ToolManager()


class ToolExecuteRequest(BaseModel):
    tool: str
    params: Dict[str, Any]


class ToolConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


@router.get("/list")
async def list_tools():
    """利用可能なツール一覧を取得"""
    return {
        "tools": tool_manager.get_tools_schema()
    }


@router.get("/instructions")
async def get_tools_instructions():
    """ツールの使用方法の説明を取得"""
    return {
        "instructions": tool_manager.get_tools_usage_instructions()
    }


@router.post("/execute")
async def execute_tool(request: ToolExecuteRequest):
    """ツールを実行"""
    if request.tool not in tool_manager.tools:
        raise HTTPException(status_code=404, detail=f"ツール '{request.tool}' が見つかりません")
    
    try:
        result = await tool_manager.execute_tool(request.tool, request.params)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ツール実行エラー: {str(e)}")


@router.post("/process")
async def process_text(text: str = Body(..., embed=True)):
    """テキスト内のツールコマンドを処理"""
    try:
        processed_text, results = await tool_manager.process_text(text)
        return {
            "processed_text": processed_text,
            "tool_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テキスト処理エラー: {str(e)}")


@router.get("/config/{tool_name}")
async def get_config(tool_name: str):
    """ツール設定を取得"""
    config = get_tool_config(tool_name)
    
    # 機密情報を削除したコピーを作成
    safe_config = config.copy() if config else {}
    
    # APIキーやトークンなどの機密情報をマスク
    sensitive_keys = ["api_key", "access_token", "secret", "password", "key"]
    for key in sensitive_keys:
        if key in safe_config:
            safe_config[key] = "********" if safe_config[key] else ""
    
    return {
        "tool": tool_name,
        "config": safe_config
    }


@router.put("/config/{tool_name}")
async def update_config(tool_name: str, request: ToolConfigUpdateRequest):
    """ツール設定を更新"""
    try:
        # 既存の設定を取得
        current_config = get_tool_config(tool_name)
        
        # 機密情報を保持（マスクされた値での更新を防止）
        for key, value in request.config.items():
            if value == "********" and key in current_config:
                request.config[key] = current_config[key]
        
        # 設定を更新
        update_tool_config(tool_name, request.config)
        
        return {
            "success": True,
            "message": f"{tool_name} の設定を更新しました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定更新エラー: {str(e)}")


@router.post("/verify/{tool_name}")
async def verify_tool_config(tool_name: str):
    """ツール設定の検証"""
    try:
        if tool_name == "github":
            # GitHubツールの検証
            from .github.client import GitHubClient
            client = GitHubClient()
            user_info = await client.get_user()
            return {
                "success": True,
                "message": f"GitHub認証成功: {user_info.get('login')}",
                "user": user_info
            }
        else:
            return {
                "success": False,
                "message": f"ツール '{tool_name}' の検証はサポートされていません"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"検証エラー: {str(e)}"
        }
