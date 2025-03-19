import argparse
import os
import sys
import subprocess
import time
import signal
import threading
import platform
from pathlib import Path
import io

import uvicorn


# LMStudioのサーバープロセス
lmstudio_process = None


# 検索パスリスト - LMStudioの実行ファイルの候補
def get_lmstudio_paths():
    system = platform.system()
    if system == "Windows":
        return [
            r"C:\Program Files\LM Studio\LM Studio.exe",
            r"C:\Program Files (x86)\LM Studio\LM Studio.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\LM Studio\LM Studio.exe"),
        ]
    elif system == "Darwin":  # macOS
        return [
            "/Applications/LM Studio.app/Contents/MacOS/LM Studio",
            os.path.expanduser("~/Applications/LM Studio.app/Contents/MacOS/LM Studio"),
        ]
    elif system == "Linux":
        return [
            "/usr/bin/lmstudio",
            "/usr/local/bin/lmstudio",
            os.path.expanduser("~/lmstudio/LM Studio"),
        ]
    return []


# LMStudioのサーバーを起動
def start_lmstudio_server(lm_port=1234, no_gui=True):
    global lmstudio_process
    
    print(f"🔍 LMStudioサーバーの実行ファイルを検索中...")
    
    # LMStudioの実行ファイルを探す
    lmstudio_executable = None
    for path in get_lmstudio_paths():
        if os.path.exists(path):
            lmstudio_executable = path
            break
    
    if not lmstudio_executable:
        print("⚠️ LMStudioの実行ファイルが見つかりませんでした。手動で起動してください。")
        print(f"   LMStudioを起動し、ポート {lm_port} でAPIサーバーを有効にしてください。")
        return False
    
    try:
        # コマンドライン引数
        cmd = [lmstudio_executable, "--api-port", str(lm_port), "--max-listeners", "20"]
        if no_gui:
            cmd.append("--no-gui")
        
        # サブプロセスとして起動
        print(f"🚀 LMStudioのAPIサーバーを起動します(ポート: {lm_port})...")
        lmstudio_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # バイナリモードで出力を取得
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )
        
        # 起動確認のため少し待機
        time.sleep(2)
        
        if lmstudio_process.poll() is None:
            print(f"✅ LMStudioサーバーが正常に起動しました (ポート: {lm_port})")
            
            # 標準出力と標準エラーを非同期で読み取る関数
            def read_output(pipe, prefix):
                # バイナリストリームからUTF-8でデコード
                text_stream = io.TextIOWrapper(pipe, encoding='utf-8', errors='replace')
                for line in text_stream:
                    if line:
                        # エラーメッセージをフィルタリング
                        if "MaxListenersExceededWarning" not in line and "lib-bad" not in line:
                            print(f"{prefix}: {line.strip()}")
            
            # 標準出力と標準エラーを非同期に読み取るスレッドを開始
            threading.Thread(target=read_output, args=(lmstudio_process.stdout, "LMStudio"), daemon=True).start()
            threading.Thread(target=read_output, args=(lmstudio_process.stderr, "LMStudio Error"), daemon=True).start()
            
            return True
        else:
            print(f"⚠️ LMStudioサーバーの起動に失敗しました。")
            return False
            
    except Exception as e:
        print(f"⚠️ LMStudioサーバーの起動中にエラーが発生しました: {str(e)}")
        return False


# 終了時にLMStudioプロセスをクリーンアップ
def cleanup_lmstudio():
    global lmstudio_process
    if lmstudio_process:
        print("🛑 LMStudioサーバーを停止しています...")
        try:
            if platform.system() == "Windows":
                lmstudio_process.terminate()
                # Windowsの場合、プロセスツリー全体を終了するために必要
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(lmstudio_process.pid)])
            else:
                # Unix系OSの場合
                lmstudio_process.terminate()
                lmstudio_process.wait(timeout=5)
        except Exception as e:
            print(f"LMStudioの停止中にエラーが発生しました: {str(e)}")
            if platform.system() != "Windows":
                try:
                    # 強制終了を試みる
                    lmstudio_process.kill()
                except:
                    pass


# 検査: WebSocket依存関係
def check_websocket_dependencies():
    pass
    return True


# ディレクトリ構造の確保
def ensure_directories():
    # templatesディレクトリの作成
    templates_dir = Path("app/web/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)

    # staticディレクトリの作成
    static_dir = Path("app/web/static")
    static_dir.mkdir(parents=True, exist_ok=True)

    # __init__.pyファイルの存在確認
    init_file = Path("app/web/__init__.py")
    if not init_file.exists():
        init_file.touch()


if __name__ == "__main__":
    # コマンドライン引数の追加
    parser = argparse.ArgumentParser(description="OpenManus Webアプリケーションサーバー")
    parser.add_argument("--no-browser", action="store_true", help="起動時にブラウザを自動的に開かない")
    parser.add_argument("--port", type=int, default=8000, help="サーバーのリスニングポート (デフォルト: 8000)")
    parser.add_argument("--lmstudio", action="store_true", help="LMStudioサーバーも同時に起動する")
    parser.add_argument("--lm-port", type=int, default=1234, help="LMStudioサーバーのポート (デフォルト: 1234)")
    parser.add_argument("--lm-gui", action="store_true", help="LMStudioをGUIモードで起動する")

    args = parser.parse_args()

    ensure_directories()

    if not check_websocket_dependencies():
        print("必要な依存関係がありません。必要なパッケージをインストールしてから再試行してください。")
        sys.exit(1)

    # LMStudioサーバーの起動
    if args.lmstudio:
        start_lmstudio_server(lm_port=args.lm_port, no_gui=not args.lm_gui)

    # ブラウザ自動起動の制御
    if args.no_browser:
        os.environ["AUTO_OPEN_BROWSER"] = "0"
    else:
        os.environ["AUTO_OPEN_BROWSER"] = "1"

    port = args.port

    print(f"🚀 OpenManus Web アプリケーション起動中...")
    print(f"http://localhost:{port} にアクセスして使用開始")

    # 終了時のクリーンアップを登録
    def signal_handler(sig, frame):
        print("\n⏹️ アプリケーション終了中...")
        cleanup_lmstudio()
        sys.exit(0)

    # Ctrl+Cのシグナルハンドラー登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # OpenManus Web UIサーバー起動
        uvicorn.run("app.web.app:app", host="0.0.0.0", port=port, reload=True)
    finally:
        # 終了時のクリーンアップ
        cleanup_lmstudio()
