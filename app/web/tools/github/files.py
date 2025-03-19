"""
ファイル操作関連のツール
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolResultStatus, register_tool
from .client import GitHubClient


class GetFileContentParameters(BaseModel):
    """GitHubファイル内容取得パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")
    path: str = Field(..., description="ファイルパス")
    ref: Optional[str] = Field(None, description="ブランチ名、タグ名、コミットSHA（指定しない場合はデフォルトブランチ）")


@register_tool
class GetFileContentTool(Tool):
    """GitHubリポジトリのファイル内容を取得するツール"""
    name = "github_get_file_content"
    description = "GitHubリポジトリ内のファイルの内容を取得します。"
    version = "1.0.0"
    parameters_model = GetFileContentParameters

    async def execute(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        ref: Optional[str] = None
    ) -> ToolResult:
        """ファイル内容を取得"""
        try:
            client = GitHubClient()
            
            # ファイル内容取得（デコード済み）
            content = await client.get_file_content(owner, repo, path, ref)
            
            # 拡張子でファイルタイプを判別
            file_ext = path.split(".")[-1].lower() if "." in path else ""
            file_type = "text"
            
            if file_ext in ["py", "js", "ts", "jsx", "tsx", "java", "c", "cpp", "cs", "go", "rb", "php", "swift"]:
                file_type = "code"
            elif file_ext in ["json", "yml", "yaml", "xml", "toml"]:
                file_type = "data"
            elif file_ext in ["md", "txt", "rst"]:
                file_type = "document"
            
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"ファイル {path} の内容を取得しました",
                data={
                    "content": content,
                    "path": path,
                    "repo": f"{owner}/{repo}",
                    "ref": ref or "デフォルトブランチ",
                    "type": file_type,
                    "extension": file_ext
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"ファイル内容取得エラー: {str(e)}",
                data=None
            )


class CreateFileParameters(BaseModel):
    """GitHubファイル作成パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")
    path: str = Field(..., description="作成するファイルのパス")
    content: str = Field(..., description="ファイルの内容")
    message: str = Field(..., description="コミットメッセージ")
    branch: Optional[str] = Field(None, description="ブランチ名（指定しない場合はデフォルトブランチ）")


@register_tool
class CreateFileTool(Tool):
    """GitHubリポジトリにファイルを作成するツール"""
    name = "github_create_file"
    description = "GitHubリポジトリに新しいファイルを作成します。"
    version = "1.0.0"
    parameters_model = CreateFileParameters

    async def execute(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str,
        message: str,
        branch: Optional[str] = None
    ) -> ToolResult:
        """ファイルを作成"""
        try:
            client = GitHubClient()
            
            # ファイル作成
            result = await client.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                branch=branch
            )
            
            # 結果整形
            if "content" in result:
                content_info = result["content"]
                
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    message=f"ファイル {path} を作成しました",
                    data={
                        "path": content_info.get("path"),
                        "sha": content_info.get("sha"),
                        "html_url": content_info.get("html_url"),
                        "commit": {
                            "sha": result.get("commit", {}).get("sha"),
                            "html_url": result.get("commit", {}).get("html_url")
                        }
                    }
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message="ファイル作成のレスポンスが不正です",
                    data=result
                )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"ファイル作成エラー: {str(e)}",
                data=None
            )


class UpdateFileParameters(BaseModel):
    """GitHubファイル更新パラメータ"""
    owner: str = Field(..., description="リポジトリのオーナー名")
    repo: str = Field(..., description="リポジトリ名")
    path: str = Field(..., description="更新するファイルのパス")
    content: str = Field(..., description="新しいファイル内容")
    message: str = Field(..., description="コミットメッセージ")
    sha: str = Field(..., description="更新するファイルの現在のSHA（get_file_contentで取得可能）")
    branch: Optional[str] = Field(None, description="ブランチ名（指定しない場合はデフォルトブランチ）")


@register_tool
class UpdateFileTool(Tool):
    """GitHubリポジトリのファイルを更新するツール"""
    name = "github_update_file"
    description = "GitHubリポジトリの既存ファイルを更新します。"
    version = "1.0.0"
    parameters_model = UpdateFileParameters

    async def execute(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str,
        message: str,
        sha: str,
        branch: Optional[str] = None
    ) -> ToolResult:
        """ファイルを更新"""
        try:
            client = GitHubClient()
            
            # ファイル更新
            result = await client.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                sha=sha,
                branch=branch
            )
            
            # 結果整形
            if "content" in result:
                content_info = result["content"]
                
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    message=f"ファイル {path} を更新しました",
                    data={
                        "path": content_info.get("path"),
                        "sha": content_info.get("sha"),
                        "html_url": content_info.get("html_url"),
                        "commit": {
                            "sha": result.get("commit", {}).get("sha"),
                            "html_url": result.get("commit", {}).get("html_url")
                        }
                    }
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message="ファイル更新のレスポンスが不正です",
                    data=result
                )
            
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"ファイル更新エラー: {str(e)}",
                data=None
            )
