import asyncio
import json
import os
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.utils.language_utils import detect_language, get_template
from app.web.enhanced_agent_factory import create_enhanced_agent
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.web.log_handler import capture_session_logs, get_logs
from app.web.log_parser import get_all_logs_info, get_latest_log_info, parse_log_file
from app.web.thinking_tracker import ThinkingTracker, set_language, t
from app.web.models import (
    Project, ProjectCreate, ProjectUpdate, 
    Session, SessionCreate, SessionUpdate,
    MessageCreate, ChatRequest, ChatResponse,
    ProjectWithSessions, SessionWithMessages
)
import app.web.database as db

# MCP関連ツールのインポート
from app.web.tools.routes import router as tools_router
# 生成ファイル取得APIルーターのインポート
from app.web.routes.generated_files import router as generated_files_router

# ロギング設定ミドルウェアのインポート
from app.web.logging_config import configure_app_logging, setup_logging

# 控制是否自动打开浏览器 (读取环境变量，默认为True)
AUTO_OPEN_BROWSER = os.environ.get("AUTO_OPEN_BROWSER", "1") == "1"
last_opened = False  # 跟踪浏览器是否已打开

app = FastAPI(title="OpenManus Web")

# ロギング設定の初期化
setup_logging()
configure_app_logging(app, min_duration_ms=1000)  # 1秒以上かかるリクエストのみログに記録

# ツールAPIルーターの登録
app.include_router(tools_router)
# 生成ファイル取得APIルーターの登録
app.include_router(generated_files_router)

# 获取当前文件所在目录
current_dir = Path(__file__).parent
# 设置静态文件目录
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")
# 设置模板目录
templates = Jinja2Templates(directory=current_dir / "templates")

# 存储活跃的会话及其结果
active_sessions: Dict[str, dict] = {}

# 存储任务取消事件
cancel_events: Dict[str, asyncio.Event] = {}

# 存储处理中任务的上下文信息 - 追加指示用
active_tasks: Dict[str, dict] = {}

# 创建工作区根目录
WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)

# プロジェクト専用ワークスペース
PROJECT_WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "project_workspace"
PROJECT_WORKSPACE_ROOT.mkdir(exist_ok=True)

# 日志目录
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 导入日志监视器
from app.utils.log_monitor import LogFileMonitor


# 存储活跃的日志监视器
active_log_monitors: Dict[str, LogFileMonitor] = {}


# 创建工作区目录的函数
def create_workspace(session_id: str, project_id: Optional[str] = None) -> Path:
    """为会话创建工作区目录"""
    # プロジェクトIDが指定されている場合、プロジェクト専用ワークスペースを使用
    if project_id:
        # プロジェクト用ディレクトリを確保
        project_dir = PROJECT_WORKSPACE_ROOT / f"project_{project_id[:8]}"
        project_dir.mkdir(exist_ok=True)
        
        # セッション用サブディレクトリを作成
        session_dir = project_dir / f"session_{session_id[:8]}"
        session_dir.mkdir(exist_ok=True)
        
        return session_dir
    
    # 従来の方法（プロジェクトIDなし）
    job_id = f"job_{session_id[:8]}"
    workspace_dir = WORKSPACE_ROOT / job_id
    workspace_dir.mkdir(exist_ok=True)
    return workspace_dir


@app.on_event("startup")
async def startup_event():
    """启动事件：应用启动时自动打开浏览器"""
    global last_opened
    if AUTO_OPEN_BROWSER and not last_opened:
        # 延迟1秒以确保服务已经启动
        threading.Timer(1.0, lambda: webbrowser.open("http://localhost:8000")).start()
        print("🌐 自动打开浏览器...")
        last_opened = True


class SessionRequest(BaseModel):
    prompt: str


class LanguageRequest(BaseModel):
    language: str


class AdditionalInstructionRequest(BaseModel):
    instruction: str


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """主页入口 - テンプレートシステムを使用してHTMLを返す"""
    return templates.TemplateResponse("connected_interface.html", {"request": request})


