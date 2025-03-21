from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import config
from app.utils.db import get_db, Database
from pathlib import Path
import os
import datetime

router = APIRouter()

class GeneratedFileInfo(BaseModel):
    """生成されたファイル情報モデル"""
    filename: str
    content_preview: str
    project: Optional[str] = None
    timestamp: Optional[str] = None


class GeneratedFilesResponse(BaseModel):
    """生成ファイル一覧レスポンスモデル"""
    files: List[GeneratedFileInfo]


@router.get("/generated_files", response_model=GeneratedFilesResponse)
async def get_generated_files(
    project_id: Optional[str] = Query(None, description="プロジェクトID（省略可）"),
    db: Database = Depends(get_db)
):
    """
    モデルが生成したファイル一覧を取得
    
    Args:
        project_id: 特定のプロジェクトのファイルのみを取得する場合のプロジェクトID
        db: データベース接続
    
    Returns:
        生成ファイル情報のリスト
    """
    try:
        files = []
        
        # プロジェクト指定に基づいてワークスペースパスを取得
        workspace_path = config.get_workspace_path(project_id)
        
        # ワークスペースが存在しない場合は空のリストを返す
        if not workspace_path.exists():
            return {"files": []}
        
        # ワークスペース内のファイルを走査
        for root, _, filenames in os.walk(workspace_path):
            for filename in filenames:
                try:
                    # ファイルの絶対パス
                    file_path = Path(root) / filename
                    
                    # ファイルの相対パス（ワークスペースのルートからの相対）
                    rel_path = file_path.relative_to(workspace_path)
                    
                    # ファイルの更新日時
                    mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    
                    # ファイルサイズが大きすぎる場合はスキップ（オプション）
                    if file_path.stat().st_size > 1024 * 1024:  # 1MB以上のファイルはスキップ
                        continue
                    
                    # ファイル内容のプレビュー
                    preview = ""
                    try:
                        # バイナリファイルの場合はスキップ
                        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf', '.zip', '.exe']:
                            preview = "[バイナリファイル]"
                        else:
                            # テキストファイルの場合は先頭200文字を取得
                            with open(file_path, 'r', encoding='utf-8') as f:
                                preview = f.read(200)
                                if len(preview) == 200:
                                    preview += "..."
                    except UnicodeDecodeError:
                        # テキストとして読めない場合はバイナリファイルとして扱う
                        preview = "[バイナリファイル]"
                    except Exception as e:
                        preview = f"[プレビュー取得エラー: {str(e)}]"
                    
                    # ファイル情報を追加
                    files.append(
                        GeneratedFileInfo(
                            filename=str(rel_path),
                            content_preview=preview,
                            project=project_id,
                            timestamp=mtime
                        )
                    )
                except Exception as e:
                    # 個別ファイルの処理エラーはスキップして次へ
                    print(f"ファイル処理エラー: {str(e)}")
                    continue
        
        return {"files": files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成ファイル一覧の取得中にエラーが発生しました: {str(e)}")
