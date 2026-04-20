# FastAPI 分割設計 v0.2

## 1. 目的

本書は、画像要約アプリのバックエンドを FastAPI で実装する際の責務分割を定義する。

現在の要件では、バックエンドは単に
「画像を受け取り、OpenAI API で要約する」
だけではなく、以下を扱う必要がある。

- OCR 方式の切り替え
- 要約方式の切り替え
- 既存 `api` / `api` 経路の後方互換維持
- 将来の Ollama / `NDLOCR-Lite` 連携

そのため、HTTP 層、モード切替層、個別エンジン呼び出し層を明確に分離する。

## 2. ディレクトリ構成

```text
backend/
  app/
    __init__.py
    main.py
    config.py

    routers/
      __init__.py
      summarize.py

    schemas/
      __init__.py
      summarize.py
      error.py

    services/
      __init__.py
      pipeline.py
      extraction.py
      normalization.py
      summarization.py
      modes.py

    clients/
      __init__.py
      openai_client.py
      ollama_client.py        # Phase 2
      ndlocr_client.py        # Phase 2

    utils/
      __init__.py
      file_validation.py
      exceptions.py
      preprocessing.py

    tests/
      __init__.py
      conftest.py
      test_summarize_api.py
      test_normalization.py
```

## 3. 分割方針

今回の分割方針は以下のとおり。

- `router`: HTTP 入出力のみ
- `schema`: API 契約
- `pipeline`: 全体の処理順制御
- `service`: モードごとの業務処理
- `client`: 外部エンジン接続
- `utils`: 共通処理

### 重要な原則

- router から client を直接呼ばない
- pipeline が「順番」を知る
- extraction / summarization は「モード切替」を知る
- client は外部 API / ローカル実行の詳細だけを知る

## 4. レイヤ責務

## 4.1 `app/main.py`

責務:

- `FastAPI()` 生成
- router 登録
- CORS 設定
- 共通例外ハンドラ登録

ここでは業務処理を持たない。

## 4.2 `app/config.py`

責務:

- OpenAI 設定
- ファイルサイズ / MIME type
- 将来の Ollama 設定
- 将来の `NDLOCR-Lite` 設定

想定例:

```python
class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_timeout: float = 60.0
    max_file_size_bytes: int = 10 * 1024 * 1024
    allowed_content_types: tuple[str, ...] = ("image/jpeg", "image/png")

    ollama_base_url: str = "http://localhost:11434"
    ollama_ocr_model: str = ""
    ollama_summary_model: str = ""
    ollama_timeout_seconds: float = 60.0

    ndlocr_lite_path: str = ""
    ndlocr_timeout_seconds: float = 60.0
```

## 4.3 `app/routers/summarize.py`

責務:

- `POST /api/summarize`
- `POST /api/summarize-multiple`
- `file` / `files`
- `ocr_mode`
- `summary_mode`

の受け取り

- pipeline 呼び出し
- schema に詰めて返す

router は以下を直接扱わない。

- OpenAI 呼び出し詳細
- Ollama 呼び出し詳細
- `NDLOCR-Lite` 実行詳細
- 正規化ロジック

## 4.4 `app/schemas/summarize.py`

責務:

- `SummarizeResponse`
- `MultiSummarizeResponse`
- `SingleFileResult`
- `StructuredSummary`

ポイント:

- `ocrMode`
- `summaryMode`

をレスポンス契約として含める。

## 4.5 `app/schemas/error.py`

責務:

- `ErrorDetail`
- `ErrorResponse`

エラー形式は常に共通 JSON に揃える。

## 4.6 `app/services/pipeline.py`

責務:

- ファイルバリデーション
- OCR 実行
- 正規化
- 要約
- レスポンス DTO 構築

pipeline は以下の順番を知る唯一のレイヤにする。

1. validate
2. extract
3. normalize
4. summarize
5. build response

想定 I/F:

```python
async def process_single_image(
    file: UploadFile,
    ocr_mode: str,
    summary_mode: str,
) -> SingleFileResult:
    ...
```

## 4.7 `app/services/modes.py`

責務:

- OCR モード定義
- 要約モード定義
- 妥当性チェック

想定内容:

```python
OCR_MODES = ("api", "local_llm", "high_accuracy")
SUMMARY_MODES = ("api", "local_llm")
```

モード定義を 1 か所に寄せることで、router / service / test のずれを防ぐ。

## 4.8 `app/services/extraction.py`

責務:

- `ocr_mode` に応じた OCR 抽出の切り替え
- 前処理の呼び出し
- 抽出結果が空の場合の例外

想定 I/F:

