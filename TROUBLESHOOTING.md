# トラブルシューティングガイド

OpenManus Web UIを使用する際に発生する可能性のある一般的な問題と解決方法をこのガイドで説明します。

## LMStudioの起動関連の問題

### MaxListenersExceededWarning エラー

```
LMStudio Error: MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added to [Server]. MaxListeners is 10.
```

**解決策:** バージョン1.1.0以降では、自動的に最大リスナー数を増やすパラメータが追加されています。古いバージョンを使用している場合は更新してください。

### LMStudioが見つからないというエラー

```
⚠️ LMStudioの実行ファイルが見つかりませんでした。手動で起動してください。
```

**解決策:** 
1. LMStudioが正しくインストールされていることを確認
2. 標準的なインストール場所にインストールされていない場合は、手動で起動する
3. LMStudioを起動し、APIサーバーを有効にして、ポートを設定する

## 権限関連の問題

### Chocolateyの権限エラー

以下のようなエラーメッセージが表示される場合：

```
Chocolatey detected you are not running from an elevated command shell (cmd/powershell).
You may experience errors - many functions/packages require admin rights.

Unable to obtain lock file access on 'C:\ProgramData\chocolatey\lib\...'

パス 'C:\ProgramData\chocolatey\lib-bad' へのアクセスが拒否されました。
```

**解決策:**

1. **管理者としてOpenManus Web UIを実行**:
   - Windowsの場合、コマンドプロンプトまたはPowerShellを「管理者として実行」し、その中で `python web_run.py` を実行
   - MacOS/Linuxの場合、`sudo python web_run.py` コマンドを使用

2. **プロジェクト指示でパッケージマネージャーの使用を避ける**:
   - AIに対して、管理者権限が必要なツール（Chocolatey、npm、pip など）の使用を避けるよう指示を追加
   - 例：「管理者権限が必要なツールやパッケージマネージャーの使用は避けてください」

3. **Chocolateyのロックファイルをクリーンアップ** (Windows管理者のみ):
   - 管理者としてコマンドプロンプトを開く
   - `cd C:\ProgramData\chocolatey\lib` に移動
   - `dir /a` で隠しファイルを含むすべてのファイルを表示
   - `*.lock` ファイルを見つけて削除: `del *.lock`

## AIとの対話における問題

### AI応答が不適切または不完全

**解決策:**
1. プロジェクト指示を明確にする
2. プロンプトを具体的に記述する
3. 段階的な指示を与える

### ファイル生成エラー

```
[WinError 2] 指定されたファイルが見つかりません。
```

**解決策:**
1. 相対パスではなく絶対パスを使用するようAIに指示
2. AIに現在のディレクトリ構造を確認するよう依頼
3. ファイル名に特殊文字や空白を使用しないように指示

## その他の一般的な問題

### Webサーバー起動エラー

```
Address already in use
```

**解決策:**
1. 別のポートを指定: `python web_run.py --port 8080`
2. 既存のプロセスを終了: `taskkill /F /IM python.exe` (Windowsの場合)

### メモリ不足エラー

**解決策:**
1. 不要なアプリケーションを閉じる
2. 大きなファイルの処理を避ける
3. チャット履歴を定期的にクリアする

### セッション/プロジェクトの保存エラー

**解決策:**
1. ディスク容量を確認
2. `data` ディレクトリのアクセス権限を確認
3. データベースファイルの破損がないか確認: `app/web/database.py` を参照

## サポートの受け方

問題が解決しない場合は、以下の情報を含めて問題を報告してください：

1. 使用しているオペレーティングシステムとバージョン
2. 発生したエラーメッセージの詳細なコピー
3. 問題を再現するための手順
4. ログファイル（`logs` ディレクトリ内）

## アップデート情報

新しいバージョンがリリースされた場合は、最新の機能やバグ修正を利用するため、リポジトリを更新することをお勧めします：

```bash
git pull
pip install -r requirements.txt
```

最新のトラブルシューティング情報については、このドキュメントを定期的に確認してください。
