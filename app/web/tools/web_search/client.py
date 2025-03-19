"""
Web検索APIクライアント

Google Custom Search JSON API クライアント
"""
import aiohttp
import json
from typing import Dict, List, Any, Optional
import logging

from ..config import get_tool_config

logger = logging.getLogger(__name__)

class WebSearchClient:
    """Google Custom Search JSON APIクライアント"""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self):
        """クライアントの初期化"""
        config = get_tool_config('web_search')
        self.api_key = config.get('api_key', '')
        self.cse_id = config.get('cse_id', '')
        
        if not self.api_key:
            logger.warning("Web検索APIキーが設定されていません")
        if not self.cse_id:
            logger.warning("Web検索カスタム検索エンジンIDが設定されていません")
    
    async def search(self, 
                    query: str, 
                    num_results: int = 5, 
                    start_index: int = 1) -> Dict[str, Any]:
        """
        検索クエリを実行し、結果を返します
        
        Args:
            query: 検索クエリ
            num_results: 取得する結果の数 (最大10)
            start_index: 検索結果の開始インデックス (1から始まる)
            
        Returns:
            検索結果の辞書
        """
        if not self.api_key or not self.cse_id:
            return {
                "error": "Web検索APIの設定が不足しています。APIキーとカスタム検索エンジンIDを設定してください。",
                "items": []
            }
        
        # API制限を守るために調整
        if num_results > 10:
            num_results = 10
        
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.cse_id,
            'num': num_results,
            'start': start_index
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        results = await response.json()
                        return results
                    else:
                        error_text = await response.text()
                        logger.error(f"Web検索APIエラー: {response.status} - {error_text}")
                        return {
                            "error": f"API呼び出し中にエラーが発生しました: {response.status}",
                            "details": error_text,
                            "items": []
                        }
        except Exception as e:
            logger.error(f"Web検索実行中に例外が発生しました: {str(e)}")
            return {
                "error": f"検索実行中にエラーが発生しました: {str(e)}",
                "items": []
            }
    
    def format_results(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        API結果をフォーマットして標準化された結果リストを返します
        
        Args:
            results: Google Custom Search APIからの結果
            
        Returns:
            フォーマットされた検索結果リスト
        """
        formatted_results = []
        
        if "error" in results:
            return [{"title": "エラー", "link": "", "snippet": results["error"]}]
        
        items = results.get("items", [])
        for item in items:
            formatted_results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "displayLink": item.get("displayLink", ""),
                "source": "Google"
            })
        
        return formatted_results
