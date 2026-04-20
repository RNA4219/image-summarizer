# Phase 1 実装順チェックリスト v0.1

## 1. 目的

本書は、Phase 1 着手時に「どこから手を付けるか」を短く確認できる実装順チェックリストである。

詳細設計や依存関係は [06_実装タスク分解.md](./06_実装タスク分解.md) を参照し、
本書は着手順の簡易確認に利用する。

## 2. 着手前確認

- [ ] [01_要件定義.md](./01_要件定義.md) を確認した
- [ ] [02_仕様書.md](./02_仕様書.md) を確認した
- [ ] [04_APIインターフェース定義.md](./04_APIインターフェース定義.md) を確認した
- [ ] [05_画面仕様書.md](./05_画面仕様書.md) を確認した
- [ ] `api` / `api` 後方互換を維持する方針を確認した

## 3. バックエンド

- [ ] OCR モード / 要約モードの列挙値を定義する
- [ ] `INVALID_OCR_MODE` / `INVALID_SUMMARY_MODE` を追加する
- [ ] `LOCAL_LLM_UNAVAILABLE` / `NDLOCR_UNAVAILABLE` を追加する
- [ ] `/api/summarize` に `ocr_mode` / `summary_mode` を追加する
- [ ] `/api/summarize-multiple` に `ocr_mode` / `summary_mode` を追加する
- [ ] OCR サービスをモード付き共通入口へ寄せる
- [ ] 要約サービスをモード付き共通入口へ寄せる
- [ ] Pipeline にモード引数を通す
- [ ] レスポンスに `ocrMode` / `summaryMode` を追加する

## 4. フロントエンド

- [ ] `OcrMode` / `SummaryMode` / `ProcessingOptions` 型を追加する
- [ ] API 呼び出しに `ocr_mode` / `summary_mode` を追加する
- [ ] OCR 方式ラジオボタンを追加する
- [ ] 要約方式ラジオボタンを追加する
- [ ] ローカル系モードの補助メッセージを追加する
- [ ] `onSubmit` からモード情報を渡せるようにする
- [ ] 結果表示に `ocrMode` / `summaryMode` を追加する

## 5. テスト

- [ ] 既存 API テストを新契約に追従させる
- [ ] `INVALID_OCR_MODE` の異常系を追加する
- [ ] `INVALID_SUMMARY_MODE` の異常系を追加する
- [ ] `LOCAL_LLM_UNAVAILABLE` の異常系を追加する
- [ ] `NDLOCR_UNAVAILABLE` の異常系を追加する
- [ ] フロントビルド確認を行う

## 6. 完了確認

- [ ] UI で OCR 方式を選べる
- [ ] UI で要約方式を選べる
- [ ] API が `ocr_mode` / `summary_mode` を受け取る
- [ ] `api` / `api` が従来どおり動く
- [ ] `local_llm` / `high_accuracy` は未接続でも明示エラーを返す
- [ ] 結果表示に利用モードが出る
- [ ] テストが更新済みである
- [ ] ビルドが通る

## 7. 保留事項

- [ ] Ollama 実接続は Phase 2 に回す
- [ ] NDLOCR-Lite 実接続は Phase 2 に回す
- [ ] 推奨モード表示は Phase 3 に回す

