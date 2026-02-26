# タスクリスト — メールアドレス変更バッチ作成

## 実装タスク

- [x] `.steering/20260226-メールアドレス変更バッチ作成/` ディレクトリ作成
- [x] `requirements.md` 作成
- [x] `design.md` 作成
- [x] `tasklist.md` 作成（本ファイル）
- [x] `infla.md` 作成
- [x] `main.py` 実装
- [x] `requirements.txt` 作成
- [x] `requirements-dev.txt` 作成
- [x] `Makefile` 作成
- [x] `Dockerfile` 作成
- [x] `.github/workflows/deploy.yml` 作成
- [x] `tests/test_main.py` 作成
- [x] `AGENTS.md` 更新
- [x] `README.md` 更新

- [x] Firebase Admin SDK への切り替え（`accounts:lookup` 400 エラー解消）
- [x] `AGENTS.md` / `README.md` / `.steering` ドキュメント更新

## コミット履歴

| # | コミットメッセージ | 内容 |
| --- | --- | --- |
| 1 | `feat: メールアドレス変更バッチの初期実装` | main.py, Dockerfile, CI/CD, テスト一式を追加 |
| 2 | `fix: Identity Toolkit REST API から Firebase Admin SDK に切り替え` | Web API キーでは `accounts:lookup` が 400 になる問題を解消。`FIREBASE_WEB_API_KEY` を `FIREBASE_CREDENTIALS_JSON` に変更 |
