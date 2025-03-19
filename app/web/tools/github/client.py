"""
GitHubクライアント - GitHub APIとの通信を担当
"""
import httpx
import logging
import json
from typing import Dict, List, Any, Optional, Union
import base64

from ..config import get_tool_config, get_env_setting

# ロガー設定
logger = logging.getLogger(__name__)

# GitHub API URL
GITHUB_API_URL = "https://api.github.com"


class GitHubClient:
    """
    GitHub APIとの通信を担当するクライアントクラス
    """
    def __init__(self):
        """GitHubクライアントの初期化"""
        self.config = get_tool_config("github")
        
        # 設定値の取得（環境変数 > 設定ファイル）
        self.access_token = get_env_setting("GITHUB_PERSONAL_ACCESS_TOKEN") or self.config.get("access_token", "")
        self.username = self.config.get("username", "")
        self.timeout = 30.0  # API呼び出しのタイムアウト（秒）
        
        logger.info(f"GitHubClient初期化: アクセストークン={bool(self.access_token)}, ユーザー名={self.username}")

    def _get_headers(self) -> Dict[str, str]:
        """API呼び出し用のヘッダー取得"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenManusWebUI-GitHub-Client"
        }
        
        if self.access_token:
            # Bearer形式での認証（新しい推奨形式）
            headers["Authorization"] = f"Bearer {self.access_token}"
            logger.debug("GitHub API認証ヘッダー: Bearer形式を使用")
        
        return headers

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GitHub APIへのリクエスト実行"""
        url = f"{GITHUB_API_URL}{endpoint}"
        headers = self._get_headers()
        
        if not self.access_token:
            logger.warning("GitHub Access Tokenが設定されていません。API呼び出しが制限される可能性があります。")
        
        logger.info(f"GitHub APIリクエスト: {method} {url}")
        
        # HTTPXクライアントを使用してリクエスト
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data
                )
                
                # レート制限情報をログに記録
                rate_limit = response.headers.get("X-RateLimit-Remaining", "N/A")
                logger.debug(f"GitHub API レスポンスステータス: {response.status_code}, 残りレート制限: {rate_limit}")
                
                # レスポンスの詳細をログに出力
                content_type = response.headers.get("Content-Type", "")
                logger.debug(f"レスポンスContent-Type: {content_type}")
                
                # エラーの場合は詳細をログに出力
                if response.status_code >= 400:
                    try:
                        error_detail = response.json()
                        logger.error(f"GitHub APIエラー: {response.status_code} - {json.dumps(error_detail)}")
                    except:
                        logger.error(f"GitHub APIエラー: {response.status_code} - {response.text}")
                
                # レスポンス確認
                response.raise_for_status()
                
                # JSONレスポンスの場合
                if "application/json" in content_type:
                    result = response.json()
                    logger.debug(f"GitHub API JSONレスポンス: {json.dumps(result)[:500]}...")
                    return result
                
                # それ以外の場合はテキストとして返す
                logger.debug(f"GitHub API テキストレスポンス: {response.text[:500]}...")
                return {"content": response.text}
            
            except httpx.HTTPStatusError as e:
                error_message = f"GitHub API エラー ({e.response.status_code}): {url}"
                
                # エラーレスポンスのJSONをパース試みる
                try:
                    error_data = e.response.json()
                    error_message += f" - {error_data.get('message', '')}"
                    if 'documentation_url' in error_data:
                        error_message += f" (ドキュメント: {error_data['documentation_url']})"
                    logger.error(f"GitHub APIエラー詳細: {json.dumps(error_data)}")
                except:
                    error_message += f" - {e.response.text}"
                
                logger.error(error_message)
                raise ValueError(error_message)
            
            except httpx.RequestError as e:
                error_message = f"GitHub API リクエストエラー: {str(e)}"
                logger.error(error_message)
                raise ValueError(error_message)

    async def search_repositories(
        self, 
        query: str, 
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        リポジトリを検索
        
        Args:
            query (str): 検索クエリ
            sort (str, optional): ソート基準（stars, forks, updated）
            order (str, optional): ソート順（asc, desc）
            page (int, optional): ページ番号
            per_page (int, optional): 1ページあたりの結果数
        
        Returns:
            Dict[str, Any]: 検索結果
        """
        params = {
            "q": query,
            "page": page,
            "per_page": per_page
        }
        
        if sort:
            params["sort"] = sort
        
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "/search/repositories", params=params)

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        リポジトリ情報を取得
        
        Args:
            owner (str): リポジトリのオーナー（ユーザー名または組織名）
            repo (str): リポジトリ名
        
        Returns:
            Dict[str, Any]: リポジトリ情報
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}")

    async def get_repository_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "",
        ref: Optional[str] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        リポジトリのコンテンツ一覧、またはファイル内容を取得
        
        Args:
            owner (str): リポジトリのオーナー
            repo (str): リポジトリ名
            path (str, optional): リポジトリ内のパス（空の場合はルート）
            ref (str, optional): ブランチ名、タグ名、またはコミットSHA
        
        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: 
                パスがディレクトリの場合はファイル/ディレクトリのリスト、
                パスがファイルの場合はファイル情報
        """
        params = {}
        if ref:
            params["ref"] = ref
        
        return await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)

    async def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        path: str,
        ref: Optional[str] = None
    ) -> str:
        """
        ファイルの内容を取得（デコード済み）
        
        Args:
            owner (str): リポジトリのオーナー
            repo (str): リポジトリ名
            path (str): ファイルパス
            ref (str, optional): ブランチ名、タグ名、またはコミットSHA
        
        Returns:
            str: デコードされたファイル内容
        """
        params = {}
        if ref:
            params["ref"] = ref
        
        response = await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)
        
        if "content" in response and "encoding" in response:
            if response["encoding"] == "base64":
                # Base64デコード
                content = base64.b64decode(response["content"]).decode("utf-8")
                return content
            else:
                logger.warning(f"未対応のエンコーディング: {response['encoding']}")
                return response["content"]
        
        return json.dumps(response, ensure_ascii=False, indent=2)

    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: Optional[str] = None,
        sha: Optional[str] = None  # 更新時に必要
    ) -> Dict[str, Any]:
        """
        ファイルの作成または更新
        
        Args:
            owner (str): リポジトリのオーナー
            repo (str): リポジトリ名
            path (str): ファイルパス
            content (str): ファイル内容
            message (str): コミットメッセージ
            branch (str, optional): ブランチ名
            sha (str, optional): 既存ファイルのSHA（更新時に必要）
        
        Returns:
            Dict[str, Any]: 作成/更新結果
        """
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
        }
        
        if branch:
            data["branch"] = branch
        
        if sha:
            data["sha"] = sha
        
        return await self._make_request(
            "PUT", 
            f"/repos/{owner}/{repo}/contents/{path}", 
            json_data=data
        )

    async def search_issues(
        self, 
        query: str, 
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Issue/PRを検索
        
        Args:
            query (str): 検索クエリ
            sort (str, optional): ソート基準（created, updated, comments）
            order (str, optional): ソート順（asc, desc）
            page (int, optional): ページ番号
            per_page (int, optional): 1ページあたりの結果数
        
        Returns:
            Dict[str, Any]: 検索結果
        """
        params = {
            "q": query,
            "page": page,
            "per_page": per_page
        }
        
        if sort:
            params["sort"] = sort
        
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "/search/issues", params=params)

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Issueを作成
        
        Args:
            owner (str): リポジトリのオーナー
            repo (str): リポジトリ名
            title (str): issueのタイトル
            body (str): issueの本文
            labels (List[str], optional): ラベルのリスト
        
        Returns:
            Dict[str, Any]: 作成結果
        """
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/issues", 
            json_data=data
        )

    async def get_user(self) -> Dict[str, Any]:
        """
        認証ユーザー情報を取得
        
        Returns:
            Dict[str, Any]: ユーザー情報
        """
        try:
            logger.info("GitHub ユーザー情報取得リクエスト")
            result = await self._make_request("GET", "/user")
            logger.info(f"GitHub ユーザー情報取得成功: {result.get('login', '不明')}")
            return result
        except Exception as e:
            logger.error(f"GitHub ユーザー情報取得失敗: {str(e)}")
            raise