```python
async def extract_text(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    ocr_mode: str,
) -> str:
    ...
```

内部実装候補:

- `api` -> `extract_text_with_openai(...)`
- `local_llm` -> `extract_text_with_ollama(...)`
- `high_accuracy` -> `extract_text_with_ndlocr(...)`

Phase 1 では、`api` 以外は未接続エラーを返す暫定実装でもよい。

## 4.9 `app/services/normalization.py`

責務:

- 改行統一
- 空白整理
- 文書系テキストの軽微整形
- warnings 生成

この層は OCR エンジンの違いを意識せず、文字列入力だけを扱う。

## 4.10 `app/services/summarization.py`

責務:

- `summary_mode` に応じた要約方式の切り替え
- 結果を `StructuredSummary` 互換の辞書へ整える
- 空要約時の例外

想定 I/F:

```python
async def summarize_text(
    normalized_text: str,
    summary_mode: str,
) -> dict:
    ...
```

内部実装候補:

- `api` -> `summarize_text_with_openai(...)`
- `local_llm` -> `summarize_text_with_ollama(...)`

## 4.11 `app/clients/openai_client.py`

責務:

- OpenAI クライアント生成
- 画像 OCR 呼び出し
- 要約呼び出し

ここでは OpenAI 固有の API 呼び出し詳細のみを扱う。

## 4.12 `app/clients/ollama_client.py`

責務:

- Ollama HTTP API 呼び出し
- OCR 用モデル実行
- 要約用モデル実行

Phase 2 で追加する想定。

## 4.13 `app/clients/ndlocr_client.py`

責務:

- `NDLOCR-Lite` 実行
- CLI 実行または内部 import のラップ
- OCR 結果文字列の取り出し

Phase 2 初期は CLI ラップが第一候補。

## 4.14 `app/utils/file_validation.py`

責務:

- MIME type 確認
- 空ファイル確認
- サイズ上限確認
- bytes 読み込み

## 4.15 `app/utils/exceptions.py`

責務:

- 共通基底例外
- 入力エラー
- OCR / 要約失敗
- 外部接続失敗
- モード不正

想定例外:

- `UnsupportedFileTypeError`
- `EmptyFileError`
- `FileTooLargeError`
- `InvalidOCRModeError`
- `InvalidSummaryModeError`
- `TextExtractionFailedError`
- `SummaryGenerationFailedError`
- `OpenAIAPIError`
- `LocalLLMUnavailableError`
- `NDLOCRUnavailableError`

## 5. 呼び出し関係

```text
main.py
  -> routers/summarize.py
       -> services/pipeline.py
            -> utils/file_validation.py
            -> services/extraction.py
                 -> services/modes.py
                 -> utils/preprocessing.py
                 -> clients/openai_client.py
                 -> clients/ollama_client.py
                 -> clients/ndlocr_client.py
            -> services/normalization.py
            -> services/summarization.py
                 -> services/modes.py
                 -> clients/openai_client.py
                 -> clients/ollama_client.py
            -> schemas/summarize.py
       -> schemas/error.py
       -> utils/exceptions.py
```

## 6. テストしやすい分割

### `test_summarize_api.py`

- API 契約
- ステータスコード
- エラー形式
- `ocr_mode` / `summary_mode`

### `test_normalization.py`

- 改行整形
- 空白整理
- warnings 生成

### 将来追加候補

- `test_extraction_modes.py`
- `test_summarization_modes.py`
- `test_pipeline_modes.py`

## 7. 最小実装ライン

Phase 1 の最小実装ラインは以下。

```text
app/main.py
app/config.py
app/routers/summarize.py
app/schemas/summarize.py
app/schemas/error.py
app/services/pipeline.py
app/services/modes.py
app/services/extraction.py
app/services/normalization.py
app/services/summarization.py
app/clients/openai_client.py
app/utils/file_validation.py
app/utils/exceptions.py
app/tests/test_summarize_api.py
app/tests/test_normalization.py
```

## 8. 推奨実装順

1. `schemas/`
2. `services/modes.py`
3. `utils/exceptions.py`
4. `utils/file_validation.py`
5. `clients/openai_client.py`
6. `services/extraction.py`
7. `services/normalization.py`
8. `services/summarization.py`
9. `services/pipeline.py`
10. `routers/summarize.py`
11. `main.py`
12. `tests/test_summarize_api.py`

## 9. 設計上のポイント

- router は薄く保つ
- pipeline が処理順を持つ
- extraction / summarization がモード切替点になる
- client は外部エンジン差異を吸収する
- 正規化は OCR 方式に依存しない

