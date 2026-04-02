"""
Unit tests for the email notification service.
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


@patch("app.services.notifications.smtplib.SMTP")
def test_send_message_called_for_reporter(mock_smtp_cls):
    """send_status_change_notification sends an email to the reporter."""
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    with patch.dict("os.environ", SMTP_ENV):
        run(
            send_status_change_notification(
                issue_id=42,
                issue_title="Login page crashes",
                old_status="open",
                new_status="in_progress",
                reporter_email="alice@example.com",
            )
        )

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_server.send_message.assert_called_once()

    sent_msg = mock_server.send_message.call_args[0][0]
    assert sent_msg["To"] == "alice@example.com"
    assert "Login page crashes" in sent_msg.get_content()
    assert "open" in sent_msg.get_content()
    assert "in_progress" in sent_msg.get_content()
    assert "#42" in sent_msg.get_content()


@patch("app.services.notifications.smtplib.SMTP")
def test_no_send_when_smtp_not_configured(mock_smtp_cls):
    """No email is sent when SMTP env vars are missing."""
    with patch.dict("os.environ", {}, clear=True):
        run(
            send_status_change_notification(
                issue_id=1,
                issue_title="Some issue",
                old_status="open",
                new_status="closed",
                reporter_email="bob@example.com",
            )
        )

    mock_smtp_cls.assert_not_called()


@patch("app.services.notifications.smtplib.SMTP")
def test_no_send_when_reporter_email_missing(mock_smtp_cls):
    """No email is sent when reporter_email is None."""
    with patch.dict("os.environ", SMTP_ENV):
        run(
            send_status_change_notification(
                issue_id=7,
                issue_title="Another issue",
                old_status="open",
                new_status="closed",
                reporter_email=None,
            )
        )

    mock_smtp_cls.assert_not_called()
