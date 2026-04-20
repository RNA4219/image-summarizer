# Phase 2 詳細仕様 v0.1

## 1. 目的

本書は、`Ollama` と `NDLOCR-Lite` を利用する Phase 2 の正式仕様を固定し、
実装時の判断ぶれをなくすための詳細設計書である。

対象は以下の 3 モードである。

- `ocr_mode=local_llm`
- `ocr_mode=high_accuracy`
- `summary_mode=local_llm`

## 2. Phase 2 の基本方針

- ユーザーが選択したモードを尊重し、自動フォールバックは行わない
- OCR と要約の責務は分離し、失敗箇所を切り分け可能にする
- `high_accuracy` は `NDLOCR-Lite` 主体の OCR モードとして扱う
- ローカル要約は厳密 JSON を必須にせず、後段整形で吸収する
- 外部依存の未整備は 503 系の明示エラーとして返す

## 3. モード定義

## 3.1 `ocr_mode=local_llm`

定義:

- Ollama 上のマルチモーダルモデルへ画像を渡して OCR を行う

想定ユースケース:

- クラウド API を使いたくない
- スクリーンショットや軽量文書をローカル完結で処理したい

成功条件:

- モデルが画像入力を受け付ける
- OCR 結果として非空の文字列を返す

非目標:

- 文書 OCR の最高精度保証
- 表や帳票の厳密再現

## 3.2 `ocr_mode=high_accuracy`

定義:

- `NDLOCR-Lite` により文書画像からテキストを抽出する

想定ユースケース:

- 給与明細
- 帳票
- 申込書
- 印刷文書

成功条件:

- `NDLOCR-Lite` の実行が成功する
- OCR 結果が既存正規化層へ渡せるテキストとして取得できる

補足:

- Phase 2 では `NDLOCR-Lite` の単独結果を採用する
- OCR 段での複数エンジンアンサンブルは行わない

## 3.3 `summary_mode=local_llm`

定義:

- Ollama 上のローカル LLM を使い、抽出テキストを整形・要約する

想定ユースケース:

- ローカル完結
- クラウド API 不使用
- 出力文の口調や整形をローカルで調整したい

成功条件:

- 要約本文を返せる
- `structuredData` に最低限の骨格を埋められる

最低限の骨格:

- `documentType`
- `targetPeriod`
- `summary`
- `details`
- `uncertainItems`

## 4. サポート対象組み合わせ

| OCR | 要約 | サポート | 主用途 |
| --- | --- | --- | --- |
| `api` | `api` | 継続 | 標準経路 |
| `api` | `local_llm` | Phase 2 正式 | API OCR + ローカル整形 |
| `local_llm` | `api` | Phase 2 正式 | ローカル OCR + API 要約 |
| `local_llm` | `local_llm` | Phase 2 正式 | 完全ローカル |
| `high_accuracy` | `api` | Phase 2 正式 | 文書 OCR + API 要約 |
| `high_accuracy` | `local_llm` | Phase 2 正式 | 文書 OCR + ローカル要約 |

## 5. 実行シーケンス

## 5.1 `local_llm` OCR

1. 画像バイト列を受け取る
2. Ollama へ画像付きリクエストを送る
3. テキストを抽出する
4. 正規化へ渡す

## 5.2 `high_accuracy` OCR

1. 一時ディレクトリへ入力画像を保存する
2. `NDLOCR-Lite` CLI を実行する
3. OCR 結果ファイルまたは標準出力から文字列を取得する
4. 正規化へ渡す
5. 一時ファイルを削除する

## 5.3 `local_llm` 要約

1. 正規化済みテキストを受け取る
2. Ollama へ要約プロンプトを送る
3. 自然文要約を取得する
4. 必要に応じて後段で `structuredData` を補完する

## 6. 設定値仕様

## 6.1 必須設定

| 変数名 | 用途 | Phase | 必須条件 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API 認証 | 1/2 | `api` 系利用時のみ必須 |
| `OPENAI_MODEL` | OpenAI モデル名 | 1/2 | `api` 系利用時のみ必須 |
| `OLLAMA_BASE_URL` | Ollama 接続先 | 2 | `local_llm` 利用時必須 |
| `OLLAMA_OCR_MODEL` | OCR 用モデル | 2 | `ocr_mode=local_llm` で必須 |
| `OLLAMA_SUMMARY_MODEL` | 要約用モデル | 2 | `summary_mode=local_llm` で必須 |
| `NDLOCR_LITE_PATH` | `ndlocr-lite` 配置先 | 2 | `ocr_mode=high_accuracy` で必須 |

## 6.2 任意設定

