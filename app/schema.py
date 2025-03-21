from enum import Enum
from typing import Any, List, Literal, Optional, Union
import re

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent execution states"""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Represents a tool/function call in a message"""

    id: str
    type: str = "function"
    function: Function


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: Literal["system", "user", "assistant", "tool"] = Field(...)
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    # メッセージの重要度（1-10、デフォルトは5）
    importance: int = Field(default=5)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """Convert message to dictionary format"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.dict() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        return message

    @classmethod
    def user_message(cls, content: str) -> "Message":
        """Create a user message"""
        return cls(role="user", content=content, importance=8)  # ユーザーメッセージは重要度が高い

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """Create a system message"""
        return cls(role="system", content=content, importance=10)  # システムメッセージは最高重要度

    @classmethod
    def assistant_message(cls, content: Optional[str] = None) -> "Message":
        """Create an assistant message"""
        return cls(role="assistant", content=content, importance=5)  # アシスタントメッセージは標準重要度

    @classmethod
    def tool_message(cls, content: str, name, tool_call_id: str) -> "Message":
        """Create a tool message"""
        # ツール実行結果のメッセージ重要度を内容に基づいて調整
        importance = 6  # デフォルト重要度
        if content and len(content) > 500:
            # 長いツール実行結果は重要
            importance = 7
        return cls(role="tool", content=content, name=name, tool_call_id=tool_call_id, importance=importance)

    @classmethod
    def from_tool_calls(
        cls, tool_calls: List[Any], content: Union[str, List[str]] = "", **kwargs
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
        """
        formatted_calls = [
            {"id": call.id, "function": call.function.model_dump(), "type": "function"}
            for call in tool_calls
        ]
        return cls(
            role="assistant", content=content, tool_calls=formatted_calls, importance=7, **kwargs
        )
    
    def summarize_content(self, max_length: int = 100) -> str:
        """内容を要約する（長い内容の場合）"""
        if not self.content or len(self.content) <= max_length:
            return self.content or ""
        
        # 内容を要約（先頭部分を保持）
        summary = self.content[:max_length].strip()
        return f"{summary}... (略, 全{len(self.content)}文字)"


