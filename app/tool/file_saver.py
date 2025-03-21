import os
from typing import Dict, Union, Optional
from pathlib import Path
from pydantic import BaseModel

import aiofiles

from app.tool.base import BaseTool
from app.config import config


class SaveFileParams(BaseModel):
    """
    ファイル保存パラメータモデル
    """
    content: str
    file_path: str
    mode: Optional[str] = "w"
    project: Optional[str] = None


class FileSaver(BaseTool):
    name: str = "file_saver"
    description: str = """Save content to a file in the workspace.
Use this tool when you need to save text, code, or generated content to a file.
The file will be saved in the current workspace or project directory.
You can specify a project name to save the file in a specific project's workspace.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "(required) The content to save to the file.",
            },
            "file_path": {
                "type": "string",
                "description": "(required) The filename to save, including any subdirectories and extension.",
            },
            "mode": {
                "type": "string",
                "description": "(optional) The file opening mode. Default is 'w' for write. Use 'a' for append.",
                "enum": ["w", "a"],
                "default": "w",
            },
            "project": {
                "type": "string",
                "description": "(optional) The project name to save the file to. Defaults to current project.",
            },
        },
        "required": ["content", "file_path"],
    }

    async def execute(self, content: str, file_path: str, mode: str = "w", project: Optional[str] = None) -> str:
        """
        Save content to a file in the workspace.

        Args:
            content (str): The content to save to the file.
            file_path (str): The filename to save (not the full path).
            mode (str, optional): The file opening mode. Default is 'w' for write. Use 'a' for append.
            project (str, optional): The project name to save the file to. Defaults to current project.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # プロジェクト指定に基づいてワークスペースパスを取得
            workspace_path = config.get_workspace_path(project)
            
            # パスにディレクトリセパレータがある場合、ディレクトリ部分のみを抽出
            # file_pathからディレクトリ部分を抽出するため、Path()を使用
            path = Path(file_path)
            
            # 絶対パスを構築
            absolute_path = workspace_path / path
            
            # 親ディレクトリを取得し、必要に応じて作成
            directory = absolute_path.parent
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

            # ファイルに書き込み
            async with aiofiles.open(absolute_path, mode, encoding="utf-8") as file:
                await file.write(content)

            return f"Content successfully saved to {file_path} in workspace"
            
        except Exception as e:
            return f"Error saving file: {str(e)}"
            

class FileReader(BaseTool):
    name: str = "file_reader"
    description: str = """Read content from a file in the workspace.
Use this tool when you need to read text, code, or other content from a file in the workspace.
The file will be read from the current workspace or project directory.
You can specify a project name to read the file from a specific project's workspace.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "(required) The filename to read, including any subdirectories and extension.",
            },
            "project": {
                "type": "string",
                "description": "(optional) The project name to read the file from. Defaults to current project.",
            },
        },
        "required": ["file_path"],
    }

    async def execute(self, file_path: str, project: Optional[str] = None) -> str:
        """
        Read content from a file in the workspace.

        Args:
            file_path (str): The filename to read (not the full path).
            project (str, optional): The project name to read the file from. Defaults to current project.

        Returns:
            str: The content of the file or an error message.
        """
        try:
            # プロジェクト指定に基づいてワークスペースパスを取得
            workspace_path = config.get_workspace_path(project)
            
            # 絶対パスを構築
            absolute_path = workspace_path / file_path
            
            # ファイルが存在するか確認
            if not absolute_path.exists():
                return f"Error: File {file_path} does not exist in workspace"

            # ファイルから読み込み
            async with aiofiles.open(absolute_path, 'r', encoding="utf-8") as file:
                content = await file.read()

            return content
            
        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileList(BaseTool):
    name: str = "file_list"
    description: str = """List all files in the workspace or a specific directory within the workspace.
Use this tool to get a list of available files in the current workspace or project directory.
You can specify a project name to list files from a specific project's workspace.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "(optional) The subdirectory within the workspace to list files from. Default is root directory.",
            },
            "project": {
                "type": "string",
                "description": "(optional) The project name to list files from. Defaults to current project.",
            },
        },
    }

    async def execute(self, directory: str = "", project: Optional[str] = None) -> str:
        """
        List all files in the workspace or a specific directory within the workspace.

        Args:
            directory (str, optional): The subdirectory within the workspace to list files from.
            project (str, optional): The project name to list files from. Defaults to current project.

        Returns:
            str: A list of files in the requested directory or an error message.
        """
        try:
            # プロジェクト指定に基づいてワークスペースパスを取得
            workspace_path = config.get_workspace_path(project)
            
            # ディレクトリが指定された場合、そのディレクトリを含むパスを構築
            target_path = workspace_path
            if directory:
                target_path = workspace_path / directory
            
            # ディレクトリが存在するか確認
            if not target_path.exists() or not target_path.is_dir():
                return f"Error: Directory {directory} does not exist in workspace"

            # ファイル一覧を取得
            files = []
            for item in target_path.iterdir():
                # 相対パスを計算
                relative_path = item.relative_to(workspace_path)
                file_info = {
                    "name": item.name,
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                }
                files.append(file_info)
            
            # 結果をテキスト形式で整形
            if not files:
                return "No files found in the specified directory."
                
            result = "Files in workspace:\n"
            for file in files:
                file_type = "[DIR]" if file["type"] == "directory" else "[FILE]"
                result += f"{file_type} {file['path']} ({file['size']} bytes)\n"
                
            return result
            
        except Exception as e:
            return f"Error listing files: {str(e)}"
