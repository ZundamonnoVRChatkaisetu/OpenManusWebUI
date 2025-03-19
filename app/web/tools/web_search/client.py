"""
Web検索APIクライアント

Brave Search API クライアント
"""
import aiohttp
import json
from typing import Dict, List, Any, Optional
import logging

from ..config import get_tool_config

logger = logging.getLogger(__name__)

class WebSearchClient:
    """Brave Search APIクライアント"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self):
        """クライアントの初期化"""
        config = get_tool_config('web_search')
        self.api_key = config.get('api_key', '')
        
        if not self.api_key:
            logger.warning("Brave Search APIキーが設定されていません")
    
    async def search(self, 
                    query: str, 
                    count: int = 5, 
                    offset: int = 0) -> Dict[str, Any]:
        """
        検索クエリを実行し、結果を返します
        
        Args:
            query: 検索クエリ
            count: 取得する結果の数 (最大20)
            offset: 検索結果の開始インデックス (ページネーション用)
            
        Returns:
            検索結果の辞書
        """
        if not self.api_key:
            return {
                "error": "Brave Search APIの設定が不足しています。APIキーを設定してください。",
                "items": []
            }
        
        # API制限を守るために調整
        if count > 20:
            count = 20
        
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.api_key
        }
        
        params = {
            'q': query,
            'count': count,
            'offset': offset
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, headers=headers) as response:
                    if response.status == 200:
                        results = await response.json()
                        return results
                    else:
                        error_text = await response.text()
                        logger.error(f"Brave Search APIエラー: {response.status} - {error_text}")
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
            results: Brave Search APIからの結果
            
        Returns:
            フォーマットされた検索結果リスト
        """
        formatted_results = []
        
        if "error" in results:
            return [{"title": "エラー", "link": "", "snippet": results["error"]}]
        
        web_results = results.get("web", {}).get("results", [])
        for item in web_results:
            formatted_results.append({
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "displayLink": item.get("display_url", ""),
                "source": "Brave"
            })
        
        return formatted_results