class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=100)
    # 会話履歴の長さ制限（トークン数ではなく文字数で簡易計算）
    context_length_limit: int = Field(default=8192)
    # 会話履歴の最適化フラグ
    optimize_history: bool = Field(default=True)
    # 重要なメッセージは常に保持
    preserve_important: bool = Field(default=True)
    # 中間ステップやツール実行の要約
    summarize_tools: bool = Field(default=True)

    def add_message(self, message: Message) -> None:
        """Add a message to memory"""
        # LM Studio対応: 連続した同じロールのメッセージを防止する
        if len(self.messages) > 0 and self.messages[-1].role == message.role:
            # 内容が空でなければ、前のメッセージの内容を更新する
            if message.content:
                # 前のメッセージに内容を追加する
                if self.messages[-1].content:
                    self.messages[-1].content += "\n" + message.content
                else:
                    self.messages[-1].content = message.content
            
            # tool_callsが存在する場合、前のメッセージのtool_callsを更新
            if message.tool_calls:
                if self.messages[-1].tool_calls:
                    # 既存のtool_callsとマージする
                    self.messages[-1].tool_calls.extend(message.tool_calls)
                else:
                    self.messages[-1].tool_calls = message.tool_calls
            
            # 重要度を更新（より高い方を採用）
            self.messages[-1].importance = max(self.messages[-1].importance, message.importance)
        else:
            # 異なるロールの場合は通常通り追加
            self.messages.append(message)
        
        # 履歴の最適化（コンテキスト長が制限を超えた場合）
        if self.optimize_history:
            self._optimize_history()

    def add_messages(self, messages: List[Message]) -> None:
        """Add multiple messages to memory"""
        # メッセージを1つずつ追加して、ロールの交互配置を確保
        for message in messages:
            self.add_message(message)

    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages"""
        return self.messages[-n:]

    def to_dict_list(self) -> List[dict]:
        """Convert messages to list of dicts"""
        return [msg.to_dict() for msg in self.messages]
    
    def _optimize_history(self) -> None:
        """会話履歴を最適化し、コンテキスト長を制限内に保つ"""
        # 現在のコンテキスト長（単純な文字数で計算）
        current_length = sum(len(msg.content or "") for msg in self.messages)
        
        # コンテキスト長が制限以下なら何もしない
        if current_length <= self.context_length_limit:
            return
        
        # 削減すべき文字数
        reduction_needed = current_length - self.context_length_limit + 500  # 余裕を持たせる
        
        # メッセージをロールと重要度でグループ化
        grouped_msgs = {}
        for i, msg in enumerate(self.messages):
            key = msg.role
            if key not in grouped_msgs:
                grouped_msgs[key] = []
            grouped_msgs[key].append((i, msg))
        
        # 最適化候補を選定（最初のユーザーメッセージと最新の数メッセージは保持）
        preserved_indices = set()
        if self.messages and self.messages[0].role == "user":
            preserved_indices.add(0)  # 最初のユーザーメッセージは保持
        
        # 最新のメッセージも保持（直近3-5メッセージ）
        recent_count = min(5, len(self.messages) // 3)
        for i in range(max(0, len(self.messages) - recent_count), len(self.messages)):
            preserved_indices.add(i)
        
        # 重要なメッセージは保持
        if self.preserve_important:
            for i, msg in enumerate(self.messages):
                if msg.importance >= 8:  # 重要度8以上は保持
                    preserved_indices.add(i)
        
        # 削減対象のメッセージを選択（重要度が低い中間メッセージから）
        to_optimize = []
        for role, msgs in grouped_msgs.items():
            if role in ["tool", "assistant"]:  # tool/assistantメッセージを主に最適化
                # 重要度が低く、保持対象でないメッセージを選択
                candidates = [(i, msg) for i, msg in msgs if i not in preserved_indices]
                # 重要度の低い順にソート
                candidates.sort(key=lambda x: x[1].importance)
                to_optimize.extend(candidates)
        
        # 最適化を実行
        chars_reduced = 0
        for i, msg in sorted(to_optimize, key=lambda x: x[1].importance):
            if chars_reduced >= reduction_needed:
                break
                
            if i < len(self.messages) and self.messages[i].content:
                # ツールメッセージの要約
                if self.messages[i].role == "tool" and self.summarize_tools:
                    original_len = len(self.messages[i].content)
                    # ツール実行結果を要約
                    self.messages[i].content = self._summarize_tool_output(self.messages[i].content)
                    chars_reduced += original_len - len(self.messages[i].content)
                
                # 長い内容の要約
                elif len(self.messages[i].content) > 200:
                    original_len = len(self.messages[i].content)
                    # 内容を30%に要約
                    max_len = max(150, int(original_len * 0.3))
                    self.messages[i].content = self.messages[i].content[:max_len] + f"... (略, 元の長さ: {original_len}文字)"
                    chars_reduced += original_len - len(self.messages[i].content)
    
    def _summarize_tool_output(self, content: str) -> str:
        """ツール実行結果を要約"""
        if not content or len(content) < 300:
            return content
            
        # コマンド実行結果のパターン
        if content.startswith("Observed output of cmd"):
            lines = content.split("\n")
            header = lines[0]
            
            # 出力が長い場合、主要部分のみ保持
            if len(lines) > 6:
                body = "\n".join(lines[1:3])  # 最初の数行
                footer = f"\n... (略, 元の出力: {len(lines)}行)"
                return f"{header}\n{body}{footer}"
        
        # 長いテキストの一般的な要約
        if len(content) > 500:
            # 先頭部分を保持
            short_version = content[:200].strip()
            # 末尾部分も一部保持
            tail = content[-100:].strip()
            return f"{short_version}\n...\n{tail}\n(略, 元の長さ: {len(content)}文字)"
            
        return content
