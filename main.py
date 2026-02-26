"""メールアドレス変更バッチ.

GCS 上の CSV を読み込み、Firebase Authentication のメールアドレスを一括変更する。

CSV フォーマット（1 行目はヘッダー: old_email,new_email）:
    old_email,new_email
    current@example.com,new@example.com
"""

from __future__ import annotations

import csv
import io
import logging
import os
import sys

import requests
from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_IDENTITY_TOOLKIT_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
)
_LOOKUP_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
)


def get_env(key: str) -> str:
    """環境変数を取得する。未設定の場合は ValueError を送出する。"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"環境変数 {key} が設定されていません。")
    return value


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


def get_id_token(api_key: str, email: str, password: str) -> str:
    """メールアドレスとパスワードで Firebase にサインインし、ID トークンを取得する。

    注意: この関数はパスワード認証が有効なアカウント向け。
    パスワードなしで変更する場合は update_email_by_uid を使用すること。
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    resp = requests.post(
        url,
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["idToken"]


def update_email_with_id_token(api_key: str, id_token: str, new_email: str) -> None:
    """ID トークンを使って Firebase Authentication のメールアドレスを更新する。"""
    url = _IDENTITY_TOOLKIT_URL.format(api_key=api_key)
    resp = requests.post(
        url,
        json={"idToken": id_token, "email": new_email, "returnSecureToken": False},
        timeout=10,
    )
    resp.raise_for_status()


def update_email(api_key: str, old_email: str, new_email: str) -> None:
    """Firebase Authentication のメールアドレスを 1 件更新する。

    Identity Toolkit の accounts:update エンドポイントを使用する。
    ユーザーの ID トークンが必要なため、管理者による強制変更には
    Admin SDK（サービスアカウント）の利用を推奨する。
    本実装では Web API キーを用いた ID トークンベースの更新を行う。
    """
    # メールアドレスから localId を検索
    lookup_url = _LOOKUP_URL.format(api_key=api_key)
    lookup_resp = requests.post(
        lookup_url,
        json={"email": [old_email]},
        timeout=10,
    )
    lookup_resp.raise_for_status()
    users = lookup_resp.json().get("users", [])
    if not users:
        raise ValueError(f"ユーザーが見つかりません: {old_email}")

    local_id = users[0]["localId"]

    # accounts:update でメールアドレスを更新（管理者権限不要の操作）
    update_url = _IDENTITY_TOOLKIT_URL.format(api_key=api_key)
    update_resp = requests.post(
        update_url,
        json={"localId": local_id, "email": new_email},
        timeout=10,
    )
    update_resp.raise_for_status()
    logger.info("更新成功: %s -> %s (localId=%s)", old_email, new_email, local_id)


def main() -> None:
    """バッチ処理のエントリーポイント。"""
    bucket_name = get_env("GCS_BUCKET_NAME")
    file_name = get_env("GCS_CSV_FILE_NAME")
    api_key = get_env("FIREBASE_WEB_API_KEY")

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
            update_email(api_key, old_email, new_email)
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
