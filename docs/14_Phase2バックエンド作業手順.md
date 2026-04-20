# Phase 2 バックエンド作業手順

## 1. 目的

Phase 2 のバックエンド実装を、そのまま着手できる順序に分解した手順書。

対象:

- `ocr_mode=local_llm`
- `summary_mode=local_llm`
- `ocr_mode=high_accuracy`

## 2. 事前確認

- 既存 `api/api` 経路が動くこと
- `.env.example` に Phase 2 設定があること
- 参照ドキュメント:
  - `docs/12_Phase2詳細仕様.md`
  - `docs/13_Phase2実装エージェント指示.md`
  - `docs/03_FastAPI 分割設計.md`

## 3. 作業順

### B2-01 設定値を実装へ反映

やること:

- `OLLAMA_BASE_URL`
- `OLLAMA_OCR_MODEL`
- `OLLAMA_SUMMARY_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `NDLOCR_LITE_PATH`
- `NDLOCR_TIMEOUT_SECONDS`
- `NDLOCR_TEMP_DIR`

を `config.py` に揃える。

完了条件:

- Phase 2 で必要な設定値をコードから参照できる
- 未設定でもサーバ起動自体は失敗しない

### B2-02 例外とエラーコードを追加

やること:

- `LOCAL_LLM_MODEL_MISSING`
- `LOCAL_LLM_TIMEOUT`
- `NDLOCR_EXECUTION_FAILED`
- `NDLOCR_TIMEOUT`

に対応する例外を追加する。

完了条件:

- 例外から API エラーレスポンスへ変換できる

### B2-03 Ollama クライアントを追加

やること:

- `clients/ollama_client.py` を追加
- OCR 用呼び出し関数を追加
- 要約用呼び出し関数を追加
- タイムアウト処理を追加

固定仕様:

- 推奨既定モデル名は `Qwen3.6-35B-A3B`
- OCR 用と要約用で別設定を許可する
- モデル未設定時は `LOCAL_LLM_MODEL_MISSING`

完了条件:

- OCR 用と要約用の 2 経路を個別に呼べる
- 接続失敗とタイムアウトを区別できる

### B2-04 要約の `local_llm` を先に実装

やること:

- `services/summarization.py` に `local_llm` 分岐を追加
- Ollama へ整形 / 要約プロンプトを送る
- 要約本文を返す
- `structuredData` は不足分を後段補完する

完了条件:

- `summary_mode=local_llm` が単独で動作する
- 空要約時に `SUMMARY_GENERATION_FAILED` を返せる

### B2-05 OCR の `local_llm` を実装

やること:

- `services/extraction.py` に `local_llm` 分岐を追加
- 画像を Ollama へ渡して OCR を実行する
- 非空文字列を返す

完了条件:

- `ocr_mode=local_llm` が単独で動作する
- 空 OCR 時に `TEXT_EXTRACTION_FAILED` を返せる

### B2-06 NDLOCR クライアントを追加

やること:

- `clients/ndlocr_client.py` を追加
- 単一画像実行ラッパを追加
- 一時ディレクトリ制御を追加
- 出力 `.txt` 読み取りを追加

固定仕様:

- 正式実行:
  - `ndlocr-lite --sourceimg <input-image-path> --output <output-dir>`
- フォールバック実行:
  - `python ocr.py --sourceimg <input-image-path> --output <output-dir>`
- `<stem>.txt` を一次採用

完了条件:

- `NDLOCR-Lite` 実行から OCR 本文取得まで 1 関数で完結する
- `.txt` 不在時に `TEXT_EXTRACTION_FAILED` を返せる
- 実行失敗時に `NDLOCR_EXECUTION_FAILED` を返せる

### B2-07 OCR の `high_accuracy` を実装

やること:

- `services/extraction.py` に `high_accuracy` 分岐を追加
- `ndlocr_client.py` を呼ぶ
- 取得した `.txt` を正規化層へ渡す

完了条件:

- `ocr_mode=high_accuracy` が動作する
- OpenAI OCR へ自動切替しない

### B2-08 pipeline を通しで接続

やること:

- `pipeline.py` で新モードを通す
- `ocrMode` / `summaryMode` をレスポンスへ反映する
- warnings と error の責務を分ける

完了条件:

- 以下の組み合わせが処理可能
  - `api + local_llm`
  - `local_llm + api`
  - `local_llm + local_llm`
  - `high_accuracy + api`
  - `high_accuracy + local_llm`

### B2-09 テストを追加

やること:

- Ollama 要約正常系
- Ollama OCR 正常系
- NDLOCR 正常系
- `LOCAL_LLM_MODEL_MISSING`
- `LOCAL_LLM_TIMEOUT`
- `NDLOCR_EXECUTION_FAILED`
- `NDLOCR_TIMEOUT`

のテストを追加する。

完了条件:

- Phase 2 の主要正常系と失敗系が最低限カバーされる

### B2-10 回帰確認

やること:

- `api/api` 経路を再確認
- 既存レスポンス形式が壊れていないか確認
- 追加エラーコードで既存処理を壊していないか確認

完了条件:

- 既存標準経路に回帰がない

## 4. 実装順の原則

順番は必ず以下を守る。

1. 要約 `local_llm`
2. OCR `local_llm`
3. `high_accuracy`

理由:

- 要約のほうが画像入力差分が少なく実装難度が低い
- `NDLOCR-Lite` は外部プロセス制御が入るため最後に回す

## 5. 禁止事項

- 失敗時に別モードへ自動フォールバックしない
- `high_accuracy` で OpenAI OCR を使わない
- `LOCAL_LLM_MODEL_MISSING` を `LOCAL_LLM_UNAVAILABLE` へ雑にまとめない
- `NDLOCR` 出力の `.json` を一次採用しない

## 6. 完了判定

- `summary_mode=local_llm` 実装済み
- `ocr_mode=local_llm` 実装済み
- `ocr_mode=high_accuracy` 実装済み
- Phase 2 エラーコードの出し分けがある
- `api/api` 回帰なし

