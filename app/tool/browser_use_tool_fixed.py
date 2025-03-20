"""
ブラウザツールのクロスプラットフォーム対応版
Windows環境では常にSeleniumを使用するように修正
"""
import asyncio
import json
import logging
import platform
import sys
import os
import importlib.util
from typing import Optional, Dict, Any

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.tool.base import BaseTool, ToolResult

# ロガー設定
logger = logging.getLogger(__name__)

# Windows環境をチェック（最優先）
_is_windows = platform.system() == "Windows"

# グローバル変数定義（早期に定義してモジュールスコープで利用可能にする）
_browser_use_available = False
_browser_module = None
_BrowserUseBrowser = None
_BrowserConfig = None
_playwright_available = False
_is_ms_store_python = False
_use_selenium = False

# Windows環境特有の処理
if _is_windows:
    logger.warning("Windows環境が検出されました。Seleniumをブラウザバックエンドとして使用します。")
    
    # Playwrightの使用を完全に無効化するための処理
    try:
        # モジュールを無効化して、インポートできないようにする
        sys.modules['playwright'] = None
        sys.modules['playwright.async_api'] = None
        
        # 既にインポートされている場合に備えて除去
        if 'playwright' in sys.modules:
            del sys.modules['playwright']
        if 'playwright.async_api' in sys.modules:
            del sys.modules['playwright.async_api']
        
        # Windowsでも動作する代替関数を定義
        original_create_subprocess_exec = None
        if hasattr(asyncio, 'create_subprocess_exec'):
            # オリジナルの関数をバックアップ
            original_create_subprocess_exec = asyncio.create_subprocess_exec
            
            # エラーを投げる代替関数
            async def disabled_create_subprocess_exec(*args, **kwargs):
                """Windows環境でのcreate_subprocess_execの代替実装"""
                logger.warning("Windows環境でcreate_subprocess_execが呼び出されました。無効化されています。")
                raise NotImplementedError("Windows環境ではこの機能は無効化されています")
            
            # モンキーパッチ適用
            asyncio.create_subprocess_exec = disabled_create_subprocess_exec
        
        logger.info("Playwrightと関連モジュールが無効化されました")
    except Exception as e:
        logger.error(f"Playwright無効化中にエラーが発生しました: {e}")
    
    # Windows環境ではSeleniumを強制的に使用
    _is_ms_store_python = True  # Microsoft Store Pythonとして扱う
    _browser_module = "selenium"  # 強制的にSeleniumを使用
    _use_selenium = True  # Selenium使用フラグをオン

# モジュール存在チェック関数
def is_module_available(module_name):
    """指定されたモジュールが使用可能かチェックする"""
    return importlib.util.find_spec(module_name) is not None

# Windows以外の環境ではブラウザバックエンドの自動検出を実行
if not _is_windows:
    # まずbrowser_useを試す
    if is_module_available("browser_use"):
        try:
            from browser_use import Browser as BrowserUseBrowser
            from browser_use import BrowserConfig
            _browser_use_available = True
            _browser_module = "browser_use"
            _BrowserUseBrowser = BrowserUseBrowser
            _BrowserConfig = BrowserConfig
            logger.info("browser_use モジュールを正常にロードしました")
        except (ImportError, NotImplementedError) as e:
            logger.warning(f"browser_use モジュールのロードに失敗しました: {str(e)}")
    
    # browser_useが利用できない場合はPlaywrightを試す
    if not _browser_use_available and is_module_available("playwright"):
        try:
            _playwright_available = True
            _browser_module = "playwright"
            logger.info("Playwright モジュールを代替としてロードしました")
        except (ImportError, NotImplementedError) as e:
            logger.warning(f"Playwrightモジュールのロードにも失敗しました: {str(e)}")
            _playwright_available = False

# 最終手段としてSeleniumを試行（Windows環境または他のバックエンドが使用できない場合）
if _is_windows or not _browser_use_available or not _playwright_available:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import WebDriverException
        
        # Seleniumの使用を有効化
        _browser_use_available = True
        _browser_module = "selenium"
        _use_selenium = True
        logger.info("Selenium WebDriverをブラウザバックエンドとして使用します")
    except ImportError as e:
        logger.error(f"すべてのブラウザ自動化ライブラリのロードに失敗しました: {str(e)}")
        _browser_use_available = False

# Windows環境では常にSeleniumを強制
if _is_windows and _browser_module != "selenium":
    logger.warning("Windows環境でSelenium以外のバックエンドが指定されています。強制的にSeleniumを使用します。")
    _browser_module = "selenium"
    _use_selenium = True

