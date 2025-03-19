"""
Web検索ツール

Google検索を実行するためのツール
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
                     num_results: int = 5, 
                     start_index: int = 1) -> ToolResult:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            num_results: 取得する結果の数 (デフォルト: 5, 最大: 10)
            start_index: 検索結果の開始インデックス (デフォルト: 1)
            
        Returns:
            ToolResult: 検索結果
        """
        try:
            logger.info(f"Web検索実行: '{query}' (結果数: {num_results}, 開始インデックス: {start_index})")
            
            # 入力値の検証
            if not query or not isinstance(query, str):
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message="検索クエリが指定されていないか、無効です",
                    data=None
                )
            
            # 結果数の検証と調整
            if not isinstance(num_results, int) or num_results < 1:
                num_results = 5
            elif num_results > 10:
                num_results = 10
            
            # 開始インデックスの検証
            if not isinstance(start_index, int) or start_index < 1:
                start_index = 1
            
            # 検索実行
            results = await self.client.search(query, num_results, start_index)
            
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
            search_info = results.get("searchInformation", {})
            total_results = search_info.get("totalResults", "0")
            search_time = search_info.get("searchTime", 0)
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"'{query}'の検索結果: {len(formatted_results)}件 (全{total_results}件中、{search_time:.2f}秒)",
                data={
                    "query": query,
                    "items": formatted_results,
                    "total_results": total_results,
                    "current_page": start_index,
                    "items_per_page": num_results
                }
            )
            
        except Exception as e:
            logger.error(f"Web検索ツール実行中にエラーが発生しました: {str(e)}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"検索実行中に予期しないエラーが発生しました: {str(e)}",
                data=None
            )
