"""
Notification service for DevBoard.

Sends email to the issue reporter when an issue's status changes.
SMTP settings are read from environment variables:
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
    Notify the issue reporter when an issue status changes.

    Reads SMTP configuration from environment variables. Logs a warning and
    returns without raising if config is missing or reporter email is absent.
    """
    logger.info(
        "[NOTIFY] Issue #%d ('%s') changed: %s → %s | "
        "assignee=%s reporter=%s",
        issue_id,
        issue_title,
        old_status,
        new_status,
        assignee_email or "unassigned",
        reporter_email or "unknown",
    )

    if not reporter_email:
        logger.warning("Issue #%d has no reporter email; skipping notification.", issue_id)
        return

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port_raw = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.warning(
            "SMTP not configured (need SMTP_HOST, SMTP_USER, SMTP_PASS); "
            "skipping notification for issue #%d.",
            issue_id,
        )
        return

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        logger.warning("Invalid SMTP_PORT '%s'; skipping notification.", smtp_port_raw)
        return

    base_url = os.environ.get("APP_BASE_URL", "http://localhost:3000")
    issue_link = f"{base_url}/issues/{issue_id}"

    body = (
        f"The status of your reported issue has changed.\n\n"
        f"Issue:      #{issue_id} — {issue_title}\n"
        f"Old status: {old_status}\n"
        f"New status: {new_status}\n"
        f"Link:       {issue_link}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = f"[DevBoard] Issue #{issue_id} status changed: {old_status} → {new_status}"
    msg["From"] = smtp_user
    msg["To"] = reporter_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        logger.info("Notification sent to %s for issue #%d.", reporter_email, issue_id)
    except Exception as exc:
        logger.error(
            "Failed to send notification for issue #%d: %s",
            issue_id,
            exc,
        )
