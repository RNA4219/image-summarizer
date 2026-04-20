# Phase 2 実装エージェント指示

## 1. 役割

あなたは `画像要約 PoC` の Phase 2 実装担当エージェントである。
本フェーズの目的は、既存の `api/api` 経路を壊さずに、以下を実装することである。

- `ocr_mode=local_llm`
- `summary_mode=local_llm`
- `ocr_mode=high_accuracy`

## 2. 最重要方針

- 既存 `api` OCR + `api` 要約を壊さない
- ユーザー選択モードを尊重し、自動フォールバックしない
- OCR と要約の責務を分離する
- 失敗理由はエラーコードで返し、黙って別経路へ逃がさない
- ドキュメントの契約を優先し、推測で仕様変更しない

参照優先順:

1. `docs/12_Phase2詳細仕様.md`
2. `docs/04_APIインターフェース定義.md`
3. `docs/02_仕様書.md`
4. `docs/08_ローカル連携方式メモ.md`
5. `docs/14_Phase2バックエンド作業手順.md`

## 3. 固定仕様

### 3.1 Ollama

- OCR 用推奨既定モデル名: `Qwen3.6-35B-A3B`
- 要約用推奨既定モデル名: `Qwen3.6-35B-A3B`
- 接続先は `OLLAMA_BASE_URL`
- OCR 用モデル名は `OLLAMA_OCR_MODEL`
- 要約用モデル名は `OLLAMA_SUMMARY_MODEL`
- 未設定時は `LOCAL_LLM_MODEL_MISSING`

### 3.2 NDLOCR-Lite

- `ocr_mode=high_accuracy` では `NDLOCR-Lite` を使う
- 単一画像の正式実行形式:

```powershell
ndlocr-lite --sourceimg <input-image-path> --output <output-dir>
```

- フォールバック実行形式:

```powershell
python ocr.py --sourceimg <input-image-path> --output <output-dir>
```

- 出力ファイルは `<stem>.txt` / `<stem>.json` / `<stem>.xml`
- 本アプリでは `<stem>.txt` を OCR 本文として一次採用する
- `.txt` 不在または空文字時は `TEXT_EXTRACTION_FAILED`

## 4. 実装対象

### 4.1 バックエンド

- Ollama クライアント層を追加する
- `local_llm` OCR 実装を追加する
- `local_llm` 要約実装を追加する
- `NDLOCR-Lite` 実行ラッパを追加する
- タイムアウトとエラーコードを出し分ける

### 4.2 フロントエンド

- 既存 UI 契約を維持する
- ローカル系モード選択時の補助説明を表示できるようにする
- エラー文言を Phase 2 のエラーコード体系に追従させる

### 4.3 設定

- `.env.example` と実装が一致していること
- ローカル依存未整備でもサーバ起動自体は可能とすること
- 依存チェックはリクエスト処理時に行うこと

## 5. やってはいけないこと

- `high_accuracy` で内部的に OpenAI OCR へ切り替えない
- `local_llm` 失敗時に黙って `api` 要約へ切り替えない
- エラーを warnings に落として成功扱いにしない
- `structuredData` が不完全だからといって要約本文まで捨てない
- ドキュメント未更新のまま契約変更しない

## 6. 完了条件

- `local_llm` OCR が動作する
- `local_llm` 要約が動作する
- `high_accuracy` OCR が動作する
- `high_accuracy + local_llm` が動作する
- 主要失敗系で以下を出し分けられる
  - `LOCAL_LLM_UNAVAILABLE`
  - `LOCAL_LLM_MODEL_MISSING`
  - `LOCAL_LLM_TIMEOUT`
  - `NDLOCR_UNAVAILABLE`
  - `NDLOCR_EXECUTION_FAILED`
  - `NDLOCR_TIMEOUT`
- 既存 `api/api` 経路の回帰がない

## 7. 実装順推奨

1. Ollama 要約を実装する
2. Ollama OCR を実装する
3. `NDLOCR-Lite` 実行ラッパを実装する
4. エラーコードとタイムアウトを揃える
5. UI の補助表示とエラー表示を整える
6. 回帰確認を行う

## 8. 判断に迷ったとき

- モード意味は `docs/12_Phase2詳細仕様.md` を優先する
- API 契約は `docs/04_APIインターフェース定義.md` を優先する
- 実装簡便性より後方互換と責務分離を優先する

