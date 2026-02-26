"""main.py のユニットテスト."""

from __future__ import annotations

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
    mock_blob.download_as_text.return_value = "old_email,new_email\na@example.com,b@example.com\n"
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
    mock_lookup_resp = MagicMock()
    mock_lookup_resp.json.return_value = {"users": [{"localId": "uid-abc"}]}
    mock_lookup_resp.raise_for_status = MagicMock()

    mock_update_resp = MagicMock()
    mock_update_resp.raise_for_status = MagicMock()

    with patch("main.requests.post", side_effect=[mock_lookup_resp, mock_update_resp]) as mock_post:
        main.update_email("api-key-123", "old@example.com", "new@example.com")

    assert mock_post.call_count == 2
    # 1 回目: lookup
    first_call_json = mock_post.call_args_list[0].kwargs["json"]
    assert first_call_json == {"email": ["old@example.com"]}
    # 2 回目: update
    second_call_json = mock_post.call_args_list[1].kwargs["json"]
    assert second_call_json == {"localId": "uid-abc", "email": "new@example.com"}


def test_update_email_raises_when_user_not_found() -> None:
    mock_lookup_resp = MagicMock()
    mock_lookup_resp.json.return_value = {"users": []}
    mock_lookup_resp.raise_for_status = MagicMock()

    with patch("main.requests.post", return_value=mock_lookup_resp):
        with pytest.raises(ValueError, match="ユーザーが見つかりません"):
            main.update_email("api-key-123", "notfound@example.com", "new@example.com")


# ---------------------------------------------------------------------------
# main (integration-like)
# ---------------------------------------------------------------------------


def test_main_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("GCS_CSV_FILE_NAME", "file.csv")
    monkeypatch.setenv("FIREBASE_WEB_API_KEY", "dummy-api-key")

    with (
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
    monkeypatch.setenv("FIREBASE_WEB_API_KEY", "dummy-api-key")

    with (
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
    monkeypatch.setenv("FIREBASE_WEB_API_KEY", "dummy-api-key")

    with (
        patch("main.fetch_csv_from_gcs", return_value="old_email,new_email\n"),
        patch("main.update_email") as mock_update,
    ):
        main.main()
        mock_update.assert_not_called()
