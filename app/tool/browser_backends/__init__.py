"""ブラウザバックエンド選択モジュール

このモジュールは、Windowsを含む様々な環境でブラウザ操作を行うための
バックエンド選択と初期化機能を提供します。

このモジュールが読み込まれると、Windows環境では自動的にasyncioの一部関数が
無効化され、安全なバックエンド（Selenium）のみが提供されます。
"""

# Windows環境ではasyncioの一部機能を先に無効化
# ここで先にインポートすることで、他のモジュールがインポートされる前に適用される
from .asyncio_patch import apply_asyncio_patches, restore_asyncio_patches

# プラットフォーム検出機能
from .platform_detector import is_windows, is_ms_store_python, is_module_available

# バックエンド管理機能
from .backend_manager import get_browser_backend, cleanup_all_backends
from .backend_manager import BACKEND_NONE, BACKEND_SELENIUM, BACKEND_PLAYWRIGHT, BACKEND_BROWSER_USE

__all__ = [
    # プラットフォーム検出
    'is_windows',
    'is_ms_store_python',
    'is_module_available',
    
    # asyncioパッチ
    'apply_asyncio_patches',
    'restore_asyncio_patches',
    
    # バックエンド管理
    'get_browser_backend',
    'cleanup_all_backends',
    
    # バックエンド定数
    'BACKEND_NONE',
    'BACKEND_SELENIUM',
    'BACKEND_PLAYWRIGHT',
    'BACKEND_BROWSER_USE'
]
