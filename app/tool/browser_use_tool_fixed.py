"""
ブラウザツールのクロスプラットフォーム対応版
"""
import asyncio
import json
import logging
import platform
import sys
import os
from typing import Optional, Dict, Any

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.tool.base import BaseTool, ToolResult

# ロガー設定
logger = logging.getLogger(__name__)

# Windows対応のため、直接importではなく動的ロードを使用
_browser_use_available = False
_browser_module = None
_BrowserUseBrowser = None
_BrowserConfig = None

# Microsoft StoreのPythonを検出（NotImplementedError対策）
_is_ms_store_python = False
if platform.system() == "Windows" and sys.executable.startswith("C:\\Program Files\\WindowsApps\\"):
    _is_ms_store_python = True
    logger.warning("Microsoft Store版Pythonが検出されました。ブラウザツールが制限される可能性があります。")

# Selenium WebDriverを使用するフラグ（フォールバック用）
_use_selenium = False

try:
    from browser_use import Browser as BrowserUseBrowser
    from browser_use import BrowserConfig
    from browser_use.browser.context import BrowserContext
    from browser_use.dom.service import DomService
    _browser_use_available = True
    _browser_module = "browser_use"
    _BrowserUseBrowser = BrowserUseBrowser
    _BrowserConfig = BrowserConfig
    logger.info("browser_use モジュールを正常にロードしました")
except (ImportError, NotImplementedError) as e:
    logger.warning(f"browser_use モジュールのロードに失敗しました: {str(e)}")
    
    # Microsoft Store版Pythonの場合はPlaywrightを試さない
    if not _is_ms_store_python:
        try:
            # 代替として手動でPlaywrightを使用
            from playwright.async_api import async_playwright
            _browser_use_available = True
            _browser_module = "playwright"
            logger.info("Playwright モジュールを代替としてロードしました")
        except (ImportError, NotImplementedError) as e:
            logger.warning(f"Playwrightモジュールのロードにも失敗しました: {str(e)}")
    
    # 最終手段としてSeleniumを試行
    if not _browser_use_available or _is_ms_store_python:
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
            logger.info("Selenium WebDriverを最終手段として使用します")
        except ImportError as e:
            logger.error(f"全てのブラウザ自動化ライブラリのロードに失敗しました: {str(e)}")


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
        if not _browser_use_available:
            raise RuntimeError("ブラウザツールの初期化に失敗しました: 必要なモジュールがインストールされていません")

        if _browser_module == "browser_use":
            # browser_useモジュールが使える場合はそちらを使用
            if self.browser is None:
                self.browser = _BrowserUseBrowser(_BrowserConfig(headless=False))
            if self.context is None:
                self.context = await self.browser.new_context()
                self.page = await self.context.get_current_page()
            return self.context
        
        elif _browser_module == "playwright":
            # Playwrightを直接使用
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=False)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            return self.page
        
        elif _browser_module == "selenium":
            # Seleniumを使用
            if self.selenium_driver is None:
                # Chromeオプションの設定
                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                # ヘッドレスモードの設定
                # chrome_options.add_argument("--headless") # ヘッドレスは無効化
                
                try:
                    # WebDriverを初期化
                    self.selenium_driver = webdriver.Chrome(options=chrome_options)
                    logger.info("Selenium WebDriverを初期化しました")
                except WebDriverException as e:
                    logger.error(f"Selenium WebDriverの初期化に失敗しました: {str(e)}")
                    raise RuntimeError(f"Seleniumの初期化に失敗: {str(e)}")
            
            return self.selenium_driver
        
        raise RuntimeError("初期化に必要なブラウザモジュールが見つかりません")

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
        if not _browser_use_available:
            return ToolResult(error="ブラウザツールが利用できません: 必要なライブラリがインストールされていません")

        async with self.lock:
            try:
                if _browser_module == "browser_use":
                    # browser_useモジュールを使用する場合
                    return await self._execute_with_browser_use(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                elif _browser_module == "playwright":
                    # Playwrightを直接使用する場合
                    return await self._execute_with_playwright(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                elif _browser_module == "selenium":
                    # Seleniumを使用する場合
                    return await self._execute_with_selenium(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                else:
                    return ToolResult(error="対応するブラウザライブラリが見つかりません")
            except Exception as e:
                logger.error(f"ブラウザアクション '{action}' の実行中にエラーが発生しました: {str(e)}")
                return ToolResult(error=f"ブラウザアクション '{action}' の実行に失敗: {str(e)}")

    async def _execute_with_browser_use(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """browser_useモジュールを使用したブラウザアクションの実行"""
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
        
        # その他のアクションの実装...
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

    async def _execute_with_playwright(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """Playwrightを直接使用したブラウザアクションの実行"""
        page = await self._ensure_browser_initialized()

        if action == "navigate":
            if not url:
                return ToolResult(error="URL is required for 'navigate' action")
            await page.goto(url)
            return ToolResult(output=f"Navigated to {url}")

        elif action == "click":
            if index is None:
                return ToolResult(error="Index is required for 'click' action")
            # Playwrightでは要素のインデックスによるアクセスが直接サポートされていないため
            # JavaScriptを使用してアクセス
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

    async def _execute_with_selenium(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """Seleniumを使用したブラウザアクションの実行"""
        # 非同期関数内で同期的なSelenium操作を行うため
        # asyncio.to_thread または run_in_executor を使うべきだが、
        # 簡略化のため直接実行する
        
        driver = await self._ensure_browser_initialized()
        
        # actionに応じた処理を実装
        if action == "navigate":
            if not url:
                return ToolResult(error="URL is required for 'navigate' action")
            driver.get(url)
            return ToolResult(output=f"Navigated to {url}")
            
        elif action == "get_text":
            text = driver.find_element(By.TAG_NAME, "body").text
            return ToolResult(output=text)
            
        elif action == "get_html":
            html = driver.page_source
            truncated = html[:2000] + "..." if len(html) > 2000 else html
            return ToolResult(output=truncated)
            
        elif action == "read_links":
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
            
        elif action == "click":
            if index is None:
                return ToolResult(error="Index is required for 'click' action")
            # JavaScriptでインデックスによる要素アクセスとクリック
            try:
                driver.execute_script(f"document.querySelectorAll('*')[{index}].click()")
                return ToolResult(output=f"Clicked element at index {index}")
            except Exception as e:
                return ToolResult(error=f"Click failed: {str(e)}")
                
        elif action == "input_text":
            if index is None or not text:
                return ToolResult(error="Index and text are required for 'input_text' action")
            # JavaScriptで値を設定
            try:
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

    async def cleanup(self):
        """リソースのクリーンアップ"""
        try:
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
                if _browser_module == "selenium" and hasattr(self, "selenium_driver") and self.selenium_driver:
                    # Seleniumの場合は同期的にクリーンアップ
                    self.selenium_driver.quit()
                    return
                
                # 非同期クリーンアップ（Playwright/browser_use用）
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
                logger.error(f"ブラウザリソースのクリーンアップに失敗しました: {str(e)}")
