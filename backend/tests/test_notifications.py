"""
Unit tests for the notifications service.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.notifications import send_status_change_notification


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


SMTP_ENV = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "devboard@example.com",
    "SMTP_PASS": "secret",
}


def test_send_message_called_for_reporter(monkeypatch):
    """send_message is called when SMTP is configured and reporter_email is present."""
    for k, v in SMTP_ENV.items():
        monkeypatch.setenv(k, v)

    mock_smtp_instance = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_smtp_instance)
    # Support context manager protocol
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    with patch("app.services.notifications.smtplib.SMTP", mock_smtp_cls):
        run(
            send_status_change_notification(
                issue_id=42,
                issue_title="Login broken",
                old_status="open",
                new_status="in_progress",
                reporter_email="reporter@example.com",
            )
        )

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("devboard@example.com", "secret")
    mock_smtp_instance.send_message.assert_called_once()


def test_no_send_when_smtp_not_configured(monkeypatch):
    """No SMTP call is made when SMTP_HOST is missing."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_USER", "devboard@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    with patch("app.services.notifications.smtplib.SMTP") as mock_smtp_cls:
        run(
            send_status_change_notification(
                issue_id=1,
                issue_title="Some issue",
                old_status="open",
                new_status="closed",
                reporter_email="reporter@example.com",
            )
        )
    mock_smtp_cls.assert_not_called()


def test_no_send_when_reporter_email_missing(monkeypatch):
    """No SMTP call is made when reporter_email is None."""
    for k, v in SMTP_ENV.items():
        monkeypatch.setenv(k, v)

    with patch("app.services.notifications.smtplib.SMTP") as mock_smtp_cls:
        run(
            send_status_change_notification(
                issue_id=7,
                issue_title="No reporter",
                old_status="open",
                new_status="closed",
                reporter_email=None,
            )
        )
    mock_smtp_cls.assert_not_called()


def test_email_body_contains_expected_fields(monkeypatch):
    """The sent message contains issue title, old/new status, and a link."""
    for k, v in SMTP_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("APP_BASE_URL", "https://devboard.example.com")

    mock_smtp_instance = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    with patch("app.services.notifications.smtplib.SMTP", mock_smtp_cls):
        run(
            send_status_change_notification(
                issue_id=99,
                issue_title="Crash on startup",
                old_status="open",
                new_status="resolved",
                reporter_email="reporter@example.com",
            )
        )

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    body = sent_msg.get_body().get_content()
    assert "Crash on startup" in body
    assert "open" in body
    assert "resolved" in body
    assert "https://devboard.example.com/issues/99" in body
