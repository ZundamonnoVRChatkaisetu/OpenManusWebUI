import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from collections import defaultdict

# 翻訳辞書
translations = {
    "en-US": {
        "start_processing": "Starting processing...",
        "workspace_dir": "Workspace directory",
        "send_to_llm": "Sending to LLM",
        "receive_from_llm": "Received from LLM",
        "user_input": "User input",
        "ai_response": "AI response",
        "tool_execution": "Tool execution",
        "tool_result": "Tool result",
        "processing_stopped": "Processing stopped",
        "processing_completed": "Processing completed",
        "processing_error": "Processing error",
        "additional_instruction": "Additional instruction received",
    },
    "zh-CN": {
        "start_processing": "开始处理...",
        "workspace_dir": "工作区目录",
        "send_to_llm": "发送至LLM",
        "receive_from_llm": "接收自LLM",
        "user_input": "用户输入",
        "ai_response": "AI响应",
        "tool_execution": "工具执行",
        "tool_result": "工具结果",
        "processing_stopped": "处理已停止",
        "processing_completed": "处理已完成",
        "processing_error": "处理出错",
        "additional_instruction": "收到额外指示",
    },
    "ja-JP": {
        "start_processing": "処理を開始しています...",
        "workspace_dir": "ワークスペースディレクトリ",
        "send_to_llm": "LLMに送信",
        "receive_from_llm": "LLMから受信",
        "user_input": "ユーザー入力",
        "ai_response": "AI応答",
        "tool_execution": "ツール実行",
        "tool_result": "ツール結果",
        "processing_stopped": "処理が停止されました",
        "processing_completed": "処理が完了しました",
        "processing_error": "処理エラー",
        "additional_instruction": "追加指示を受信しました",
        "file_generation": "ファイルが生成されました",
    },
}

# 現在の言語設定
current_language = "ja-JP"

def set_language(language: str) -> None:
    """
    言語設定を更新
    
    Args:
        language: 言語コード
    """
    global current_language
    if language in translations:
        current_language = language


def t(key: str, params: Dict[str, Any] = None) -> str:
    """
    指定されたキーの翻訳を取得
    
    Args:
        key: 翻訳キー
        params: 翻訳パラメータ
        
    Returns:
        翻訳されたテキスト
    """
    if current_language not in translations:
        return key
    
    translation = translations[current_language].get(key, key)
    
    # パラメータ置換（簡易的な実装）
    if params:
        for param_key, param_value in params.items():
            translation = translation.replace(f"{{{param_key}}}", str(param_value))
    
    return translation


