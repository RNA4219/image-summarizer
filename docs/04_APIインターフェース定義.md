# APIインターフェース定義 v0.1

## 1. 目的

本書は、[01_要件定義.md](./01_要件定義.md) および
[02_仕様書.md](./02_仕様書.md) をもとに、
フロントエンドとバックエンドの間で合意すべき API 契約を固定するための文書である。

特に以下を明確にする。

- リクエストで送る項目
- レスポンスで返す項目
- モード値の固定表現
- エラーコードの扱い
- フロントエンド型とバックエンドスキーマの対応

本書は、実装開始前のインターフェース合意面として扱う。

## 2. 対象 API

本書の主対象は以下の API とする。

| メソッド | パス | 用途 | 備考 |
| --- | --- | --- | --- |
| POST | `/api/summarize` | 単一画像の OCR / 要約実行 | 正式対象 |
| POST | `/api/summarize-multiple` | 複数画像の OCR / 要約実行 | 拡張対象 |
| GET | `/health` | ヘルスチェック | 補助 |

## 3. 共通方針

### 3.1 データ交換形式

- ファイルアップロード API は `multipart/form-data` を使用する
- 正常レスポンス、異常レスポンスは JSON を使用する
- モード値は日本語表示名ではなく、固定の英字識別子を使用する

### 3.2 命名方針

- リクエストのフォーム項目は `snake_case`
- レスポンスの JSON フィールドは既存実装との整合上 `camelCase` を維持する
- エラーコードは英大文字 + アンダースコアで統一する

### 3.3 バージョニング方針

- 現時点では URI バージョニングは行わない
- 破壊的変更が必要になった場合は v2 エンドポイントを別途検討する

## 4. 列挙値定義

## 4.1 OCR モード

| 値 | 表示ラベル例 | 意味 |
| --- | --- | --- |
| `api` | `標準 (API OCR)` | OpenAI API ベース OCR |
| `local_llm` | `ローカル (Ollama OCR)` | Ollama マルチモーダル OCR |
| `high_accuracy` | `高精度 (NDLOCR-Lite)` | `NDLOCR-Lite` を利用する OCR |

## 4.2 要約モード

| 値 | 表示ラベル例 | 意味 |
| --- | --- | --- |
| `api` | `クラウド要約 (API)` | OpenAI API ベース要約 |
| `local_llm` | `ローカル要約 (Ollama)` | Ollama ローカル LLM 要約 |

## 5. `POST /api/summarize`

## 5.1 リクエスト

### Content-Type

```http
Content-Type: multipart/form-data
```

### フォーム項目

| 項目名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `file` | binary | 必須 | 対象画像ファイル |
| `ocr_mode` | string | 必須 | OCR 実行方式 |
| `summary_mode` | string | 必須 | 要約実行方式 |

### 制約

- `file` は JPG / JPEG / PNG のみを正式対象とする
- `ocr_mode` は `api` / `local_llm` / `high_accuracy` のみ許可
- `summary_mode` は `api` / `local_llm` のみ許可
- 空ファイルは不可
- サイズ上限は 10MB を想定する

### リクエスト例

```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@salary-slip.png" \
  -F "ocr_mode=high_accuracy" \
  -F "summary_mode=api"
```

## 5.2 正常レスポンス

### ステータスコード

```http
200 OK
```

### JSON 例

```json
{
  "filename": "salary-slip.png",
  "ocrMode": "high_accuracy",
  "summaryMode": "api",
  "summary": "この画像は給与明細です。対象期間と主要な金額項目が読み取れます。",
  "structuredData": {
    "documentType": "給与明細",
    "targetPeriod": "2024年10月",
    "recordCount": null,
    "summary": "この画像は給与明細です。対象期間と主要な金額項目が読み取れます。",
    "details": [
      {
        "label": "差引支給額",
        "value": "314,720円",
        "confidence": "high"
      }
    ],
    "uncertainItems": []
  },
  "extractedText": "平成22年10月度給与 ... 差引支給額 314,720 ...",
  "warnings": []
}
```

### フィールド定義

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `filename` | string | 必須 | 元ファイル名 |
| `ocrMode` | string | 必須 | 実際に使用した OCR モード |
| `summaryMode` | string | 必須 | 実際に使用した要約モード |
| `summary` | string | 必須 | 自然文要約 |
| `structuredData` | object | 必須 | 構造化された補助出力 |
| `extractedText` | string | 必須 | 抽出・整形後テキスト |
| `warnings` | string[] | 必須 | 軽微な問題や補足 |

## 5.3 異常レスポンス

### 共通 JSON 形式

```json
{
  "error": {
    "code": "INVALID_OCR_MODE",
    "message": "OCR方式が不正です。"
  }
}
```

### フィールド定義

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `error.code` | string | 必須 | エラー識別子 |
| `error.message` | string | 必須 | ユーザー向けメッセージ |

## 6. `POST /api/summarize-multiple`

## 6.1 リクエスト

### フォーム項目

| 項目名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `files` | binary[] | 必須 | 対象画像ファイル群 |
| `ocr_mode` | string | 必須 | OCR 実行方式 |
| `summary_mode` | string | 必須 | 要約実行方式 |

## 6.2 正常レスポンス

