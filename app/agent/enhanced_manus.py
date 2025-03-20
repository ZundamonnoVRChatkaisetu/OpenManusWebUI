"""
EnhancedManus - 言語対応と出力最適化機能が強化されたManusエージェント
"""

from typing import Dict, List, Optional, Union
from pydantic import Field

from app.agent.manus import Manus
from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection, BrowserUseTool
from app.tool.file_saver import FileSaver, SaveFileParams
from app.tool.google_search import GoogleSearch
from app.tool.python_execute import PythonExecute
from app.utils.language_utils import Language, detect_language, get_template
from app.utils.output_formatter import (
    extract_final_result,
    format_error_message,
    format_file_generation_result,
    format_thought_process,
    format_tool_result
)
from app.utils.file_templates import (
    generate_app_spec,
    generate_app_prototype
)


class EnhancedManus(Manus):
    """
    強化版Manusエージェント - 言語対応と出力最適化機能を備えています。
    
    - 自動言語検出と多言語対応
    - 思考プロセスと最終結果の区別
    - アプリ設計書やプロトタイプの自動生成
    - ファイル生成機能の強化
    """
    
    name: str = "EnhancedManus"
    description: str = (
        "An enhanced versatile agent with multi-language support and improved output formatting"
    )
    
    # ユーザー指定の言語（設定されていない場合は自動検出）
    language: Optional[Language] = None
    
    # 思考プロセスを記録
    thought_steps: List[str] = Field(default_factory=list)
    
    # 生成されたファイルを記録
    generated_files: List[Dict[str, str]] = Field(default_factory=list)
    
    # 追加機能フラグ
    hide_thought_process: bool = True  # デフォルトで思考プロセスを非表示
    auto_generate_files: bool = True   # デフォルトでファイル自動生成を有効化
    
    async def run(self, prompt: str, **kwargs) -> str:
        """
        ユーザープロンプトを処理し、適切な言語で応答する
        
        Args:
            prompt: ユーザープロンプト
            **kwargs: 追加のパラメータ
            
        Returns:
            処理結果
        """
        # プロンプトから言語を検出（言語が明示的に設定されていない場合）
        if not self.language:
            self.language = detect_language(prompt)
            logger.info(f"言語を検出しました: {self.language}")
        
        # 思考ステップをリセット
        self.thought_steps = []
        
        # 生成ファイルをリセット
        self.generated_files = []
        
        # 標準のrun処理を実行
        full_result = await super().run(prompt, **kwargs)
        
        # APIの場合は完全な出力を返す
        is_api_call = kwargs.get("api_call", False)
        if is_api_call:
            return full_result
        
        # 思考プロセスを非表示にするかどうかに基づいて出力を処理
        if self.hide_thought_process:
            # 思考プロセスを除外し、最終結果のみを抽出
            final_result = extract_final_result(full_result)
            return final_result
        else:
            # 思考プロセスと最終結果を含む完全な出力を返す
            return full_result
        
    async def execute_tool(self, command) -> str:
        """
        拡張したツール実行機能 - 言語対応と出力整形を追加
        """
        # 思考ステップを記録
        self.thought_steps.append(f"ツール '{command.function.name}' を実行します...")
        
        # 標準のツール実行処理
        result = await super().execute_tool(command)
        
        # ツール結果に基づいて追加処理を実行
        name = command.function.name if command and command.function else "unknown"
        
        # FileSaverツールの場合は生成ファイルを記録
        if name == "file_saver":
            try:
                args = command.function.arguments or "{}"
                args_dict = eval(args) if isinstance(args, str) else args
                file_path = args_dict.get("file_path", "")
                content = args_dict.get("content", "")[:200]  # プレビュー用に先頭200文字
                
                self.generated_files.append({
                    "filename": file_path,
                    "content_preview": content
                })
                
                # 整形された結果を返す
                formatted_result = format_file_generation_result(
                    filename=file_path,
                    content_preview=f"{content}...",
                    language=self.language
                )
                return formatted_result
            except Exception as e:
                logger.error(f"ファイル生成結果の処理中にエラー: {e}")
                return result
        
        # アプリ設計に関する機能を検出し、自動ファイル生成を実行
        if self.auto_generate_files and "app" in result.lower() and "design" in result.lower():
            try:
                # 結果からアプリ名と説明を抽出する試み
                import re
                app_name_match = re.search(r'app(?:\s+name)?[:\s]+([\"\']?)([^\"\':\n]+)\1', result, re.IGNORECASE)
                app_name = app_name_match.group(2) if app_name_match else "SampleApp"
                
                # 機能リストを抽出する試み
                features = []
                features_section = re.search(r'features?:?\s*\n((?:.+\n)+)', result, re.IGNORECASE)
                if features_section:
                    feature_lines = features_section.group(1).strip().split('\n')
                    for line in feature_lines:
                        line = line.strip()
                        if line.startswith('-') or line.startswith('*'):
                            title_match = re.search(r'[*-]\s*([^:]+):\s*(.+)', line)
                            if title_match:
                                features.append({
                                    "title": title_match.group(1).strip(),
                                    "description": title_match.group(2).strip()
                                })
                            else:
                                features.append({
                                    "title": line[1:].strip(),
                                    "description": "詳細な説明はこちら"
                                })
                
                # デフォルトの機能が不足している場合
                if len(features) < 3:
                    features = [
                        {"title": "高速処理", "description": "最新のアルゴリズムによる高速な処理を実現"},
                        {"title": "使いやすいUI", "description": "直感的に操作できるユーザーインターフェース"},
                        {"title": "多機能", "description": "様々な用途に対応できる多機能設計"}
                    ]
                
                # アプリ説明を抽出する試み
                description_match = re.search(r'description:?\s*([\"\']?)([^\"\']+)\1', result, re.IGNORECASE)
                app_description = description_match.group(2) if description_match else "革新的なアプリケーション"
                
                # アプリ設計書を生成
                spec_content = generate_app_spec(
                    app_name=app_name,
                    app_description=app_description,
                    features=features,
                    architecture="クライアント-サーバーアーキテクチャを採用",
                    technologies=["Next.js", "React", "Node.js", "TypeScript"],
                    language=self.language
                )
                
                # プロトタイプHTMLを生成
                prototype_content = generate_app_prototype(
                    app_name=app_name,
                    app_headline=f"{app_name} - {app_description}",
                    app_subheadline="革新的な機能で、あなたの生活をもっと便利に",
                    features=features,
                    language=self.language
                )
                
                # ファイルを保存
                spec_filename = f"{app_name.lower().replace(' ', '_')}_spec.md"
                prototype_filename = f"{app_name.lower().replace(' ', '_')}_prototype.html"
                
                # FileSaverを使用してファイルを保存
                await self.available_tools.execute(
                    name="file_saver",
                    tool_input={"content": spec_content, "file_path": spec_filename}
                )
                await self.available_tools.execute(
                    name="file_saver",
                    tool_input={"content": prototype_content, "file_path": prototype_filename}
                )
                
                # 生成ファイルを記録
                self.generated_files.append({
                    "filename": spec_filename,
                    "content_preview": spec_content[:200]
                })
                self.generated_files.append({
                    "filename": prototype_filename,
                    "content_preview": prototype_content[:200]
                })
                
                # 思考ステップに自動生成を記録
                self.thought_steps.append(f"アプリ '{app_name}' の設計書とプロトタイプを自動生成しました")
                
                # 元の結果に成果物の生成情報を追加
                gen_msg = f"\n\n以下のファイルが自動生成されました:\n- {spec_filename}: アプリケーション設計書\n- {prototype_filename}: UIプロトタイプ"
                result += gen_msg
            except Exception as e:
                logger.error(f"アプリ設計の自動生成中にエラー: {e}")
                # エラーが発生しても元の結果は返す
        
        return result
