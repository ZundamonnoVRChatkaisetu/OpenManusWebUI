# -*- coding: utf-8 -*-

"""
思考跟踪器模块，实现Manus风格的任务进展日志系统
"""
import asyncio
import json
import threading
import time
from enum import Enum
from typing import Any, Dict, List, Optional


# 多语言消息翻译
TRANSLATIONS = {
    'zh-CN': {
        'start_processing': '开始处理用户请求',
        'workspace_dir': '工作区目录',
        'user_input': '用户输入',
        'init_agent': '初始化AI代理和任务流程',
        'analyze_request': '分析用户请求',
        'task_complete': '任务处理完成！已生成结果。',
        'current_step': '当前步骤',
        'initialization': '初始化',
        'completed': '已完成',
        'not_started': '未开始',
        'send_to_llm': '发送到LLM',
        'receive_from_llm': '从LLM接收',
        'create_task_plan': '创建任务执行计划',
        'start_execute_plan': '开始执行任务计划',
        'executing': '执行',
        'complete': '完成',
        'info': '信息',
        'warning': '警告',
        'error': '错误',
        'communication': '通信',
        'tool_usage': '使用工具',
        'terminal_command': '执行命令',
        'browser_operation': '浏览器操作',
        'file_operation': '文件操作',
        'api_request': 'API请求',
        'github_operation': 'GitHub操作',
        'database_operation': '数据库操作'
    },
    'en-US': {
        'start_processing': 'Start processing user request',
        'workspace_dir': 'Workspace directory',
        'user_input': 'User input',
        'init_agent': 'Initialize AI agent and task flow',
        'analyze_request': 'Analyze user request',
        'task_complete': 'Task processing completed! Results have been generated.',
        'current_step': 'Current step',
        'initialization': 'Initialization',
        'completed': 'Completed',
        'not_started': 'Not started',
        'send_to_llm': 'Send to LLM',
        'receive_from_llm': 'Receive from LLM',
        'create_task_plan': 'Create task execution plan',
        'start_execute_plan': 'Start executing task plan',
        'executing': 'Executing',
        'complete': 'Complete',
        'info': 'Info',
        'warning': 'Warning',
        'error': 'Error',
        'communication': 'Communication',
        'tool_usage': 'Using Tool',
        'terminal_command': 'Terminal Command',
        'browser_operation': 'Browser Operation',
        'file_operation': 'File Operation',
        'api_request': 'API Request',
        'github_operation': 'GitHub Operation',
        'database_operation': 'Database Operation'
    },
    'ja-JP': {
        'start_processing': 'ユーザーリクエストの処理を開始',
        'workspace_dir': 'ワークスペースディレクトリ',
        'user_input': 'ユーザー入力',
        'init_agent': 'AIエージェントとタスクフローを初期化',
        'analyze_request': 'ユーザーリクエストを分析',
        'task_complete': 'タスク処理が完了しました！結果が生成されました。',
        'current_step': '現在のステップ',
        'initialization': '初期化中',
        'completed': '完了',
        'not_started': '未開始',
        'send_to_llm': 'LLMへ送信',
        'receive_from_llm': 'LLMから受信',
        'create_task_plan': 'タスク実行計画を作成',
        'start_execute_plan': 'タスク計画の実行を開始',
        'executing': '実行中',
        'complete': '完了',
        'info': '情報',
        'warning': '警告',
        'error': 'エラー',
        'communication': '通信',
        'tool_usage': 'ツール使用',
        'terminal_command': 'ターミナルコマンド',
        'browser_operation': 'ブラウザ操作',
        'file_operation': 'ファイル操作',
        'api_request': 'APIリクエスト',
        'github_operation': 'GitHub操作',
        'database_operation': 'データベース操作'
    }
}

# 現在の言語設定（デフォルトは中国語）
CURRENT_LANGUAGE = 'zh-CN'

# 言語設定を変更する関数
def set_language(lang):
    """言語設定を変更する"""
    global CURRENT_LANGUAGE
    if lang in TRANSLATIONS:
        CURRENT_LANGUAGE = lang
        return True
    return False

# 翻訳を取得する関数
def t(key, lang=None):
    """指定されたキーの翻訳を返す"""
    language = lang or CURRENT_LANGUAGE
    if language in TRANSLATIONS and key in TRANSLATIONS[language]:
        return TRANSLATIONS[language][key]
    # 言語またはキーが存在しない場合、中国語の翻訳を返す
    return TRANSLATIONS['zh-CN'].get(key, key)