### JSON 例

```json
{
  "totalFiles": 2,
  "successCount": 1,
  "errorCount": 1,
  "results": [
    {
      "filename": "ok.png",
      "ocrMode": "api",
      "summaryMode": "api",
      "summary": "この画像は帳票です。",
      "structuredData": {
        "documentType": "帳票",
        "targetPeriod": null,
        "recordCount": null,
        "summary": "この画像は帳票です。",
        "details": [],
        "uncertainItems": []
      },
      "extractedText": "帳票テキスト...",
      "warnings": []
    },
    {
      "filename": "ng.png",
      "ocrMode": "api",
      "summaryMode": "api",
      "summary": "",
      "structuredData": {
        "documentType": "不明",
        "targetPeriod": null,
        "recordCount": null,
        "summary": "",
        "details": [],
        "uncertainItems": []
      },
      "extractedText": "",
      "warnings": [],
      "error": "テキスト抽出に失敗しました。"
    }
  ]
}
```

## 7. エラーコード定義

| HTTP | code | 用途 |
| --- | --- | --- |
| 400 | `FILE_REQUIRED` | ファイル未指定 |
| 400 | `EMPTY_FILE` | 空ファイル |
| 400 | `UNSUPPORTED_FILE_TYPE` | 非対応形式 |
| 400 | `INVALID_OCR_MODE` | OCR モード不正 |
| 400 | `INVALID_SUMMARY_MODE` | 要約モード不正 |
| 413 | `FILE_TOO_LARGE` | サイズ超過 |
| 422 | `TEXT_EXTRACTION_FAILED` | 抽出失敗 |
| 422 | `SUMMARY_GENERATION_FAILED` | 要約失敗 |
| 502 | `OPENAI_API_ERROR` | OpenAI API 呼び出し失敗 |
| 503 | `LOCAL_LLM_UNAVAILABLE` | Ollama 利用不可 |
| 503 | `LOCAL_LLM_MODEL_MISSING` | Ollama モデル未設定 |
| 503 | `LOCAL_LLM_TIMEOUT` | Ollama 応答タイムアウト |
| 503 | `NDLOCR_UNAVAILABLE` | `NDLOCR-Lite` 利用不可 |
| 503 | `NDLOCR_EXECUTION_FAILED` | `NDLOCR-Lite` 実行失敗 |
| 503 | `NDLOCR_TIMEOUT` | `NDLOCR-Lite` 実行タイムアウト |
| 500 | `INTERNAL_SERVER_ERROR` | 想定外エラー |

## 8. 型定義対応

## 8.1 フロントエンド側の想定型

```ts
type OcrMode = "api" | "local_llm" | "high_accuracy";
type SummaryMode = "api" | "local_llm";

interface ProcessingOptions {
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
}

interface SummarizeResponse {
  filename: string;
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
  summary: string;
  structuredData: StructuredSummary;
  extractedText: string;
  warnings: string[];
}
```

## 8.2 バックエンド側の想定スキーマ

```python
class SummarizeResponse(BaseModel):
    filename: str
    ocrMode: str
    summaryMode: str
    summary: str
    structuredData: StructuredSummary
    extractedText: str
    warnings: list[str]
```

## 8.3 対応方針

- フロントエンドは `snake_case` で送信し、`camelCase` を受信する
- バックエンドはフォーム受信時に `snake_case` を読み取る
- バックエンドはレスポンス時に `camelCase` フィールドを返す

## 9. UI 連携要件

フロントエンド画面では少なくとも以下を保持する。

- 選択ファイル
- OCR モード
- 要約モード
- ローディング状態
- エラーメッセージ
- 単一 / 複数処理結果

また結果表示では以下を扱えるようにする。

- 要約文
- 抽出テキスト
- warnings
- `ocrMode`
- `summaryMode`
- `structuredData`

## 10. 後方互換ポリシー

- `api` OCR + `api` 要約は既存の標準経路として維持する
- 追加モードは既存 UI や既存 API 利用者を壊さない形で導入する
- 将来 `structuredData` を省略不可から任意に変更する場合は、互換性影響を別途評価する

## 11. Phase 2 契約補足

- `ocr_mode=high_accuracy` は `NDLOCR-Lite` を利用する固定意味を持つ
- `summary_mode=local_llm` はローカル整形 / 要約を意味し、OCR エンジンの切替を含まない
- ローカル系モードで依存が不足している場合、自動的に `api` モードへ変更しない
- warnings は処理継続可能な軽微問題のみを格納し、依存未整備や実行失敗は error で返す
- `summary_mode=local_llm` の推奨既定モデルは `Qwen3.6-35B-A3B` とする
- `ocr_mode=local_llm` の推奨既定モデルは `Qwen3.6-35B-A3B` とする
- `ocr_mode=high_accuracy` では `NDLOCR-Lite` 出力の `<stem>.txt` を OCR 本文として採用する

## 12. 未確定事項

- `local_llm` OCR の入力形式を Ollama API にどう渡すか
- `local_llm` 要約の出力を `structuredData` 形式へどこまで合わせるか
- `high_accuracy` OCR の CLI 引数と出力形式の確定値
- `warnings` の生成責務を正規化層に限定するか、OCR / 要約層にも広げるか

