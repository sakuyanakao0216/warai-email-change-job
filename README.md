# warai-email-change-job

Firebase Authentication に登録されているユーザーのメールアドレスを、GCS 上の CSV を元に一括変更する Cloud Run Jobs バッチ。

## 概要

- GCS に格納した CSV を読み込み、Firebase Authentication のメールアドレスを更新する
- 1 件ずつ処理し、失敗しても後続レコードの処理を継続する（部分失敗を許容）
- 処理完了後に成功/失敗件数をログ出力する
- 失敗したレコードは処理完了後に一覧（old_email / new_email / 理由）でまとめてログ出力する

## CSV フォーマット

```text
old_email,new_email
current@example.com,new@example.com
```

- 1 行目はヘッダー行（`old_email,new_email`）
- 文字コード: UTF-8

## 環境変数

| 変数名 | 内容 | 必須 |
| ------ | ---- | ---- |
| `GCS_BUCKET_NAME` | CSV を格納する GCS バケット名 | ✓ |
| `GCS_CSV_FILE_NAME` | バケット内 CSV ファイルのパス（例: `inputs/changes.csv`） | ✓ |
| `FIREBASE_WEB_API_KEY` | Firebase コンソール「プロジェクトの設定 > 全般」の Web API キー | ✓ |

## ローカル開発

```bash
# 依存パッケージのインストール
make install-dev

# コードチェック（CI と同等）
make check

# 自動整形
make fmt
```

## デプロイ

main ブランチへの push で GitHub Actions が自動的に CI を実行し、Cloud Run Jobs へデプロイする。

手動実行:

```bash
gcloud run jobs execute email-change-job --region asia-northeast1
```

詳細なインフラ設定は [.steering/20260226-メールアドレス変更バッチ作成/infla.md](.steering/20260226-メールアドレス変更バッチ作成/infla.md) を参照。
