import json
from typing import Any, List, Literal

from pydantic import Field

from app.agent.react import ReActAgent
from app.logger import logger
from app.prompt.toolcall import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import AgentState, Message, ToolCall
from app.tool import CreateChatCompletion, Terminate, ToolCollection


TOOL_CALL_REQUIRED = "Tool calls required but none provided"


class ToolCallAgent(ReActAgent):
    """Base agent class for handling tool/function calls with enhanced abstraction"""

    name: str = "toolcall"
    description: str = "an agent that can execute tool calls."

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
        CreateChatCompletion(), Terminate()
    )
    tool_choices: Literal["none", "auto", "required"] = "auto"
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    tool_calls: List[ToolCall] = Field(default_factory=list)

    max_steps: int = 100  # max_stepsを30から100に増加
    
    # 思考プロセスの精度向上のためのパラメータ
    step_review_interval: int = 5  # 何ステップごとに進捗を確認するか
    adaptive_planning: bool = True  # 状況に応じて計画を調整するか
    verbose_thinking: bool = True   # 詳細な思考ログを出力するか

    async def think(self) -> bool:
        """Process current state and decide next actions using tools"""
        # ステップに応じた自己評価と計画調整
        if self.adaptive_planning and self.current_step > 0 and self.current_step % self.step_review_interval == 0:
            await self._review_progress()
        
        # 次のステップのプロンプトを設定
        if self.next_step_prompt:
            # 長いプロンプトの場合は最適化（重要な指示を保持）
            effective_prompt = self._optimize_next_step_prompt() if len(self.next_step_prompt) > 500 else self.next_step_prompt
            user_msg = Message.user_message(effective_prompt)
            self.messages += [user_msg]

        # 思考ステップのログ記録
        if self.verbose_thinking:
            logger.info(f"💭 Step {self.current_step}: 思考開始 - コンテキスト長約{self._estimate_context_length()}文字")

        # Get response with tool options
        response = await self.llm.ask_tool(
            messages=self.messages,
            system_msgs=[Message.system_message(self.system_prompt)]
            if self.system_prompt
            else None,
            tools=self.available_tools.to_params(),
            tool_choice=self.tool_choices,
        )
        self.tool_calls = response.tool_calls

        # Log response info
        logger.info(f"✨ {self.name}'s thoughts: {response.content}")
        logger.info(
            f"🛠️ {self.name} selected {len(response.tool_calls) if response.tool_calls else 0} tools to use"
        )
        if response.tool_calls:
            logger.info(
                f"🧰 Tools being prepared: {[call.function.name for call in response.tool_calls]}"
            )

        try:
            # Handle different tool_choices modes
            if self.tool_choices == "none":
                if response.tool_calls:
                    logger.warning(
                        f"🤔 Hmm, {self.name} tried to use tools when they weren't available!"
                    )
                if response.content:
                    self.memory.add_message(Message.assistant_message(response.content))
                    return True
                return False

            # Create and add assistant message
            assistant_msg = (
                Message.from_tool_calls(
                    content=response.content, tool_calls=self.tool_calls
                )
                if self.tool_calls
                else Message.assistant_message(response.content)
            )
            self.memory.add_message(assistant_msg)

            if self.tool_choices == "required" and not self.tool_calls:
                return True  # Will be handled in act()

            # For 'auto' mode, continue with content if no commands but content exists
            if self.tool_choices == "auto" and not self.tool_calls:
                return bool(response.content)

            return bool(self.tool_calls)
        except Exception as e:
            logger.error(f"🚨 Oops! The {self.name}'s thinking process hit a snag: {e}")
            self.memory.add_message(
                Message.assistant_message(
                    f"Error encountered while processing: {str(e)}"
                )
            )
            return False

    async def act(self) -> str:
        """Execute tool calls and handle their results"""
        if not self.tool_calls:
            if self.tool_choices == "required":
                raise ValueError(TOOL_CALL_REQUIRED)

            # Return last message content if no tool calls
            return self.messages[-1].content or "No content or commands to execute"

        results = []
        for command in self.tool_calls:
            # ツール実行前のログ記録（詳細モード）
            if self.verbose_thinking:
                logger.info(f"🔧 ツール '{command.function.name}' の実行を開始します...")
                
            result = await self.execute_tool(command)
            logger.info(
                f"🎯 Tool '{command.function.name}' completed its mission! Result: {result[:100]}..." if len(result) > 100 else result
            )

            # Add tool response to memory
            tool_msg = Message.tool_message(
                content=result, tool_call_id=command.id, name=command.function.name
            )
            self.memory.add_message(tool_msg)
            results.append(result)

        # 各実行ステップ後のメモリ状態を確認
        if self.verbose_thinking:
            msg_count = len(self.memory.messages)
            ctx_len = self._estimate_context_length()
            logger.info(f"📊 実行後のメモリ状態: {msg_count}メッセージ, 約{ctx_len}文字")

        return "\n\n".join(results)

    async def execute_tool(self, command: ToolCall) -> str:
        """Execute a single tool call with robust error handling"""
        if not command or not command.function or not command.function.name:
            return "Error: Invalid command format"

        name = command.function.name
        if name not in self.available_tools.tool_map:
            return f"Error: Unknown tool '{name}'"

        try:
            # Parse arguments
            args = json.loads(command.function.arguments or "{}")

            # Execute the tool
            logger.info(f"🔧 Activating tool: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)

            # Format result for display
            observation = (
                f"Observed output of cmd `{name}` executed:\n{str(result)}"
                if result
                else f"Cmd `{name}` completed with no output"
            )

            # Handle special tools like `finish`
            await self._handle_special_tool(name=name, result=result)

            return observation
        except json.JSONDecodeError:
            error_msg = f"Error parsing arguments for {name}: Invalid JSON format"
            logger.error(
                f"📝 Oops! The arguments for '{name}' don't make sense - invalid JSON, arguments:{command.function.arguments}"
            )
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"⚠️ Tool '{name}' encountered a problem: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """Handle special tool execution and state changes"""
        if not self._is_special_tool(name):
            return

        if self._should_finish_execution(name=name, result=result, **kwargs):
            # Set agent state to finished
            logger.info(f"🏁 Special tool '{name}' has completed the task!")
            self.state = AgentState.FINISHED

    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """Determine if tool execution should finish the agent"""
        return True

    def _is_special_tool(self, name: str) -> bool:
        """Check if tool name is in special tools list"""
        return name.lower() in [n.lower() for n in self.special_tool_names]
    
    async def _review_progress(self) -> None:
        """定期的な進捗確認と戦略の調整"""
        logger.info(f"📝 ステップ{self.current_step}: 進捗確認と戦略の調整")
        
        # 進捗の要約
        summary = f"現在、ステップ{self.current_step}/{self.max_steps}を実行中です。"
        
        # 現在のメモリ状態を分析
        memory_analysis = self._analyze_memory_state()
        
        # 次のステップのプロンプトに追加する進捗確認情報
        progress_note = f"\n\n# 進捗確認（ステップ{self.current_step}）\n{summary}\n{memory_analysis}\n\n"
        
        # 根本的な問題解決に焦点を当てる指示を追加
        focus_instruction = "これまでの進捗を踏まえ、問題の根本的な解決に焦点を当ててください。"
        
        # next_step_promptがある場合は末尾に追加、ない場合は新たに設定
        if self.next_step_prompt:
            self.next_step_prompt += progress_note + focus_instruction
        else:
            self.next_step_prompt = progress_note + focus_instruction
    
    def _analyze_memory_state(self) -> str:
        """メモリの状態を分析し、適切な戦略調整のための情報を提供"""
        # メッセージの総数
        msg_count = len(self.memory.messages)
        
        # ユーザーの最新の指示を取得
        last_user_msg = None
        for msg in reversed(self.memory.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break
        
        # 実行済みのツールを集計
        tool_usage = {}
        for msg in self.memory.messages:
            if msg.role == "tool" and msg.name:
                tool_usage[msg.name] = tool_usage.get(msg.name, 0) + 1
        
        # 分析結果の構築
        analysis = [
            f"- 会話履歴: {msg_count}メッセージ",
            f"- 推定コンテキスト長: 約{self._estimate_context_length()}文字"
        ]
        
        if tool_usage:
            tools_str = ", ".join([f"{name}({count}回)" for name, count in tool_usage.items()])
            analysis.append(f"- 使用ツール: {tools_str}")
        
        if last_user_msg:
            # 長すぎる場合は要約
            if len(last_user_msg) > 100:
                last_user_msg = last_user_msg[:100] + "..."
            analysis.append(f"- 最新の指示: {last_user_msg}")
        
        return "\n".join(analysis)
    
    def _optimize_next_step_prompt(self) -> str:
        """長いnext_step_promptを最適化して重要な部分を保持"""
        if not self.next_step_prompt or len(self.next_step_prompt) <= 500:
            return self.next_step_prompt
        
        # プロンプトの構造を分析
        prompt = self.next_step_prompt
        
        # 重要な指示を検出（先頭部分と#または*で始まる行を保持）
        lines = prompt.split("\n")
        important_lines = []
        
        # 先頭の数行は常に保持
        header_lines = min(3, len(lines) // 4)
        important_lines.extend(lines[:header_lines])
        
        # 重要な指示（#または*で始まる行）を検出
        for line in lines[header_lines:]:
            stripped = line.strip()
            if stripped.startswith(("#", "*", "-", "1.", "2.", "3.", ">")):
                important_lines.append(line)
            elif "注意" in line or "重要" in line or "必須" in line:
                important_lines.append(line)
        
        # 末尾の指示も重要であることが多いので保持
        if len(lines) > header_lines + len(important_lines):
            footer_lines = min(3, len(lines) // 5)
            important_lines.extend(lines[-footer_lines:])
        
        # 最適化されたプロンプトを構築
        if len(important_lines) < len(lines) // 2:
            optimized = "\n".join(important_lines)
            # 重要部分の間に省略があることを示す
            if header_lines > 0 and len(important_lines) > header_lines:
                header = "\n".join(important_lines[:header_lines])
                rest = "\n".join(important_lines[header_lines:])
                optimized = f"{header}\n...(中略)...\n{rest}"
            return optimized
        
        # 十分な最適化ができない場合は元のプロンプトを返す
        return prompt
    
    def _estimate_context_length(self) -> int:
        """会話履歴のおおよそのコンテキスト長（文字数）を推定"""
        total_chars = 0
        for msg in self.memory.messages:
            # content部分の長さ
            if msg.content:
                total_chars += len(msg.content)
            
            # tool_calls部分の長さを推定
            if msg.tool_calls:
                for call in msg.tool_calls:
                    # function.nameとargumentsの長さを加算
                    total_chars += len(call.function.name) + len(call.function.arguments or "")
                    # その他のメタデータの長さも考慮
                    total_chars += 50  # id, typeなどを含む概算
            
            # ロールや名前などのメタデータ分も加算
            total_chars += 20  # 役割や名前のための追加文字数
        
        return total_chars
