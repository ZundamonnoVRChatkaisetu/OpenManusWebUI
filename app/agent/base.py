import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Memory, Message


class BaseAgent(BaseModel, ABC):
    """Abstract base class for managing agent state and execution.

    Provides foundational functionality for state transitions, memory management,
    and a step-based execution loop. Subclasses must implement the `step` method.
    """

    # Core attributes
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Optional agent description")

    # Prompts
    system_prompt: Optional[str] = Field(
        None, description="System-level instruction prompt"
    )
    next_step_prompt: Optional[str] = Field(
        None, description="Prompt for determining next action"
    )

    # Dependencies
    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")
    state: AgentState = Field(
        default=AgentState.IDLE, description="Current agent state"
    )

    # Execution control
    max_steps: int = Field(default=100, description="Maximum steps before termination")
    current_step: int = Field(default=0, description="Current step in execution")

    # 精度低下検出と対策
    duplicate_threshold: int = 3  # 繰り返し検出のしきい値
    accuracy_monitor_interval: int = 10  # 精度モニタリングの間隔
    automatic_recovery: bool = True  # 自動リカバリーを有効化
    
    # 精度向上のための状態維持
    recent_tools_used: List[str] = Field(default_factory=list)  # 最近使用したツール
    accuracy_issues_detected: int = 0  # 検出された精度問題の数
    recovery_attempts: int = 0  # 回復試行の回数

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields for flexibility in subclasses

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """Initialize agent with default settings if not provided."""
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """Context manager for safe agent state transitions.

        Args:
            new_state: The state to transition to during the context.

        Yields:
            None: Allows execution within the new state.

        Raises:
            ValueError: If the new_state is invalid.
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Invalid state: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # Transition to ERROR on failure
            raise e
        finally:
            self.state = previous_state  # Revert to previous state

    def update_memory(
        self,
        role: Literal["user", "system", "assistant", "tool"],
        content: str,
        **kwargs,
    ) -> None:
        """Add a message to the agent's memory.

        Args:
            role: The role of the message sender (user, system, assistant, tool).
            content: The message content.
            **kwargs: Additional arguments (e.g., tool_call_id for tool messages).

        Raises:
            ValueError: If the role is unsupported.
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        msg_factory = message_map[role]
        msg = msg_factory(content, **kwargs) if role == "tool" else msg_factory(content)
        self.memory.add_message(msg)

    async def run(
        self, request: Optional[str] = None, cancel_event: asyncio.Event = None
    ) -> str:
        """Execute the agent's main loop asynchronously.

        Args:
            request: Optional initial user request to process.
            cancel_event: Optional asyncio event to signal cancellation.

        Returns:
            A string summarizing the execution results.

        Raises:
            RuntimeError: If the agent is not in IDLE state at start.
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                # Check for cancellation
                if cancel_event and cancel_event.is_set():
                    return "操作は取り消されました"

                self.current_step += 1
                logger.info(f"Executing step {self.current_step}/{self.max_steps}")
                
                # 精度低下の監視と対策（一定間隔で実行）
                if self.automatic_recovery and self.current_step % self.accuracy_monitor_interval == 0:
                    await self._monitor_accuracy()
                
                step_result = await self.step()

                # Check for stuck state
                if self.is_stuck():
                    self.handle_stuck_state()

                # 精度向上のための状態追跡
                if step_result and "cmd `" in step_result:
                    # ツール名をリストに追加
                    tool_match = step_result.split("cmd `")[1].split("`")[0]
                    if tool_match:
                        self.recent_tools_used.append(tool_match)
                        # 最大5つのツールを記録
                        if len(self.recent_tools_used) > 5:
                            self.recent_tools_used.pop(0)

                results.append(f"Step {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                results.append(f"Terminated: Reached max steps ({self.max_steps})")

        return "\n".join(results) if results else "No steps executed"

    @abstractmethod
    async def step(self) -> str:
        """Execute a single step in the agent's workflow.

        Must be implemented by subclasses to define specific behavior.
        """

    def handle_stuck_state(self):
        """Handle stuck state by adding a prompt to change strategy"""
        self.accuracy_issues_detected += 1
        
        # スタック状態の検出回数に応じて異なる対応
        if self.accuracy_issues_detected <= 2:
            # 軽度の対応（最初の数回）
            stuck_prompt = "\
            同じアプローチが繰り返し試されています。新しいアプローチを検討し、すでに試して効果がなかった方法は避けてください。"
        else:
            # より積極的な対応（何度も検出された場合）
            stuck_prompt = f"\
            重要: 現在のアプローチは機能していません。{self.accuracy_issues_detected}回目の検出です。\
            ここで完全に異なる視点から問題を再評価してください。\
            これまでとは異なるツールや方法を使用してください。\
            作業中の問題を基本から捉え直し、解決に向けた新しい視点を示してください。"
        
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt or ''}"
        logger.warning(f"Agent detected stuck state ({self.accuracy_issues_detected}回目). Added recovery prompt.")

    def is_stuck(self) -> bool:
        """Check if the agent is stuck in a loop by detecting duplicate content"""
        if len(self.memory.messages) < 2:
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # Count identical content occurrences
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )

        # 精度低下の兆候: 同じツールが何度も連続して使われる場合
        if len(self.recent_tools_used) >= 3:
            # 最新の3つのツールが同じかどうか
            if len(set(self.recent_tools_used[-3:])) == 1:
                logger.warning(f"同じツール '{self.recent_tools_used[-1]}' が連続して使用されています")
                return True

        return duplicate_count >= self.duplicate_threshold
        
    async def _monitor_accuracy(self):
        """精度低下を監視し、必要に応じて対策を実施"""
        if len(self.memory.messages) < 5:
            return  # 十分なメッセージがない場合はスキップ
            
        # 会話履歴の長さとメッセージ数をチェック
        msg_count = len(self.memory.messages)
        total_length = sum(len(msg.content or "") for msg in self.memory.messages)
        
        logger.info(f"精度モニタリング: {msg_count}メッセージ, 約{total_length}文字")
        
        # 長い会話履歴の場合、重要な情報を要約して次のステップに含める
        if total_length > 5000 and self.current_step > 20:
            # 要約頻度を調整（精度問題が検出されるほど頻繁に）
            if self.accuracy_issues_detected == 0 or self.current_step % max(5, 20 - self.accuracy_issues_detected * 3) == 0:
                await self._create_progress_summary()
    
    async def _create_progress_summary(self):
        """現在の進捗を要約し、重要なポイントを次のステップに含める"""
        # ユーザーの最初の指示を取得
        initial_request = None
        for msg in self.memory.messages:
            if msg.role == "user":
                initial_request = msg.content
                break
                
        if not initial_request:
            return
            
        # 最近のメッセージとツール実行結果を抽出
        recent_msgs = self.memory.messages[-min(15, len(self.memory.messages)):]
        
        # 中間結果を要約して次のプロンプトに追加
        summary = "## 進捗の要約\n"
        summary += f"- 初期指示: {initial_request[:100]}{'...' if len(initial_request) > 100 else ''}\n"
        summary += f"- 現在のステップ: {self.current_step}/{self.max_steps}\n"
        
        if self.recent_tools_used:
            summary += f"- 最近使用したツール: {', '.join(self.recent_tools_used[-3:])}\n"
            
        # 重要なツール実行結果の抽出
        tool_results = []
        for msg in recent_msgs:
            if msg.role == "tool" and msg.content:
                tool_name = msg.name or "unknown"
                # 内容の要約（長い場合）
                content_summary = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                tool_results.append(f"- {tool_name}: {content_summary}")
                
        if tool_results:
            summary += "## 重要なツール実行結果\n"
            summary += "\n".join(tool_results[-3:])  # 最新の3つの結果
        
        # 次のステップのプロンプトに追加
        current_progress_note = f"\n\n{summary}\n\nこれらの情報を踏まえて次のステップを実行してください。特に重要な点に焦点を当て、目標達成に向けて効率的に進めてください。"
        
        if self.next_step_prompt:
            self.next_step_prompt += current_progress_note
        else:
            self.next_step_prompt = current_progress_note
            
        self.recovery_attempts += 1
        logger.info(f"進捗要約を追加しました（{self.recovery_attempts}回目）")

    @property
    def messages(self) -> List[Message]:
        """Retrieve a list of messages from the agent's memory."""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """Set the list of messages in the agent's memory."""
        self.memory.messages = value
