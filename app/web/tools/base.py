"""
ツールフレームワークの基本クラスと関数
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Type, TypeVar, Union, get_type_hints
import inspect
import json
from pydantic import BaseModel, Field, create_model

# 使用可能なツールの登録リスト
_AVAILABLE_TOOLS: Dict[str, Type['Tool']] = {}

T = TypeVar('T', bound='Tool')


class ToolResultStatus(str, Enum):
    """ツール実行結果のステータス"""
    SUCCESS = "success"  # 成功
    ERROR = "error"      # エラー
    INFO = "info"        # 情報提供


class ToolResult(BaseModel):
    """ツールの実行結果を表すクラス"""
    status: ToolResultStatus = Field(ToolResultStatus.SUCCESS, description="実行結果のステータス")
    message: str = Field("", description="実行結果のメッセージ")
    data: Any = Field(None, description="実行結果のデータ")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """結果を辞書に変換"""
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data
        }

    def to_json(self) -> str:
        """結果をJSON文字列に変換"""
        return json.dumps(self.to_dict(), default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o))


class Tool(ABC):
    """
    ツールの基本クラス。
    すべてのツールはこのクラスを継承して実装します。
    """
    name: str = ""  # ツールの名前
    description: str = ""  # ツールの説明
    version: str = "1.0.0"  # ツールのバージョン
    parameters_model: Type[BaseModel] = None  # パラメータを表すPydanticモデル

    def __init__(self):
        """ツールの初期化"""
        if not self.name:
            self.name = self.__class__.__name__.lower()

        # パラメータのモデルが定義されていない場合は、execute_methodから自動生成
        if self.parameters_model is None:
            self.parameters_model = self._create_parameters_model()

    def _create_parameters_model(self) -> Type[BaseModel]:
        """executeメソッドの引数からパラメータモデルを自動生成"""
        execute_method = getattr(self, 'execute')
        sig = inspect.signature(execute_method)
        
        # selfを除外した引数を取得
        params = {}
        for name, param in list(sig.parameters.items())[1:]:  # self を除外
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                annotation = Any
            default = ... if param.default is inspect.Parameter.empty else param.default
            params[name] = (annotation, default)
        
        # パラメータモデルを動的に生成
        model_name = f"{self.__class__.__name__}Parameters"
        return create_model(model_name, **params)

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """受け取ったパラメータをバリデーション"""
        if self.parameters_model:
            validated = self.parameters_model(**params)
            return validated.dict()
        return params

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        ツールの実行メソッド。継承先で実装する必要があります。
        
        Returns:
            ToolResult: ツールの実行結果
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        ツールのスキーマ情報を返します。
        LLMへの指示生成などに使用します。
        """
        if self.parameters_model:
            schema = self.parameters_model.schema()
            # 必要に応じてスキーマを調整
            properties = schema.get("properties", {})
            required = schema.get("required", [])
        else:
            properties = {}
            required = []

        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


def register_tool(cls: Type[T]) -> Type[T]:
    """
    ツールクラスを登録するデコレータ
    """
    tool_instance = cls()
    _AVAILABLE_TOOLS[tool_instance.name] = cls
    return cls


def get_available_tools() -> Dict[str, Type[Tool]]:
    """
    登録されている使用可能なツール一覧を返します
    """
    return _AVAILABLE_TOOLS.copy()
