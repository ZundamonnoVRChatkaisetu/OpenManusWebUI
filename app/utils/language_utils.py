"""
言語検出と多言語対応のためのユーティリティ
"""

import re
from typing import Dict, Literal, Optional

Language = Literal["en", "ja", "zh", "auto"]

# 言語検出用の正規表現パターン
LANGUAGE_PATTERNS = {
    "ja": r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]",  # ひらがな、カタカナ、漢字
    "zh": r"[\u4E00-\u9FFF\u3400-\u4DBF]",  # 簡体字、繁体字
    # 英語はデフォルト
}

# 多言語テンプレート
DEFAULT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "file_generation": {
        "en": "I've created the file '{filename}' based on your request.",
        "ja": "ご要望に基づいて、'{filename}'ファイルを作成しました。",
        "zh": "我已根据您的要求创建了文件'{filename}'。"
    },
    "analysis_complete": {
        "en": "Analysis complete. Here are the results:",
        "ja": "分析が完了しました。結果は以下の通りです：",
        "zh": "分析完成。结果如下："
    },
    "tool_execution": {
        "en": "Executed tool '{tool_name}' with the following result:",
        "ja": "ツール'{tool_name}'を実行しました。結果は次の通りです：",
        "zh": "执行了工具'{tool_name}'，结果如下："
    },
    "error_message": {
        "en": "An error occurred: {error}",
        "ja": "エラーが発生しました：{error}",
        "zh": "发生错误：{error}"
    },
    "processing_message": {
        "en": "Processing your request...",
        "ja": "リクエストを処理中です...",
        "zh": "正在处理您的请求..."
    }
}


def detect_language(text: str) -> Language:
    """
    テキストから言語を検出する
    
    Args:
        text: 検出対象のテキスト
        
    Returns:
        検出された言語コード（"en", "ja", "zh"）
    """
    if not text:
        return "en"
    
    # 日本語検出
    if re.search(LANGUAGE_PATTERNS["ja"], text):
        # 日本語の文字が多く含まれているか確認
        ja_chars = len(re.findall(LANGUAGE_PATTERNS["ja"], text))
        if ja_chars > len(text) * 0.1:  # 10%以上が日本語文字の場合
            return "ja"
    
    # 中国語検出
    if re.search(LANGUAGE_PATTERNS["zh"], text):
        # 中国語の文字が多く含まれているか確認
        zh_chars = len(re.findall(LANGUAGE_PATTERNS["zh"], text))
        # 日本語と中国語は漢字を共有するため、追加チェックが必要
        if zh_chars > len(text) * 0.1 and "的" in text:  # 中国語によく出現する「的」を含む
            return "zh"
    
    # デフォルトは英語
    return "en"


def get_template(template_key: str, language: Optional[Language] = None, **kwargs) -> str:
    """
    指定された言語とキーに基づいてテンプレートを取得し、必要に応じて変数を置換
    
    Args:
        template_key: テンプレートキー
        language: 言語コード（未指定の場合は英語）
        **kwargs: テンプレート内の変数に対応する値
        
    Returns:
        フォーマット済みテンプレート文字列
    """
    templates = DEFAULT_TEMPLATES.get(template_key, {})
    lang = language or "en"
    
    # 指定された言語が利用できない場合は英語にフォールバック
    template = templates.get(lang, templates.get("en", "Template not found"))
    
    # 変数置換
    return template.format(**kwargs)
