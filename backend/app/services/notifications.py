"""
Notification service for DevBoard.

TODO: Implement email notifications when issue status changes.
      Currently logs to stdout only. A real implementation should:
        1. Load SMTP settings from config (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS)
        2. Look up the issue assignee and reporter emails from the database
        3. Render an HTML template with the status change details
        4. Send via smtplib or an async library like aiosmtplib

      A stub for the async email send is left below.
"""

import logging
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
    Notify relevant users when an issue status changes.

    Currently a no-op stub — replace with real email logic.
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

    # TODO: implement actual email sending
    # Example skeleton:
    #
    # import aiosmtplib
    # from email.mime.text import MIMEText
    #
    # if not assignee_email:
    #     return
    #
    # message = MIMEText(
    #     f"Issue '{issue_title}' moved from {old_status} to {new_status}."
    # )
    # message["Subject"] = f"[DevBoard] Issue #{issue_id} status update"
    # message["From"] = settings.smtp_user
    # message["To"] = assignee_email
    #
    # await aiosmtplib.send(
    #     message,
    #     hostname=settings.smtp_host,
    #     port=settings.smtp_port,
    #     username=settings.smtp_user,
    #     password=settings.smtp_pass,
    #     use_tls=True,
    # )
