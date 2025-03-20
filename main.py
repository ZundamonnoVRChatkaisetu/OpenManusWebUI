import argparse
import asyncio
import os
import sys

from app.agent.enhanced_manus import EnhancedManus
from app.logger import logger


async def run_cli():
    """コマンドライン対話モード"""
    agent = EnhancedManus()
    while True:
        try:
            prompt = input("プロンプトを入力（'exit'/'quit'で終了）: ")
            prompt_lower = prompt.lower()
            if prompt_lower in ["exit", "quit"]:
                logger.info("終了します")
                break
            if not prompt.strip():
                logger.warning("空のプロンプトはスキップします")
                continue
            logger.warning("リクエストを処理中...")
            result = await agent.run(prompt)
            print("\n" + result + "\n")
        except KeyboardInterrupt:
            logger.warning("終了します")
            break


async def run_web():
    """Webアプリケーションを起動"""
    # サブプロセスとしてweb_run.pyを実行
    import uvicorn

    # ディレクトリ構造を確保
    from web_run import check_websocket_dependencies, ensure_directories

    ensure_directories()

    if not check_websocket_dependencies():
        logger.error("必要な依存関係がありません。必要なパッケージをインストールしてから再試行してください。")
        return

    logger.info("🚀 OpenManus Web アプリケーション起動中...")
    logger.info("http://localhost:8000 にアクセスして使用開始")

    # ブラウザ自動起動を有効化する環境変数を設定
    os.environ["AUTO_OPEN_BROWSER"] = "1"

    # 現在のプロセスでUvicornサーバーを起動
    uvicorn.run("app.web.app:app", host="0.0.0.0", port=8000)


def main():
    """メインエントリーポイント - コマンドライン引数を解析して実行モードを決定"""
    parser = argparse.ArgumentParser(description="OpenManus - AIアシスタント")
    parser.add_argument("--web", action="store_true", help="Webアプリケーションモードで実行（デフォルトはコマンドラインモード）")
    parser.add_argument("--show-thoughts", action="store_true", help="思考プロセスを表示する（デバッグ用）")
    parser.add_argument("--disable-auto-files", action="store_true", help="ファイルの自動生成を無効化する")
    parser.add_argument("--language", choices=["en", "ja", "zh", "auto"], default="auto", 
                        help="使用する言語（en=英語, ja=日本語, zh=中国語, auto=自動検出）")

    args = parser.parse_args()

    # EnhancedManusの設定を環境変数として保存
    if args.show_thoughts:
        os.environ["ENHANCED_MANUS_SHOW_THOUGHTS"] = "1"
    if args.disable_auto_files:
        os.environ["ENHANCED_MANUS_DISABLE_AUTO_FILES"] = "1"
    if args.language != "auto":
        os.environ["ENHANCED_MANUS_LANGUAGE"] = args.language

    try:
        if args.web:
            # Webアプリケーションモードを起動
            logger.info("Webアプリケーションモードを起動中...")
            asyncio.run(run_web())
        else:
            # コマンドライン対話モードを起動
            logger.info("コマンドライン対話モードを起動中...")
            asyncio.run(run_cli())
    except KeyboardInterrupt:
        logger.warning("プログラムを終了します")
    except Exception as e:
        logger.error(f"プログラムがエラーで終了しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
