## 作業開始時のステアリングディレクトリ設定

新しい機能開発・改修作業を開始する際は、以下の手順でステアリングディレクトリを作成し、作業記録を静的に残すこと。

### 機能名の指定方法

以下のどちらの形式でも受け付ける:

- インラインテキスト: 「機能名: `xxx` で作業を開始して」
- コマンド形式: `/start xxx`

### ステップ

1. 現在のタスクコンテキストを確立する:
   - 機能名: `[上記いずれかの形式で与えられた機能名]`
   - 日付: `[現在の日付を YYYYMMDD 形式で取得]`
   - ステアリングディレクトリパス: `.steering/[日付]-[機能名]/`
2. 上記ステアリングディレクトリを作成する。
3. 下に md をぶら下げる。必要に応じて分割して良い。確定事項など重要事項をまとめていく。
   例:
   - `.steering/[日付]-[機能名]/requirements.md` ：要求事項
   - `.steering/[日付]-[機能名]/design.md`　：設計内容
   - `.steering/[日付]-[機能名]/tasklist.md` ：実装内容詳細
   - `.steering/[日付]-[機能名]/infla.md` ：GCPなどインフラの設定詳細

## ソースコード修正時のルール

ソースコード（`main.py` 等）を修正した場合は以下を行うこと。

1. **テストの実行**: 修正後は必ず `make check` を実行し、全チェックがパスすることを確認する。
　　　　　　　　　　　テスト結果は- `.steering/[日付]-[機能名]/test.md`に記載する。
2. **ドキュメントの更新**: 動作仕様・設定値・注意事項に影響する変更は `AGENTS.md` と `README.md` を適宜更新する
3. **コミット文言の作成**: 修正内容と理由を簡潔に示すコミットメッセージを**チャット上に出力する**。また `tasklist.md` にも追記する。
   - 形式: `<type>: <概要（日本語可）>` + 本文（原因・対処内容）
   - type 例: `fix`, `feat`, `refactor`, `docs`, `chore`
   - **必ずチャット上でコードブロックとして提示すること**（ユーザーがそのままコピーして使えるように）


## ドキュメント更新ルール

以下の変更時は `README.md` の該当セクションを必ず更新すること:

- 新エンドポイントの追加・削除
- リクエスト/レスポンス形式の変更
- 環境変数の追加・変更・削除
- 依存ライブラリの変更
- デプロイ手順の変更

## CI / CD

`.github/workflows/deploy.yml` が **main ブランチへの push** を契機に自動実行される。

### CI ジョブ（`ci`）チェック内容

| ツール | コマンド | 目的 |
| ------ | -------- | ---- |
| Black | `black --check .` | フォーマットチェック |
| isort | `isort --profile black --check-only .` | import 順チェック |
| Ruff | `ruff check .` | lint |
| mypy | `mypy main.py` | 型チェック（段階導入・`main.py` のみ） |
| pytest | `pytest --cov=. --cov-report=term-missing` | テスト + カバレッジ 40% 以上 |
| pip-audit | `pip-audit` | 依存パッケージ脆弱性スキャン |

### ローカルでの実行

```bash
make install-dev  # 開発用ライブラリをインストール
make check        # CI と同じチェックを全実行
make fmt          # black + isort で自動整形
```

### 必要な GitHub Secrets

秘匿情報のみ Secrets に登録する。

| Secret 名 | 内容 |
| --------- | ---- |
| `GCP_SA_KEY` | サービスアカウントキー JSON（Artifact Registry & Cloud Run 権限） |
| `FIREBASE_WEB_API_KEY` | Firebase コンソール「プロジェクトの設定 > 全般」の Web API キー |

### 必要な GitHub Variables

秘匿不要な設定値は Variables に登録する。

| Variable 名 | 内容 |
| ----------- | ---- |
| `GCP_PROJECT_ID` | GCP プロジェクト ID |
| `GCS_BUCKET_NAME` | CSV 格納 GCS バケット名 |
| `GCS_CSV_FILE_NAME` | バケット内 CSV ファイルパス |

## ファイル構成

```text
warai-email-change-job/
├── main.py                    # エントリーポイント（バッチ本体）
├── requirements.txt           # 本番依存パッケージ
├── requirements-dev.txt       # 開発用パッケージ
├── Makefile                   # make check / fmt / install-dev
├── Dockerfile                 # Cloud Run Jobs 用コンテナ定義
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI + Cloud Run デプロイ
└── tests/
    └── test_main.py           # pytest ユニットテスト
```

## 環境変数一覧

| 変数名 | 内容 | 必須 |
| ------ | ---- | ---- |
| `GCS_BUCKET_NAME` | CSV を格納する GCS バケット名 | ✓ |
| `GCS_CSV_FILE_NAME` | バケット内 CSV ファイルのパス | ✓ |
| `FIREBASE_WEB_API_KEY` | Firebase コンソール「プロジェクトの設定 > 全般」の Web API キー | ✓ |
