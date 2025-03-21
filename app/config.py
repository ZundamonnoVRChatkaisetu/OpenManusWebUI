import threading
import tomllib
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
PROJECT_WORKSPACE_ROOT = PROJECT_ROOT / "project_workspace"

# ワークスペースディレクトリの作成
WORKSPACE_ROOT.mkdir(exist_ok=True)
PROJECT_WORKSPACE_ROOT.mkdir(exist_ok=True)


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(8192, description="Maximum number of tokens per request")  # 4096から8192に増加
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="AzureOpenai or Openai")
    api_version: str = Field(..., description="Azure Openai version if AzureOpenai")


class WorkspaceSettings(BaseModel):
    enabled: bool = Field(True, description="Whether to use workspace for file operations")
    auto_read: bool = Field(True, description="Automatically read files in workspace")
    auto_write: bool = Field(True, description="Automatically write files to workspace")
    default_path: Path = Field(default=WORKSPACE_ROOT, description="Default workspace path")
    current_project: Optional[str] = Field(None, description="Current active project name")


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    workspace: WorkspaceSettings = Field(default_factory=WorkspaceSettings)


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 8192),  # 4096から8192に増加
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
        }

        workspace_config = raw_config.get("workspace", {})

        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "workspace": {
                "enabled": workspace_config.get("enabled", True),
                "auto_read": workspace_config.get("auto_read", True),
                "auto_write": workspace_config.get("auto_write", True),
                "default_path": Path(workspace_config.get("default_path", str(WORKSPACE_ROOT))),
                "current_project": workspace_config.get("current_project", None),
            }
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm
        
    @property
    def workspace(self) -> WorkspaceSettings:
        return self._config.workspace

    def get_workspace_path(self, project_name: Optional[str] = None) -> Path:
        """
        プロジェクト名を受け取り、対応するワークスペースパスを返す
        
        Args:
            project_name: プロジェクト名。None の場合は現在のプロジェクトまたはデフォルトのワークスペース
            
        Returns:
            対応するワークスペースパス
        """
        # プロジェクト名が指定されている場合
        if project_name:
            project_path = PROJECT_WORKSPACE_ROOT / project_name
            project_path.mkdir(exist_ok=True)
            return project_path
            
        # 設定に現在のプロジェクトがある場合
        if self.workspace.current_project:
            project_path = PROJECT_WORKSPACE_ROOT / self.workspace.current_project
            project_path.mkdir(exist_ok=True)
            return project_path
            
        # それ以外はデフォルトのワークスペース
        return self.workspace.default_path
        
    def set_current_project(self, project_name: Optional[str]):
        """
        現在のプロジェクトを設定する
        
        Args:
            project_name: 設定するプロジェクト名。None の場合はデフォルトワークスペースに戻す
        """
        self._config.workspace.current_project = project_name


config = Config()
