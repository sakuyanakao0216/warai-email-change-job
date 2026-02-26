# インフラ設定 — メールアドレス変更バッチ作成

## GCP 構成

| リソース | 設定値 | 備考 |
| -------- | ------ | ---- |
| サービス | Cloud Run Jobs | 常時起動不要のバッチ向け |
| リージョン | asia-northeast1（東京）推奨 | |
| コンテナイメージ | `asia-northeast1-docker.pkg.dev/<PROJECT_ID>/warai/email-change-job:latest` | Artifact Registry |
| メモリ | 512Mi | |
| CPU | 1 | |
| タイムアウト | 600s（10分） | CSV 件数による調整可 |

## GCS バケット

| 項目 | 設定値 |
| ---- | ------ |
| バケット名 | 環境変数 `GCS_BUCKET_NAME` で指定 |
| CSV ファイルパス | 環境変数 `GCS_CSV_FILE_NAME` で指定 |
| 配置例 | `gs://<BUCKET>/inputs/email_changes.csv` |

## Firebase

| 項目 | 設定値 |
| ---- | ------ |
| 認証方式 | Firebase Admin SDK（サービスアカウント JSON） |
| 利用 SDK | `firebase-admin` Python パッケージ |
| 利用関数 | `auth.get_user_by_email()` / `auth.update_user()` |

## 環境変数（Cloud Run Job）

```bash
GCS_BUCKET_NAME=<バケット名>
GCS_CSV_FILE_NAME=inputs/email_changes.csv
FIREBASE_CREDENTIALS_JSON=<サービスアカウントキー JSON 全文字列>
```

## IAM 権限

Cloud Run Job のサービスアカウントに以下の権限が必要:

| ロール | 用途 |
| ------ | ---- |
| `roles/storage.objectViewer` | GCS から CSV を読み取る |

Firebase Admin SDK 用サービスアカウントに必要な権限:

| ロール | 用途 |
| ------ | ---- |
| `roles/firebaseauth.admin`（または Firebase Admin SDK 権限） | ユーザー情報の参照・更新 |

## GitHub Secrets（CI/CD）

秘匿情報のみ Secrets に登録する。

| Secret 名 | 内容 |
| --------- | ---- |
| `GCP_SA_KEY` | サービスアカウントキー JSON（Artifact Registry & Cloud Run 権限） |
| `FIREBASE_CREDENTIALS_JSON` | Firebase Admin SDK 用サービスアカウントキー JSON（Firebase Authentication 操作権限） |

## GitHub Variables（CI/CD）

秘匿不要な設定値は Variables に登録する。

| Variable 名 | 内容 | 値 |
| ----------- | ---- | -- |
| `GCP_PROJECT_ID` | GCP プロジェクト ID | `hoikuenai-planner` |
| `GCS_BUCKET_NAME` | CSV 格納バケット名 | `hoikux-email-change` |
| `GCS_CSV_FILE_NAME` | CSV ファイルパス | `inputs/email_changes.csv` |

## デプロイコマンド（手動実行時）

```bash
# イメージビルド & プッシュ
docker build -t asia-northeast1-docker.pkg.dev/$PROJECT_ID/warai/email-change-job:latest .
docker push asia-northeast1-docker.pkg.dev/$PROJECT_ID/warai/email-change-job:latest

# Cloud Run Job 作成 / 更新
gcloud run jobs update email-change-job \
  --image asia-northeast1-docker.pkg.dev/$PROJECT_ID/warai/email-change-job:latest \
  --region asia-northeast1 \
  --set-env-vars "GCS_BUCKET_NAME=$BUCKET,GCS_CSV_FILE_NAME=$CSV_PATH,FIREBASE_CREDENTIALS_JSON=$CREDS_JSON"

# Job 実行
gcloud run jobs execute email-change-job --region asia-northeast1
```
