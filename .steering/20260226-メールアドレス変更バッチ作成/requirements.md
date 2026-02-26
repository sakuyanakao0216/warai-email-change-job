# 要求事項 — メールアドレス変更バッチ作成

## 概要

Firebase Authentication に登録されているユーザーの識別子（メールアドレス）を
一括で変更する Cloud Run ジョブ（バッチ）を作成する。

## 機能要件

| # | 要件 |
| - | ---- |
| 1 | GCS 上の CSV ファイルを読み込み、複数ユーザーのメールアドレスを一括変更する |
| 2 | CSV 形式は 1 行目ヘッダー `old_email,new_email`、2 行目以降がデータ |
| 3 | Firebase Identity Toolkit REST API を使用して認証情報を更新する |
| 4 | 接続情報・設定はすべて環境変数で管理する |
| 5 | 1 件ずつ処理し、成功/失敗を逐次ログ出力する |
| 6 | 失敗しても後続レコードの処理を継続する。失敗したレコード（old_email / new_email / 理由）を処理完了後に一覧でログ出力する |

## 環境変数一覧

| 変数名 | 内容 | 必須 |
| ------ | ---- | ---- |
| `GCS_BUCKET_NAME` | CSV を格納する GCS バケット名 | ✓ |
| `GCS_CSV_FILE_NAME` | バケット内 CSV ファイルのパス（例: `inputs/changes.csv`） | ✓ |
| `FIREBASE_WEB_API_KEY` | Firebase コンソール「プロジェクトの設定 > 全般」の Web API キー | ✓ |

## 非機能要件

- Cloud Run Jobs として実行可能なコンテナとして構成する
- Python 3.12
- CI: Black / isort / Ruff / mypy / pytest（カバレッジ 40%以上）/ pip-audit
