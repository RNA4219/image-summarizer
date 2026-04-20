# 画像要約 PoC

画像ファイルをアップロードし、画像内テキストを抽出・整形・要約する画像要約 PoC です。

本リポジトリは既存アプリの流用前提ではなく、新規にプロトタイプから PoC を構築した体裁で整理しています。

現在は、既存の OpenAI API ベース経路を維持しつつ、以下の拡張方針で設計を進めています。

- OCR 方式を選択可能にする
- 要約方式を選択可能にする
- ローカル LLM（Ollama）連携に対応する
- `NDLOCR-Lite` を利用した高精度 OCR に対応する
- フロントエンドを青と白を基調にしたモダンな UI へ整える

**GitHub リポジトリ**: [RNA4219/image-summary-poc](https://github.com/RNA4219/image-summary-poc)

## 現在の設計方針

本リポジトリでは、以下の 2 軸で処理方式を切り替えられる構成を目指しています。

### OCR 方式

- `api`: 標準 API OCR
- `local_llm`: ローカル LLM OCR
- `high_accuracy`: 高精度 OCR (`NDLOCR-Lite`)

### 要約方式

- `api`: クラウド要約
- `local_llm`: ローカル要約

詳細は以下を参照してください。

- [要件定義](./docs/01_要件定義.md)
- [仕様書](./docs/02_仕様書.md)
- [API インターフェース定義](./docs/04_APIインターフェース定義.md)
- [画面仕様書](./docs/05_画面仕様書.md)
- [実装タスク分解](./docs/06_実装タスク分解.md)
- [テスト観点一覧](./docs/07_テスト観点一覧.md)
- [ローカル連携方式メモ](./docs/08_ローカル連携方式メモ.md)
- [フロントデザインガイド](./docs/10_フロントデザインガイド.md)
- [UI コンポーネント指針](./docs/11_UIコンポーネント指針.md)
- [Phase 2 詳細仕様](./docs/12_Phase2詳細仕様.md)
- [Phase 2 実装エージェント指示](./docs/13_Phase2実装エージェント指示.md)
- [Phase 2 バックエンド作業手順](./docs/14_Phase2バックエンド作業手順.md)
- [Phase 2 エージェント依頼文](./docs/15_Phase2エージェント依頼文.md)
- [RUNBOOK](./docs/RUNBOOK.md)

`docs/src.txt` は初期検討時のメモを残した履歴参照用ファイルです。現行仕様の正本は、上記の Markdown ドキュメント群を優先します。

## スクリーンショット

### 画像選択前
![画像選択前](docs/screenshots/画像選択前.png)

### 画像選択
![画像選択](docs/screenshots/画像選択.png)

### 出力例

- E2E の参考出力は `tests/e2e/test-results/TEST_RESULTS.md` を参照してください。

## 構成

- フロントエンド: Next.js 14 (App Router) + Material UI + TypeScript
- バックエンド: FastAPI
- 既存クラウド経路: OpenAI API
- 前処理: Pillow（2x 拡大、2 値化）
- E2E テスト: Playwright

## UI 方針

- 青と白を基調としたクリーンな配色
- 業務利用でも違和感のないモダンな印象
- カードベースで情報を整理し、結果を読みやすく表示

## フェーズ計画

### Phase 1

- OCR 方式 / 要約方式のモード切替土台を実装
- API 契約更新
- UI へのラジオボタン導入
- 既存 `api` / `api` 経路の後方互換維持

### Phase 2

- Ollama OCR / 要約の接続
- `NDLOCR-Lite` 高精度 OCR の接続

### Phase 3

- 推奨モード表示
- 高精度後処理改善
- warnings 表示改善

## セットアップ

### 前提条件

- Node.js 18 以上
- Python 3.11 以上
- OpenAI API キー

Phase 2 以降では以下も必要です。

- Ollama
- マルチモーダル対応モデル
- `C:\Users\ryo-n\Codex_dev\ndlocr-lite`

### 環境変数

ルートディレクトリで `.env.example` を `.env` にコピーして設定します。

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

`.env.example` には上記の Phase 2 候補も含めています。Phase 1 の時点では OpenAI 系設定を中心に利用し、未使用項目は空欄のままで問題ありません。

### バックエンド

```powershell
cd <project-root>\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### フロントエンド

```powershell
cd <project-root>\frontend
npm install
```

### E2E テスト

```powershell
cd <project-root>\tests\e2e
npm install
npx playwright install chromium
```

## 起動

### 手動起動

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

### 補助スクリプト

- `start.bat`
- `start.ps1`
- `start-backend.ps1`
- `start-frontend.ps1`

## アクセス先

- アプリ: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000](http://localhost:8000)
- API ドキュメント: [http://localhost:8000/docs](http://localhost:8000/docs)

## API 概要

### `POST /api/summarize`

単一ファイルを処理する正式対象 API です。

フォーム項目:

- `file`
- `ocr_mode`
- `summary_mode`

### `POST /api/summarize-multiple`

複数ファイルを処理する拡張 API です。

フォーム項目:

- `files`
- `ocr_mode`
- `summary_mode`

詳細は [04_APIインターフェース定義.md](./04_APIインターフェース定義.md) を参照してください。

## テスト

### バックエンド

```powershell
cd <project-root>\backend
.\.venv\Scripts\Activate.ps1
pytest app/tests -q
```

### フロントエンドビルド

```powershell
cd <project-root>\frontend
npm run build
```

### E2E

```powershell
cd <project-root>\tests\e2e
npm run test:e2e
```

## ディレクトリ構成

```text
.
├── .env
├── .env.example
├── README.md
├── docs/
│   ├── 01_要件定義.md
│   ├── 02_仕様書.md
│   ├── 04_APIインターフェース定義.md
│   ├── 05_画面仕様書.md
│   ├── 06_実装タスク分解.md
│   ├── 07_テスト観点一覧.md
│   ├── 08_ローカル連携方式メモ.md
│   ├── 09_Phase1実装順チェックリスト.md
│   ├── 10_フロントデザインガイド.md
│   ├── 11_UIコンポーネント指針.md
│   ├── 12_Phase2詳細仕様.md
│   ├── 13_Phase2実装エージェント指示.md
│   ├── 14_Phase2バックエンド作業手順.md
│   ├── 15_Phase2エージェント依頼文.md
│   ├── CHECKLIST.md
│   ├── RUNBOOK.md
│   ├── src.txt
│   └── screenshots/
├── backend/
├── frontend/
└── tests/
```

## メモ

- `api` OCR + `api` 要約は既存の標準経路として維持します
- ローカル系モードは Phase 2 で実接続する前提です
- `NDLOCR-Lite` は初期案として CLI 連携を優先します

## ライセンス

MIT

