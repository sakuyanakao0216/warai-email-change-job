# GitHub 初期作成内容（2026-02-26）

## ローカル Git 設定
- user.name: Sakuya Nakao
- user.email: sakuya.nakao.0216@gmail.com

## リモートリポジトリ
- GitHub アカウント: sakuyanakao0216
- リポジトリ名: warai-email-change-job
- URL: https://github.com/sakuyanakao0216/warai-email-change-job
- origin: https://github.com/sakuyanakao0216/warai-email-change-job.git

## 初期コミット
- 追加ファイル: README.md
- コミットメッセージ: Initial commit
- ブランチ: main
- Push 済み: origin/main

## 実行コマンド手順
1. `git init`
2. `git config user.name "Sakuya Nakao"`
3. `git config user.email "sakuya.nakao.0216@gmail.com"`
4. `git remote add origin https://github.com/sakuyanakao0216/warai-email-change-job.git`
5. `gh repo create sakuyanakao0216/warai-email-change-job --public --source . --remote origin --push`
6. `git add README.md`
7. `git commit -m "Initial commit"`
8. `git push -u origin main`

## 補足で実行したコマンド
- `gh auth status`（GitHub CLI 認証状態確認）
- `git remote remove origin`（既存 origin がある場合の削除）
- `git remote set-url origin https://github.com/sakuyanakao0216/warai-email-change-job.git`（origin URL の整合）
