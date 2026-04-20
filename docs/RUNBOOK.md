# RUNBOOK v0.2

## 1. 目的

本書は、`画像要約 PoC` における開発・検証・ローカル連携の運用手順をまとめた実行ガイドである。

本書は以下の用途で利用する。

- 開発開始前の確認
- Phase 1 実装時の進行順確認
- ローカル起動とテスト実行
- Phase 2 の Ollama / NDLOCR-Lite 連携準備

## 2. 参照順

実装または検討を始める前に、以下の順で読む。

1. [01_要件定義.md](./01_要件定義.md)
2. [02_仕様書.md](./02_仕様書.md)
3. [04_APIインターフェース定義.md](./04_APIインターフェース定義.md)
4. [05_画面仕様書.md](./05_画面仕様書.md)
5. [10_フロントデザインガイド.md](./10_フロントデザインガイド.md)
6. [11_UIコンポーネント指針.md](./11_UIコンポーネント指針.md)
7. [12_Phase2詳細仕様.md](./12_Phase2詳細仕様.md)
8. [13_Phase2実装エージェント指示.md](./13_Phase2実装エージェント指示.md)
9. [14_Phase2バックエンド作業手順.md](./14_Phase2バックエンド作業手順.md)
10. [15_Phase2エージェント依頼文.md](./15_Phase2エージェント依頼文.md)
11. [06_実装タスク分解.md](./06_実装タスク分解.md)
12. [07_テスト観点一覧.md](./07_テスト観点一覧.md)
13. [08_ローカル連携方式メモ.md](./08_ローカル連携方式メモ.md)

`src.txt` は初期の検討メモとして保持する履歴資料であり、現行仕様の正本ではない。判断に迷う場合は上記の Markdown ドキュメントを優先する。

## 3. 開発方針

- 既存の `api` OCR + `api` 要約経路を壊さずに拡張する
- まず Phase 1 でモード切替の枠組みを入れる
- Ollama と NDLOCR-Lite の実接続は Phase 2 で行う
- UI / API / テストを契約ベースで揃えて進める
- ドキュメント変更を先行させ、実装変更はそれに追従させる

## 4. 実行フェーズ

## 4.1 Phase 1

目的:

- OCR 方式 / 要約方式のモード選択を導入する
- API 契約を新仕様に揃える
- 既存経路の後方互換を維持する

対象:

- `ocr_mode` / `summary_mode` 導入
- フロントラジオボタン導入
- 抽象化ポイント追加
- API / UI / テスト更新

完了条件:

- [06_実装タスク分解.md](./06_実装タスク分解.md) の Phase 1 完了条件を満たす

## 4.2 Phase 2

目的:

- Ollama OCR / 要約を接続する
- NDLOCR-Lite 高精度 OCR を接続する

対象:

- Ollama HTTP API
- NDLOCR-Lite 連携
- ローカル連携テスト

## 4.3 Phase 3

目的:

- 推奨モード表示
- 高精度後処理改善
- warnings 表示改善

## 5. ローカル開発環境

## 5.1 前提条件

- Node.js 18 以上
- Python 3.11 以上
- OpenAI API キー
- Windows 環境を基本想定

Phase 2 以降では以下も必要。

- Ollama
- マルチモーダル対応モデル
- `C:\Users\ryo-n\Codex_dev\ndlocr-lite`

## 5.2 環境変数

ルートの `.env` を利用する。

最低限:

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5-mini
```

Phase 2 の候補:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_OCR_MODEL=<model-name>
OLLAMA_SUMMARY_MODEL=<model-name>
OLLAMA_TIMEOUT_SECONDS=60
NDLOCR_LITE_PATH=C:\Users\ryo-n\Codex_dev\ndlocr-lite
NDLOCR_TIMEOUT_SECONDS=60
```

ルートの `.env.example` には上記候補を記載済みとし、Phase 1 では OpenAI 系設定のみでも開発を進められる前提とする。未使用項目は空欄運用を許容する。

## 6. セットアップ

## 6.1 バックエンド

```powershell
cd <project-root>\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 6.2 フロントエンド

```powershell
cd <project-root>\frontend
npm install
```

## 6.3 E2E

```powershell
cd <project-root>\tests\e2e
npm install
npx playwright install chromium
```

## 7. 起動

## 7.1 手動起動

バックエンド:

```powershell
cd <project-root>\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

フロントエンド:

```powershell
cd <project-root>\frontend
npm run dev
```

## 7.2 補助スクリプト

- `start.bat`
- `start.ps1`
- `start-backend.ps1`
- `start-frontend.ps1`

ただし、Phase 1 実装中は手動起動のほうが切り分けしやすい。

## 8. テスト実行

## 8.1 バックエンド

```powershell
cd <project-root>\backend
.\.venv\Scripts\Activate.ps1
pytest app/tests -q
```

## 8.2 フロントエンドビルド確認

```powershell
cd <project-root>\frontend
npm run build
```

## 8.3 E2E

```powershell
cd <project-root>\tests\e2e
npm run test:e2e
```

## 9. Phase 1 の進め方

推奨順は以下とする。

1. API 契約に必要なモード値と例外定義を追加する
2. Router / Pipeline / Service の抽象化を入れる
3. レスポンススキーマへ `ocrMode` / `summaryMode` を追加する
4. フロント型定義と API 呼び出しを更新する
5. 画面に OCR / 要約ラジオボタンを追加する
6. 結果表示へ利用モードを追加する
7. テストを新契約へ追従させる

詳細は [06_実装タスク分解.md](./06_実装タスク分解.md) を参照する。

## 10. Phase 2 の進め方

### Ollama

1. 接続先とモデル名を設定値化する
2. ヘルスチェックまたは疎通確認を行う
3. `summary_mode=local_llm` を先に実装する
4. `ocr_mode=local_llm` を実装する

### NDLOCR-Lite

1. CLI 実行方式で疎通確認する
2. 一時ファイル運用を決める
3. OCR テキストを既存正規化層に接続する

詳細は [08_ローカル連携方式メモ.md](./08_ローカル連携方式メモ.md) を参照する。

## 11. よくある確認ポイント

- `.env` が正しく読まれているか
- `api` / `api` 経路が壊れていないか
- `ocr_mode` / `summary_mode` が API へ届いているか
- `ocrMode` / `summaryMode` がレスポンスへ返っているか
- UI 上の表示ラベルが仕様書と一致しているか
- ローカル未設定時に適切なエラーが出ているか

## 12. 障害切り分け

### API が 400 を返す

- フォーム項目不足
- モード値不正
- 非対応形式
- 空ファイル

### API が 502 を返す

- OpenAI API 呼び出し失敗

### API が 503 を返す

- Ollama 未起動
- Ollama モデル未準備
- NDLOCR-Lite 未設定

### 画面に結果が出ない

- フロント型定義とレスポンス JSON の不整合
- `ocrMode` / `summaryMode` の表示漏れ

## 13. 今後更新が必要な箇所

- Phase 2 実装後の具体コマンド
- Ollama モデル名
- NDLOCR-Lite 実行手順の確定版
- warnings 表示運用

