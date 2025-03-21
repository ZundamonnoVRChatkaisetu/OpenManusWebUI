"""
TaskProgressTracker - タスクの進捗管理と追跡を行うツール

このツールは以下の機能を提供します：
- 進捗管理ファイルの作成と更新
- タスクの追加、更新、完了のマーキング
- プロジェクトとディレクトリ構造の記録
- 作成したファイルとその役割の追跡
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import aiofiles

from app.tool.base import BaseTool
from app.config import config


class TaskProgressParams:
    """タスク進捗パラメータの定義クラス"""
    
    CREATE = "create"  # 初期ファイル作成
    READ = "read"      # 現在の進捗読み取り
    ADD_TASK = "add_task"  # 新しいタスク追加
    COMPLETE_TASK = "complete_task"  # タスク完了マーク
    UPDATE_TASK = "update_task"  # タスク更新
    ADD_FILE = "add_file"  # 作成/更新したファイル追加


class TaskProgressTracker(BaseTool):
    name: str = "task_progress_tracker"
    description: str = """Track and manage task progress by creating and updating a progress file.
    
This tool helps you track the progress of implementation tasks by:
1. Creating a progress management file
2. Adding new tasks and marking tasks as completed
3. Recording created files and their roles
4. Documenting directory structure

Use this whenever you need to keep track of your progress on complex implementations.
The progress file will be used in future steps to maintain context and understand what has been done.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The action to perform (create, read, add_task, complete_task, update_task, add_file)",
                "enum": [
                    TaskProgressParams.CREATE,
                    TaskProgressParams.READ,
                    TaskProgressParams.ADD_TASK,
                    TaskProgressParams.COMPLETE_TASK,
                    TaskProgressParams.UPDATE_TASK,
                    TaskProgressParams.ADD_FILE,
                ],
            },
            "project": {
                "type": "string",
                "description": "(optional) The project name for the progress file. Defaults to current project.",
            },
            "file_path": {
                "type": "string",
                "description": "(optional) Custom filename for the progress file. Default is 'task_progress.md'.",
            },
            "task_id": {
                "type": "string",
                "description": "The ID or name of the task (required for add_task, complete_task, update_task).",
            },
            "task_description": {
                "type": "string",
                "description": "Description of the task (required for add_task, update_task).",
            },
            "file_created": {
                "type": "string",
                "description": "Path to the file that was created (for add_file action).",
            },
            "file_role": {
                "type": "string",
                "description": "Description of the file's role/purpose (for add_file action).",
            },
            "directory_structure": {
                "type": "string",
                "description": "Description of the directory structure (for documentation).",
            },
            "status_note": {
                "type": "string",
                "description": "Additional notes about task status or progress.",
            }
        },
        "required": ["action"],
    }

    async def execute(
        self,
        action: str,
        project: Optional[str] = None,
        file_path: Optional[str] = "task_progress.md",
        task_id: Optional[str] = None,
        task_description: Optional[str] = None,
        file_created: Optional[str] = None,
        file_role: Optional[str] = None,
        directory_structure: Optional[str] = None,
        status_note: Optional[str] = None,
    ) -> str:
        """
        タスク進捗の追跡と管理を行う

        Args:
            action: 実行するアクション (create, read, add_task, complete_task, update_task, add_file)
            project: プロジェクト名 (オプション)
            file_path: 進捗ファイルのパス (デフォルト: task_progress.md)
            task_id: タスクID (add_task, complete_task, update_taskで必須)
            task_description: タスクの説明 (add_task, update_taskで必須)
            file_created: 作成したファイルパス (add_fileで使用)
            file_role: ファイルの役割 (add_fileで使用)
            directory_structure: ディレクトリ構造の説明
            status_note: 追加のステータスメモ

        Returns:
            str: 操作結果のメッセージ
        """
        try:
            # プロジェクト指定に基づいてワークスペースパスを取得
            workspace_path = config.get_workspace_path(project)
            
            # 進捗ファイルの完全パスを構築
            progress_file_path = workspace_path / file_path
            
            # アクションに基づいて処理を実行
            if action == TaskProgressParams.CREATE:
                return await self._create_progress_file(progress_file_path, project)
            elif action == TaskProgressParams.READ:
                return await self._read_progress_file(progress_file_path)
            elif action == TaskProgressParams.ADD_TASK:
                if not task_id or not task_description:
                    return "Error: task_id and task_description are required for add_task action"
                return await self._add_task(progress_file_path, task_id, task_description, status_note)
            elif action == TaskProgressParams.COMPLETE_TASK:
                if not task_id:
                    return "Error: task_id is required for complete_task action"
                return await self._complete_task(progress_file_path, task_id, status_note)
            elif action == TaskProgressParams.UPDATE_TASK:
                if not task_id:
                    return "Error: task_id is required for update_task action"
                return await self._update_task(progress_file_path, task_id, task_description, status_note)
            elif action == TaskProgressParams.ADD_FILE:
                if not file_created or not file_role:
                    return "Error: file_created and file_role are required for add_file action"
                return await self._add_file(progress_file_path, file_created, file_role, task_id)
            else:
                return f"Error: Unknown action '{action}'"
                
        except Exception as e:
            return f"Error in task progress tracker: {str(e)}"
    
    async def _create_progress_file(self, file_path: Path, project: Optional[str] = None) -> str:
        """新しい進捗ファイルを作成する"""
        # 親ディレクトリが存在することを確認
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 現在の日時を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 進捗ファイルの初期内容を作成
        content = f"""# タスク進捗管理ファイル

## プロジェクト情報
- プロジェクト: {project or "デフォルト"}
- 作成日時: {now}
- 最終更新: {now}

## 進捗概要
- 完了タスク: 0
- 未完了タスク: 0
- 総タスク数: 0

## タスク一覧

| ID | 説明 | ステータス | 最終更新 |
|---|---|---|---|

## 作成/更新されたファイル

| ファイルパス | 役割 | 関連タスク | 作成日時 |
|---|---|---|---|

## ディレクトリ構成とファイルの役割

まだ記録されていません。

"""
        
        # ファイルに書き込み
        async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
            await file.write(content)
        
        return f"進捗管理ファイルを作成しました: {file_path.name}"
    
    async def _read_progress_file(self, file_path: Path) -> str:
        """進捗ファイルの内容を読み取る"""
        if not file_path.exists():
            return f"Error: Progress file {file_path.name} does not exist. Use 'create' action to create it first."
        
        # ファイルを読み込む
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        
        return content
    
    async def _add_task(
        self, 
        file_path: Path, 
        task_id: str, 
        task_description: str, 
        status_note: Optional[str] = None
    ) -> str:
        """新しいタスクを追加する"""
        if not file_path.exists():
            return f"Error: Progress file {file_path.name} does not exist. Use 'create' action to create it first."
        
        # 現在の日時を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ファイルを読み込む
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        
        # タスク一覧テーブルを検索
        tasks_section_start = content.find("## タスク一覧")
        if tasks_section_start == -1:
            return "Error: Tasks section not found in progress file"
        
        next_section_start = content.find("##", tasks_section_start + 1)
        if next_section_start == -1:
            next_section_start = len(content)
        
        tasks_section = content[tasks_section_start:next_section_start]
        
        # 既存のタスクを確認（重複防止）
        if f"| {task_id} |" in tasks_section:
            return f"Error: Task with ID '{task_id}' already exists"
        
        # 新しいタスク行を作成
        new_task_row = f"| {task_id} | {task_description} | 未完了 | {now} |"
        
        # テーブルの行を追加
        table_end = tasks_section.rfind("|")
        if table_end == -1:
            # テーブルがない場合は新しく作成
            new_tasks_section = f"## タスク一覧\n\n| ID | 説明 | ステータス | 最終更新 |\n|---|---|---|---|\n{new_task_row}\n"
            content = content.replace("## タスク一覧", new_tasks_section)
        else:
            # 既存のテーブルに行を追加
            content = content[:table_end + 1] + "\n" + new_task_row + content[table_end + 1:]
        
        # 進捗概要を更新
        content = self._update_progress_summary(content)
        
        # 最終更新日時を更新
        content = self._update_last_modified(content, now)
        
        # ファイルに書き込み
        async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
            await file.write(content)
        
        return f"タスク '{task_id}' を追加しました"
    
    async def _complete_task(
        self, 
        file_path: Path, 
        task_id: str, 
        status_note: Optional[str] = None
    ) -> str:
        """タスクを完了としてマークする"""
        if not file_path.exists():
            return f"Error: Progress file {file_path.name} does not exist. Use 'create' action to create it first."
        
        # 現在の日時を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ファイルを読み込む
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        
        # タスク一覧を検索
        tasks_section_start = content.find("## タスク一覧")
        if tasks_section_start == -1:
            return "Error: Tasks section not found in progress file"
        
        # タスクを検索
        lines = content.split("\n")
        task_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"| {task_id} |"):
                # タスクが未完了の場合のみ更新
                if "未完了" in line:
                    # ステータスを「完了 ✅」に変更し、最終更新日時を更新
                    parts = line.split("|")
                    if len(parts) >= 5:
                        parts[3] = f" 完了 ✅ "
                        parts[4] = f" {now} "
                        lines[i] = "|".join(parts)
                        task_found = True
                else:
                    return f"タスク '{task_id}' は既に完了しています"
                break
        
        if not task_found:
            return f"Error: Task with ID '{task_id}' not found"
        
        # 更新された内容
        updated_content = "\n".join(lines)
        
        # 進捗概要を更新
        updated_content = self._update_progress_summary(updated_content)
        
        # 最終更新日時を更新
        updated_content = self._update_last_modified(updated_content, now)
        
        # ファイルに書き込み
        async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
            await file.write(updated_content)
        
        return f"タスク '{task_id}' を完了としてマークしました"
    
    async def _update_task(
        self, 
        file_path: Path, 
        task_id: str, 
        task_description: Optional[str] = None, 
        status_note: Optional[str] = None
    ) -> str:
        """タスクの情報を更新する"""
        if not file_path.exists():
            return f"Error: Progress file {file_path.name} does not exist. Use 'create' action to create it first."
        
        # 現在の日時を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ファイルを読み込む
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        
        # タスク一覧を検索
        tasks_section_start = content.find("## タスク一覧")
        if tasks_section_start == -1:
            return "Error: Tasks section not found in progress file"
        
        # タスクを検索
        lines = content.split("\n")
        task_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"| {task_id} |"):
                # タスクを更新
                parts = line.split("|")
                if len(parts) >= 5:
                    if task_description:
                        parts[2] = f" {task_description} "
                    parts[4] = f" {now} "
                    lines[i] = "|".join(parts)
                    task_found = True
                break
        
        if not task_found:
            return f"Error: Task with ID '{task_id}' not found"
        
        # 更新された内容
        updated_content = "\n".join(lines)
        
        # 最終更新日時を更新
        updated_content = self._update_last_modified(updated_content, now)
        
        # ファイルに書き込み
        async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
            await file.write(updated_content)
        
        return f"タスク '{task_id}' を更新しました"
    
    async def _add_file(
        self, 
        file_path: Path, 
        file_created: str, 
        file_role: str, 
        related_task: Optional[str] = None
    ) -> str:
        """作成/更新されたファイルを記録する"""
        if not file_path.exists():
            return f"Error: Progress file {file_path.name} does not exist. Use 'create' action to create it first."
        
        # 現在の日時を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ファイルを読み込む
        async with aiofiles.open(file_path, 'r', encoding="utf-8") as file:
            content = await file.read()
        
        # ファイル一覧セクションを検索
        files_section_start = content.find("## 作成/更新されたファイル")
        if files_section_start == -1:
            return "Error: Files section not found in progress file"
        
        next_section_start = content.find("##", files_section_start + 1)
        if next_section_start == -1:
            next_section_start = len(content)
        
        files_section = content[files_section_start:next_section_start]
        
        # 新しいファイル行を作成
        new_file_row = f"| {file_created} | {file_role} | {related_task or '未指定'} | {now} |"
        
        # テーブルの行を追加
        table_end = files_section.rfind("|")
        if table_end == -1:
            # テーブルがない場合は新しく作成
            new_files_section = f"## 作成/更新されたファイル\n\n| ファイルパス | 役割 | 関連タスク | 作成日時 |\n|---|---|---|---|\n{new_file_row}\n"
            content = content.replace("## 作成/更新されたファイル", new_files_section)
        else:
            # 既存のテーブルに行を追加
            end_of_table = content.find("\n\n", files_section_start)
            if end_of_table == -1 or end_of_table > next_section_start:
                end_of_table = next_section_start
            
            # テーブルの最後に新しい行を追加
            content = (
                content[:table_end + 1] + 
                "\n" + new_file_row + 
                content[table_end + 1:]
            )
        
        # 最終更新日時を更新
        content = self._update_last_modified(content, now)
        
        # ファイルに書き込み
        async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
            await file.write(content)
        
        return f"ファイル '{file_created}' を進捗ファイルに追加しました"
    
    def _update_progress_summary(self, content: str) -> str:
        """進捗概要セクションを更新する"""
        # タスク一覧を解析して完了/未完了タスク数をカウント
        lines = content.split("\n")
        completed_tasks = 0
        incomplete_tasks = 0
        
        for line in lines:
            if "| " in line and " |" in line:  # テーブル行の判定
                if "完了" in line:
                    completed_tasks += 1
                elif "未完了" in line:
                    incomplete_tasks += 1
        
        # ヘッダー行は除外するための調整（タスク一覧テーブルにヘッダー行が含まれる場合）
        if completed_tasks > 0 or incomplete_tasks > 0:
            # ヘッダー行を確認
            header_detected = False
            for line in lines:
                if line.strip() == "| ID | 説明 | ステータス | 最終更新 |":
                    header_detected = True
                    break
            
            if header_detected and completed_tasks + incomplete_tasks > 0:
                # ヘッダー行があるため、合計からヘッダー行を除外
                total_tasks = completed_tasks + incomplete_tasks
            else:
                total_tasks = completed_tasks + incomplete_tasks
        else:
            total_tasks = 0
        
        # 進捗概要を更新
        progress_section_start = content.find("## 進捗概要")
        if progress_section_start == -1:
            return content
        
        next_section_start = content.find("##", progress_section_start + 1)
        if next_section_start == -1:
            return content
        
        # 新しい進捗概要セクション
        new_progress_section = f"""## 進捗概要
- 完了タスク: {completed_tasks}
- 未完了タスク: {incomplete_tasks}
- 総タスク数: {total_tasks}

"""
        
        # 進捗概要セクションを置き換え
        return content[:progress_section_start] + new_progress_section + content[next_section_start:]
    
    def _update_last_modified(self, content: str, timestamp: str) -> str:
        """最終更新日時を更新する"""
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if line.startswith("- 最終更新:"):
                lines[i] = f"- 最終更新: {timestamp}"
                break
        
        return "\n".join(lines)