@app.get("/original", response_class=HTMLResponse)
async def get_original_interface(request: Request):
    """原始界面入口"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/connected", response_class=HTMLResponse)
async def get_connected_interface(request: Request):
    """连接后端的新界面入口 (テンプレートシステムを使用)"""
    return templates.TemplateResponse("connected_interface.html", {"request": request})


@app.post("/api/set_language")
async def update_language(lang_req: LanguageRequest):
    """更新后端语言设置"""
    language = lang_req.language
    if language in ["zh-CN", "en-US", "ja-JP"]:
        # 更新thinking_tracker的语言设置
        set_language(language)
        return {"success": True, "language": language}
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")


# プロジェクト関連エンドポイント
@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """プロジェクト一覧を取得"""
    projects = db.get_all_projects()
    
    # SQLiteのタイムスタンプを日時に変換
    for project in projects:
        project["created_at"] = datetime.fromisoformat(project["created_at"])
        project["updated_at"] = datetime.fromisoformat(project["updated_at"])
    
    return projects

@app.post("/api/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """新規プロジェクトを作成"""
    project_id = str(uuid.uuid4())
    success = db.create_project(project_id, project.name, project.instructions)
    
    if not success:
        raise HTTPException(status_code=500, detail="プロジェクト作成に失敗しました")
    
    project_data = db.get_project(project_id)
    
    if not project_data:
        raise HTTPException(status_code=404, detail="作成したプロジェクトが見つかりません")
    
    # SQLiteのタイムスタンプを日時に変換
    project_data["created_at"] = datetime.fromisoformat(project_data["created_at"])
    project_data["updated_at"] = datetime.fromisoformat(project_data["updated_at"])
    
    # プロジェクト用ディレクトリを作成
    project_dir = PROJECT_WORKSPACE_ROOT / f"project_{project_id[:8]}"
    project_dir.mkdir(exist_ok=True)
    
    return project_data

@app.get("/api/projects/{project_id}", response_model=ProjectWithSessions)
async def get_project(project_id: str):
    """プロジェクト詳細を取得"""
    project = db.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    
    # SQLiteのタイムスタンプを日時に変換
    project["created_at"] = datetime.fromisoformat(project["created_at"])
    project["updated_at"] = datetime.fromisoformat(project["updated_at"])
    
    # プロジェクトに属するセッションを取得
    sessions = db.get_project_sessions(project_id)
    
    # セッションの日時変換
    for session in sessions:
        session["created_at"] = datetime.fromisoformat(session["created_at"])
    
    project["sessions"] = sessions
    
    return project

@app.put("/api/projects/{project_id}", response_model=Project)
async def update_project_endpoint(project_id: str, project_update: ProjectUpdate):
    """プロジェクトを更新"""
    project = db.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    
    success = db.update_project(
        project_id, 
        project_update.name, 
        project_update.instructions
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="プロジェクト更新に失敗しました")
    
    updated_project = db.get_project(project_id)
    
    # SQLiteのタイムスタンプを日時に変換
    updated_project["created_at"] = datetime.fromisoformat(updated_project["created_at"])
    updated_project["updated_at"] = datetime.fromisoformat(updated_project["updated_at"])
    
    return updated_project

@app.delete("/api/projects/{project_id}")
async def delete_project_endpoint(project_id: str):
    """プロジェクトを削除"""
    project = db.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    
    success = db.delete_project(project_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="プロジェクト削除に失敗しました")
    
    return {"success": True}

# セッション関連エンドポイント
@app.post("/api/projects/{project_id}/sessions", response_model=Session)
async def create_session_endpoint(project_id: str, session_create: SessionCreate):
    """新規セッションを作成"""
    project = db.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    
    session_id = str(uuid.uuid4())
    
    # プロジェクト専用のワークスペースディレクトリを作成
    workspace_dir = create_workspace(session_id, project_id)
    workspace_path = str(workspace_dir)
    
    success = db.create_session(
        session_id, 
        project_id, 
        session_create.title, 
        workspace_path
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="セッション作成に失敗しました")
    
    session_data = db.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="作成したセッションが見つかりません")
    
    # SQLiteのタイムスタンプを日時に変換
    session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
    
    return session_data

@app.get("/api/sessions/{session_id}", response_model=SessionWithMessages)
async def get_session_endpoint(session_id: str):
    """セッション詳細を取得"""
    session = db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    # SQLiteのタイムスタンプを日時に変換
    session["created_at"] = datetime.fromisoformat(session["created_at"])
    
    # セッションに属するメッセージを取得
    messages = db.get_session_messages(session_id)
    
    # メッセージの日時変換
    for message in messages:
        message["created_at"] = datetime.fromisoformat(message["created_at"])
    
    session["messages"] = messages
    
    return session

@app.put("/api/sessions/{session_id}", response_model=Session)
async def update_session_endpoint(session_id: str, session_update: SessionUpdate):
    """セッションを更新"""
    session = db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    success = db.update_session(
        session_id, 
        session_update.title
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="セッション更新に失敗しました")
    
    updated_session = db.get_session(session_id)
    
    # SQLiteのタイムスタンプを日時に変換
    updated_session["created_at"] = datetime.fromisoformat(updated_session["created_at"])
    
    return updated_session

@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """セッションを削除"""
    session = db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    success = db.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="セッション削除に失敗しました")
    
    return {"success": True}

@app.post("/api/chat")
async def create_chat_session(
    chat_req: ChatRequest, background_tasks: BackgroundTasks
):
    # ユーザーがプロジェクトとセッションを指定した場合はそれを使用
    project_id = chat_req.project_id
    session_id = chat_req.session_id
    
    # セッションIDがある場合は既存セッションを使用
    if session_id:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="指定されたセッションが見つかりません")
        
        project_id = session["project_id"]
    
    # プロジェクトIDがある場合は新しいセッションを作成
    elif project_id:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="指定されたプロジェクトが見つかりません")
        
        # 新しいセッションを作成
        session_id = str(uuid.uuid4())
        
        # セッションのタイトルを設定（デフォルトはプロンプトの最初の20文字）
        title = chat_req.prompt[:20] + ("..." if len(chat_req.prompt) > 20 else "")
        
        # プロジェクト専用のワークスペースディレクトリを作成
        workspace_dir = create_workspace(session_id, project_id)
        workspace_path = str(workspace_dir)
        
        # セッションをデータベースに保存
        db.create_session(session_id, project_id, title, workspace_path)
    
    # どちらも指定がない場合は新しいプロジェクトと新しいセッションを作成
    else:
        # 新しいプロジェクトを作成
        project_id = str(uuid.uuid4())
        project_name = "プロジェクト " + datetime.now().strftime("%Y-%m-%d %H:%M")
        db.create_project(project_id, project_name)
        
        # プロジェクト用ディレクトリを作成
        project_dir = PROJECT_WORKSPACE_ROOT / f"project_{project_id[:8]}"
        project_dir.mkdir(exist_ok=True)
        
        # 新しいセッションを作成
        session_id = str(uuid.uuid4())
        title = chat_req.prompt[:20] + ("..." if len(chat_req.prompt) > 20 else "")
        
        # プロジェクト専用のワークスペースディレクトリを作成
        workspace_dir = create_workspace(session_id, project_id)
        workspace_path = str(workspace_dir)
        
        # セッションをデータベースに保存
        db.create_session(session_id, project_id, title, workspace_path)
    
    # 既存のコードと互換性を持たせるための処理
    active_sessions[session_id] = {
        "status": "processing",
        "result": None,
        "log": [],
        "workspace": None,
    }

    # 创建取消事件
    cancel_events[session_id] = asyncio.Event()

    # セッションのワークスペースパスを取得
    session = db.get_session(session_id)
    workspace_path = session["workspace_path"]
    
    # ユーザーメッセージをデータベースに保存
    message_id = str(uuid.uuid4())
    db.create_message(message_id, session_id, "user", chat_req.prompt)
    
    # 既存のactive_sessionsを更新
    workspace_dir = Path(workspace_path)
    active_sessions[session_id]["workspace"] = workspace_path
    
    # タスク上下文情報を保存
    active_tasks[session_id] = {
        "original_prompt": chat_req.prompt,
        "additional_instructions": [],
        "project_id": project_id,
        "modified": False
    }

    background_tasks.add_task(process_prompt, session_id, chat_req.prompt, project_id)
    return {
        "session_id": session_id,
        "project_id": project_id,
        "workspace": workspace_path,
    }


@app.post("/api/chat/{session_id}/add_instruction")
async def add_instruction(session_id: str, instruction_req: AdditionalInstructionRequest):
    """追加指示を現在実行中のタスクに追加する"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if active_sessions[session_id]["status"] != "processing":
        raise HTTPException(status_code=400, detail="Session is not in processing state")
    
    # 追加指示をタスク上下文に保存
    if session_id in active_tasks:
        active_tasks[session_id]["additional_instructions"].append(instruction_req.instruction)
        active_tasks[session_id]["modified"] = True
        
        # データベースに追加指示を保存
        message_id = str(uuid.uuid4())
        db.create_message(message_id, session_id, "user", instruction_req.instruction)
        
        # ログに追加
        ThinkingTracker.add_thinking_step(
            session_id, 
            f"追加指示を受信しました: {instruction_req.instruction[:50]}{'...' if len(instruction_req.instruction) > 50 else ''}"
        )
        
        return {"success": True, "message": "Instruction added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Task context not found")


