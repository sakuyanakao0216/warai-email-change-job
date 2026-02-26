# 設計内容 — メールアドレス変更バッチ作成

## 処理フロー

```text
Cloud Run Job 起動
  │
  ├─ 環境変数の検証（GCS_BUCKET_NAME / GCS_CSV_FILE_NAME / FIREBASE_CREDENTIALS_JSON）
  │
  ├─ Firebase Admin SDK 初期化（サービスアカウント JSON をパース）
  │
  ├─ GCS から CSV を取得
  │    └─ GCS_BUCKET_NAME / GCS_CSV_FILE_NAME
  │
  ├─ CSV をパース
  │    └─ 1 行目: ヘッダー（old_email,new_email）→ スキップ
  │       2 行目以降: データレコード
  │
  ├─ 各レコードを処理
  │    ├─ auth.get_user_by_email(old_email) で UID を取得
  │    ├─ auth.update_user(uid, email=new_email) でメールアドレスを更新
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
| `init_firebase(credentials_json)` | Firebase Admin SDK 初期化 |
| `fetch_csv_from_gcs(bucket, file_name)` | GCS から CSV テキストを取得 |
| `parse_csv(text)` | CSV テキスト → `list[tuple[str, str]]`（ヘッダー行スキップ） |
| `update_email(old_email, new_email)` | Firebase Admin SDK で 1 件更新 |
| `main()` | 全体の処理統括 |

## 利用 SDK / API

| SDK/API | 用途 |
| ------- | ---- |
| `firebase-admin` Python SDK | Firebase Authentication のユーザー操作（管理者権限） |
| `auth.get_user_by_email(email)` | メールアドレスで UID を検索 |
| `auth.update_user(uid, email=new_email)` | メールアドレスを更新 |
| `google-cloud-storage` | GCS から CSV を取得 |

## エラーハンドリング方針

- 環境変数未設定 → `ValueError` を raise してプロセス異常終了
- CSV 取得失敗 → 例外を raise してプロセス異常終了
- 個別レコードの更新失敗 → ERROR ログ出力 + 失敗リストに追記して処理継続
- 最終サマリー（成功数/失敗数）をログ出力
- 失敗件数 > 0 の場合、失敗一覧（old_email / new_email / 理由）を出力して exit 1
