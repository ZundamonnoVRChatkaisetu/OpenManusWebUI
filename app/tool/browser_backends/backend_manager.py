"""ブラウザバックエンド管理モジュール

ブラウザ自動化用の各種バックエンド（Selenium、Playwright、browser_use）を管理し、
環境や設定に応じて最適なバックエンドを提供します。
"""

import asyncio
import importlib
import logging
from typing import Any, Dict, Optional, Tuple, List

from .platform_detector import is_windows, is_ms_store_python, is_module_available

# ロガー設定
logger = logging.getLogger(__name__)

# 利用可能なバックエンドの定数
BACKEND_NONE = 'none'
BACKEND_SELENIUM = 'selenium'
BACKEND_PLAYWRIGHT = 'playwright'
BACKEND_BROWSER_USE = 'browser_use'

# グローバル状態管理
_available_backends = []
_preferred_backend = None
_current_backend_instances = {}


def _detect_available_backends() -> List[str]:
    """利用可能なブラウザバックエンドを検出します
    
    Returns:
        List[str]: 利用可能なバックエンドのリスト
    """
    global _available_backends
    
    # 既に検出済みならその結果を返す
    if _available_backends:
        return _available_backends
    
    backends = []
    
    # Windows環境では常にSeleniumのみを推奨
    if is_windows():
        logger.info("Windows環境ではSeleniumバックエンドのみがサポートされます")
        if is_module_available('selenium'):
            backends.append(BACKEND_SELENIUM)
        else:
            logger.warning("seleniumモジュールが見つかりません。pip install seleniumでインストールしてください")
    else:
        # 非Windows環境ではすべてのバックエンドを検出
        
        # browser_useのチェック
        if is_module_available('browser_use'):
            backends.append(BACKEND_BROWSER_USE)
            
        # Playwrightのチェック
        if is_module_available('playwright'):
            backends.append(BACKEND_PLAYWRIGHT)
            
        # Seleniumのチェック (すべての環境で利用可能なら追加)
        if is_module_available('selenium'):
            backends.append(BACKEND_SELENIUM)
    
    if not backends:
        logger.warning("利用可能なブラウザバックエンドが見つかりませんでした")
        backends = [BACKEND_NONE]
    
    _available_backends = backends
    logger.info(f"利用可能なバックエンド: {', '.join(backends)}")
    return backends


def _get_preferred_backend() -> str:
    """現在の環境に最適なバックエンドを返します
    
    Returns:
        str: 推奨バックエンド名か、利用可能なものがない場合は 'none'
    """
    global _preferred_backend
    
    # 既に設定済みならその値を返す
    if _preferred_backend is not None:
        return _preferred_backend
    
    # 利用可能なバックエンドを取得
    backends = _detect_available_backends()
    
    # 利用可能なものがない場合
    if BACKEND_NONE in backends:
        _preferred_backend = BACKEND_NONE
        return BACKEND_NONE
    
    # Windows環境ではSeleniumのみを使用
    if is_windows():
        if BACKEND_SELENIUM in backends:
            _preferred_backend = BACKEND_SELENIUM
            return BACKEND_SELENIUM
        else:
            logger.error("Windows環境でSeleniumが使用できません。pip install seleniumでインストールしてください")
            _preferred_backend = BACKEND_NONE
            return BACKEND_NONE
    
    # 非Windows環境では優先順位に従ってバックエンドを選択
    priority_order = [BACKEND_BROWSER_USE, BACKEND_PLAYWRIGHT, BACKEND_SELENIUM]
    
    for backend in priority_order:
        if backend in backends:
            _preferred_backend = backend
            logger.info(f"推奨バックエンド: {backend}")
            return backend
    
    # 例外処理（通常はここに来ない）
    _preferred_backend = BACKEND_NONE
    return BACKEND_NONE


