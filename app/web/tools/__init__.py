"""
OpenManus Tools Framework
========================

このモジュールは、OpenManus WebUIにMCP（Model Control Panel）のようなツール連携機能を提供します。
AIアシスタントにGitHub操作などの外部ツールを利用させるためのフレームワークです。
"""

from .base import Tool, ToolResult, register_tool, get_available_tools
from .tool_manager import ToolManager

__all__ = ['Tool', 'ToolResult', 'register_tool', 'get_available_tools', 'ToolManager']
