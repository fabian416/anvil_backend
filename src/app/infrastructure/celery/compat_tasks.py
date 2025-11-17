import logging
from typing import Any

import requests

from app.infrastructure.celery.app import celery_app
from app.setup.config.settings import load_settings
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.app_factory import create_async_ioc_container

log = logging.getLogger(__name__)


def _send_email_via_mailgun(to_email: str, subject: str, body: str) -> None:
    settings = load_settings()
    mailgun = getattr(settings, "mailgun", None)
    if not mailgun:
        log.info("Mailgun not configured; skipping email to %s. Subject: %s", to_email, subject)
        return
    domain = getattr(mailgun, "domain", None)
    api_key = getattr(mailgun, "api_key", None)
    if not (domain and api_key):
        log.info("Mailgun keys missing; skipping email to %s. Subject: %s", to_email, subject)
        return
    try:
        resp = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"noreply@{domain}",
                "to": [to_email],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
        if resp.status_code >= 300:
            log.warning("Mailgun send failed (%s): %s", resp.status_code, resp.text)
    except Exception as e:  # noqa: BLE001
        log.warning("Mailgun exception: %s", e)


def _safe_get(d: dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key)
    return v if isinstance(v, str) else default


@celery_app.task(name="send_email")
def send_email_compat(to_email: str | None = None, subject: str | None = None, body: str | None = None, **_: Any) -> None:
    if not to_email or not subject or not body:
        log.info("send_email called with missing args; to=%s subject=%s", to_email, subject)
        return
    _send_email_via_mailgun(to_email, subject, body)


@celery_app.task(name="tasks.email_tasks.send_email")
def send_email_namespaced(**kwargs: Any) -> None:
    send_email_compat(
        to_email=_safe_get(kwargs, "to_email"),
        subject=_safe_get(kwargs, "subject"),
        body=_safe_get(kwargs, "body"),
    )


@celery_app.task(name="tasks.email_tasks.send_password_change_notification")
def send_password_change_notification(**kwargs: Any) -> None:
    to_email = _safe_get(kwargs, "to_email")
    username = _safe_get(kwargs, "username")
    ip = _safe_get(kwargs, "ip_address")
    ua = _safe_get(kwargs, "user_agent")
    subject = "Password Changed"
    body = (
        f"Hello {username},\n\nYour password was changed.\n"
        f"IP: {ip}\nUser-Agent: {ua}\n\nIf this was not you, contact support."
    )
    if to_email:
        _send_email_via_mailgun(to_email, subject, body)


@celery_app.task(name="tasks.email_tasks.send_verification_email")
def send_verification_email(**kwargs: Any) -> None:
    to_email = _safe_get(kwargs, "to_email")
    verification_url = _safe_get(kwargs, "verification_url")
    subject = "Verify your email"
    body = (
        "use the code below to verify your email\n"
        f"{verification_url}\n\n"
    )
    if to_email and verification_url:
        _send_email_via_mailgun(to_email, subject, body)


@celery_app.task(name="tasks.email_tasks.send_password_reset_email")
def send_password_reset_email(**kwargs: Any) -> None:
    to_email = _safe_get(kwargs, "to_email")
    reset_token = _safe_get(kwargs, "reset_token")
    subject = "Password reset request"
    body = (
        "Use the code below to reset your password\n"
        f"{reset_token}\n\n"
        "If you did not request this, you can ignore this email."
    )
    if to_email and reset_token:
        _send_email_via_mailgun(to_email, subject, body)


@celery_app.task(name="invalidate_all_sessions")
def invalidate_all_sessions_task(**_: Any) -> None:
    # Backward-compatibility stub; no args provided in messages seen.
    # If needed, extend to accept user_id and call AuthSessionService.invalidate_all_sessions_for_user.
    log.info("invalidate_all_sessions: no-op (no user_id provided)")


