"""
イシュー操作関連のツール
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolResultStatus, register_tool
from .client import GitHubClient


class SearchIssuesParameters(BaseModel):
    """GitHubイシュー検索パラメータ"""
    query: str = Field(..., description="検索クエリ（例: 'repo:owner/repo state:open label:bug'）")
    sort: Optional[str] = Field(None, description="ソート基準（created, updated, comments）")
    order: Optional[str] = Field(None, description="ソート順（asc, desc）")
    page: int = Field(1, description="ページ番号")
    per_page: int = Field(10, description="1ページあたりの結果数（最大100）")


@register_tool
class SearchIssuesTool(Tool):
    """GitHubイシューとPRを検索するツール"""
    name = "github_search_issues"
    description = "GitHubイシューとプルリクエストを検索します。様々な条件で絞り込みが可能です。"
    version = "1.0.0"
    parameters_model = SearchIssuesParameters

    async def execute(
        self, 
        query: str, 
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> ToolResult:
        """イシューとPRを検索"""
        try:
            client = GitHubClient()
            
            # 検索実行
            result = await client.search_issues(
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
            
            # 各イシュー/PRの情報を整形
            for item in result.get("items", []):
                is_pr = "pull_request" in item
                
                formatted_item = {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "html_url": item.get("html_url"),
                    "state": item.get("state"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "closed_at": item.get("closed_at"),
                    "comments": item.get("comments"),
                    "body": item.get("body"),
                    "is_pull_request": is_pr,
                    "labels": [label.get("name") for label in item.get("labels", [])],
                    "user": {
                        "login": item.get("user", {}).get("login"),
                        "avatar_url": item.get("user", {}).get("avatar_url"),
                        "html_url": item.get("user", {}).get("html_url")
                    },
                    "repository": {
                        "full_name": item.get("repository_url", "").split("/repos/")[-1] if "repository_url" in item else ""
                    }
                }
                
                formatted_result["items"].append(formatted_item)
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{formatted_result['total_count']}件のイシュー/PRが見つかりました",
                data=formatted_result
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"イシュー検索エラー: {str(e)}",
                data=None
            )


class CreateIssueParameters(BaseModel):
    """GitHubイシュー作成パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")
    title: str = Field(..., description="イシューのタイトル")
    body: str = Field(..., description="イシューの本文")
    labels: Optional[List[str]] = Field(None, description="付けるラベルのリスト")


@register_tool
class CreateIssueTool(Tool):
    """GitHubリポジトリにイシューを作成するツール"""
    name = "github_create_issue"
    description = "GitHubリポジトリに新しいイシューを作成します。"
    version = "1.0.0"
    parameters_model = CreateIssueParameters

    async def execute(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        body: str,
        labels: Optional[List[str]] = None
    ) -> ToolResult:
        """イシューを作成"""
        try:
            client = GitHubClient()
            
            # イシュー作成
            result = await client.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                labels=labels
            )
            
            # 結果整形
            formatted_result = {
                "number": result.get("number"),
                "title": result.get("title"),
                "html_url": result.get("html_url"),
                "state": result.get("state"),
                "created_at": result.get("created_at"),
                "body": result.get("body"),
                "labels": [label.get("name") for label in result.get("labels", [])],
                "user": {
                    "login": result.get("user", {}).get("login"),
                    "avatar_url": result.get("user", {}).get("avatar_url"),
                    "html_url": result.get("user", {}).get("html_url")
                }
            }
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"イシュー #{result.get('number')} を作成しました",
                data=formatted_result
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"イシュー作成エラー: {str(e)}",
                data=None
            )
