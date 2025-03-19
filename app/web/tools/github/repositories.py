"""
リポジトリ操作関連のツール
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolResultStatus, register_tool
from .client import GitHubClient


class SearchReposParameters(BaseModel):
    """GitHubリポジトリ検索パラメータ"""
    query: str = Field(..., description="検索クエリ（例: 'language:python stars:>1000'）")
    sort: Optional[str] = Field(None, description="ソート基準（stars, forks, updated）")
    order: Optional[str] = Field(None, description="ソート順（asc, desc）")
    page: int = Field(1, description="ページ番号")
    per_page: int = Field(10, description="1ページあたりの結果数（最大100）")


@register_tool
class SearchReposTool(Tool):
    """GitHubリポジトリを検索するツール"""
    name = "github_search_repos"
    description = "GitHubリポジトリを検索します。言語、スター数などで絞り込みが可能です。"
    version = "1.0.0"
    parameters_model = SearchReposParameters

    async def execute(
        self, 
        query: str, 
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> ToolResult:
        """リポジトリを検索"""
        try:
            client = GitHubClient()
            
            # 検索実行
            result = await client.search_repositories(
                query=query,
                sort=sort,
                order=order,
                page=page,
                per_page=per_page
            )
            
            # 結果整形
            formatted_result = {
                "total_count": result.get("total_count", 0),
                "items": []
            }
            
            # 各リポジトリの情報を整形
            for repo in result.get("items", []):
                formatted_result["items"].append({
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "html_url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count"),
                    "forks": repo.get("forks_count"),
                    "language": repo.get("language"),
                    "updated_at": repo.get("updated_at"),
                    "owner": {
                        "login": repo.get("owner", {}).get("login"),
                        "avatar_url": repo.get("owner", {}).get("avatar_url"),
                        "html_url": repo.get("owner", {}).get("html_url")
                    }
                })
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{formatted_result['total_count']}件のリポジトリが見つかりました",
                data=formatted_result
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"リポジトリ検索エラー: {str(e)}",
                data=None
            )


class GetRepoInfoParameters(BaseModel):
    """GitHubリポジトリ情報取得パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")


@register_tool
class GetRepoInfoTool(Tool):
    """GitHubリポジトリの詳細情報を取得するツール"""
    name = "github_get_repo_info"
    description = "指定したGitHubリポジトリの詳細情報を取得します。"
    version = "1.0.0"
    parameters_model = GetRepoInfoParameters

    async def execute(self, owner: str, repo: str) -> ToolResult:
        """リポジトリ情報を取得"""
        try:
            client = GitHubClient()
            
            # リポジトリ情報取得
            result = await client.get_repository(owner, repo)
            
            # 結果整形
            formatted_result = {
                "name": result.get("name"),
                "full_name": result.get("full_name"),
                "description": result.get("description"),
                "html_url": result.get("html_url"),
                "stars": result.get("stargazers_count"),
                "forks": result.get("forks_count"),
                "language": result.get("language"),
                "created_at": result.get("created_at"),
                "updated_at": result.get("updated_at"),
                "pushed_at": result.get("pushed_at"),
                "default_branch": result.get("default_branch"),
                "open_issues_count": result.get("open_issues_count"),
                "topics": result.get("topics", []),
                "license": result.get("license", {}).get("name"),
                "owner": {
                    "login": result.get("owner", {}).get("login"),
                    "avatar_url": result.get("owner", {}).get("avatar_url"),
                    "html_url": result.get("owner", {}).get("html_url")
                }
            }
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"リポジトリ {owner}/{repo} の情報を取得しました",
                data=formatted_result
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"リポジトリ情報取得エラー: {str(e)}",
                data=None
            )


class ListRepoContentsParameters(BaseModel):
    """GitHubリポジトリのコンテンツ一覧取得パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")
    path: str = Field("", description="リポジトリ内のパス（空=ルート）")
    ref: Optional[str] = Field(None, description="ブランチ名、タグ名、コミットSHA（指定しない場合はデフォルトブランチ）")


@register_tool
class ListRepoContentsTool(Tool):
    """GitHubリポジトリのコンテンツ一覧を取得するツール"""
    name = "github_list_repo_contents"
    description = "GitHubリポジトリ内のファイルやディレクトリ一覧を取得します。"
    version = "1.0.0"
    parameters_model = ListRepoContentsParameters

    async def execute(
        self, 
        owner: str, 
        repo: str, 
        path: str = "", 
        ref: Optional[str] = None
    ) -> ToolResult:
        """リポジトリのコンテンツ一覧を取得"""
        try:
            client = GitHubClient()
            
            # コンテンツ一覧取得
            result = await client.get_repository_contents(owner, repo, path, ref)
            
            # 単一ファイルが返された場合はリストではないので注意
            if not isinstance(result, list):
                # 単一ファイルの場合
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    message=f"ファイル {path} の情報を取得しました",
                    data={
                        "type": "file",
                        "name": result.get("name"),
                        "path": result.get("path"),
                        "sha": result.get("sha"),
                        "size": result.get("size"),
                        "html_url": result.get("html_url"),
                        "download_url": result.get("download_url")
                    }
                )
            
            # ディレクトリの場合：結果整形
            formatted_results = []
            for item in result:
                item_type = item.get("type", "")
                formatted_item = {
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "type": item_type,
                    "sha": item.get("sha"),
                    "size": item.get("size") if item_type == "file" else 0,
                    "html_url": item.get("html_url")
                }
                
                # ファイルの場合はダウンロードURLも追加
                if item_type == "file":
                    formatted_item["download_url"] = item.get("download_url")
                
                formatted_results.append(formatted_item)
            
            # 種類別にソート（ディレクトリ → ファイル、それぞれ名前順）
            formatted_results.sort(key=lambda x: (0 if x["type"] == "dir" else 1, x["name"]))
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"リポジトリ {owner}/{repo} のパス {path or 'ルート'} に{len(formatted_results)}個のアイテムがあります",
                data={
                    "items": formatted_results,
                    "path": path,
                    "repo": f"{owner}/{repo}",
                    "ref": ref or "デフォルトブランチ"
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"リポジトリコンテンツ取得エラー: {str(e)}",
                data=None
            )
