# ブラウザバックエンド選択モジュール
# 各種ブラウザバックエンドを管理し、環境に応じて適切なバックエンドを提供します

from .platform_detector import is_windows, is_ms_store_python
from .backend_manager import get_browser_backend, cleanup_all_backends

__all__ = [
    'is_windows',
    'is_ms_store_python',
    'get_browser_backend',
    'cleanup_all_backends'
]
