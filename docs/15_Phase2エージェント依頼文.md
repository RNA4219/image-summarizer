# Phase 2 エージェント依頼文

以下をそのまま実装担当エージェントへ渡すこと。

```text
あなたは `画像要約 PoC` の Phase 2 バックエンド実装担当です。

目的:
- 既存 `api/api` 経路を壊さずに、以下を実装してください。
  - `ocr_mode=local_llm`
  - `summary_mode=local_llm`
  - `ocr_mode=high_accuracy`

参照順:
1. `docs/12_Phase2詳細仕様.md`
2. `docs/14_Phase2バックエンド作業手順.md`
3. `docs/13_Phase2実装エージェント指示.md`
4. `docs/04_APIインターフェース定義.md`
5. `docs/02_仕様書.md`

固定仕様:
- 自動フォールバックは禁止
- `ocr_mode=high_accuracy` は `NDLOCR-Lite` 固定
- `summary_mode=local_llm` は Ollama 要約
- `ocr_mode=local_llm` は Ollama マルチモーダル OCR
- 推奨既定モデル名は OCR / 要約ともに `Qwen3.6-35B-A3B`

NDLOCR-Lite 実行仕様:
- 正式実行:
  - `ndlocr-lite --sourceimg <input-image-path> --output <output-dir>`
- フォールバック実行:
  - `python ocr.py --sourceimg <input-image-path> --output <output-dir>`
- 出力は `<stem>.txt` / `<stem>.json` / `<stem>.xml`
- 本アプリでは `<stem>.txt` を OCR 本文として一次採用

必須エラーコード:
- `LOCAL_LLM_UNAVAILABLE`
- `LOCAL_LLM_MODEL_MISSING`
- `LOCAL_LLM_TIMEOUT`
- `NDLOCR_UNAVAILABLE`
- `NDLOCR_EXECUTION_FAILED`
- `NDLOCR_TIMEOUT`
- `TEXT_EXTRACTION_FAILED`
- `SUMMARY_GENERATION_FAILED`

実装順:
1. 設定値を `config.py` に反映
2. 例外とエラーコードを追加
3. `clients/ollama_client.py` を追加
4. `summary_mode=local_llm` を実装
5. `ocr_mode=local_llm` を実装
6. `clients/ndlocr_client.py` を追加
7. `ocr_mode=high_accuracy` を実装
8. `pipeline.py` を接続
9. テスト追加
10. `api/api` 回帰確認

禁止事項:
- `high_accuracy` で OpenAI OCR に逃がさない
- `local_llm` 失敗時に `api` へ切り替えない
- error を warnings に落として成功扱いしない
- ドキュメント未更新のまま契約変更しない

完了条件:
- `summary_mode=local_llm` が動作
- `ocr_mode=local_llm` が動作
- `ocr_mode=high_accuracy` が動作
- `high_accuracy + local_llm` が動作
- 必須エラーコードを出し分け可能
- 既存 `api/api` 経路に回帰なし

作業後は、変更ファイル一覧、実施内容、未解決事項、テスト結果を簡潔に報告してください。
```