class ThinkingTracker:
    """
    思考ステップを追跡するクラス
    """
    # セッションIDごとの思考ステップ
    _thinking_steps: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    # セッションIDごとのコミュニケーションログ
    _communication_logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    # セッションIDごとのステータス
    _status: Dict[str, str] = {}
    
    # セッションIDごとの進捗情報
    _progress: Dict[str, Dict[str, Any]] = {}
    
    # セッションIDごとの一般ログ
    _logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    # WebSocket送信コールバック
    _ws_callbacks: Dict[str, Callable[[str], Awaitable[None]]] = {}
    
    # ファイル生成情報
    _generated_files: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    @classmethod
    def start_tracking(cls, session_id: str) -> None:
        """
        指定されたセッションの追跡を開始
        
        Args:
            session_id: セッションID
        """
        cls._thinking_steps[session_id] = []
        cls._communication_logs[session_id] = []
        cls._logs[session_id] = []
        cls._status[session_id] = "processing"
        cls._progress[session_id] = {
            "total": 100,
            "completed": 0,
            "current_task": "initialization",
        }
        cls._generated_files[session_id] = []
    
    @classmethod
    def add_thinking_step(cls, session_id: str, message: str, details: Any = None) -> None:
        """
        思考ステップを追加
        
        Args:
            session_id: セッションID
            message: ステップメッセージ
            details: 追加詳細（オプション）
        """
        step = {
            "message": message,
            "type": "reasoning",
            "details": details,
            "timestamp": time.time()
        }
        
        # 追加
        cls._thinking_steps[session_id].append(step)
        
        # 進捗状況更新
        if cls._progress[session_id]["total"] > 0:
            cls._progress[session_id]["completed"] = min(
                int(len(cls._thinking_steps[session_id]) / 10 * 100), 90
            )
            cls._progress[session_id]["current_task"] = message[:30] + "..." if len(message) > 30 else message
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "thinking_steps": [step]
        })
    
    @classmethod
    def add_communication(cls, session_id: str, direction: str, content: str) -> None:
        """
        通信ログを追加
        
        Args:
            session_id: セッションID
            direction: 通信方向（送信/受信）
            content: 通信内容
        """
        log = {
            "direction": direction,
            "content": content,
            "timestamp": time.time()
        }
        
        # 追加
        cls._communication_logs[session_id].append(log)
        
        # 思考ステップにも追加（表示用）
        cls.add_thinking_step(
            session_id, 
            f"{direction}: {content[:50]}{'...' if len(content) > 50 else ''}", 
            {"type": "communication", "content": content}
        )
    
    @classmethod
    def add_conclusion(cls, session_id: str, message: str) -> None:
        """
        結論ステップを追加
        
        Args:
            session_id: セッションID
            message: 結論メッセージ
        """
        # ステータス更新
        cls._status[session_id] = "completed"
        
        # 進捗状況更新
        cls._progress[session_id]["completed"] = 100
        cls._progress[session_id]["current_task"] = t("processing_completed")
        
        # 思考ステップに追加
        step = {
            "message": message,
            "type": "conclusion",
            "details": None,
            "timestamp": time.time()
        }
        
        cls._thinking_steps[session_id].append(step)
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "thinking_steps": [step],
            "status": "completed"
        })
    
    @classmethod
    def add_error(cls, session_id: str, message: str) -> None:
        """
        エラーステップを追加
        
        Args:
            session_id: セッションID
            message: エラーメッセージ
        """
        # ステータス更新
        cls._status[session_id] = "error"
        
        # 進捗状況更新
        cls._progress[session_id]["current_task"] = t("processing_error")
        
        # 思考ステップに追加
        step = {
            "message": message,
            "type": "error",
            "details": None,
            "timestamp": time.time()
        }
        
        cls._thinking_steps[session_id].append(step)
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "thinking_steps": [step],
            "status": "error"
        })
    
    @classmethod
    def mark_stopped(cls, session_id: str) -> None:
        """
        セッションを停止済みとしてマーク
        
        Args:
            session_id: セッションID
        """
        # ステータス更新
        cls._status[session_id] = "stopped"
        
        # 進捗状況更新
        cls._progress[session_id]["current_task"] = t("processing_stopped")
        
        # 思考ステップに追加
        step = {
            "message": t("processing_stopped"),
            "type": "stopped",
            "details": None,
            "timestamp": time.time()
        }
        
        cls._thinking_steps[session_id].append(step)
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "thinking_steps": [step],
            "status": "stopped"
        })
    
    @classmethod
    def add_log_entry(cls, session_id: str, log_entry: Dict[str, Any]) -> None:
        """
        一般ログエントリーを追加
        
        Args:
            session_id: セッションID
            log_entry: ログエントリー
        """
        # タイムスタンプがなければ追加
        if "timestamp" not in log_entry:
            log_entry["timestamp"] = time.time()
        
        # 追加
        cls._logs[session_id].append(log_entry)
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "logs": [log_entry]
        })
    
    @classmethod
    def add_file_generation(cls, session_id: str, file_info: Dict[str, Any]) -> None:
        """
        ファイル生成情報を追加
        
        Args:
            session_id: セッションID
            file_info: ファイル情報
        """
        # タイムスタンプがなければ追加
        if "timestamp" not in file_info:
            file_info["timestamp"] = time.time()
            
        # 追加
        cls._generated_files[session_id].append(file_info)
        
        # 思考ステップにも追加
        message = f"{t('file_generation')}: {file_info.get('filename', 'unknown')}"
        cls.add_thinking_step(
            session_id, 
            message,
            {"type": "file_generation", "filename": file_info.get("filename")}
        )
        
        # WebSocketに通知
        cls._notify_websocket(session_id, {
            "file_generation_event": file_info
        })
    
    @classmethod
    def get_thinking_steps(cls, session_id: str, start_index: int = 0) -> List[Dict[str, Any]]:
        """
        思考ステップを取得
        
        Args:
            session_id: セッションID
            start_index: 開始インデックス
            
        Returns:
            思考ステップのリスト
        """
        if session_id not in cls._thinking_steps:
            return []
        
        return cls._thinking_steps[session_id][start_index:]
    
    @classmethod
    def get_communication_logs(cls, session_id: str) -> List[Dict[str, Any]]:
        """
        通信ログを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            通信ログのリスト
        """
        if session_id not in cls._communication_logs:
            return []
        
        return cls._communication_logs[session_id]
    
    @classmethod
    def get_status(cls, session_id: str) -> str:
        """
        セッションのステータスを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            ステータス
        """
        return cls._status.get(session_id, "unknown")
    
    @classmethod
    def get_progress(cls, session_id: str) -> Dict[str, Any]:
        """
        進捗情報を取得
        
        Args:
            session_id: セッションID
            
        Returns:
            進捗情報
        """
        return cls._progress.get(session_id, {
            "total": 0,
            "completed": 0,
            "current_task": "unknown"
        })
    
    @classmethod
    def get_logs(cls, session_id: str, start_index: int = 0) -> List[Dict[str, Any]]:
        """
        ログを取得
        
        Args:
            session_id: セッションID
            start_index: 開始インデックス
            
        Returns:
            ログのリスト
        """
        if session_id not in cls._logs:
            return []
        
        return cls._logs[session_id][start_index:]
    
    @classmethod
    def get_generated_files(cls, session_id: str) -> List[Dict[str, Any]]:
        """
        生成されたファイル情報を取得
        
        Args:
            session_id: セッションID
            
        Returns:
            生成されたファイル情報のリスト
        """
        if session_id not in cls._generated_files:
            return []
        
        return cls._generated_files[session_id]
    
    @classmethod
    def register_ws_send_callback(cls, session_id: str, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        WebSocket送信コールバックを登録
        
        Args:
            session_id: セッションID
            callback: コールバック関数
        """
        cls._ws_callbacks[session_id] = callback
    
    @classmethod
    def unregister_ws_send_callback(cls, session_id: str) -> None:
        """
        WebSocket送信コールバックの登録を解除
        
        Args:
            session_id: セッションID
        """
        if session_id in cls._ws_callbacks:
            del cls._ws_callbacks[session_id]
    
    @classmethod
    def _notify_websocket(cls, session_id: str, data: Dict[str, Any]) -> None:
        """
        WebSocketに通知
        
        Args:
            session_id: セッションID
            data: 送信データ
        """
        if session_id in cls._ws_callbacks:
            callback = cls._ws_callbacks[session_id]
            
            # コールバックが非同期関数の場合、非同期でコールバック実行
            if asyncio.iscoroutinefunction(callback):
                asyncio.create_task(callback(json.dumps(data)))
            else:
                # 同期関数の場合はそのまま実行（これはあまり想定されていない）
                try:
                    callback(json.dumps(data))
                except Exception as e:
                    print(f"WebSocket notification failed: {e}")
