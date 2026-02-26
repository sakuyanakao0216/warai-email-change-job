"""メールアドレス変更バッチ.

GCS 上の CSV を読み込み、Firebase Authentication のメールアドレスを一括変更する。

CSV フォーマット（1 行目はヘッダー: old_email,new_email）:
    old_email,new_email
    current@example.com,new@example.com
"""

from __future__ import annotations

import base64
import csv
import io
import json
import logging
import os
import sys

import firebase_admin
from firebase_admin import auth, credentials
from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_env(key: str) -> str:
    """環境変数を取得する。未設定の場合は ValueError を送出する。"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"環境変数 {key} が設定されていません。")
    return value


def init_firebase(credentials_json: str) -> None:
    """Firebase Admin SDK を初期化する。

    credentials_json は JSON 文字列または base64 エンコードされた JSON 文字列を受け付ける。
    """
    # base64 エンコードされている場合はデコードする
    try:
        decoded = base64.b64decode(credentials_json).decode("utf-8")
        json.loads(decoded)  # 有効な JSON か確認
        credentials_json = decoded
    except Exception:
        pass  # base64 でなければそのまま使う
    cred_dict = json.loads(credentials_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)


def fetch_csv_from_gcs(bucket_name: str, file_name: str) -> str:
    """GCS から CSV ファイルの内容を文字列で取得する。"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    content = blob.download_as_text(encoding="utf-8")
    logger.info("GCS から CSV を取得しました: gs://%s/%s", bucket_name, file_name)
    return content


def parse_csv(text: str) -> list[tuple[str, str]]:
    """CSV テキストをパースし、(old_email, new_email) のリストを返す。

    1 行目はヘッダー行（old_email,new_email）としてスキップする。
    """
    reader = csv.DictReader(io.StringIO(text))
    records: list[tuple[str, str]] = []
    for row in reader:
        old_email = (row.get("old_email") or "").strip()
        new_email = (row.get("new_email") or "").strip()
        if old_email and new_email:
            records.append((old_email, new_email))
    logger.info("CSV をパースしました: %d 件", len(records))
    return records


def update_email(old_email: str, new_email: str) -> None:
    """Firebase Authentication のメールアドレスを 1 件更新する。

    Firebase Admin SDK を使用して、メールアドレスで検索し更新する。
    """
    user = auth.get_user_by_email(old_email)
    auth.update_user(user.uid, email=new_email)
    logger.info("更新成功: %s -> %s (uid=%s)", old_email, new_email, user.uid)


def main() -> None:
    """バッチ処理のエントリーポイント。"""
    bucket_name = get_env("GCS_BUCKET_NAME")
    file_name = get_env("GCS_CSV_FILE_NAME")
    credentials_json = get_env("FIREBASE_CREDENTIALS_JSON")

    init_firebase(credentials_json)

    csv_text = fetch_csv_from_gcs(bucket_name, file_name)
    records = parse_csv(csv_text)

    if not records:
        logger.warning("処理対象レコードが 0 件です。CSV の内容を確認してください。")
        return

    success_count = 0
    failure_count = 0
    failed_rows: list[tuple[str, str, str]] = []

    for old_email, new_email in records:
        try:
            update_email(old_email, new_email)
            success_count += 1
        except Exception as e:
            logger.error(
                "更新失敗: old_email=%s new_email=%s エラー=%s",
                old_email,
                new_email,
                e,
            )
            failed_rows.append((old_email, new_email, str(e)))
            failure_count += 1

    logger.info(
        "処理完了: 成功=%d 件 / 失敗=%d 件 / 合計=%d 件",
        success_count,
        failure_count,
        len(records),
    )

    if failed_rows:
        logger.error("--- 失敗一覧 ---")
        for i, (old_email, new_email, reason) in enumerate(failed_rows, start=1):
            logger.error(
                "[%d] old_email=%s new_email=%s 理由=%s",
                i,
                old_email,
                new_email,
                reason,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
