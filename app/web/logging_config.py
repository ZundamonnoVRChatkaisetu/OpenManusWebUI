"""
ロギング設定モジュール - FastAPIとアプリケーション全体のロギング設定を管理
"""
import logging
import os
from typing import List, Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import FastAPI, Request, Response
import uvicorn

# 頻繁にアクセスされるエンドポイントのパスを保存するセット
SILENT_ENDPOINTS: Set[str] = set()

# デフォルトで無視するパスパターン
DEFAULT_IGNORED_PATHS = [
    "/api/files",  # ファイル取得エンドポイント
    "/api/projects/",  # プロジェクト情報取得エンドポイント
    "/api/sessions/",  # セッション情報取得エンドポイント
    "/static/",  # 静的ファイル
    "/favicon.ico",  # ファビコン
]


class LogFilterMiddleware(BaseHTTPMiddleware):
    """
    特定のエンドポイントへのリクエストログをフィルタリングするミドルウェア
    """
    def __init__(
        self, 
        app: ASGIApp, 
        ignored_paths: Optional[List[str]] = None,
        min_duration_ms: int = 500  # 500ミリ秒以上かかったリクエストのみログ出力
    ):
        super().__init__(app)
        self.ignored_paths = ignored_paths or DEFAULT_IGNORED_PATHS
        self.min_duration_ms = min_duration_ms
        
        # UvicornのアクセスロガーのログレベルをWARNINGに設定
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_access_logger.setLevel(logging.WARNING)
        
        # SILENT_ENDPOINTSは明示的に無視するエンドポイントの完全なパスを格納
        global SILENT_ENDPOINTS
        for path in self.ignored_paths:
            # 無視するパスを追加
            SILENT_ENDPOINTS.add(path)

    async def dispatch(self, request: Request, call_next):
        # リクエストパスを取得
        path = request.url.path
        query = request.url.query
        
        # パスが無視リストに含まれるかチェック
        is_ignored = any(path.startswith(ignored) for ignored in self.ignored_paths)
        
        # 処理と応答時間の計測
        import time
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ミリ秒単位
        
        # 条件に基づいてロギング
        if not is_ignored and process_time >= self.min_duration_ms:
            # 遅いリクエストのみログ出力
            logging.getLogger("uvicorn.access").info(
                f"{request.client.host}:{request.client.port} - "
                f"\"{request.method} {path}{('?' + query) if query else ''} HTTP/{request.scope['http_version']}\" "
                f"{response.status_code} - {process_time:.2f}ms"
            )
        
        return response


def setup_logging(level: int = logging.INFO):
    """
    アプリケーション全体のロギング設定を構成する
    
    Args:
        level: ログレベル（デフォルトはINFO）
    """
    # ルートロガーの設定
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 不要なモジュールのログレベル抑制
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def configure_app_logging(app: FastAPI, min_duration_ms: int = 500):
    """
    FastAPIアプリケーションにログフィルタリングミドルウェアを追加
    
    Args:
        app: FastAPIアプリインスタンス
        min_duration_ms: ログに記録する最小リクエスト処理時間（ミリ秒）
    """
    # ログフィルタリングミドルウェアを追加
    app.add_middleware(
        LogFilterMiddleware,
        min_duration_ms=min_duration_ms
    )
    
    # Uvicornのロガー設定
    uvicorn_loggers = [
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("uvicorn.error"),
    ]
    
    for logger in uvicorn_loggers:
        # uvicornのハンドラを確認
        if not logger.handlers:
            # ハンドラが未設定の場合は基本設定
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                '%Y-%m-%d %H:%M:%S'
            ))
            logger.addHandler(handler)