_BROWSER_DESCRIPTION = """
Interact with a web browser to perform various actions such as navigation, element interaction,
content extraction, and tab management. Supported actions include:
- 'navigate': Go to a specific URL
- 'click': Click an element by index
- 'input_text': Input text into an element
- 'screenshot': Capture a screenshot
- 'get_html': Get page HTML content
- 'get_text': Get text content of the page
- 'read_links': Get all links on the page
- 'execute_js': Execute JavaScript code
- 'scroll': Scroll the page
- 'switch_tab': Switch to a specific tab
- 'new_tab': Open a new tab
- 'close_tab': Close the current tab
- 'refresh': Refresh the current page
"""


class BrowserUseTool(BaseTool):
    name: str = "browser_use"
    description: str = _BROWSER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "navigate",
                    "click",
                    "input_text",
                    "screenshot",
                    "get_html",
                    "get_text",
                    "read_links",
                    "execute_js",
                    "scroll",
                    "switch_tab",
                    "new_tab",
                    "close_tab",
                    "refresh",
                ],
                "description": "The browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL for 'navigate' or 'new_tab' actions",
            },
            "index": {
                "type": "integer",
                "description": "Element index for 'click' or 'input_text' actions",
            },
            "text": {"type": "string", "description": "Text for 'input_text' action"},
            "script": {
                "type": "string",
                "description": "JavaScript code for 'execute_js' action",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Pixels to scroll (positive for down, negative for up) for 'scroll' action",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID for 'switch_tab' action",
            },
        },
        "required": ["action"],
        "dependencies": {
            "navigate": ["url"],
            "click": ["index"],
            "input_text": ["index", "text"],
            "execute_js": ["script"],
            "switch_tab": ["tab_id"],
            "new_tab": ["url"],
            "scroll": ["scroll_amount"],
        },
    }

    lock: asyncio.Lock = Field(default_factory=asyncio.Lock)
    browser: Optional[Any] = Field(default=None, exclude=True)
    context: Optional[Any] = Field(default=None, exclude=True)
    page: Optional[Any] = Field(default=None, exclude=True)
    playwright: Optional[Any] = Field(default=None, exclude=True)
    selenium_driver: Optional[Any] = Field(default=None, exclude=True)

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v

    async def _ensure_browser_initialized(self) -> Any:
        """ブラウザーとコンテキストが初期化されていることを確認"""
        global _browser_module, _is_windows, _use_selenium
        
        # Windows環境では常にSeleniumを使用
        if _is_windows:
            _browser_module = "selenium"
            _use_selenium = True
            
        if not _browser_use_available:
            raise RuntimeError("ブラウザツールの初期化に失敗しました: 必要なモジュールがインストールされていません")

        try:
            if _browser_module == "browser_use" and not _is_windows:
                # browser_useモジュールが使える場合はそちらを使用
                if self.browser is None:
                    # プラグインのConfigが正しくインポートされているか確認
                    if _BrowserUseBrowser is None or _BrowserConfig is None:
                        logger.error("browser_useモジュールが正しくインポートされていません")
                        raise ImportError("browser_useモジュールが正しくインポートされていません")
                    
                    self.browser = _BrowserUseBrowser(_BrowserConfig(headless=False))
                if self.context is None:
                    self.context = await self.browser.new_context()
                    self.page = await self.context.get_current_page()
                return self.context
            
            elif _browser_module == "playwright" and not _is_windows:
                # Playwrightを直接使用（Windows以外の環境のみ）
                try:
                    if self.playwright is None:
                        # 必要なモジュールを遅延インポート（エラー処理のため）
                        try:
                            from playwright.async_api import async_playwright
                            self.playwright = await async_playwright().start()
                            self.browser = await self.playwright.chromium.launch(headless=False)
                            self.context = await self.browser.new_context()
                            self.page = await self.context.new_page()
                        except ImportError as e:
                            logger.error(f"Playwrightのインポートに失敗しました: {e}")
                            raise
                        except Exception as e:
                            logger.error(f"Playwrightの初期化に失敗しました: {e}")
                            raise
                    return self.page
                except Exception as e:
                    logger.error(f"Playwrightの初期化に失敗しました。Seleniumへフォールバックします: {e}")
                    _browser_module = "selenium"
                    _use_selenium = True
                    # ここで再帰的に呼び出す代わりに、次のブロックにフォールスルーする
            
            # Seleniumを使用（標準バックエンドまたはフォールバック）
            if _browser_module == "selenium" or _use_selenium:
                # Selenium WebDriverが初期化されていなければ初期化
                if self.selenium_driver is None:
                    # Seleniumが正しくインポートされているか確認
                    if 'webdriver' not in globals():
                        try:
                            from selenium import webdriver
                            from selenium.webdriver.chrome.service import Service as ChromeService
                            from selenium.webdriver.common.by import By
                            from selenium.webdriver.chrome.options import Options
                            from selenium.common.exceptions import WebDriverException
                        except ImportError as e:
                            logger.error(f"Seleniumモジュールのインポートに失敗しました: {e}")
                            raise RuntimeError(f"Seleniumモジュールのインポートに失敗: {e}")
                    
                    # Chromeオプションの設定
                    chrome_options = Options()
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--disable-gpu")
                    # ヘッドレスモードの設定（必要に応じてコメント解除）
                    # chrome_options.add_argument("--headless")
                    
                    try:
                        # WebDriverを初期化
                        self.selenium_driver = webdriver.Chrome(options=chrome_options)
                        logger.info("Selenium WebDriverを初期化しました")
                    except Exception as e:
                        # 詳細なエラーログ
                        logger.error(f"Selenium WebDriverの初期化に失敗しました: {str(e)}")
                        # 可能ならWebDriverのバージョン情報を取得
                        try:
                            logger.info(f"Selenium Version: {webdriver.__version__}")
                        except:
                            pass
                        
                        raise RuntimeError(f"Seleniumの初期化に失敗: {str(e)}")
                
                return self.selenium_driver
            
            # すべてのバックエンドが失敗した場合
            raise RuntimeError("有効なブラウザバックエンドが見つかりませんでした")
            
        except Exception as e:
            logger.error(f"ブラウザの初期化中にエラーが発生しました: {e}")
            raise

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        script: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """
        ブラウザアクションを実行
        """
        global _browser_module, _is_windows, _use_selenium
        
        # Windows環境では常にSeleniumを使う
        if _is_windows:
            _browser_module = "selenium"
            _use_selenium = True
        
        if not _browser_use_available:
            return ToolResult(error="ブラウザツールが利用できません: 必要なライブラリがインストールされていません")

        async with self.lock:
            try:
                # ブラウザ実行前のセーフティチェック（メソッド実行時のWindows検出）
                if platform.system() == "Windows":
                    logger.info("Windows環境でブラウザアクションを実行します。Seleniumを使用します。")
                    return await self._execute_with_selenium(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                
                # 通常の分岐処理
                if _browser_module == "browser_use" and not _is_windows:
                    # browser_useモジュールを使用する場合（Windows以外）
                    return await self._execute_with_browser_use(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                elif _browser_module == "playwright" and not _is_windows:
                    # Playwrightを直接使用する場合（Windows以外）
                    try:
                        return await self._execute_with_playwright(
                            action, url, index, text, script, scroll_amount, tab_id, **kwargs
                        )
                    except Exception as e:
                        logger.error(f"Playwrightの実行中にエラーが発生しました: {e}")
                        logger.warning(f"Seleniumへフォールバックします")
                        _browser_module = "selenium"
                        _use_selenium = True
                        return await self._execute_with_selenium(
                            action, url, index, text, script, scroll_amount, tab_id, **kwargs
                        )
                else:
                    # Seleniumを使用する場合（または強制的にWindowsの場合）
                    return await self._execute_with_selenium(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
            except Exception as e:
                logger.error(f"ブラウザアクション '{action}' の実行中にエラーが発生しました: {str(e)}")
                return ToolResult(error=f"ブラウザアクション '{action}' の実行に失敗: {str(e)}")

    async def _execute_with_browser_use(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """browser_useモジュールを使用したブラウザアクションの実行"""
        # Windows環境チェック（追加の安全策）
        if platform.system() == "Windows":
            logger.warning("Windows環境でbrowser_useが呼び出されました。Seleniumにリダイレクトします。")
            return await self._execute_with_selenium(action, url, index, text, script, scroll_amount, tab_id, **kwargs)
            
        try:
            context = await self._ensure_browser_initialized()

            if action == "navigate":
                if not url:
                    return ToolResult(error="URL is required for 'navigate' action")
                await context.navigate_to(url)
                return ToolResult(output=f"Navigated to {url}")

            elif action == "click":
                if index is None:
                    return ToolResult(error="Index is required for 'click' action")
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return ToolResult(error=f"Element with index {index} not found")
                download_path = await context._click_element_node(element)
                output = f"Clicked element at index {index}"
                if download_path:
                    output += f" - Downloaded file to {download_path}"
                return ToolResult(output=output)

            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="Index and text are required for 'input_text' action")
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return ToolResult(error=f"Element with index {index} not found")
                await context._input_text_element_node(element, text)
                return ToolResult(output=f"Input '{text}' into element at index {index}")

            elif action == "get_text":
                text = await context.execute_javascript("document.body.innerText")
                return ToolResult(output=text)
            
            elif action == "read_links":
                links = await context.execute_javascript('''
                const links = Array.from(document.querySelectorAll('a')).map(a => {
                    return {
                        text: a.textContent.trim(),
                        href: a.href,
                        index: [...document.querySelectorAll('*')].indexOf(a)
                    };
                });
                return JSON.stringify(links);
                ''')
                return ToolResult(output=links)
            
            elif action == "get_html":
                html = await context.get_page_html()
                truncated = html[:2000] + "..." if len(html) > 2000 else html
                return ToolResult(output=truncated)

            elif action == "execute_js":
                if not script:
                    return ToolResult(error="Script is required for 'execute_js' action")
                result = await context.execute_javascript(script)
                return ToolResult(output=str(result))

            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"browser_useでの処理中にエラーが発生しました: {e}")
            # Seleniumへのフォールバック
            logger.warning("Seleniumにフォールバックします")
            return await self._execute_with_selenium(action, url, index, text, script, scroll_amount, tab_id, **kwargs)

    async def _execute_with_playwright(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """Playwrightを直接使用したブラウザアクションの実行"""
        # Windows環境ではPlaywrightを無効化（追加の安全策）
        if platform.system() == "Windows":
            logger.warning("Windows環境でPlaywrightが呼び出されました。Seleniumにリダイレクトします。")
            return await self._execute_with_selenium(action, url, index, text, script, scroll_amount, tab_id, **kwargs)
            
        try:
            # Playwrightのページオブジェクトを取得
            page = await self._ensure_browser_initialized()

            if action == "navigate":
                if not url:
                    return ToolResult(error="URL is required for 'navigate' action")
                await page.goto(url)
                return ToolResult(output=f"Navigated to {url}")

            elif action == "click":
                if index is None:
                    return ToolResult(error="Index is required for 'click' action")
                # JavaScriptを使用して要素をクリック
                await page.evaluate(f"document.querySelectorAll('*')[{index}].click()")
                return ToolResult(output=f"Clicked element at index {index}")

            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="Index and text are required for 'input_text' action")
                # JavaScriptでインデックスでの要素アクセスと入力
                result = await page.evaluate(f"""
                    (function() {{
                        const el = document.querySelectorAll('*')[{index}];
                        if (!el) return false;
                        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                            el.value = '{text}';
                            return true;
                        }}
                        return false;
                    }})()
                """)
                if not result:
                    return ToolResult(error=f"Unable to input text to element at index {index}")
                return ToolResult(output=f"Input '{text}' into element at index {index}")

            elif action == "get_text":
                text = await page.evaluate("document.body.innerText")
                return ToolResult(output=text)

            elif action == "read_links":
                links = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a')).map(a => {
                        return {
                            text: a.textContent.trim(),
                            href: a.href,
                            index: [...document.querySelectorAll('*')].indexOf(a)
                        };
                    });
                    return JSON.stringify(links);
                }
                ''')
                return ToolResult(output=links)

            elif action == "get_html":
                html = await page.content()
                truncated = html[:2000] + "..." if len(html) > 2000 else html
                return ToolResult(output=truncated)

            elif action == "execute_js":
                if not script:
                    return ToolResult(error="Script is required for 'execute_js' action")
                result = await page.evaluate(script)
                return ToolResult(output=str(result))

            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"Playwrightでの処理中にエラーが発生しました: {e}")
            # Seleniumへのフォールバック
            logger.warning("Seleniumにフォールバックします")
            return await self._execute_with_selenium(action, url, index, text, script, scroll_amount, tab_id, **kwargs)

    async def _execute_with_selenium(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """Seleniumを使用したブラウザアクションの実行"""
        # 非同期関数内で同期的なSelenium操作を行うため、安全に実行する
        
        try:
            # Selenium WebDriverを初期化
            driver = await self._ensure_browser_initialized()
            
            # actionに応じた処理を実装
            if action == "navigate":
                if not url:
                    return ToolResult(error="URL is required for 'navigate' action")
                try:
                    driver.get(url)
                    return ToolResult(output=f"Navigated to {url}")
                except Exception as e:
                    return ToolResult(error=f"Navigation failed: {str(e)}")
                
            elif action == "get_text":
                try:
                    text = driver.find_element(By.TAG_NAME, "body").text
                    return ToolResult(output=text)
                except Exception as e:
                    return ToolResult(error=f"Failed to get text: {str(e)}")
                
            elif action == "get_html":
                try:
                    html = driver.page_source
                    truncated = html[:2000] + "..." if len(html) > 2000 else html
                    return ToolResult(output=truncated)
                except Exception as e:
                    return ToolResult(error=f"Failed to get HTML: {str(e)}")
                
            elif action == "read_links":
                try:
                    # JavaScriptで全リンクを取得
                    links = driver.execute_script('''
                    const links = Array.from(document.querySelectorAll('a')).map(a => {
                        return {
                            text: a.textContent.trim(),
                            href: a.href,
                            index: [...document.querySelectorAll('*')].indexOf(a)
                        };
                    });
                    return JSON.stringify(links);
                    ''')
                    return ToolResult(output=links)
                except Exception as e:
                    return ToolResult(error=f"Failed to read links: {str(e)}")
                
            elif action == "click":
                if index is None:
                    return ToolResult(error="Index is required for 'click' action")
                try:
                    # JavaScriptでインデックスによる要素アクセスとクリック
                    driver.execute_script(f"document.querySelectorAll('*')[{index}].click()")
                    return ToolResult(output=f"Clicked element at index {index}")
                except Exception as e:
                    return ToolResult(error=f"Click failed: {str(e)}")
                    
            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="Index and text are required for 'input_text' action")
                try:
                    # JavaScriptで値を設定
                    result = driver.execute_script(f"""
                        const el = document.querySelectorAll('*')[{index}];
                        if (!el) return false;
                        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                            el.value = '{text}';
                            return true;
                        }}
                        return false;
                    """)
                    if not result:
                        return ToolResult(error=f"Unable to input text to element at index {index}")
                    return ToolResult(output=f"Input '{text}' into element at index {index}")
                except Exception as e:
                    return ToolResult(error=f"Input text failed: {str(e)}")
                    
            elif action == "execute_js":
                if not script:
                    return ToolResult(error="Script is required for 'execute_js' action")
                try:
                    result = driver.execute_script(script)
                    return ToolResult(output=str(result))
                except Exception as e:
                    return ToolResult(error=f"JavaScript execution failed: {str(e)}")
                    
            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"Seleniumでの処理中にエラーが発生しました: {str(e)}")
            return ToolResult(error=f"ブラウザ操作に失敗しました: {str(e)}")

    async def cleanup(self):
        """リソースのクリーンアップ"""
        global _browser_module
        
        try:
            # 各バックエンド別のクリーンアップ処理
            if _browser_module == "browser_use":
                if hasattr(self, "context") and self.context and not getattr(self.context, "is_closed", lambda: False)():
                    await self.context.close()
                if hasattr(self, "browser") and self.browser and not getattr(self.browser, "is_closed", lambda: False)():
                    await self.browser.close()
            elif _browser_module == "playwright":
                if hasattr(self, "context") and self.context:
                    await self.context.close()
                if hasattr(self, "browser") and self.browser:
                    await self.browser.close()
                if hasattr(self, "playwright") and self.playwright:
                    await self.playwright.stop()
            elif _browser_module == "selenium":
                if hasattr(self, "selenium_driver") and self.selenium_driver:
                    self.selenium_driver.quit()
            
            # リソース参照をクリア
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            self.selenium_driver = None
        except Exception as e:
            logger.error(f"ブラウザリソースのクリーンアップ中にエラーが発生しました: {str(e)}")

    def __del__(self):
        """オブジェクト破棄時のクリーンアップ"""
        if hasattr(self, "browser") and self.browser is not None:
            try:
                # Seleniumの場合は同期的にクリーンアップ
                if _browser_module == "selenium" and hasattr(self, "selenium_driver") and self.selenium_driver:
                    # try-exceptで囲んで確実に閉じる
                    try:
                        self.selenium_driver.quit()
                    except Exception as e:
                        logger.error(f"Seleniumドライバーのクリーンアップに失敗: {e}")
                    return
                
                # 非同期クリーンアップ（Playwright/browser_use用）
                # ランタイムエラーを避けるためのチェック
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        logger.warning("イベントループ実行中のため非同期クリーンアップをスキップします")
                        return
                    
                    # 新しいイベントループを作成してクリーンアップ
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(self.cleanup())
                    new_loop.close()
                except Exception as e:
                    logger.error(f"非同期クリーンアップ処理中にエラーが発生: {e}")
            except Exception as e:
                logger.error(f"ブラウザリソースのクリーンアップに失敗しました: {str(e)}")
