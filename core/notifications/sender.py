from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
import logging
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig

logger = logging.getLogger("bandit")


@dataclass
class SendResult:
    """Result of a single notification send attempt."""
    vendor_name: str
    channel: str        # "slack" | "email" | "both" | "none"
    success: bool
    error: Optional[str] = None
    sent_at: Optional[str] = None


@dataclass
class SendSummary:
    """Result of send_all_pending()."""
    sent: list[SendResult]
    failed: list[SendResult]
    skipped: int        # vendors with no pending notification
    total_processed: int

    def to_json(self) -> str:
        import dataclasses
        return json.dumps(
            dataclasses.asdict(self),
            indent=2,
            default=str,
        )


def _build_slack_payload(
    vendor_name: str,
    notification: dict,
) -> dict:
    """Build Slack block kit payload."""
    actions = notification.get("it_actions", [])
    integrations = notification.get("integrations", [])

    action_text = "\n".join(
        f"• {a}" for a in actions[:10]
    )
    if len(actions) > 10:
        action_text += f"\n• ... and {len(actions)-10} more"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"New vendor onboarding: {vendor_name}",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{vendor_name}* has been added to "
                        f"Bandit. The following IT actions "
                        f"are required before this vendor "
                        f"goes live.\n\n"
                        f"*Integrations:* "
                        f"{', '.join(integrations) or 'None'}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Required IT Actions:*\n{action_text}"
                }
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": (
                        f"Sent by Bandit · "
                        f"{datetime.now().strftime('%Y-%m-%d')}"
                    )
                }]
            }
        ]
    }


def _send_slack(
    webhook_url: str,
    payload: dict,
) -> None:
    """Send Slack webhook. Raises on failure."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(
                f"Slack returned {resp.status}"
            )


def _send_email(
    to_address: str,
    vendor_name: str,
    notification: dict,
    smtp_config: dict,
) -> None:
    """Send email notification. Raises on failure."""
    actions = notification.get("it_actions", [])
    integrations = notification.get("integrations", [])

    subject = (
        f"Bandit: IT actions required for {vendor_name}"
    )

    body_lines = [
        f"{vendor_name} has been added to Bandit vendor "
        f"risk management.",
        "",
        f"Integrations: {', '.join(integrations) or 'None'}",
        "",
        "Required IT Actions:",
    ] + [f"  - {a}" for a in actions] + [
        "",
        "---",
        "Sent by Bandit · github.com/conorrusso/bandit",
    ]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = smtp_config.get(
        "from_address", "bandit@localhost"
    )
    msg["To"] = to_address
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    host = smtp_config.get("smtp_host", "localhost")
    port = smtp_config.get("smtp_port", 587)

    with smtplib.SMTP(host, port, timeout=10) as server:
        if smtp_config.get("use_tls", True):
            server.starttls()
        if smtp_config.get("username"):
            server.login(
                smtp_config["username"],
                smtp_config.get("password", "")
            )
        server.sendmail(
            msg["From"], [to_address], msg.as_string()
        )


def send_it_notification(
    vendor_name: str,
) -> SendResult:
    """
    Send IT notification for a single vendor.
    Reads pending_it_notification from vendor profile.
    Marks as sent in profile after successful send.
    Returns SendResult — never prints.
    """
    cache = VendorProfileCache()
    config = BanditConfig()
    profile = cache.get(vendor_name)

    if not profile:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="No vendor profile found",
        )

    notification = getattr(
        profile, "pending_it_notification", None
    )

    if not notification:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="No pending notification",
        )

    if notification.get("status") == "sent":
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error="Already sent",
        )

    it_contact = config.get_it_contact()
    slack_webhook = it_contact.get("slack_webhook_url")
    email_address = it_contact.get("it_contact_email")

    if not slack_webhook and not email_address:
        return SendResult(
            vendor_name=vendor_name,
            channel="none",
            success=False,
            error=(
                "No notification channels configured. "
                "Run: bandit setup --notify"
            ),
        )

    channels_sent = []
    errors = []

    # Slack
    if slack_webhook:
        try:
            payload = _build_slack_payload(
                vendor_name, notification
            )
            _send_slack(slack_webhook, payload)
            channels_sent.append("slack")
        except Exception as e:
            errors.append(f"Slack: {e}")
            logger.warning(f"Slack send failed: {e}")

    # Email
    if email_address:
        try:
            smtp_cfg = it_contact.get("smtp", {})
            _send_email(
                email_address, vendor_name,
                notification, smtp_cfg
            )
            channels_sent.append("email")
        except Exception as e:
            errors.append(f"Email: {e}")
            logger.warning(f"Email send failed: {e}")

    success = len(channels_sent) > 0
    channel = (
        "both" if len(channels_sent) == 2
        else channels_sent[0] if channels_sent
        else "none"
    )

    if success:
        # Mark as sent in profile
        notification["status"] = "sent"
        notification["sent_at"] = datetime.now().isoformat()
        notification["sent_via"] = channels_sent
        profile.pending_it_notification = notification
        cache.save(vendor_name, profile)

    return SendResult(
        vendor_name=vendor_name,
        channel=channel,
        success=success,
        error="; ".join(errors) if errors else None,
        sent_at=(
            datetime.now().isoformat() if success else None
        ),
    )


def send_all_pending() -> SendSummary:
    """
    Send IT notifications for all vendors with
    pending notifications. Returns SendSummary.
    Never prints — caller renders results.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()

    sent = []
    failed = []
    skipped = 0

    for profile in profiles:
        notification = getattr(
            profile, "pending_it_notification", None
        )
        if (not notification
                or notification.get("status") == "sent"):
            skipped += 1
            continue

        result = send_it_notification(profile.vendor_name)
        if result.success:
            sent.append(result)
        else:
            failed.append(result)

    return SendSummary(
        sent=sent,
        failed=failed,
        skipped=skipped,
        total_processed=len(sent) + len(failed),
    )
