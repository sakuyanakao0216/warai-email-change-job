"""main.py のユニットテスト."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import main

# ---------------------------------------------------------------------------
# get_env
# ---------------------------------------------------------------------------


def test_get_env_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_KEY", "hello")
    assert main.get_env("TEST_KEY") == "hello"


def test_get_env_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)
    with pytest.raises(ValueError, match="MISSING_KEY"):
        main.get_env("MISSING_KEY")


# ---------------------------------------------------------------------------
# parse_csv
# ---------------------------------------------------------------------------


def test_parse_csv_basic() -> None:
    text = "old_email,new_email\nold@example.com,new@example.com\n"
    result = main.parse_csv(text)
    assert result == [("old@example.com", "new@example.com")]


def test_parse_csv_multiple_rows() -> None:
    text = "old_email,new_email\na@example.com,b@example.com\nc@example.com,d@example.com\n"
    result = main.parse_csv(text)
    assert len(result) == 2
    assert result[0] == ("a@example.com", "b@example.com")


def test_parse_csv_skips_header_only() -> None:
    text = "old_email,new_email\n"
    result = main.parse_csv(text)
    assert result == []


def test_parse_csv_strips_whitespace() -> None:
    text = "old_email,new_email\n  a@example.com , b@example.com  \n"
    result = main.parse_csv(text)
    assert result == [("a@example.com", "b@example.com")]


def test_parse_csv_skips_empty_fields() -> None:
    text = "old_email,new_email\n,\n"
    result = main.parse_csv(text)
    assert result == []


# ---------------------------------------------------------------------------
# fetch_csv_from_gcs
# ---------------------------------------------------------------------------


def test_fetch_csv_from_gcs_returns_text() -> None:
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = (
        "old_email,new_email\na@example.com,b@example.com\n"
    )
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    with patch("main.storage.Client", return_value=mock_client):
        result = main.fetch_csv_from_gcs("my-bucket", "path/to/file.csv")

    assert "a@example.com" in result
    mock_client.bucket.assert_called_once_with("my-bucket")
    mock_bucket.blob.assert_called_once_with("path/to/file.csv")


# ---------------------------------------------------------------------------
# update_email
# ---------------------------------------------------------------------------


def test_update_email_success() -> None:
    mock_user = MagicMock()
    mock_user.uid = "uid-abc"

    with (
        patch("main.auth.get_user_by_email", return_value=mock_user) as mock_get,
        patch("main.auth.update_user") as mock_update,
    ):
        main.update_email("old@example.com", "new@example.com")

    mock_get.assert_called_once_with("old@example.com")
    mock_update.assert_called_once_with("uid-abc", email="new@example.com")


def test_update_email_raises_when_user_not_found() -> None:
    from firebase_admin import exceptions

    with patch(
        "main.auth.get_user_by_email",
        side_effect=exceptions.NotFoundError("User not found"),
    ):
        with pytest.raises(exceptions.NotFoundError):
            main.update_email("notfound@example.com", "new@example.com")


# ---------------------------------------------------------------------------
# main (integration-like)
# ---------------------------------------------------------------------------

_DUMMY_CREDS = json.dumps(
    {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4PAtEsHAXXFWAhsKEgfJSYWLzq\nA-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test",
    }
)


def test_main_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_CSV_FILE_NAME", "file.csv")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_JSON", _DUMMY_CREDS)

    with (
        patch("main.init_firebase"),
        patch(
            "main.fetch_csv_from_gcs",
            return_value="old_email,new_email\na@example.com,b@example.com\n",
        ),
        patch("main.update_email"),
    ):
        main.main()


def test_main_exits_1_on_partial_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_CSV_FILE_NAME", "file.csv")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_JSON", _DUMMY_CREDS)

    with (
        patch("main.init_firebase"),
        patch(
            "main.fetch_csv_from_gcs",
            return_value="old_email,new_email\na@example.com,b@example.com\n",
        ),
        patch("main.update_email", side_effect=Exception("not found")),
        pytest.raises(SystemExit) as exc_info,
    ):
        main.main()

    assert exc_info.value.code == 1


def test_main_empty_csv_no_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_CSV_FILE_NAME", "file.csv")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_JSON", _DUMMY_CREDS)

    with (
        patch("main.init_firebase"),
        patch("main.fetch_csv_from_gcs", return_value="old_email,new_email\n"),
        patch("main.update_email") as mock_update,
    ):
        main.main()
        mock_update.assert_not_called()
