"""
出力フォーマットと結果表示の最適化
"""

import re
from typing import Dict, List, Optional, Union

from app.utils.language_utils import Language, detect_language, get_template


def format_thought_process(thoughts: List[str], include_steps: bool = False) -> str:
    """
    思考プロセスを整形して、ユーザーに表示する最終結果から除外する
    
    Args:
        thoughts: 思考ステップのリスト
        include_steps: 思考ステップ番号を含めるかどうか
        
    Returns:
        整形された思考プロセス（デバッグ用）
    """
    if not thoughts:
        return ""
    
    formatted_thoughts = []
    for i, thought in enumerate(thoughts):
        if include_steps:
            formatted_thoughts.append(f"Step {i+1}: {thought}")
        else:
            formatted_thoughts.append(thought)
    
    return "\n".join(formatted_thoughts)


def extract_final_result(full_output: str) -> str:
    """
    AIの完全な出力から最終結果のみを抽出する
    
    Args:
        full_output: AIからの完全な出力
        
    Returns:
        ユーザーに表示するための最終結果
    """
    # デバッグ情報、思考ステップ、中間結果などを除外するパターン
    patterns_to_remove = [
        r"Step \d+:.*?\n",  # ステップ番号と説明
        r"\[TOOL_REQUEST\].*?\[END_TOOL_REQUEST\]",  # ツールリクエスト
        r"\[TOOL_RESULT\].*?\[END_TOOL_RESULT\]",  # ツール結果
        r"Observed output of cmd.*?executed:.*?\n",  # ツール実行の観察結果
        r"Thinking complete.*?\n",  # 思考完了メッセージ
        r"Terminated:.*?\n",  # 終了メッセージ
    ]
    
    # 各パターンにマッチする部分を削除
    cleaned_output = full_output
    for pattern in patterns_to_remove:
        cleaned_output = re.sub(pattern, "", cleaned_output, flags=re.DOTALL)
    
    # 空行の連続を1つの空行に置換
    cleaned_output = re.sub(r"\n\s*\n+", "\n\n", cleaned_output)
    
    # 先頭と末尾の空白を削除
    cleaned_output = cleaned_output.strip()
    
    return cleaned_output


def format_tool_result(
    tool_name: str, 
    result: Union[str, Dict], 
    language: Optional[Language] = None
) -> str:
    """
    ツール実行結果を整形する
    
    Args:
        tool_name: ツール名
        result: ツール実行結果
        language: 使用言語
        
    Returns:
        整形されたツール実行結果
    """
    # 結果が辞書の場合は、文字列に変換
    if isinstance(result, dict):
        # 言語が指定されていなければ検出
        if not language:
            # 辞書のすべての文字列値を連結
            all_text = " ".join([str(v) for v in result.values() if isinstance(v, str)])
            language = detect_language(all_text)
        
        # テンプレートを使用して結果を整形
        prefix = get_template("tool_execution", language, tool_name=tool_name)
        
        # 結果の整形（キーと値のペアを表示）
        formatted_result = []
        for key, value in result.items():
            formatted_result.append(f"- {key}: {value}")
        
        return f"{prefix}\n\n" + "\n".join(formatted_result)
    
    # 結果が文字列の場合
    else:
        # 言語が指定されていなければ検出
        if not language:
            language = detect_language(result)
        
        # テンプレートを使用して結果を整形
        prefix = get_template("tool_execution", language, tool_name=tool_name)
        
        return f"{prefix}\n\n{result}"


def format_file_generation_result(
    filename: str,
    content_preview: Optional[str] = None,
    project: Optional[str] = None,
    language: Optional[Language] = None
) -> str:
    """
    ファイル生成結果を整形する
    
    Args:
        filename: 生成されたファイル名
        content_preview: ファイル内容のプレビュー（省略可）
        project: ファイルが保存されたプロジェクト名（省略可）
        language: 使用言語
        
    Returns:
        整形されたファイル生成結果
    """
    # 言語が指定されていなければ検出
    if not language:
        # ファイル名とプレビュー（存在する場合）から言語を検出
        detect_text = filename
        if content_preview:
            detect_text += " " + content_preview
        language = detect_language(detect_text)
    
    # テンプレートを使用して結果を整形
    result = get_template("file_generation", language, filename=filename)
    
    # プロジェクト情報がある場合は追加
    if project:
        result += f" (プロジェクト: {project})"
    
    # プレビューがある場合は追加
    if content_preview:
        # ファイルの種類に基づいてプレビューをフォーマット
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # コード形式のファイル
        if file_ext in ['py', 'js', 'html', 'css', 'json', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs', 'go', 'rs', 'rb', 'php', 'sh']:
            result += f"\n\n```{file_ext}\n{content_preview}\n```"
        # マークダウンファイル
        elif file_ext == 'md':
            result += f"\n\n```markdown\n{content_preview}\n```"
        # その他のテキストファイル
        else:
            result += f"\n\n{content_preview}"
    
    return result


def format_error_message(
    error: str,
    language: Optional[Language] = None
) -> str:
    """
    エラーメッセージを整形する
    
    Args:
        error: エラーメッセージ
        language: 使用言語
        
    Returns:
        整形されたエラーメッセージ
    """
    # 言語が指定されていなければ検出
    if not language:
        language = detect_language(error)
    
    # テンプレートを使用して結果を整形
    return get_template("error_message", language, error=error)