@app.get("/api/chat/{session_id}")
async def get_chat_result(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # 使用新的日志处理模块获取日志
    session = active_sessions[session_id]
    session["log"] = get_logs(session_id)

    return session


@app.post("/api/chat/{session_id}/stop")
async def stop_processing(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in cancel_events:
        cancel_events[session_id].set()

    active_sessions[session_id]["status"] = "stopped"
    active_sessions[session_id]["result"] = "処理がユーザーによって停止されました"

    return {"status": "stopped"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await websocket.accept()

        if session_id not in active_sessions:
            await websocket.send_text(json.dumps({"error": "Session not found"}))
            await websocket.close()
            return

        session = active_sessions[session_id]

        # 注册 WebSocket 发送回调函数
        async def ws_send(message: str):
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"WebSocket 发送消息失败: {str(e)}")

        ThinkingTracker.register_ws_send_callback(session_id, ws_send)

        # 初始状态通知中添加日志信息
        await websocket.send_text(
            json.dumps(
                {
                    "status": session["status"],
                    "log": session["log"],
                    "thinking_steps": ThinkingTracker.get_thinking_steps(session_id),
                    "logs": ThinkingTracker.get_logs(session_id),  # 添加日志信息
                }
            )
        )

        # 获取工作区名称(job_id) - 优先从环境变量获取
        job_id = None
        # 首先检查当前会话的工作空间关联
        if "workspace" in session:
            job_id = session["workspace"]

        # 如果当前没有日志监控器，则创建一个
        if session_id not in active_log_monitors and job_id:
            log_path = LOGS_DIR / f"{job_id}.log"
            if log_path.exists():
                log_monitor = LogFileMonitor(job_id)
                log_monitor.start_monitoring()
                active_log_monitors[session_id] = log_monitor

        # 跟踪日志更新
        last_log_entries = []
        if job_id and session_id in active_log_monitors:
            last_log_entries = active_log_monitors[session_id].get_log_entries()

        # 等待结果更新
        last_log_count = 0
        last_thinking_step_count = 0
        last_tracker_log_count = 0  # 添加ThinkingTracker日志计数
        
        # 生成ファイル情報の追跡
        last_generated_files_count = 0

        while session["status"] == "processing":
            await asyncio.sleep(0.2)  # 降低检查间隔提高实时性

            # 检查系统日志更新 (新增)
            if job_id and session_id in active_log_monitors:
                current_log_entries = active_log_monitors[session_id].get_log_entries()
                if len(current_log_entries) > len(last_log_entries):
                    new_logs = current_log_entries[len(last_log_entries) :]
                    await websocket.send_text(
                        json.dumps(
                            {
                                "status": session["status"],
                                "system_logs": new_logs,
                                # 添加一个chat_logs字段，将系统日志作为聊天消息发送
                                "chat_logs": new_logs,
                            }
                        )
                    )
                    last_log_entries = current_log_entries

            # 检查日志更新
            current_log_count = len(session["log"])
            if current_log_count > last_log_count:
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": session["status"],
                            "log": session["log"][last_log_count:],
                        }
                    )
                )
                last_log_count = current_log_count

            # 检查思考步骤更新
            thinking_steps = ThinkingTracker.get_thinking_steps(session_id)
            current_thinking_step_count = len(thinking_steps)
            if current_thinking_step_count > last_thinking_step_count:
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": session["status"],
                            "thinking_steps": thinking_steps[last_thinking_step_count:],
                        }
                    )
                )
                last_thinking_step_count = current_thinking_step_count

            # 检查ThinkingTracker日志更新
            tracker_logs = ThinkingTracker.get_logs(session_id)
            current_tracker_log_count = len(tracker_logs)
            if current_tracker_log_count > last_tracker_log_count:
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": session["status"],
                            "logs": tracker_logs[last_tracker_log_count:],
                        }
                    )
                )
                last_tracker_log_count = current_tracker_log_count
                
            # 生成されたファイル情報の更新を確認
            generated_files = ThinkingTracker.get_generated_files(session_id)
            current_generated_files_count = len(generated_files)
            if current_generated_files_count > last_generated_files_count:
                # 生成されたファイル情報をフロントエンドに送信
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": session["status"],
                            "generated_files": generated_files[last_generated_files_count:],
                        }
                    )
                )
                last_generated_files_count = current_generated_files_count

            # 检查结果更新
            if session["result"]:
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": session["status"],
                            "result": session["result"],
                            "log": session["log"][last_log_count:],
                            "thinking_steps": ThinkingTracker.get_thinking_steps(
                                session_id, last_thinking_step_count
                            ),
                            "system_logs": last_log_entries,  # 添加系统日志
                            "logs": ThinkingTracker.get_logs(
                                session_id, last_tracker_log_count
                            ),  # 添加ThinkingTracker日志
                            "generated_files": ThinkingTracker.get_generated_files(session_id),  # 添加生成されたファイル情報
                        }
                    )
                )
                break  # 结果已发送，退出循环，避免重复发送

        # 仅在循环没有因result而break时才发送最终结果
        if not session["result"]:
            await websocket.send_text(
                json.dumps(
                    {
                        "status": session["status"],
                        "result": session["result"],
                        "log": session["log"][last_log_count:],
                        "thinking_steps": ThinkingTracker.get_thinking_steps(
                            session_id, last_thinking_step_count
                        ),
                        "system_logs": last_log_entries,  # 添加系统日志
                        "logs": ThinkingTracker.get_logs(
                            session_id, last_tracker_log_count
                        ),  # 添加ThinkingTracker日志
                        "generated_files": ThinkingTracker.get_generated_files(session_id),  # 添加生成されたファイル情報
                    }
                )
            )

        # 取消注册 WebSocket 发送回调函数
        ThinkingTracker.unregister_ws_send_callback(session_id)
        await websocket.close()
    except WebSocketDisconnect:
        # 客户端断开连接，正常操作
        ThinkingTracker.unregister_ws_send_callback(session_id)
    except Exception as e:
        # 其他异常，记录日志但不中断应用
        print(f"WebSocket错误: {str(e)}")
        ThinkingTracker.unregister_ws_send_callback(session_id)


