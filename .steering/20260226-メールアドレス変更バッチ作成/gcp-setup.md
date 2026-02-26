# GCP 初期構築手順 — メールアドレス変更バッチ

ローカルターミナルで順番に実行する。
`<...>` の部分は実際の値に置き換えること。

---

## 0. 事前確認

```bash
# gcloud CLI がインストールされているか確認
gcloud version

# Docker が起動しているか確認
docker info
```

---

## 1. gcloud ログイン

```bash
# ブラウザが開き Google アカウントで認証する
gcloud auth login

# Docker push 用の認証も設定する
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

---

## 2. プロジェクト作成・設定

```bash
# プロジェクト作成（既存プロジェクトを使う場合はスキップ）
gcloud projects create <PROJECT_ID> --name="<表示名>"

# 作業プロジェクトをセット
gcloud config set project <PROJECT_ID>

# 現在の設定を確認
gcloud config list
```

---

## 3. 必要な API を有効化

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com
```

---

## 4. Artifact Registry リポジトリ作成

```bash
gcloud artifacts repositories create warai \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="warai email change job"
```

---

## 5. GCS バケット作成

```bash
# バケット名はグローバルで一意である必要がある
gcloud storage buckets create gs://<BUCKET_NAME> \
  --location=asia-northeast1 \
  --uniform-bucket-level-access

# inputs フォルダに CSV を配置（ローカルの CSV を指定）
gcloud storage cp <ローカルのCSVパス> gs://<BUCKET_NAME>/inputs/email_changes.csv
```

---

## 6. デプロイ用サービスアカウント作成（GitHub Actions 用）

```bash
# サービスアカウント作成
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Deploy SA"

# Artifact Registry への書き込み権限
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:github-actions-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run Jobs の作成・更新権限
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:github-actions-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Cloud Run が使うデフォルト SA に権限を委任するための権限
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:github-actions-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# キー JSON を発行（このファイルを GitHub Secret に登録する）
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account="github-actions-sa@<PROJECT_ID>.iam.gserviceaccount.com"
```

> **注意**: `gcp-sa-key.json` はリポジトリにコミットしないこと。

---

## 7. Cloud Run Jobs 実行用サービスアカウントに GCS 権限を付与

Cloud Run Jobs はデフォルトで Compute Engine デフォルト SA で動く。
GCS バケットへのアクセスに `storage.objectViewer` が必要。

```bash
# Compute Engine デフォルト SA のメールアドレスを確認
gcloud iam service-accounts list

# GCS 読み取り権限を付与（<PROJECT_NUMBER> は数字のプロジェクト番号）
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

---

## 8. GitHub Secrets に登録

GitHub リポジトリの `Settings > Secrets and variables > Actions` で以下を登録する。

| Secret 名 | 値の取得元 |
| --------- | ---------- |
| `GCP_PROJECT_ID` | 手順 2 で設定した `<PROJECT_ID>` |
| `GCP_SA_KEY` | 手順 6 で発行した `gcp-sa-key.json` の中身（JSON 全文） |
| `GCS_BUCKET_NAME` | 手順 5 で作成した `<BUCKET_NAME>` |
| `GCS_CSV_FILE_NAME` | `inputs/email_changes.csv`（配置パスに合わせて変更） |
| `FIREBASE_WEB_API_KEY` | Firebase コンソール「プロジェクトの設定 > 全般 > ウェブ API キー」 |

---

## 9. 初回デプロイ（手動）

main ブランチに push すると GitHub Actions が自動実行されるが、
初回のみ以下で Cloud Run Job を手動作成しておくと確実。

```bash
# PROJECT_ID などを変数にセット
PROJECT_ID=<PROJECT_ID>
REGION=asia-northeast1
IMAGE=asia-northeast1-docker.pkg.dev/$PROJECT_ID/warai/email-change-job

# イメージをビルド & プッシュ
docker build -t $IMAGE:latest .
docker push $IMAGE:latest

# Cloud Run Job を作成
gcloud run jobs create email-change-job \
  --image $IMAGE:latest \
  --region $REGION \
  --project $PROJECT_ID \
  --memory 512Mi \
  --task-timeout 600 \
  --set-env-vars "GCS_BUCKET_NAME=<BUCKET_NAME>,GCS_CSV_FILE_NAME=inputs/email_changes.csv,FIREBASE_WEB_API_KEY=<API_KEY>"
```

---

## 10. 動作確認

```bash
# Job を手動実行
gcloud run jobs execute email-change-job --region asia-northeast1

# 実行ログを確認
gcloud run jobs executions list --job=email-change-job --region=asia-northeast1
```
