# 設計内容 — メールアドレス変更バッチ作成

## 処理フロー

```text
Cloud Run Job 起動
  │
  ├─ 環境変数の検証（GCS_BUCKET_NAME / GCS_CSV_FILE_NAME / FIREBASE_WEB_API_KEY）
  │
  ├─ GCS から CSV を取得
  │    └─ GCS_BUCKET_NAME / GCS_CSV_FILE_NAME
  │
  ├─ CSV をパース
  │    └─ 1 行目: ヘッダー（old_email,new_email）→ スキップ
  │       2 行目以降: データレコード
  │
  ├─ 各レコードを処理
  │    ├─ Identity Toolkit accounts:lookup で old_email から localId を取得
  │    ├─ Identity Toolkit accounts:update で new_email に更新
  │    ├─ 成功 → INFO ログ出力して次へ
  │    └─ 失敗 → ERROR ログ出力 + 失敗リストに追記して次へ（処理継続）
  │
  ├─ 処理サマリー（成功数/失敗数/合計数）を INFO ログ出力
  │
  └─ 失敗があれば失敗一覧（old_email / new_email / 理由）を ERROR ログ出力して exit 1
```

## ファイル構成

```text
warai-email-change-job/
├── main.py                    # エントリーポイント
├── requirements.txt           # 本番依存パッケージ
├── requirements-dev.txt       # 開発用パッケージ
├── Makefile                   # make check / fmt / install-dev
├── Dockerfile                 # Cloud Run Jobs 用コンテナ定義
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI + Cloud Run デプロイ
├── tests/
│   └── test_main.py           # pytest ユニットテスト
└── .steering/
    └── 20260226-メールアドレス変更バッチ作成/
```

## 主要関数

| 名前 | 役割 |
| ---- | ---- |
| `get_env(key)` | 環境変数取得（未設定時に ValueError） |
| `fetch_csv_from_gcs(bucket, file_name)` | GCS から CSV テキストを取得 |
| `parse_csv(text)` | CSV テキスト → `list[tuple[str, str]]`（ヘッダー行スキップ） |
| `update_email(api_key, old_email, new_email)` | Identity Toolkit REST API で 1 件更新 |
| `main()` | 全体の処理統括 |

## 利用 API

| API | エンドポイント | 用途 |
| --- | -------------- | ---- |
| Identity Toolkit | `accounts:lookup` | old_email から localId を検索 |
| Identity Toolkit | `accounts:update` | localId 指定でメールアドレスを更新 |

## エラーハンドリング方針

- 環境変数未設定 → `ValueError` を raise してプロセス異常終了
- CSV 取得失敗 → 例外を raise してプロセス異常終了
- 個別レコードの更新失敗 → ERROR ログ出力 + 失敗リストに追記して処理継続
- 最終サマリー（成功数/失敗数）をログ出力
- 失敗件数 > 0 の場合、失敗一覧（old_email / new_email / 理由）を出力して exit 1