# 在适当位置添加LLM通信钩子
from app.web.thinking_tracker import ThinkingTracker


# 修改通信跟踪器の実装を改善
class LLMCommunicationTracker:
    """LLMとの通信を追跡し、追加指示を統合するトラッカー"""

    def __init__(self, session_id: str, agent=None):
        self.session_id = session_id
        self.agent = agent
        self.original_completion = None
        self.original_ask_tool = None
        self.active = False

        # エージェントが提供されている場合、フックをインストール
        if agent and hasattr(agent, "llm"):
            self.install_hooks()

    def install_hooks(self):
        """フックをインストールしてLLM通信を捕捉"""
        if not self.agent or not hasattr(self.agent, "llm"):
            return False

        # LLMインスタンスの取得
        llm = self.agent.llm
        
        # completion メソッドのフック（存在する場合）
        if hasattr(llm, "completion"):
            self.original_completion = llm.completion
            llm.completion = self._wrap_completion(self.original_completion)
        
        # ask_tool メソッドのフック（存在する場合）- 重要：これが主要な通信パス
        if hasattr(llm, "ask_tool"):
            self.original_ask_tool = llm.ask_tool
            llm.ask_tool = self._wrap_ask_tool(self.original_ask_tool)
        
        self.active = True
        return True

    def uninstall_hooks(self):
        """フックを削除し、元のメソッドを復元"""
        if not self.active or not self.agent or not hasattr(self.agent, "llm"):
            return
        
        llm = self.agent.llm
        
        # completion メソッドの復元
        if self.original_completion and hasattr(llm, "completion"):
            llm.completion = self.original_completion
        
        # ask_tool メソッドの復元
        if self.original_ask_tool and hasattr(llm, "ask_tool"):
            llm.ask_tool = self.original_ask_tool
        
        self.active = False

    def _wrap_completion(self, original_method):
        """LLMのcompletion メソッドをラップして入出力を捕捉"""
        session_id = self.session_id

        async def wrapped_completion(*args, **kwargs):
            # 入力を記録
            prompt = kwargs.get("prompt", "")
            if not prompt and args:
                prompt = args[0]
            if prompt:
                ThinkingTracker.add_communication(
                    session_id,
                    t('send_to_llm'),
                    prompt[:500] + ("..." if len(prompt) > 500 else ""),
                )
            
            # 元のメソッドを呼び出し
            result = await original_method(*args, **kwargs)

            # 出力を記録
            if result:
                content = result
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                elif hasattr(result, "content"):
                    content = result.content

                if isinstance(content, str):
                    ThinkingTracker.add_communication(
                        session_id,
                        t('receive_from_llm'),
                        content[:500] + ("..." if len(content) > 500 else ""),
                    )

            return result

        return wrapped_completion

    def _wrap_ask_tool(self, original_method):
        """LLMのask_tool メソッドをラップして入出力を捕捉し、追加指示を統合"""
        session_id = self.session_id

        async def wrapped_ask_tool(*args, **kwargs):
            # 引数からメッセージを取得
            messages = kwargs.get("messages", [])
            if not messages and len(args) > 0:
                messages = args[0]
            
            # 追加指示がある場合、統合する
            if session_id in active_tasks and active_tasks[session_id]["modified"]:
                additional_instructions = active_tasks[session_id]["additional_instructions"]
                if additional_instructions:
                    # 追加指示テキストの生成
                    combined_instructions = "\n\n**追加指示**:\n" + "\n".join([
                        f"- {instr}" for instr in additional_instructions
                    ])
                    
                    # これを新しいユーザーメッセージとして追加
                    from app.schema import Message
                    user_msg = Message.user_message(combined_instructions)
                    
                    # 元のメッセージリストに追加
                    if isinstance(messages, list):
                        messages.append(user_msg)
                        
                        # kwargsまたはargsを更新
                        if "messages" in kwargs:
                            kwargs["messages"] = messages
                        else:
                            args = list(args)
                            args[0] = messages
                            args = tuple(args)
                        
                        # 追加指示を統合したことを記録
                        ThinkingTracker.add_thinking_step(
                            session_id,
                            f"追加指示 ({len(additional_instructions)}件) をプロセスに統合しました"
                        )
                        
                        # 追加指示の内容を記録
                        for i, instr in enumerate(additional_instructions):
                            ThinkingTracker.add_thinking_step(
                                session_id,
                                f"統合した追加指示 #{i+1}: {instr}"
                            )
                        
                        # 修正フラグをリセット（処理済みとマーク）
                        active_tasks[session_id]["modified"] = False
            
            # LLMへの送信内容をログに記録
            complete_messages = []
            if messages:
                for msg in messages:
                    if isinstance(msg, dict):
                        msg_content = msg.get("content", "")
                        if msg_content:
                            complete_messages.append(
                                f"{msg.get('role', 'unknown')}: {msg_content[:200]}..."
                            )
                    elif hasattr(msg, "content") and msg.content:
                        complete_messages.append(
                            f"{getattr(msg, 'role', 'unknown')}: {msg.content[:200]}..."
                        )
            
            # メッセージのログを記録（要約形式）
            if complete_messages:
                msg_summary = f"メッセージ数: {len(messages)}, 最後のメッセージ: {complete_messages[-1]}"
                ThinkingTracker.add_communication(
                    session_id,
                    t('send_to_llm'),
                    msg_summary
                )
            
            # 元のメソッドを呼び出し
            result = await original_method(*args, **kwargs)
            
            # 応答を記録
            if result:
                content = ""
                if hasattr(result, "content") and result.content:
                    content = result.content
                    ThinkingTracker.add_communication(
                        session_id,
                        t('receive_from_llm'),
                        content[:500] + ("..." if len(content) > 500 else ""),
                    )
                
                # ツール呼び出しの記録
                if hasattr(result, "tool_calls") and result.tool_calls:
                    tools_info = []
                    for i, tool in enumerate(result.tool_calls):
                        if hasattr(tool, "function") and hasattr(tool.function, "name"):
                            tools_info.append(f"ツール{i+1}: {tool.function.name}")
                    
                    if tools_info:
                        tool_summary = ", ".join(tools_info)
                        ThinkingTracker.add_communication(
                            session_id,
                            t('receive_from_llm'),
                            f"ツール呼び出し: {tool_summary}"
                        )
            
            return result

        return wrapped_ask_tool


