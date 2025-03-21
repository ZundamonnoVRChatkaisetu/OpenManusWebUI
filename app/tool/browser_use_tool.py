"""ブラウザツールの改善実装

このモジュールは、異なる環境（Windows、macOS、Linux）でも動作するブラウザ操作ツールを提供します。
環境に応じて最適なバックエンド（Selenium、Playwright、browser_use）を選択し、
統一的なインターフェースでブラウザ操作を行うことができます。

Windows環境では自動的にSeleniumバックエンドを使用します。
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.tool.base import BaseTool, ToolResult
from app.tool.browser_backends import is_windows, get_browser_backend, cleanup_all_backends
from app.tool.browser_backends.backend_manager import (
    BACKEND_NONE, BACKEND_SELENIUM, BACKEND_PLAYWRIGHT, BACKEND_BROWSER_USE
)

# ロガー設定
logger = logging.getLogger(__name__)

# ツールの説明
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
    """ブラウザ操作ツール
    
    このツールは環境に応じて最適なバックエンドを選択し、
    ブラウザ操作を行うことができます。
    主要アクションには、ページ遷移、要素のクリック、
    テキスト入力、HTML取得などが含まれます。
    """
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
    backend_name: Optional[str] = Field(default=None, exclude=True)
    backend_instance: Optional[Any] = Field(default=None, exclude=True)

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        if not v:
            raise ValueError("パラメータを空にすることはできません")
        return v

    async def _ensure_browser_initialized(self) -> bool:
        """ブラウザーとバックエンドが初期化されていることを確認します
        
        Returns:
            bool: 初期化に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # 既に初期化済みならそのまま使用
            if self.backend_name and self.backend_instance:
                logger.debug(f"既存のバックエンド {self.backend_name} を再利用します")
                return True
            
            # Windows環境の場合の追加チェック
            if is_windows():
                logger.info("Windows環境ではバックエンドマネージャーからSeleniumのみが提供されます")
            
            # バックエンドマネージャーから適切なバックエンドを取得
            backend_name, backend_instance = await get_browser_backend()
            
            if backend_name == BACKEND_NONE or backend_instance is None:
                logger.error("使用可能なブラウザバックエンドが見つかりませんでした")
                return False
            
            # バックエンド情報を保存
            self.backend_name = backend_name
            self.backend_instance = backend_instance
            logger.info(f"バックエンド {backend_name} を正常に初期化しました")
            return True
            
        except Exception as e:
            logger.error(f"ブラウザの初期化中にエラーが発生しました: {e}")
            return False

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
        """ブラウザアクションを実行します
        
        Args:
            action: 実行するアクション名
            url: URL（navigate, new_tabアクション用）
            index: 要素インデックス（click, input_textアクション用）
            text: 入力テキスト（input_textアクション用）
            script: JavaScriptコード（execute_jsアクション用）
            scroll_amount: スクロール量（scrollアクション用）
            tab_id: タブID（switch_tabアクション用）
            
        Returns:
            ToolResult: アクションの実行結果
        """
        if is_windows():
            logger.info("Windows環境でブラウザアクションを実行します")

        async with self.lock:
            try:
                # ブラウザ初期化確認
                if not await self._ensure_browser_initialized():
                    return ToolResult(error="ブラウザツールが利用できません: 初期化に失敗しました")
                
                # バックエンドに応じた処理の分岐
                if self.backend_name == BACKEND_SELENIUM:
                    return await self._execute_with_selenium(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                elif self.backend_name == BACKEND_PLAYWRIGHT:
                    return await self._execute_with_playwright(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                elif self.backend_name == BACKEND_BROWSER_USE:
                    return await self._execute_with_browser_use(
                        action, url, index, text, script, scroll_amount, tab_id, **kwargs
                    )
                else:
                    return ToolResult(error=f"サポートされていないバックエンドです: {self.backend_name}")
                    
            except Exception as e:
                logger.error(f"ブラウザアクション '{action}' の実行中にエラーが発生しました: {str(e)}")
                return ToolResult(error=f"ブラウザアクション '{action}' の実行に失敗: {str(e)}")

    async def _execute_with_browser_use(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """ブラウザアクションをbrowser_useバックエンドで実行します"""
        try:
            # browser_useバックエンドでは、contextがメインのインターフェース
            context = self.backend_instance['context']

            if action == "navigate":
                if not url:
                    return ToolResult(error="navigateアクションにはURLが必要です")
                await context.navigate_to(url)
                return ToolResult(output=f"{url}にアクセスしました")

            elif action == "click":
                if index is None:
                    return ToolResult(error="clickアクションには要素インデックスが必要です")
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return ToolResult(error=f"インデックス {index} の要素が見つかりませんでした")
                download_path = await context._click_element_node(element)
                output = f"インデックス {index} の要素をクリックしました"
                if download_path:
                    output += f" - ファイルを {download_path} にダウンロードしました"
                return ToolResult(output=output)

            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="input_textアクションには要素インデックスとテキストが必要です")
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return ToolResult(error=f"インデックス {index} の要素が見つかりませんでした")
                await context._input_text_element_node(element, text)
                return ToolResult(output=f"インデックス {index} の要素にテキスト '{text}' を入力しました")

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
                    return ToolResult(error="execute_jsアクションにはJavaScriptコードが必要です")
                result = await context.execute_javascript(script)
                return ToolResult(output=str(result))

            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"browser_useでの処理中にエラーが発生しました: {e}")
            # バックエンドの再選択が必要な場合はクリーンアップして再度初期化
            await self.cleanup()
            self.backend_name = None
            self.backend_instance = None
            if await self._ensure_browser_initialized():
                # 新しいバックエンドで再試行
                return await self.execute(action, url, index, text, script, scroll_amount, tab_id, **kwargs)
            
            return ToolResult(error=f"browser_useでの処理に失敗しました: {str(e)}")

    async def _execute_with_playwright(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """ブラウザアクションをPlaywrightバックエンドで実行します"""
        try:
            # Playwrightバックエンドでは、pageがメインのインターフェース
            page = self.backend_instance['page']

            if action == "navigate":
                if not url:
                    return ToolResult(error="navigateアクションにはURLが必要です")
                await page.goto(url)
                return ToolResult(output=f"{url}にアクセスしました")

            elif action == "click":
                if index is None:
                    return ToolResult(error="clickアクションには要素インデックスが必要です")
                # JavaScriptを使用して要素をクリック
                await page.evaluate(f"document.querySelectorAll('*')[{index}].click()")
                return ToolResult(output=f"インデックス {index} の要素をクリックしました")

            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="input_textアクションには要素インデックスとテキストが必要です")
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
                    return ToolResult(error=f"インデックス {index} の要素にテキストを入力できませんでした")
                return ToolResult(output=f"インデックス {index} の要素にテキスト '{text}' を入力しました")

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
                    return ToolResult(error="execute_jsアクションにはJavaScriptコードが必要です")
                result = await page.evaluate(script)
                return ToolResult(output=str(result))

            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"Playwrightでの処理中にエラーが発生しました: {e}")
            # バックエンドの再選択が必要な場合はクリーンアップして再度初期化
            await self.cleanup()
            self.backend_name = None
            self.backend_instance = None
            if await self._ensure_browser_initialized():
                # 新しいバックエンドで再試行
                return await self.execute(action, url, index, text, script, scroll_amount, tab_id, **kwargs)
            
            return ToolResult(error=f"Playwrightでの処理に失敗しました: {str(e)}")

    async def _execute_with_selenium(
        self, action, url, index, text, script, scroll_amount, tab_id, **kwargs
    ) -> ToolResult:
        """ブラウザアクションをSeleniumバックエンドで実行します"""
        # 非同期関数内で同期的なSelenium操作を行うため、安全に実行する
        from selenium.webdriver.common.by import By
        
        try:
            # Selenium WebDriverを取得
            driver = self.backend_instance
            
            # actionに応じた処理を実装
            if action == "navigate":
                if not url:
                    return ToolResult(error="navigateアクションにはURLが必要です")
                try:
                    driver.get(url)
                    return ToolResult(output=f"{url}にアクセスしました")
                except Exception as e:
                    return ToolResult(error=f"ページの読み込みに失敗しました: {str(e)}")
                
            elif action == "get_text":
                try:
                    text = driver.find_element(By.TAG_NAME, "body").text
                    return ToolResult(output=text)
                except Exception as e:
                    return ToolResult(error=f"テキストの取得に失敗しました: {str(e)}")
                
            elif action == "get_html":
                try:
                    html = driver.page_source
                    truncated = html[:2000] + "..." if len(html) > 2000 else html
                    return ToolResult(output=truncated)
                except Exception as e:
                    return ToolResult(error=f"HTMLの取得に失敗しました: {str(e)}")
                
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
                    return ToolResult(error=f"リンクの読み取りに失敗しました: {str(e)}")
                
            elif action == "click":
                if index is None:
                    return ToolResult(error="clickアクションには要素インデックスが必要です")
                try:
                    # JavaScriptでインデックスによる要素アクセスとクリック
                    driver.execute_script(f"document.querySelectorAll('*')[{index}].click()")
                    return ToolResult(output=f"インデックス {index} の要素をクリックしました")
                except Exception as e:
                    return ToolResult(error=f"クリックに失敗しました: {str(e)}")
                    
            elif action == "input_text":
                if index is None or not text:
                    return ToolResult(error="input_textアクションには要素インデックスとテキストが必要です")
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
                        return ToolResult(error=f"インデックス {index} の要素にテキストを入力できませんでした")
                    return ToolResult(output=f"インデックス {index} の要素にテキスト '{text}' を入力しました")
                except Exception as e:
                    return ToolResult(error=f"テキスト入力に失敗しました: {str(e)}")
                    
            elif action == "execute_js":
                if not script:
                    return ToolResult(error="execute_jsアクションにはJavaScriptコードが必要です")
                try:
                    result = driver.execute_script(script)
                    return ToolResult(output=str(result))
                except Exception as e:
                    return ToolResult(error=f"JavaScriptの実行に失敗しました: {str(e)}")
                    
            else:
                return ToolResult(error=f"未実装または不明なアクション: {action}")
                
        except Exception as e:
            logger.error(f"Seleniumでの処理中にエラーが発生しました: {str(e)}")
            # バックエンドの再選択が必要な場合はクリーンアップして再度初期化
            await self.cleanup()
            self.backend_name = None
            self.backend_instance = None
            if await self._ensure_browser_initialized():
                # 新しいバックエンドで再試行
                return await self.execute(action, url, index, text, script, scroll_amount, tab_id, **kwargs)
            
            return ToolResult(error=f"ブラウザ操作に失敗しました: {str(e)}")

    async def cleanup(self):
        """リソースのクリーンアップを行います"""
        try:
            # バックエンドマネージャーを使って全てのバックエンドをクリーンアップ
            await cleanup_all_backends()
            
            # インスタンス参照をクリア
            self.backend_name = None
            self.backend_instance = None
            
            logger.info("ブラウザリソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"ブラウザリソースのクリーンアップ中にエラーが発生しました: {str(e)}")

    def __del__(self):
        """オブジェクト破棄時のクリーンアップ"""
        # 以前の実装ではイベントループが実行中の場合でも非同期クリーンアップを試みていたが、
        # これはエラーの原因となる可能性がある。イベントループ実行中の場合は単に警告を出すだけにする
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("イベントループ実行中のため非同期クリーンアップをスキップします")
                return
            
            # 非同期クリーンアップが安全に実行できる場合のみ実行
            try:
                # この場合は新しいイベントループは作成せず、既存のループを使用
                asyncio.run(self.cleanup())
            except RuntimeError:
                # RuntimeErrorは「イベントループが既に閉じられている」または
                # 「イベントループが既に実行中」の場合に発生する可能性がある
                logger.warning("既存のイベントループを使用できないため、クリーンアップをスキップします")
            except Exception as e:
                logger.error(f"非同期クリーンアップ処理中にエラーが発生: {e}")
        except Exception as e:
            # イベントループが取得できない場合など
            logger.error(f"クリーンアップ前の状態チェック中にエラーが発生: {e}")
