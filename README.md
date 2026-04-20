# 画像要約アプリ

画像ファイルをアップロードし、画像内テキストを抽出・整形・要約する Web アプリケーションです。

OCRと要約の処理方式を選択可能。クラウドAPI、ローカルLLM、高精度OCRを組み合わせて利用できます。

## 使い方

1. OCR方式と要約方式をラジオボタンで選択
2. JPG/PNG画像をアップロード（複数可）
3. 「要約実行」をクリック
4. 抽出テキスト、要約、構造化データを表示

## モード選択

### OCR方式（画像→テキスト抽出）

| モード | 用途 | 必要環境 |
|--------|------|----------|
| `api` | 一般用途（推奨） | OpenAI API キーのみ |
| `local_llm` | クラウド回避 | Ollama + マルチモーダルモデル |
| `high_accuracy` | 帳票・給与明細 | NDLOCR-Lite インストール |

### 要約方式（テキスト→要約生成）

| モード | 用途 | 必要環境 |
|--------|------|----------|
| `api` | 高品質要約（推奨） | OpenAI API キーのみ |
| `local_llm` | クラウド回避 | Ollama + モデル |

### 推奨組み合わせ

| ケース | OCR | 要約 |
|--------|-----|------|
| 通常利用 | `api` | `api` |
| 完全ローカル | `local_llm` | `local_llm` |
| 給与明細・帳票 | `high_accuracy` | `api` |

## APIレスポンス

```json
{
  "filename": "salary-slip.png",
  "ocrMode": "high_accuracy",
  "summaryMode": "api",
  "summary": "この画像は給与明細です...",
  "structuredData": {
    "documentType": "給与明細",
    "targetPeriod": "2024年10月",
    "details": [
      { "label": "差引支給額", "value": "314,720円", "confidence": "high" }
    ],
    "uncertainItems": []
  },
  "extractedText": "平成22年10月度給与...",
  "warnings": []
}
```

## エラーコード

| HTTP | Code | 原因 |
|------|------|------|
| 400 | `INVALID_OCR_MODE` | OCR方式指定不正 |
| 400 | `INVALID_SUMMARY_MODE` | 要約方式指定不正 |
| 503 | `LOCAL_LLM_UNAVAILABLE` | Ollama接続不可 |
| 503 | `LOCAL_LLM_MODEL_MISSING` | モデル未設定 |
| 503 | `NDLOCR_UNAVAILABLE` | NDLOCR-Lite未インストール |
| 422 | `TEXT_EXTRACTION_FAILED` | OCR結果空 |

## ドキュメント

- [API インターフェース定義](./docs/04_APIインターフェース定義.md)
- [Phase 2 詳細仕様](./docs/12_Phase2詳細仕様.md)
- [RUNBOOK](./docs/RUNBOOK.md)

## 構成

| Layer | 技術 |
|-------|------|
| Frontend | Next.js 14 + Material UI + TypeScript |
| Backend | FastAPI |
| Cloud API | OpenAI GPT-4 Vision |
| Local OCR | Ollama / NDLOCR-Lite |

## クイックスタート

### 一括起動

プロジェクトルートから実行してください。

```powershell
# Windows
.\start.bat
```

```bash
# macOS/Linux
./start.sh
```

### 手動起動

```powershell
# Windows
# 1. 環境変数設定
copy .env.example .env
# .env に OPENAI_API_KEY を設定

# 2. バックエンド起動
cd backend
py -3 -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. フロントエンド起動（別ターミナル）
cd frontend
npm install && npm run dev

# 4. アプリにアクセス
# http://localhost:3000 を開く
```

```bash
# macOS/Linux
# 1. 環境変数設定
cp .env.example .env
# .env に OPENAI_API_KEY を設定

# 2. バックエンド起動
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. フロントエンド起動（別ターミナル）
cd frontend
npm install && npm run dev

# 4. アプリにアクセス
# http://localhost:3000 を開く
```

## 環境変数

`.env.example` を `.env` にコピーして設定。

```env
# 必須
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini

# local_llm 利用時
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_OCR_MODEL=gemma4:e2b
OLLAMA_SUMMARY_MODEL=gemma4:e2b

# high_accuracy 利用時
NDLOCR_LITE_PATH=/path/to/ndlocr-lite
```

## 前提条件

- Node.js 18+
- Python 3.11+
- OpenAI API キー
- （local_llm）Ollama + マルチモーダルモデル
- （high_accuracy）NDLOCR-Lite

## API

| Endpoint | Description |
|----------|-------------|
| `POST /api/summarize` | 単一画像処理 |
| `POST /api/summarize-multiple` | 複数画像処理 |
| `GET /health` | ヘルスチェック |

## テスト

```powershell
# Backend unit tests
cd backend
pytest app/tests -q

# Frontend build
cd frontend
npm run build
```

## ライセンス

MIT