# 导入新创建的LLM包装器
from app.agent.llm_wrapper import LLMCallbackWrapper
from app.web.tools.tool_manager import ToolManager

# ツールマネージャーの初期化
tool_manager = ToolManager()


# 修改文件API，支持工作区目录
@app.get("/api/files")
async def get_generated_files(project_id: Optional[str] = None):
    """获取工作区目录和文件、プロジェクトIDが指定された場合はプロジェクト専用ファイルを返す"""
    result = []

    if project_id:
        # プロジェクト専用ワークスペースからファイルを取得
        project_dir = PROJECT_WORKSPACE_ROOT / f"project_{project_id[:8]}"
        if project_dir.exists():
            # プロジェクトディレクトリ内のセッションディレクトリをすべて取得
            session_dirs = list(project_dir.glob("session_*"))
            session_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            for session_dir in session_dirs:
                workspace_name = session_dir.name
                # セッションディレクトリ内のファイルを取得
                files = []
                with os.scandir(session_dir) as it:
                    for entry in it:
                        if entry.is_file() and entry.name.split(".")[-1] in [
                            "txt", "md", "html", "css", "js", "py", "json",
                        ]:
                            files.append(entry)
                
                # 修正時間でソート
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # ファイルがある場合、そのセッションを追加
                if files:
                    workspace_item = {
                        "name": workspace_name,
                        "path": str(session_dir),
                        "modified": session_dir.stat().st_mtime,
                        "files": [],
                    }
                    
                    # セッションディレクトリ内のファイルを追加
                    for file in sorted(files, key=lambda p: p.name):
                        workspace_item["files"].append(
                            {
                                "name": file.name,
                                "path": str(Path(file.path)),
                                "type": Path(file.path).suffix[1:],  # 拡張子
                                "size": file.stat().st_size,
                                "modified": file.stat().st_mtime,
                            }
                        )
                    
                    result.append(workspace_item)
    else:
        # 従来のワークスペース (project_idなし)の場合
        # 获取所有工作区目录
        workspaces = list(WORKSPACE_ROOT.glob("job_*"))
        workspaces.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for workspace in workspaces:
            workspace_name = workspace.name
            # 获取工作区内所有文件并按修改时间排序
            files = []
            with os.scandir(workspace) as it:
                for entry in it:
                    if entry.is_file() and entry.name.split(".")[-1] in [
                        "txt",
                        "md",
                        "html",
                        "css",
                        "js",
                        "py",
                        "json",
                    ]:
                        files.append(entry)
            # 按修改时间倒序排序
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 如果有文件，添加该工作区
            if files:
                workspace_item = {
                    "name": workspace_name,
                    "path": str(workspace.relative_to(Path(__file__).parent.parent.parent)),
                    "modified": workspace.stat().st_mtime,
                    "files": [],
                }

                # 添加工作区下的文件
                for file in sorted(files, key=lambda p: p.name):
                    workspace_item["files"].append(
                        {
                            "name": file.name,
                            "path": str(
                                Path(file.path).relative_to(
                                    Path(__file__).parent.parent.parent
                                )
                            ),
                            "type": Path(file.path).suffix[1:],  # 去掉.的扩展名
                            "size": file.stat().st_size,
                            "modified": file.stat().st_mtime,
                        }
                    )

                result.append(workspace_item)

    return {"workspaces": result}