| 変数名 | 用途 | 既定値 |
| --- | --- | --- |
| `OLLAMA_TIMEOUT_SECONDS` | Ollama タイムアウト | `60` |
| `NDLOCR_TIMEOUT_SECONDS` | NDLOCR 実行タイムアウト | `60` |
| `NDLOCR_TEMP_DIR` | 一時ファイル配置先 | OS 既定 temp |

## 6.3 推奨モデル固定値

- OCR 用推奨モデル名: `Qwen3.6-35B-A3B`
- 要約用推奨モデル名: `Qwen3.6-35B-A3B`

Phase 2 では、OCR と要約の両方で上記モデルを推奨既定値として扱う。

## 6.4 `NDLOCR-Lite` 実行コマンド仕様

`ndlocr-lite` リポジトリの `pyproject.toml` では、CLI エントリポイントとして `ndlocr-lite = "ocr:main"` が定義されている。

本アプリでは、`ocr_mode=high_accuracy` 選択時に以下の形式で実行することを標準仕様とする。

```powershell
ndlocr-lite --sourceimg <input-image-path> --output <output-dir>
```

フォールバック実行形式:

```powershell
python ocr.py --sourceimg <input-image-path> --output <output-dir>
```

補足:

- 優先するのは `ndlocr-lite` コマンド
- ただし環境によっては `NDLOCR_LITE_PATH\src` 配下で `python ocr.py` 実行が必要になる可能性がある
- `--sourceimg` を単一画像向け正式仕様とし、`--sourcedir` は将来の複数画像バッチ用とする
- `--viz` は本アプリの標準経路では利用必須としない

## 6.5 `NDLOCR-Lite` 出力採用仕様

`NDLOCR-Lite` は画像ごとに以下の出力を生成する。

- `<stem>.txt`
- `<stem>.json`
- `<stem>.xml`

本アプリでの採用優先順位:

1. `<stem>.txt` を一次採用し、OCR 本文として利用する
2. `<stem>.json` は将来の構造化補助情報として保持可能にする
3. `<stem>.xml` はデバッグおよび将来拡張用に扱う

`.txt` が存在しない、または空文字のみの場合は `TEXT_EXTRACTION_FAILED` とする。

## 7. 失敗時ポリシー

## 7.1 共通

- 自動フォールバックしない
- 失敗した層のエラーコードをそのまま返す
- サーバログには画像本文や全文 OCR 結果を出さない

## 7.2 Ollama 系

| 条件 | HTTP | code |
| --- | --- | --- |
| Ollama に接続できない | 503 | `LOCAL_LLM_UNAVAILABLE` |
| モデル未設定 | 503 | `LOCAL_LLM_MODEL_MISSING` |
| タイムアウト | 503 | `LOCAL_LLM_TIMEOUT` |
| 応答が空 | 422 | `TEXT_EXTRACTION_FAILED` または `SUMMARY_GENERATION_FAILED` |

## 7.3 NDLOCR 系

| 条件 | HTTP | code |
| --- | --- | --- |
| パス未設定 / 存在しない | 503 | `NDLOCR_UNAVAILABLE` |
| CLI 実行失敗 | 503 | `NDLOCR_EXECUTION_FAILED` |
| タイムアウト | 503 | `NDLOCR_TIMEOUT` |
| OCR 結果が空 | 422 | `TEXT_EXTRACTION_FAILED` |

## 8. warnings ポリシー

warnings は処理継続可能な軽微問題にのみ使う。

例:

- 抽出テキストが短い
- 一部の数値行が崩れている可能性がある
- ローカル要約の構造化精度が低く、補完を行った

停止が必要な問題は warnings ではなく error とする。

## 9. UI 表示ポリシー

- `local_llm` には「ローカル環境が必要」と注記する
- `high_accuracy` には「文書画像向け」と注記する
- ローカル系モード選択時は、初回案内として前提条件を補助表示してよい
- 自動推奨は Phase 3 まで導入しない

## 10. Phase 2 完了条件

- `local_llm` OCR が単一画像で動作する
- `local_llm` 要約が単一画像経路で動作する
- `high_accuracy` OCR が単一画像で動作する
- `high_accuracy + local_llm` の組み合わせが動作する
- 主要失敗系に対してエラーコードが出し分けられる
- `.env.example` と RUNBOOK が設定値に追従している

## 11. 非機能要件

- タイムアウトは既定 60 秒
- リトライは最大 1 回まで
- ローカル依存が未整備でも API サーバ自体は起動可能とする
- ローカル依存の判定はリクエスト受信時に行う

## 12. 未確定事項

- `structuredData.details` の項目抽出をどこまで Phase 2 で保証するか