# 全局思考步骤存储
class ThinkingStep:
    """表示一个思考步骤"""

    def __init__(
        self, message: str, step_type: str = "thinking", details: Optional[str] = None
    ):
        self.message = message
        self.step_type = step_type  # thinking, conclusion, error, communication, tool_usage
        self.details = details  # 用于存储通信内容或详细信息
        self.timestamp = time.time()


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    THINKING = "thinking"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


class ThinkingTracker:
    """思考跟踪器，用于记录和管理AI思考过程"""

    # 类变量，存储所有会话的思考步骤
    _session_steps: Dict[str, List[ThinkingStep]] = {}
    _session_status: Dict[str, TaskStatus] = {}
    _session_progress: Dict[str, Dict[str, Any]] = {}  # 存储进度信息
    _session_logs: Dict[str, List[Dict]] = {}  # 存储日志内容
    _ws_send_callbacks: Dict[str, Any] = {}  # 存储WebSocket发送回调函数
    _lock = threading.Lock()

    @classmethod
    def register_ws_send_callback(cls, session_id: str, callback: Any) -> None:
        """注册WebSocket发送回调函数"""
        with cls._lock:
            cls._ws_send_callbacks[session_id] = callback

    @classmethod
    def unregister_ws_send_callback(cls, session_id: str) -> None:
        """取消注册WebSocket发送回调函数"""
        with cls._lock:
            if session_id in cls._ws_send_callbacks:
                del cls._ws_send_callbacks[session_id]

    @classmethod
    def start_tracking(cls, session_id: str) -> None:
        """开始追踪一个会话的思考过程"""
        with cls._lock:
            cls._session_steps[session_id] = []
            cls._session_status[session_id] = TaskStatus.THINKING
            cls._session_progress[session_id] = {
                "current_step": t('initialization'),
                "total_steps": 0,
                "completed_steps": 0,
                "percentage": 0,
            }

    @classmethod
    def add_thinking_step(
        cls, session_id: str, message: str, details: Optional[str] = None
    ) -> None:
        """添加一个思考步骤"""
        step = ThinkingStep(message, "thinking", details)
        with cls._lock:
            if session_id in cls._session_steps:
                cls._session_steps[session_id].append(step)

                # 更新进度信息
                if session_id in cls._session_progress:
                    progress = cls._session_progress[session_id]
                    progress["current_step"] = message

                    # Attempt to extract step number and total steps from the message
                    import re

                    match = re.search(r"Executing step (\\d+)/(\\d+)", message)
                    if match:
                        current_step_num = int(match.group(1))
                        total_steps = int(match.group(2))
                        progress["total_steps"] = total_steps
                        progress["completed_steps"] = (
                            current_step_num - 1
                        )  # Mark previous as complete

                    if progress["total_steps"] > 0:
                        progress["percentage"] = min(
                            int(
                                100
                                * progress["completed_steps"]
                                / progress["total_steps"]
                            ),
                            99,
                        )

    @classmethod
    def add_communication(cls, session_id: str, direction: str, content: str) -> None:
        """添加一个通信记录

        Args:
            session_id: 会话ID
            direction: 通信方向，如 "发送到LLM"、"从LLM接收"
            content: 通信内容
        """
        # 通信方向多言語対応
        if direction == "发送到LLM":
            direction = t('send_to_llm')
        elif direction == "从LLM接收":
            direction = t('receive_from_llm')
        elif direction == "用户输入":
            direction = t('user_input')

        message = f"{direction} {t('communication')}"
        step = ThinkingStep(message, "communication", content)
        with cls._lock:
            if session_id in cls._session_steps:
                cls._session_steps[session_id].append(step)

    @classmethod
    def add_tool_usage(
        cls, session_id: str, tool_type: str, action: str, details: Optional[str] = None
    ) -> None:
        """添加一个工具使用记录

        Args:
            session_id: 会话ID
            tool_type: 工具类型，如 "terminal", "browser", "file", "api", "github"
            action: 操作，如 "execute", "navigate", "read", "write", "get", "post"
            details: 操作详情，如命令内容、URL等
        """
        # 工具类型和操作的多语言处理
        tool_type_key = {
            "terminal": "terminal_command",
            "browser": "browser_operation", 
            "file": "file_operation",
            "api": "api_request",
            "github": "github_operation",
            "database": "database_operation"
        }.get(tool_type, "tool_usage")
        
        # 创建消息
        message = f"{t(tool_type_key)}: {action}"
        step = ThinkingStep(message, "tool_usage", details)
        with cls._lock:
            if session_id in cls._session_steps:
                cls._session_steps[session_id].append(step)

    @classmethod
    def update_progress(
        cls, session_id: str, total_steps: int = None, current_step: str = None
    ):
        """更新任务进度信息"""
        with cls._lock:
            if session_id in cls._session_progress:
                progress = cls._session_progress[session_id]

                if total_steps is not None:
                    progress["total_steps"] = total_steps

                if current_step is not None:
                    progress["current_step"] = current_step

                # 重新计算百分比
                if progress["total_steps"] > 0:
                    progress["percentage"] = min(
                        int(
                            100 * progress["completed_steps"] / progress["total_steps"]
                        ),
                        99,  # 最多到99%，完成时才到100%
                    )

    @classmethod
    def add_conclusion(
        cls, session_id: str, message: str, details: Optional[str] = None
    ) -> None:
        """添加一个结论"""
        step = ThinkingStep(message, "conclusion", details)
        with cls._lock:
            if session_id in cls._session_steps:
                cls._session_steps[session_id].append(step)
                cls._session_status[session_id] = TaskStatus.COMPLETED

                # 更新进度为100%
                if session_id in cls._session_progress:
                    progress = cls._session_progress[session_id]
                    progress["percentage"] = 100
                    progress["current_step"] = t('completed')

    @classmethod
    def add_error(cls, session_id: str, message: str) -> None:
        """添加一个错误信息"""
        step = ThinkingStep(message, "error")
        with cls._lock:
            if session_id in cls._session_steps:
                cls._session_steps[session_id].append(step)
                cls._session_status[session_id] = TaskStatus.ERROR

    @classmethod
    def mark_stopped(cls, session_id: str) -> None:
        """标记任务已停止"""
        with cls._lock:
            if session_id in cls._session_status:
                cls._session_status[session_id] = TaskStatus.STOPPED

    @classmethod
    def get_thinking_steps(cls, session_id: str, start_index: int = 0) -> List[Dict]:
        """获取指定会话的思考步骤"""
        with cls._lock:
            if session_id not in cls._session_steps:
                return []

            steps = cls._session_steps[session_id][start_index:]
            return [
                {
                    "message": step.message,
                    "type": step.step_type,
                    "details": step.details,
                    "timestamp": step.timestamp,
                }
                for step in steps
            ]

    @classmethod
    def get_progress(cls, session_id: str) -> Dict[str, Any]:
        """获取任务进度信息"""
        with cls._lock:
            if session_id not in cls._session_progress:
                return {
                    "current_step": t('not_started'),
                    "total_steps": 0,
                    "completed_steps": 0,
                    "percentage": 0,
                }
            return cls._session_progress[session_id].copy()

    @classmethod
    def get_status(cls, session_id: str) -> str:
        """获取任务状态"""
        with cls._lock:
            if session_id not in cls._session_status:
                return TaskStatus.PENDING.value
            return cls._session_status[session_id].value

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        """清除指定会话的记录"""
        with cls._lock:
            if session_id in cls._session_steps:
                del cls._session_steps[session_id]
            if session_id in cls._session_status:
                del cls._session_status[session_id]
            if session_id in cls._session_progress:
                del cls._session_progress[session_id]
            if session_id in cls._session_logs:
                del cls._session_logs[session_id]

    @classmethod
    def add_log_entry(cls, session_id: str, entry: Dict) -> None:
        """添加一个日志条目"""
        with cls._lock:
            if session_id not in cls._session_logs:
                cls._session_logs[session_id] = []

            # 确保日志条目有必要的字段
            if "timestamp" not in entry:
                entry["timestamp"] = time.time()

            cls._session_logs[session_id].append(entry)

            # 根据日志级别自动添加对应的思考步骤，更详细地处理日志内容
            msg = entry.get("message", "")
            if entry.get("level") == "INFO":
                # 针对特定类型的日志内容生成更有意义的思考步骤
                if "开始执行" in msg:
                    cls.add_thinking_step(
                        session_id, f"{t('start_processing')}: {msg.replace('开始执行: ', '')}"
                    )
                elif "执行步骤" in msg or "步骤" in msg:
                    # 尝试提取步骤信息
                    cls.add_thinking_step(session_id, f"{t('executing')}: {msg}")
                elif "完成" in msg or "成功" in msg:
                    cls.add_thinking_step(session_id, f"{t('complete')}: {msg}")
                else:
                    cls.add_thinking_step(session_id, f"{t('info')}: {msg}")
                    
                # ツール使用の検出と記録
                cls._detect_and_add_tool_usage(session_id, msg)
                    
            elif entry.get("level") == "ERROR":
                cls.add_error(session_id, f"{t('error')}: {msg}")
            elif entry.get("level") == "WARNING":
                cls.add_thinking_step(session_id, f"{t('warning')}: {msg}", "warning")

            # 识别进度信息并更新
            cls._update_progress_from_log(session_id, msg)

        # 添加日志后立即通知 WebSocket 客户端
        cls._notify_ws_log_update(session_id, entry)
        
    @classmethod
    def _detect_and_add_tool_usage(cls, session_id: str, message: str):
        """ログメッセージからツール使用を検出して記録する"""
        import re
        
        # ターミナルコマンド実行の検出
        terminal_pattern = r'実行(?:中|します).*?`([^`]+)`|command[:\s]+["|\'"]?([^"|\'"\s]+)["|\'"]?'
        match = re.search(terminal_pattern, message, re.IGNORECASE)
        if match:
            command = match.group(1) or match.group(2)
            cls.add_tool_usage(session_id, "terminal", "execute", command)
            return
            
        # ブラウザ操作の検出
        browser_pattern = r'URL[:\s]+["|\'"]?(https?:\/\/[^\s"\']+)["|\'"]?|ブラウザで.*?開(?:きます|いています).*?["|\'"]?(https?:\/\/[^\s"\']+)["|\'"]?'
        match = re.search(browser_pattern, message, re.IGNORECASE)
        if match:
            url = match.group(1) or match.group(2)
            cls.add_tool_usage(session_id, "browser", "navigate", url)
            return
            
        # ファイル操作の検出
        file_pattern = r'ファイル[:\s]+["|\'"]?([^"\'\s]+\.[a-zA-Z0-9]+)["|\'"]?|reading\sfile[:\s]+["|\'"]?([^"\'\s]+\.[a-zA-Z0-9]+)["|\'"]?'
        match = re.search(file_pattern, message, re.IGNORECASE)
        if match:
            filename = match.group(1) or match.group(2)
            action = "read"
            if "作成" in message or "create" in message.lower():
                action = "create"
            elif "書き込み" in message or "write" in message.lower():
                action = "write"
            elif "更新" in message or "update" in message.lower():
                action = "update"
            elif "削除" in message or "delete" in message.lower():
                action = "delete"
            cls.add_tool_usage(session_id, "file", action, filename)
            return
            
        # API操作の検出
        api_pattern = r'API[:\s]+["|\'"]?([^"\']+)["|\'"]?|endpoint[:\s]+["|\'"]?([^"\']+)["|\'"]?'
        match = re.search(api_pattern, message, re.IGNORECASE)
        if match:
            endpoint = match.group(1) or match.group(2)
            method = "GET"
            if "POST" in message or "作成" in message or "create" in message.lower():
                method = "POST"
            elif "PUT" in message or "更新" in message or "update" in message.lower():
                method = "PUT"
            elif "DELETE" in message or "削除" in message or "delete" in message.lower():
                method = "DELETE"
            cls.add_tool_usage(session_id, "api", method, endpoint)
            return
            
        # GitHub操作の検出
        github_pattern = r'GitHub.*?リポジトリ[:\s]+["|\'"]?([^"\']+)["|\'"]?|clone.*?["|\'"]?(https:\/\/github\.com\/[^"\']+)["|\'"]?'
        match = re.search(github_pattern, message, re.IGNORECASE)
        if match:
            repo = match.group(1) or match.group(2)
            cls.add_tool_usage(session_id, "github", "access", repo)
            return

    @classmethod
    def _notify_ws_log_update(cls, session_id: str, log_entry: Dict):
        """通知 WebSocket 客户端有新的日志条目"""
        with cls._lock:
            if session_id in cls._ws_send_callbacks:
                callback = cls._ws_send_callbacks[session_id]
                try:
                    # 使用 asyncio.create_task 确保非阻塞
                    asyncio.create_task(
                        callback(
                            json.dumps(
                                {
                                    "status": cls.get_status(session_id),
                                    "logs": [log_entry],
                                }
                            )
                        )
                    )
                except Exception as e:
                    print(f"WebSocket 发送回调失败: {str(e)}")

    @classmethod
    def _update_progress_from_log(cls, session_id: str, message: str):
        """从日志消息中提取进度信息并更新"""
        import re

        # 尝试从日志中提取步骤信息
        step_match = re.search(r"步骤 (\\d+)/(\\d+)", message) or re.search(
            r"Step (\\d+)/(\\d+)", message
        )
        if step_match and session_id in cls._session_progress:
            current_step = int(step_match.group(1))
            total_steps = int(step_match.group(2))
            progress = cls._session_progress[session_id]

            progress["current_step"] = message
            progress["total_steps"] = total_steps
            progress["completed_steps"] = current_step - 1

            # 重新计算百分比
            if total_steps > 0:
                progress["percentage"] = min(
                    int(100 * progress["completed_steps"] / total_steps),
                    99,  # 最多到99%，完成时才到100%
                )

    @classmethod
    def add_log_entries(cls, session_id: str, entries: List[Dict]) -> None:
        """批量添加日志条目"""
        for entry in entries:
            cls.add_log_entry(session_id, entry)

    @classmethod
    def get_logs(cls, session_id: str, start_index: int = 0) -> List[Dict]:
        """获取指定会话的日志条目"""
        with cls._lock:
            if session_id not in cls._session_logs:
                return []
            return cls._session_logs[session_id][start_index:]


