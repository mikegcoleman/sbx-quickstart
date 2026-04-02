"""
Notification service for DevBoard.

Sends email notifications when issue status changes using smtplib.
SMTP configuration is read from environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)


async def send_status_change_notification(
    issue_id: int,
    issue_title: str,
    old_status: str,
    new_status: str,
    assignee_email: Optional[str] = None,
    reporter_email: Optional[str] = None,
) -> None:
    """
    Notify the issue reporter when an issue's status changes.

    Reads SMTP settings from environment variables. Logs a warning and
    returns without raising if config is missing or the send fails.
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.warning(
            "SMTP not configured (SMTP_HOST/SMTP_USER/SMTP_PASS missing) — "
            "skipping notification for issue #%d",
            issue_id,
        )
        return

    if not reporter_email:
        logger.info("No reporter email for issue #%d — skipping notification", issue_id)
        return

    link = f"http://localhost:3000/issues/{issue_id}"
    body = (
        f"The status of your issue has changed.\n\n"
        f"Issue:      #{issue_id} — {issue_title}\n"
        f"Old status: {old_status}\n"
        f"New status: {new_status}\n"
        f"Link:       {link}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = f"[DevBoard] Issue #{issue_id} status changed to {new_status}"
    msg["From"] = smtp_user
    msg["To"] = reporter_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(
            "[NOTIFY] Sent status-change email for issue #%d to %s (%s → %s)",
            issue_id,
            reporter_email,
            old_status,
            new_status,
        )
    except Exception:
        logger.exception("Failed to send notification email for issue #%d", issue_id)
