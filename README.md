# OpenManus Web UI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要

OpenManus Web UIは、高度なAIアシスタント機能を備えたウェブインターフェースです。プロジェクト管理機能とチャットセッション機能を組み合わせることで、複数の会話や作業を効率的に管理できます。

## 機能一覧

- 📁 **プロジェクト管理**: 複数のプロジェクトを作成・管理
- 💬 **セッション管理**: プロジェクトごとに複数のチャットセッションを作成
- 📝 **プロジェクト指示**: プロジェクトごとに指示を保存し、AIの動作をカスタマイズ
- 📊 **リアルタイム思考プロセス**: AIの思考過程をリアルタイムで確認
- 📂 **ワークスペース管理**: プロジェクトごとに生成されたファイルを整理
- 🌏 **多言語対応**: 日本語、英語、中国語に対応
- 🔄 **LMStudio連携**: ローカルLLMサーバーを自動起動

## インストール方法

以下の2つのインストール方法を提供しています。依存関係の管理の観点から、方法2（uvを使用）を推奨します。

### 方法1: condaを使用

1. 新しいconda環境を作成:

```bash
conda create -n open_manus python=3.12
conda activate open_manus
```

2. リポジトリをクローン:

```bash
git clone https://github.com/ZundamonnoVRChatkaisetu/OpenManusWebUI.git
cd OpenManusWebUI
```

3. 依存ライブラリをインストール:

```bash
pip install -r requirements.txt
```

### 方法2: uvを使用（推奨）

1. uv（高速Pythonパッケージインストーラー）をインストール:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. リポジトリをクローン:

```bash
git clone https://github.com/ZundamonnoVRChatkaisetu/OpenManusWebUI.git
cd OpenManusWebUI
```

3. 仮想環境を作成してアクティブ化:

```bash
uv venv
source .venv/bin/activate  # Unix/macOS
# または Windows:
# .venv\Scripts\activate
```

4. 依存ライブラリをインストール:

```bash
uv pip install -r requirements.txt
```

## 設定

OpenManusはLLM APIの設定が必要です。以下の手順で設定してください:

1. `config`ディレクトリに`config.toml`ファイルを作成（サンプルからコピー可能）:

```bash
cp config/config.example.toml config/config.toml
```

2. `config/config.toml`を編集してAPIキーを追加し設定をカスタマイズ:

```toml
# グローバルLLM設定
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # 実際のAPIキーに置き換え
max_tokens = 4096
temperature = 0.0

# 特定のLLMモデル向けのオプション設定
[llm.vision]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # 実際のAPIキーに置き換え
```

## クイックスタート

OpenManusを起動する一番簡単な方法:

```bash
python web_run.py
```

これでブラウザが自動的に開き、`http://localhost:8000`でWeb UIにアクセスできます。

## Web UIの起動オプション

いくつかの起動オプションを用意しています:

```bash
# 基本的な起動方法
python web_run.py

# ブラウザを自動で開かない
python web_run.py --no-browser

# ポート番号を変更する
python web_run.py --port 3000
```

## LMStudio連携機能

OpenManus Web UIは、LMStudioのAPIサーバーを自動的に起動することができるようになりました。これにより、ローカルの言語モデルを手動でLMStudioを起動・設定することなく利用できます:

```bash
# LMStudioサーバーを同時に起動
python web_run.py --lmstudio
```

LMStudio連携のその他のオプション:

```bash
# LMStudioのサーバーポートを指定（デフォルト: 1234）
python web_run.py --lmstudio --lm-port 8080

# ヘッドレスモードではなくGUIモードでLMStudioを起動
python web_run.py --lmstudio --lm-gui

# 他のOpenManus Webオプションと組み合わせて使用
python web_run.py --lmstudio --port 3000 --no-browser
```

この機能は自動的に:
- お使いのコンピューター上のLMStudioを検索
- APIサーバーを起動
- 適切なポートを設定
- OpenManusを終了する際にLMStudioも正しく終了

**注意**: この機能を使用するには、LMStudioがコンピューターにインストールされている必要があります。WindowsやmacOS、Linuxの一般的なインストール場所をシステムが自動的に検索します。

## プロジェクト管理機能

OpenManus Web UIは、プロジェクトベースのワークフローをサポートしています:

1. **プロジェクト作成**: 異なる目的や作業ごとにプロジェクトを作成できます
2. **プロジェクト指示**: 各プロジェクトに固有の指示を設定し、AIの動作をカスタマイズできます
3. **セッション管理**: 各プロジェクト内で複数のチャットセッションを作成できます
4. **ワークスペース分離**: プロジェクトごとに独立したファイル保存領域を持ちます

## インターフェース概要

Web UIは次の主要セクションで構成されています:

- **プロジェクトリスト**: 作成済みのプロジェクトを表示・選択できます
- **セッションリスト**: 現在のプロジェクト内のセッションを表示・選択できます
- **プロジェクト詳細**: プロジェクト名や指示を編集できます
- **AI思考プロセス**: AIが考えている内容をリアルタイムで表示します
- **ワークスペースファイル**: 生成されたファイルを表示・閲覧できます
- **チャットインターフェース**: AIとの対話を行うメインエリアです

## 機能の使い方

### プロジェクト管理

- **新規プロジェクト作成**: 「新規」ボタンをクリックしてプロジェクト名を入力
- **プロジェクト指示の設定**: プロジェクト詳細パネルで指示を入力し「保存」をクリック
- **プロジェクト名変更**: 「名前変更」ボタンをクリックして新しい名前を入力
- **プロジェクト削除**: 「削除」ボタンをクリックして確認

### セッション管理

- **新規セッション作成**: 「新規」ボタンをクリックして新しいセッションを開始
- **セッション切替**: セッションリストから選択してセッションを切り替え
- **セッション名変更**: 「名前変更」ボタンをクリックして新しい名前を入力
- **セッション削除**: 「削除」ボタンをクリックして確認

### チャット機能

- **メッセージ送信**: テキストエリアに入力して「送信」ボタンをクリック
- **処理停止**: 長時間の処理を「停止」ボタンで中断
- **履歴クリア**: 「クリア」ボタンでチャット履歴をリセット

## 開発者向け情報

このプロジェクトは以下の技術を使用しています:

- **バックエンド**: FastAPI, Python
- **フロントエンド**: JavaScript (ES6 Modules), HTML, CSS
- **データベース**: SQLite
- **その他**: WebSocket, TOML設定

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞

このプロジェクトは[OpenManus](https://github.com/mannaandpoem/OpenManus)をベースに拡張されています。また、Web UIの開発には[@YunQiAI](https://github.com/YunQiAI)氏の貢献が含まれています。
