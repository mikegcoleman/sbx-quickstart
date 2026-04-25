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
    """Notify the issue reporter by email when the issue status changes."""
    logger.info(
        "[NOTIFY] Issue #%d ('%s') changed: %s → %s | assignee=%s reporter=%s",
        issue_id,
        issue_title,
        old_status,
        new_status,
        assignee_email or "unassigned",
        reporter_email or "unknown",
    )

    if not reporter_email:
        logger.warning("[NOTIFY] No reporter email for issue #%d, skipping.", issue_id)
        return

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.warning(
            "[NOTIFY] SMTP config incomplete (SMTP_HOST, SMTP_USER, SMTP_PASS required), skipping."
        )
        return

    link = f"http://localhost:3000/issues/{issue_id}"
    body = (
        f"The status of issue #{issue_id} has changed.\n\n"
        f"Title:      {issue_title}\n"
        f"Old status: {old_status}\n"
        f"New status: {new_status}\n\n"
        f"View issue: {link}\n"
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
        logger.info("[NOTIFY] Email sent to %s for issue #%d.", reporter_email, issue_id)
    except Exception as exc:
        logger.error("[NOTIFY] Failed to send email for issue #%d: %s", issue_id, exc)
