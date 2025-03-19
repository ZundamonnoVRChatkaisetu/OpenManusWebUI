"""
Web検索ツール

Brave Searchを実行するためのツール
"""
from typing import Dict, List, Any, Optional
import logging

from ..base import Tool, ToolResult, ToolResultStatus, register_tool
from .client import WebSearchClient

logger = logging.getLogger(__name__)

@register_tool
class WebSearchTool(Tool):
    """Web検索ツール"""
    
    name = "web_search"
    description = "インターネット上の情報を検索します。最新の情報や事実確認に有用です。"
    version = "1.0.0"
    
    def __init__(self):
        """ツールの初期化"""
        super().__init__()
        self.client = WebSearchClient()
    
    async def execute(self, 
                     query: str, 
                     count: int = 5, 
                     offset: int = 0) -> ToolResult:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            count: 取得する結果の数 (デフォルト: 5, 最大: 20)
            offset: 検索結果の開始インデックス (デフォルト: 0)
            
        Returns:
            ToolResult: 検索結果
        """
        try:
            logger.info(f"Web検索実行: '{query}' (結果数: {count}, 開始インデックス: {offset})")
            
            # 入力値の検証
            if not query or not isinstance(query, str):
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message="検索クエリが指定されていないか、無効です",
                    data=None
                )
            
            # 結果数の検証と調整
            if not isinstance(count, int) or count < 1:
                count = 5
            elif count > 20:
                count = 20
            
            # 開始インデックスの検証
            if not isinstance(offset, int) or offset < 0:
                offset = 0
            
            # 検索実行
            results = await self.client.search(query, count, offset)
            
            # エラーチェック
            if "error" in results:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message=f"検索中にエラーが発生しました: {results['error']}",
                    data={"items": []}
                )
            
            # 検索結果の整形
            formatted_results = self.client.format_results(results)
            
            # 検索情報の取得
            total_results = results.get("web", {}).get("total", 0)
            search_info = results.get("search_info", {})
            search_time = search_info.get("time_taken_ms", 0) / 1000  # ミリ秒から秒に変換
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"'{query}'の検索結果: {len(formatted_results)}件 (全{total_results}件中、{search_time:.2f}秒)",
                data={
                    "query": query,
                    "items": formatted_results,
                    "total_results": total_results,
                    "current_page": offset // count + 1,
                    "items_per_page": count
                }
            )
            
        except Exception as e:
            logger.error(f"Web検索ツール実行中にエラーが発生しました: {str(e)}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"検索実行中に予期しないエラーが発生しました: {str(e)}",
                data=None
            )
