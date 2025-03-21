"""プラットフォーム検出モジュール

現在の実行環境に関する情報を取得し、ブラウザ操作ツールの適切な動作を支援します。
主に以下の機能を提供します：
1. Windows環境の検出
2. Microsoft Store版Pythonの検出
3. 利用可能なモジュールの検出
"""

import importlib.util
import logging
import os
import platform
import sys

# ロガー設定
logger = logging.getLogger(__name__)

# 実行時に1度だけ環境検出を行う
_is_windows = None
_is_ms_store_python = None
_module_availability_cache = {}


def is_windows() -> bool:
    """現在の環境がWindowsかどうかを確認します
    
    Returns:
        bool: Windows環境の場合はTrue、それ以外はすべてFalse
    """
    global _is_windows
    
    # 既に検出済みならキャッシュを返す
    if _is_windows is not None:
        return _is_windows
    
    # Windows環境を検出
    _is_windows = platform.system() == "Windows"
    
    if _is_windows:
        logger.info("環境検出: Windowsプラットフォームが検出されました")
    
    return _is_windows


def is_ms_store_python() -> bool:
    """現在の環境がMicrosoft Store版Pythonかどうかを確認します
    
    Microsoft Store版Pythonは一部のネイティブ機能に制限があります。
    subprocessモジュールは使用せず、パスベースの安全な検出を行います。
    
    Returns:
        bool: Microsoft Store版Pythonの場合はTrue、それ以外はすべてFalse
    """
    global _is_ms_store_python
    
    # 既に検出済みならキャッシュを返す
    if _is_ms_store_python is not None:
        return _is_ms_store_python
    
    # 非Windows環境なら常にFalse
    if not is_windows():
        _is_ms_store_python = False
        return False
    
    # パスチェックによる安全な検出（subprocessを使用しない）
    python_path = sys.executable.lower()
    sys_prefix = sys.prefix.lower()
    
    # WindowsAppsチェック - Microsoft Store版Pythonの特徴
    if 'windowsapps' in python_path or 'windowsapps' in sys_prefix:
        _is_ms_store_python = True
        logger.warning("検出: Microsoft Store版Pythonが使用されています（パスにWindowsAppsが含まれる）")
        return True
    
    # 追加のMS Store特有のパス特性チェック
    ms_store_paths = [
        "localcache",
        "packagecache", 
        "microsoft.python", 
        "pythonsoftwarefoundation.python"
    ]
    
    for path_marker in ms_store_paths:
        if path_marker in python_path or path_marker in sys_prefix:
            _is_ms_store_python = True
            logger.warning(f"検出: Microsoft Store版Pythonが使用されています（{path_marker}検出）")
            return True
    
    # 書き込み制限のチェック（Microsoft Store版は特定のシステムディレクトリに書き込めない）
    try:
        parent_dir = os.path.dirname(sys.executable)
        test_file = os.path.join(parent_dir, '.ms_store_check')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        _is_ms_store_python = False
    except (PermissionError, OSError):
        _is_ms_store_python = True
        logger.warning("検出: Microsoft Store版Pythonが使用されています（書き込み制限を検出）")
        return True
    
    logger.info("Microsoft Store版Pythonではないと判定しました")
    return False


def is_module_available(module_name: str) -> bool:
    """指定されたモジュールが利用可能かチェックします
    
    Args:
        module_name: チェックするモジュール名
        
    Returns:
        bool: モジュールが利用可能な場合はTrue、そうでない場合はFalse
    """
    global _module_availability_cache
    
    # キャッシュされた結果があればそれを返す
    if module_name in _module_availability_cache:
        return _module_availability_cache[module_name]
    
    # Windows環境では、playwright/subprocessは強制的に無効化
    if is_windows() and module_name in ['playwright', 'subprocess']:
        logger.warning(f"Windows環境では{module_name}は強制的に無効化されます")
        _module_availability_cache[module_name] = False
        return False
    
    # モジュール存在チェック
    result = importlib.util.find_spec(module_name) is not None
    _module_availability_cache[module_name] = result
    
    if result:
        logger.info(f"モジュール検出: {module_name}が利用可能です")
    else:
        logger.warning(f"モジュール検出: {module_name}が利用できません")
    
    return result


# 初期化時のログ記録
logger.info(f"Pythonバージョン: {sys.version}")
logger.info(f"Python実行パス: {sys.executable}")
logger.info(f"プラットフォーム: {platform.system()} {platform.release()}")

# Windows環境での追加ログ
if is_windows():
    if is_ms_store_python():
        logger.warning("Microsoft Store版Pythonが検出されました。一部機能が制限されます。")