async def get_browser_backend() -> Tuple[str, Any]:
    """現在の環境に最適なブラウザバックエンドを初期化して返します
    
    Returns:
        Tuple[str, Any]: (バックエンド名, バックエンドインスタンス)
        利用可能なバックエンドがない場合は('none', None)を返します
    """
    global _current_backend_instances
    
    # 推奨バックエンドを取得
    backend_name = _get_preferred_backend()
    
    # 利用可能なバックエンドがない場合
    if backend_name == BACKEND_NONE:
        if is_windows():
            logger.error("ブラウザツールに必要なPythonパッケージがインストールされていません")
            logger.error("次のコマンドを実行して必要なパッケージをインストールしてください:")
            logger.error("pip install selenium")
        return (BACKEND_NONE, None)
    
    # 既にインスタンスがあればそれを返す
    if backend_name in _current_backend_instances and _current_backend_instances[backend_name] is not None:
        logger.info(f"既存の{backend_name}バックエンドインスタンスを再利用します")
        return (backend_name, _current_backend_instances[backend_name])
    
    try:
        # バックエンドに応じた初期化処理
        if backend_name == BACKEND_SELENIUM:
            # モジュールが利用可能か再確認
            if not is_module_available('selenium'):
                logger.error("seleniumモジュールが見つかりません。pip install seleniumでインストールしてください")
                return (BACKEND_NONE, None)
                
            try:
                # Seleniumバックエンドの初期化
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                
                # Chromeオプション設定
                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                # chrome_options.add_argument("--headless")  # 必要に応じて有効化
                
                # WebDriverを初期化
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("Selenium WebDriverを正常に初期化しました")
                
                _current_backend_instances[backend_name] = driver
                return (backend_name, driver)
            except Exception as e:
                logger.error(f"Selenium WebDriverの初期化に失敗しました: {e}")
                return (BACKEND_NONE, None)
            
        elif backend_name == BACKEND_PLAYWRIGHT:
            # Playwrightバックエンドの初期化
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # クリーンアップ用にオブジェクトを保持
            instance = {
                'playwright': playwright,
                'browser': browser,
                'context': context,
                'page': page
            }
            
            logger.info("Playwrightを正常に初期化しました")
            _current_backend_instances[backend_name] = instance
            return (backend_name, instance)
            
        elif backend_name == BACKEND_BROWSER_USE:
            # browser_useバックエンドの初期化
            from browser_use import Browser, BrowserConfig
            
            browser = Browser(BrowserConfig(headless=False))
            context = await browser.new_context()
            page = await context.get_current_page()
            
            # クリーンアップ用にオブジェクトを保持
            instance = {
                'browser': browser,
                'context': context,
                'page': page
            }
            
            logger.info("browser_useを正常に初期化しました")
            _current_backend_instances[backend_name] = instance
            return (backend_name, instance)
        
        # 不明なバックエンド
        logger.error(f"不明なバックエンド: {backend_name}")
        return (BACKEND_NONE, None)
        
    except Exception as e:
        logger.error(f"{backend_name}バックエンドの初期化に失敗しました: {e}")
        
        # 現在のバックエンドが失敗した場合、別のバックエンドを試す
        backends = _detect_available_backends()
        if BACKEND_NONE in backends or len(backends) <= 1:
            # 他に使用可能なバックエンドがない
            return (BACKEND_NONE, None)
        
        # 現在のバックエンドを除外
        backends.remove(backend_name)
        
        # 次のバックエンドを試す
        next_backend = backends[0]
        logger.warning(f"{backend_name}が失敗したため、{next_backend}にフォールバックします")
        
        # グローバルの推奨バックエンドを更新
        global _preferred_backend
        _preferred_backend = next_backend
        
        # 再帰呼び出しで次のバックエンドを試す
        return await get_browser_backend()


async def cleanup_all_backends():
    """すべてのブラウザバックエンドをクリーンアップします"""
    global _current_backend_instances
    
    for backend_name, instance in _current_backend_instances.items():
        if instance is None:
            continue
            
        try:
            if backend_name == BACKEND_SELENIUM:
                # Seleniumのクリーンアップ
                instance.quit()
                logger.info("Selenium WebDriverを正常にクリーンアップしました")
                
            elif backend_name == BACKEND_PLAYWRIGHT:
                # Playwrightのクリーンアップ
                if 'context' in instance and instance['context']:
                    await instance['context'].close()
                if 'browser' in instance and instance['browser']:
                    await instance['browser'].close()
                if 'playwright' in instance and instance['playwright']:
                    await instance['playwright'].stop()
                logger.info("Playwrightを正常にクリーンアップしました")
                
            elif backend_name == BACKEND_BROWSER_USE:
                # browser_useのクリーンアップ
                if 'context' in instance and instance['context']:
                    await instance['context'].close()
                if 'browser' in instance and instance['browser']:
                    await instance['browser'].close()
                logger.info("browser_useを正常にクリーンアップしました")
            
        except Exception as e:
            logger.error(f"{backend_name}のクリーンアップ中にエラーが発生しました: {e}")
    
    # 全てのインスタンスをクリア
    _current_backend_instances.clear()