# 新增日志文件接口
@app.get("/api/logs")
async def get_system_logs(limit: int = 10):
    """获取系统日志列表"""
    log_files = []
    for entry in os.scandir(LOGS_DIR):
        if entry.is_file() and entry.name.endswith(".log"):
            log_files.append(
                {
                    "name": entry.name,
                    "size": entry.stat().st_size,
                    "modified": entry.stat().st_mtime,
                }
            )
    # 按修改时间倒序排序并限制数量
    log_files.sort(key=lambda x: x["modified"], reverse=True)
    return {"logs": log_files[:limit]}


@app.get("/api/logs/{log_name}")
async def get_log_content(log_name: str, parsed: bool = False):
    """获取特定日志文件内容"""
    log_path = LOGS_DIR / log_name
    # 安全检查
    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log file not found")

    # 如果请求解析后的日志信息
    if parsed:
        log_info = parse_log_file(str(log_path))
        log_info["name"] = log_name
        return log_info

    # 否则返回原始内容
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"name": log_name, "content": content}


@app.get("/api/logs_parsed")
async def get_parsed_logs(limit: int = 10):
    """获取解析后的日志信息列表"""
    return {"logs": get_all_logs_info(str(LOGS_DIR), limit)}


@app.get("/api/logs_parsed/{log_name}")
async def get_parsed_log(log_name: str):
    """获取特定日志文件的解析信息"""
    log_path = LOGS_DIR / log_name
    # 安全检查
    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log file not found")

    log_info = parse_log_file(str(log_path))
    log_info["name"] = log_name
    return log_info


@app.get("/api/latest_log")
async def get_latest_log():
    """获取最新日志文件的解析信息"""
    return get_latest_log_info(str(LOGS_DIR))


