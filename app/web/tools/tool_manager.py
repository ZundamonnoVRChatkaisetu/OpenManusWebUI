"""
ツール実行と管理を担当するToolManagerクラス
"""
import asyncio
import inspect
import logging
import json
import re
from typing import Dict, List, Any, Optional, Type, Union, Callable
import traceback

from .base import Tool, ToolResult, ToolResultStatus, get_available_tools

# ロガーの設定
logger = logging.getLogger(__name__)


class ToolManager:
    """
    ツールの実行と管理を担当するクラス。
    """
    def __init__(self):
        self.tools = {}  # 登録されたツールのインスタンスを保持する辞書
        self.load_available_tools()  # 使用可能なツールをロード
        self.command_pattern = re.compile(r'<tool\s+name="([^"]+)">\s*(.*?)\s*</tool>', re.DOTALL)
        self.command_json_pattern = re.compile(r'<tool\s+name="([^"]+)">\s*({.*?})\s*</tool>', re.DOTALL)
        
        # 実行結果のキャッシュ (将来的な拡張のため)
        self.result_cache = {}

    def load_available_tools(self):
        """
        登録可能なすべてのツールをロードして初期化
        """
        available_tools = get_available_tools()
        for tool_name, tool_cls in available_tools.items():
            try:
                self.tools[tool_name] = tool_cls()
                logger.info(f"ツール '{tool_name}' を登録しました")
            except Exception as e:
                logger.error(f"ツール '{tool_name}' の初期化中にエラーが発生しました: {str(e)}")

    def register_tool(self, tool: Tool):
        """
        新しいツールを登録
        """
        self.tools[tool.name] = tool
        logger.info(f"ツール '{tool.name}' を登録しました")

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        登録されているすべてのツールのスキーマを返す
        """
        return [tool.get_schema() for tool in self.tools.values()]

    def get_tools_json_schema(self) -> str:
        """
        登録されているすべてのツールのスキーマをJSON形式で返す
        """
        return json.dumps(self.get_tools_schema(), ensure_ascii=False, indent=2)

    def get_tools_usage_instructions(self) -> str:
        """
        ツールの使用方法の説明を生成
        """
        instructions = [
            "# 利用可能なツール",
            "",
            "以下のツールを使用できます。ツールを使用するには、次の形式で記述してください。",
            "",
            "```",
            '<tool name="ツール名">',
            "{",
            '  "param1": "value1",',
            '  "param2": "value2"',
            "}",
            "</tool>",
            "```",
            "",
            "## 利用可能なツール一覧",
            ""
        ]

        for tool_name, tool in sorted(self.tools.items()):
            instructions.append(f"### {tool_name}")
            instructions.append(f"{tool.description}")
            instructions.append("")
            
            # パラメータの説明
            schema = tool.get_schema()
            params = schema.get("parameters", {}).get("properties", {})
            required = schema.get("parameters", {}).get("required", [])
            
            if params:
                instructions.append("**パラメータ**:")
                instructions.append("")
                
                for param_name, param_info in params.items():
                    req = "（必須）" if param_name in required else "（任意）"
                    desc = param_info.get("description", "")
                    param_type = param_info.get("type", "any")
                    instructions.append(f"- `{param_name}`: {desc} {req} - 型: {param_type}")
                
                instructions.append("")
                
                # 使用例
                instructions.append("**使用例**:")
                instructions.append("```")
                example_params = {}
                for param_name, param_info in params.items():
                    if param_name in required:
                        if param_info.get("type") == "string":
                            example_params[param_name] = "値"
                        elif param_info.get("type") == "number" or param_info.get("type") == "integer":
                            example_params[param_name] = 0
                        elif param_info.get("type") == "boolean":
                            example_params[param_name] = False
                        elif param_info.get("type") == "array":
                            example_params[param_name] = []
                        elif param_info.get("type") == "object":
                            example_params[param_name] = {}
                instructions.append(f'<tool name="{tool_name}">')
                if example_params:
                    instructions.append(json.dumps(example_params, ensure_ascii=False, indent=2))
                instructions.append("</tool>")
                instructions.append("```")
                instructions.append("")

        return "\n".join(instructions)

    def extract_tool_commands(self, text: str) -> List[Dict[str, Any]]:
        """
        テキストからツールコマンドを抽出
        """
        commands = []
        
        # タグベースのコマンド抽出
        matches = self.command_pattern.finditer(text)
        for match in matches:
            tool_name = match.group(1)
            params_text = match.group(2).strip()
            
            try:
                # JSONパラメータの解析
                if params_text.startswith('{') and params_text.endswith('}'):
                    params = json.loads(params_text)
                else:
                    # 単純なテキストの場合（例：<tool name="search">クエリ</tool>）
                    params = {"text": params_text}
                
                commands.append({
                    "tool": tool_name,
                    "params": params
                })
            except json.JSONDecodeError:
                logger.warning(f"ツールコマンドのJSONパラメータ解析に失敗しました: {params_text}")
                # JSON解析に失敗した場合、テキストとして扱う
                commands.append({
                    "tool": tool_name,
                    "params": {"text": params_text}
                })
        
        return commands

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        指定されたツールを実行
        """
        if tool_name not in self.tools:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"ツール '{tool_name}' は存在しません",
                data=None
            )
        
        tool = self.tools[tool_name]
        
        try:
            # パラメータのバリデーション
            validated_params = tool.validate_parameters(params)
            
            # ツールの実行
            result = await tool.execute(**validated_params)
            return result
        except Exception as e:
            logger.error(f"ツール '{tool_name}' の実行中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"実行エラー: {str(e)}",
                data=None
            )

    async def process_text(self, text: str) -> (str, List[Dict[str, Any]]):
        """
        テキスト内のツールコマンドを実行し、結果を含む新しいテキストを返す
        """
        commands = self.extract_tool_commands(text)
        results = []
        
        # ツールコマンドがなければ元のテキストをそのまま返す
        if not commands:
            return text, []
        
        # 各コマンドを実行
        for cmd in commands:
            tool_name = cmd["tool"]
            params = cmd["params"]
            
            # ツールを実行
            result = await self.execute_tool(tool_name, params)
            results.append({
                "tool": tool_name,
                "params": params,
                "result": result.to_dict()
            })
            
            # テキスト内のコマンドを結果で置換
            tag = f'<tool name="{tool_name}">{json.dumps(params) if isinstance(params, dict) else params}</tool>'
            replacement = f"**ツール実行結果** ({tool_name}):\n```json\n{json.dumps(result.to_dict(), ensure_ascii=False, indent=2)}\n```"
            text = text.replace(tag, replacement)
        
        return text, results

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        指定された名前のツールを取得
        """
        return self.tools.get(name)