# 预定义的思考步骤模板
RESEARCH_STEPS = [
    "分析问题需求和上下文",
    "确定搜索关键词",
    "检索相关知识库和资料",
    "分析和整理检索到的信息",
    "评估可行的解决方案",
    "整合信息并构建解决框架",
    "生成最终回答",
]

CODING_STEPS = [
    "分析代码需求和功能规格",
    "设计代码结构和接口",
    "开发核心算法逻辑",
    "编写主要功能模块",
    "实现边界情况和错误处理",
    "进行代码测试和调试",
    "优化代码性能和可读性",
    "完成代码和文档",
]

WRITING_STEPS = [
    "收集写作主题的相关资料...",
    "构思内容大纲和关键点...",
    "撰写初稿内容...",
    "完善论述和事实核查...",
    "润色语言和格式...",
]

# 任务类型到预定义步骤的映射
TASK_TYPE_STEPS = {
    "research": RESEARCH_STEPS,
    "coding": CODING_STEPS,
    "writing": WRITING_STEPS,
}


def generate_thinking_steps(
    session_id: str,
    task_type: str = "research",
    task_description: str = "",
    show_communication: bool = True,
) -> None:
    """生成一系列思考步骤，用于模拟AI思考过程"""
    steps = TASK_TYPE_STEPS.get(task_type, RESEARCH_STEPS)

    # 如果有描述，添加更具体的步骤
    if task_description:
        specific_steps = [
            f"研究{task_description}的相关信息",
            f"分析{task_description}的关键点",
            f"整理{task_description}的解决方案",
        ]
        steps = specific_steps + steps

    ThinkingTracker.start_tracking(session_id)
    ThinkingTracker.update_progress(
        session_id, total_steps=len(steps) + 2
    )  # +2为开始和结束步骤

    # 添加初始步骤
    ThinkingTracker.add_thinking_step(
        session_id, f"{t('start_processing')}: {task_description if task_description else '新请求'}"
    )

    # 模拟每隔一段时间添加一个思考步骤
    for step in steps:
        ThinkingTracker.add_thinking_step(session_id, step)

        # 模拟与LLM的通信
        if show_communication:
            # 模拟向LLM发送请求
            ThinkingTracker.add_communication(session_id, t('send_to_llm'), f"请帮我{step}...")

            # 模拟接收LLM回复
            ThinkingTracker.add_communication(
                session_id, t('receive_from_llm'), f"我已完成{step}。这是相关结果: [详细信息]"
            )

    # 添加结论
    ThinkingTracker.add_conclusion(session_id, t('task_complete'))
