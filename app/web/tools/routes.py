"""
ツール関連のAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
import logging

from .tool_manager import ToolManager
from .config import get_tool_config, update_tool_config, TOOLS_CONFIG_FILE

# ロガー設定
logger = logging.getLogger(__name__)

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
    logger.info(f"ツール設定取得リクエスト: {tool_name}")
    config = get_tool_config(tool_name)
    
    # 設定をログに出力（APIキーや秘密情報は除く）
    log_config = config.copy() if config else {}
    sensitive_keys = ["api_key", "access_token", "secret", "password", "key"]
    for key in sensitive_keys:
        if key in log_config:
            log_config[key] = "********" if log_config[key] else ""
    logger.info(f"ツール設定の内容: {json.dumps(log_config)}")
    
    # 機密情報を削除したコピーを作成
    safe_config = config.copy() if config else {}
    
    # APIキーやトークンなどの機密情報をマスク
    for key in sensitive_keys:
        if key in safe_config:
            safe_config[key] = "********" if safe_config[key] else ""
    
    response = {
        "tool": tool_name,
        "config": safe_config
    }
    logger.info(f"ツール設定レスポンス: {json.dumps(response)}")
    return response


@router.put("/config/{tool_name}")
async def update_config(tool_name: str, request: ToolConfigUpdateRequest):
    """ツール設定を更新"""
    logger.info(f"ツール設定更新リクエスト: {tool_name}")
    try:
        # 既存の設定を取得
        current_config = get_tool_config(tool_name)
        
        # リクエスト内容をログに出力（APIキーや秘密情報は除く）
        log_config = request.config.copy()
        sensitive_keys = ["api_key", "access_token", "secret", "password", "key"]
        for key in sensitive_keys:
            if key in log_config:
                log_config[key] = "********" if log_config[key] else ""
        logger.info(f"設定更新リクエスト内容: {json.dumps(log_config)}")
        
        # 機密情報を保持（マスクされた値での更新を防止）
        for key, value in request.config.items():
            if value == "********" and key in current_config:
                request.config[key] = current_config[key]
        
        # 設定を更新
        update_tool_config(tool_name, request.config)
        
        response = {
            "success": True,
            "message": f"{tool_name} の設定を更新しました"
        }
        logger.info(f"設定更新レスポンス: {json.dumps(response)}")
        return response
    except Exception as e:
        logger.error(f"設定更新エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"設定更新エラー: {str(e)}")


@router.post("/verify/{tool_name}")
async def verify_tool_config_post(tool_name: str):
    """ツール設定の検証（POSTメソッド）"""
    return await _verify_tool_config(tool_name)


@router.get("/verify/{tool_name}")
async def verify_tool_config_get(tool_name: str):
    """ツール設定の検証（GETメソッド）"""
    return await _verify_tool_config(tool_name)


@router.get("/config_path")
async def get_config_path():
    """設定ファイルの保存パスを取得する"""
    try:
        return {
            "success": True,
            "config_path": str(TOOLS_CONFIG_FILE)
        }
    except Exception as e:
        logger.error(f"設定パス取得エラー: {str(e)}")
        return {
            "success": False,
            "message": f"設定パス取得エラー: {str(e)}"
        }


async def _verify_tool_config(tool_name: str):
    """ツール設定の検証実装（共通処理）"""
    logger.info(f"ツール設定検証リクエスト: {tool_name}")
    try:
        if tool_name == "github":
            # GitHubツールの検証
            from .github.client import GitHubClient
            client = GitHubClient()
            user_info = await client.get_user()
            
            # ユーザー情報をログに出力
            log_user_info = {k: v for k, v in user_info.items() if k not in ["access_token"]}
            logger.info(f"GitHub認証成功: {json.dumps(log_user_info)}")
            
            response = {
                "success": True,
                "message": f"GitHub認証成功: {user_info.get('login')}",
                "user": user_info
            }
            logger.info(f"設定検証レスポンス: 成功")
            return response
        elif tool_name == "web_search":
            # Web検索ツールの検証
            from .web_search.client import WebSearchClient
            client = WebSearchClient()
            
            # 簡単な検索クエリでテスト
            test_result = await client.search("test", count=1)
            
            if test_result and "web" in test_result and "results" in test_result["web"]:
                response = {
                    "success": True,
                    "message": "Web検索API設定の検証に成功しました",
                }
                logger.info(f"Web検索API設定検証: 成功")
                return response
            else:
                response = {
                    "success": False,
                    "message": "Web検索API設定の検証に失敗しました"
                }
                logger.warning(f"Web検索API設定検証: 失敗")
                return response
        else:
            response = {
                "success": False,
                "message": f"ツール '{tool_name}' の検証はサポートされていません"
            }
            logger.info(f"設定検証レスポンス: {json.dumps(response)}")
            return response
    except Exception as e:
        error_message = f"検証エラー: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "message": error_message
        }
