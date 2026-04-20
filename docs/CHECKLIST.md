# 受け入れチェックリスト v0.2

## 1. 目的

本チェックリストは、本リポジトリの Phase 1 / Phase 2 における受け入れ条件を確認するためのチェック項目である。

詳細な観点は以下を参照する。

- [06_実装タスク分解.md](./06_実装タスク分解.md)
- [07_テスト観点一覧.md](./07_テスト観点一覧.md)
- [RUNBOOK.md](./RUNBOOK.md)

## 2. Phase 1 受け入れ

## 2.1 ドキュメント

- [ ] 要件定義が最新方針に更新されている
- [ ] 仕様書が `ocr_mode` / `summary_mode` 前提に更新されている
- [ ] API インターフェース定義が存在する
- [ ] 画面仕様書が存在する
- [ ] RUNBOOK が現行運用に更新されている

## 2.2 API 契約

- [ ] `POST /api/summarize` が `file` / `ocr_mode` / `summary_mode` を受け取る
- [ ] `POST /api/summarize-multiple` が `files` / `ocr_mode` / `summary_mode` を受け取る
- [ ] レスポンスに `ocrMode` が含まれる
- [ ] レスポンスに `summaryMode` が含まれる
- [ ] `warnings` が常に配列で返る

## 2.3 バックエンド

- [ ] OCR モード列挙値を扱える
- [ ] 要約モード列挙値を扱える
- [ ] `api` / `api` 経路が維持されている
- [ ] `INVALID_OCR_MODE` を返せる
- [ ] `INVALID_SUMMARY_MODE` を返せる
- [ ] `LOCAL_LLM_UNAVAILABLE` を返せる
- [ ] `NDLOCR_UNAVAILABLE` を返せる

## 2.4 フロントエンド

- [ ] OCR 方式ラジオボタンが表示される
- [ ] 要約方式ラジオボタンが表示される
- [ ] 初期値が `api` / `api` になっている
- [ ] ローカル系モードの補助メッセージがある
- [ ] `要約実行` ボタンの活性条件が適切
- [ ] 結果表示に `ocrMode` / `summaryMode` が出る

## 2.5 テスト

- [ ] 既存 API テストが新契約に追従している
- [ ] 新規異常系テストが追加されている
- [ ] フロントビルドが通る

## 3. Phase 2 受け入れ

## 3.1 Ollama

- [ ] `summary_mode=local_llm` が実動作する
- [ ] `ocr_mode=local_llm` が実動作する
- [ ] Ollama 未起動時に明示エラーを返す
- [ ] モデル未準備時に明示エラーを返す

## 3.2 NDLOCR-Lite

- [ ] `ocr_mode=high_accuracy` が実動作する
- [ ] OCR 結果が正規化層に接続されている
- [ ] `NDLOCR-Lite` 未設定時に明示エラーを返す

## 3.3 ローカル連携テスト

- [ ] Ollama OCR 正常系テストがある
- [ ] Ollama 要約正常系テストがある
- [ ] NDLOCR-Lite 正常系テストがある
- [ ] ローカル未接続異常系テストがある

## 4. Phase 3 受け入れ

- [ ] 推奨モード表示が入っている
- [ ] 高精度後処理改善が反映されている
- [ ] warnings 表示方針が UI に反映されている

## 5. リリース前確認

- [ ] README が最新方針に追従している
- [ ] RUNBOOK が最新手順に追従している
- [ ] ローカル連携前提が明記されている
- [ ] 既知の未対応事項が整理されている