@app.get("/api/files/{file_path:path}")
async def get_file_content(file_path: str, project: Optional[str] = None):
    """获取特定文件的内容 - プロジェクト名を指定可能"""
    # 安全检查，防止目录遍历攻击
    root_dir = Path(__file__).parent.parent.parent
    
    # プロジェクト指定がある場合、そのプロジェクトのディレクトリをルートとする
    if project:
        project_dir = PROJECT_WORKSPACE_ROOT / f"project_{project[:8]}"
        if project_dir.exists():
            root_dir = project_dir
            
    # 注：file_pathが絶対パスの場合の対応
    if os.path.isabs(file_path):
        full_path = Path(file_path)
    else:
        full_path = root_dir / file_path

    # 确保文件在项目目录内
    try:
        if not os.path.commonpath([root_dir, full_path]).startswith(str(root_dir)):
            raise ValueError("File path outside of project root")
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # 读取文件内容
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 确定文件类型
        file_type = full_path.suffix[1:] if full_path.suffix else "text"

        return {
            "name": full_path.name,
            "path": file_path,
            "type": file_type,
            "content": content,
            "project": project,  # プロジェクト情報も返す
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


# 修改process_prompt函数，处理工作区
async def process_prompt(session_id: str, prompt: str, project_id: Optional[str] = None):
    # プロジェクトとセッションの情報を取得
    workspace_dir = None
    session = db.get_session(session_id)
    
    if session:
        workspace_path = session["workspace_path"]
        # パスがstringなのでPathオブジェクトに変換
        workspace_dir = Path(workspace_path)
        # ディレクトリが存在しない場合は作成
        os.makedirs(workspace_dir, exist_ok=True)
    else:
        # 参考：セッションデータがない場合の互換性維持
        if session_id in active_sessions and "workspace" in active_sessions[session_id]:
            workspace_path = active_sessions[session_id]["workspace"]
            workspace_dir = Path(workspace_path)
            os.makedirs(workspace_dir, exist_ok=True)
        # それでもワークスペースディレクトリがない場合は作成
        if not workspace_dir:
            workspace_dir = create_workspace(session_id, project_id)
            if session_id in active_sessions:
                active_sessions[session_id]["workspace"] = str(workspace_dir)

    # 设置当前工作目录为工作区
    original_cwd = os.getcwd()
    os.chdir(workspace_dir)

    # 使用工作区名称作为日志文件名前缀
    job_id = workspace_dir.name
    # 设置日志文件路径
    task_log_path = LOGS_DIR / f"{job_id}.log"

    # 创建日志监视器并开始监控
    log_monitor = LogFileMonitor(job_id)
    observer = log_monitor.start_monitoring()
    active_log_monitors[session_id] = log_monitor

    async def sync_logs():
        """定期从LogFileMonitor获取日志并实时更新到ThinkingTracker"""
        last_count = 0
        try:
            while True:
                if session_id not in active_log_monitors:
                    break
                current_logs = active_log_monitors[session_id].get_log_entries()
                if len(current_logs) > last_count:
                    # 处理新的日志条目
                    new_logs = current_logs[last_count:]
                    # 逐条处理每条新日志，确保实时性
                    for log_entry in new_logs:
                        # 单独处理每条日志，立即添加到ThinkingTracker
                        ThinkingTracker.add_log_entry(
                            session_id,
                            {
                                "level": log_entry.get("level", "INFO"),
                                "message": log_entry.get("message", ""),
                                "timestamp": log_entry.get("timestamp", time.time()),
                            },
                        )
                    last_count = len(current_logs)
                # 减少轮询间隔，提高实时性
                await asyncio.sleep(0.1)  # 每0.1秒检查一次
        except Exception as e:
            print(f"同步日志时发生错误: {str(e)}")

    # 启动日志同步任务
    sync_task = asyncio.create_task(sync_logs())

    # 设置环境变量告知logger使用此日志文件，确保两种方式都设置
    os.environ["OPENMANUS_LOG_FILE"] = str(task_log_path)
    os.environ["OPENMANUS_TASK_ID"] = job_id

    try:
        # 使用日志捕获上下文管理器解析日志级别和内容
        with capture_session_logs(session_id) as log:
            # 初始化思考跟踪
            ThinkingTracker.start_tracking(session_id)
            ThinkingTracker.add_thinking_step(session_id, t('start_processing'))
            ThinkingTracker.add_thinking_step(
                session_id, f"{t('workspace_dir')}: {workspace_dir.name}"
            )

            # 直接记录用户输入的prompt
            ThinkingTracker.add_communication(session_id, t('user_input'), prompt)
            
            # 言語を検出
            detected_language = detect_language(prompt)
            if detected_language != "en":
                language_name = {"ja": "日本語", "zh": "中国語"}.get(detected_language, detected_language)
                ThinkingTracker.add_thinking_step(
                    session_id, f"言語を検出しました: {language_name}"
                )
                # 言語に基づいて環境変数を設定
                os.environ["ENHANCED_MANUS_LANGUAGE"] = detected_language
            
            # ====== EnhancedManusを使用して処理 ======
            enhanced_agent = create_enhanced_agent(
                prompt,
                session_id=session_id,  # セッションIDを明示的に渡す
                project_id=project_id   # プロジェクトIDも渡す
            )
            
            # コミュニケーショントラッカーをインストール
            comm_tracker = LLMCommunicationTracker(session_id, enhanced_agent)
            
            # 检查任务是否被取消
            cancel_event = cancel_events.get(session_id)
            if cancel_event and cancel_event.is_set():
                log.warning("処理がユーザーによって中止されました")
                ThinkingTracker.mark_stopped(session_id)
                active_sessions[session_id]["status"] = "stopped"
                active_sessions[session_id]["result"] = "処理がユーザーによって停止されました"
                return
            
            # プロジェクト指示を取得（存在する場合）
            # セッションからプロジェクトを取得
            session_data = db.get_session(session_id)
            
            if session_data and "project_id" in session_data:
                project_id = session_data["project_id"]
                project = db.get_project(project_id)
                
                # プロジェクトに指示があれば、それをプロンプトに追加
                if project and project.get("instructions"):
                    instructions_prompt = (
                        f"以下の指示に従ってタスクを実行してください：\n\n"
                        f"{project['instructions']}\n\n"
                        f"ユーザーからの質問：\n{prompt}"
                    )
                    prompt = instructions_prompt
                    
                    # 指示を使用している旨をログに記録
                    log.info(f"プロジェクト指示を適用しました: {project_id}")
                    ThinkingTracker.add_thinking_step(
                        session_id, f"プロジェクト指示を適用: {project['instructions'][:50]}{'...' if len(project['instructions']) > 50 else ''}"
                    )
            
            log.info(f"処理を開始します: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            # EnhancedManusを使用して処理
            result = await enhanced_agent.run(prompt)
            
            # AIの応答をデータベースに保存
            message_id = str(uuid.uuid4())
            db.create_message(message_id, session_id, "assistant", result)
            
            # 処理結果を保存
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["result"] = result
            
            # 思考ステップも保存
            active_sessions[session_id]["thinking_steps"] = ThinkingTracker.get_thinking_steps(session_id)
            
            # 生成されたファイルがあれば記録
            if hasattr(enhanced_agent, "generated_files") and enhanced_agent.generated_files:
                file_list = [f['filename'] for f in enhanced_agent.generated_files]
                files_str = ", ".join(file_list)
                ThinkingTracker.add_thinking_step(
                    session_id,
                    f"ワークスペース {workspace_dir.name} で{len(file_list)}個のファイルが生成されました: {files_str}"
                )
                active_sessions[session_id]["generated_files"] = file_list
            
            # 记录完成情况
            log.info("処理完了")
            ThinkingTracker.add_conclusion(
                session_id, f"タスク処理が完了しました！ワークスペース {workspace_dir.name} に結果が生成されました。"
            )
            
            # タスク上下文をクリア
            if session_id in active_tasks:
                del active_tasks[session_id]

    except asyncio.CancelledError:
        # 处理取消情况
        print("処理がキャンセルされました")
        ThinkingTracker.mark_stopped(session_id)
        active_sessions[session_id]["status"] = "stopped"
        active_sessions[session_id]["result"] = "処理がキャンセルされました"
    except Exception as e:
        # 处理错误情况
        error_msg = f"処理エラー: {str(e)}"
        print(error_msg)
        ThinkingTracker.add_error(session_id, f"処理中にエラーが発生しました: {str(e)}")
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["result"] = f"エラーが発生しました: {str(e)}"
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)

        # 清除日志文件环境变量
        if "OPENMANUS_LOG_FILE" in os.environ:
            del os.environ["OPENMANUS_LOG_FILE"]
        if "OPENMANUS_TASK_ID" in os.environ:
            del os.environ["OPENMANUS_TASK_ID"]

        # 清理资源
        if "agent" in locals() and hasattr(agent, "llm") and isinstance(agent.llm, LLMCallbackWrapper):
            try:
                # 正确地移除回调
                if "on_before_request" in locals():
                    agent.llm._callbacks["before_request"].remove(on_before_request)
                if "on_after_request" in locals():
                    agent.llm._callbacks["after_request"].remove(on_after_request)
            except (ValueError, Exception) as e:
                print(f"コールバックのクリーンアップ中にエラーが発生しました: {str(e)}")

        # コミュニケーショントラッカーのクリーンアップ
        if "comm_tracker" in locals():
            try:
                comm_tracker.uninstall_hooks()
            except Exception as e:
                print(f"コミュニケーショントラッカーのクリーンアップ中にエラーが発生しました: {str(e)}")

        # 清理取消事件
        if session_id in cancel_events:
            del cancel_events[session_id]

        # 如果监视器存在，停止监控
        if session_id in active_log_monitors:
            observer.stop()
            observer.join(timeout=1)
            del active_log_monitors[session_id]

        # 取消日志同步任务
        if sync_task:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                pass


# 添加一个新的API端点来获取思考步骤
@app.get("/api/thinking/{session_id}")
async def get_thinking_steps(session_id: str, start_index: int = 0):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": ThinkingTracker.get_status(session_id),
        "thinking_steps": ThinkingTracker.get_thinking_steps(session_id, start_index),
    }


# 添加获取进度信息的API端点
@app.get("/api/progress/{session_id}")
async def get_progress(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return ThinkingTracker.get_progress(session_id)


# 添加API端点获取指定会话的系统日志
@app.get("/api/systemlogs/{session_id}")
async def get_system_logs(session_id: str):
    """获取指定会话的系统日志"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    job_id = None
    if "workspace" in active_sessions[session_id]:
        workspace_path = active_sessions[session_id]["workspace"]
        job_id = workspace_path

    if not job_id:
        return {"logs": []}

    # 如果有监控器使用监控器
    if session_id in active_log_monitors:
        logs = active_log_monitors[session_id].get_log_entries()
        return {"logs": logs}

    # 否则直接读取日志文件
    log_path = LOGS_DIR / f"{job_id}.log"
    if not log_path.exists():
        return {"logs": []}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = [line.strip() for line in f.readlines()]
        return {"logs": logs}
    except Exception as e:
        return {"error": f"Error reading log file: {str(e)}"}
