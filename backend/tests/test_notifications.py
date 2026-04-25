"""Unit tests for the email notification service."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.services.notifications import send_status_change_notification


@pytest.mark.asyncio
async def test_send_status_change_notification_sends_email(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "bot@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_cls:
        await send_status_change_notification(
            issue_id=42,
            issue_title="Login page broken",
            old_status="open",
            new_status="in_progress",
            reporter_email="reporter@example.com",
        )

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("bot@example.com", "secret")
    mock_smtp_instance.send_message.assert_called_once()

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert "Login page broken" in sent_msg.get_body().get_content()
    assert "open" in sent_msg.get_body().get_content()
    assert "in_progress" in sent_msg.get_body().get_content()
    assert sent_msg["To"] == "reporter@example.com"


@pytest.mark.asyncio
async def test_send_status_change_notification_no_reporter_email(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "bot@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        await send_status_change_notification(
            issue_id=1,
            issue_title="Some issue",
            old_status="open",
            new_status="closed",
            reporter_email=None,
        )

    mock_smtp_cls.assert_not_called()


@pytest.mark.asyncio
async def test_send_status_change_notification_missing_smtp_config(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)

    with patch("smtplib.SMTP") as mock_smtp_cls:
        await send_status_change_notification(
            issue_id=1,
            issue_title="Some issue",
            old_status="open",
            new_status="closed",
            reporter_email="reporter@example.com",
        )

    mock_smtp_cls.assert_not_called()
