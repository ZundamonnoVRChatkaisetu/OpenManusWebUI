"""非WindowsOS同期をWindows環境で安全に無効化するモジュール

Windows環境ではasyncio.create_subprocess_execが早期に無効化されるようにし、
これを呼び出す可能性のあるライブラリがエラーを遷移かつ該当機能を安全に無効化することを目的としています。

このモジュールは、Windows環境でPlaywrightなどが安全に無効化されるためのモンキーパッチを提供します。
"""

import asyncio
import logging
import sys
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from .platform_detector import is_windows

# ロガー設定
logger = logging.getLogger(__name__)

# 元の関数を保存するための変数
_original_create_subprocess_exec = None


async def disabled_create_subprocess_exec(*args, **kwargs) -> Any:
    """無効化されたcreate_subprocess_execの代替実装
    
    Windows環境では満足していない機能のため、NotImplementedErrorを出力します。
    
    Args:
        *args: 元の関数に渡されるための引数
        **kwargs: 元の関数に渡されるためのキーワード引数
        
    Raises:
        NotImplementedError: Windows環境では常に投げられます
    """
    logger.warning("Windows環境でcreate_subprocess_execが呼び出されました。無効化されています。")
    raise NotImplementedError("Windows環境ではこの機能は無効化されています")


def apply_asyncio_patches() -> None:
    """必要なasynicioパッチを適用します
    
    Windows環境では、asyncio.create_subprocess_execを無効化するpatched関数に置き換えます。
    これにより、Playwrightなどのライブラリが初期化時に安全に失敗し、代替手段にフォールバックするようにします。
    """
    global _original_create_subprocess_exec
    
    # Windows環境でない場合は何もしない
    if not is_windows():
        logger.debug("非Windows環境のため、asyncioパッチは適用されません")
        return
    
    # すでにパッチ適用済みなら何もしない
    if _original_create_subprocess_exec is not None:
        logger.debug("asyncioパッチはすでに適用されています")
        return
    
    try:
        # 元の関数をバックアップ
        if hasattr(asyncio, 'create_subprocess_exec'):
            _original_create_subprocess_exec = asyncio.create_subprocess_exec
            
            # モンキーパッチ適用
            asyncio.create_subprocess_exec = disabled_create_subprocess_exec
            logger.info("Windows環境用にcreat_subprocess_execが安全に無効化されました")
        else:
            logger.warning("asyncio.create_subprocess_execが存在しないため、パッチは適用されませんでした")
    except Exception as e:
        logger.error(f"asyncioパッチの適用中にエラーが発生しました: {e}")


def restore_asyncio_patches() -> None:
    """適用されたasynicioパッチを元に戻します
    
    クリーンアップ目的で使用します。主にテスト目的で使用されます。
    """
    global _original_create_subprocess_exec
    
    # 元の関数が保存されている場合は戻す
    if _original_create_subprocess_exec is not None:
        try:
            asyncio.create_subprocess_exec = _original_create_subprocess_exec
            _original_create_subprocess_exec = None
            logger.info("asyncio関数のパッチが元に戻されました")
        except Exception as e:
            logger.error(f"asyncioパッチの復元中にエラーが発生しました: {e}")


# モジュールロード時にWindows環境では自動的にパッチを適用
# これにより、モジュールインポート時に早期に無効化が行われる
# 他のモジュールがインポートされる前に適用されることが重要

apply_asyncio_patches()
