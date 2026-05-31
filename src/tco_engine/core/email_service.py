# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Transactional email for the CAL experiment platform.

SMTP pattern mirrored from Research-Lab (`app/routers/register.py`): Gmail
SSL on 465, credentials via GMAIL_USER / GMAIL_APP_PASSWORD. All sends are
best-effort — a missing config or SMTP error is logged, never raised, so the
registration / invitation flow never fails because email is unavailable.
"""
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_APP_URL = os.getenv("CAL_APP_URL", "https://researchlab.aural-syncro.com.ar/cal")


def _send(to: str, subject: str, plain: str) -> bool:
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_pass:
        logger.warning("Email skipped (GMAIL_USER/GMAIL_APP_PASSWORD unset): %s", subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Aural-Syncro CAL <{gmail_user}>"
        msg["To"] = to
        msg["Reply-To"] = gmail_user
        msg["Subject"] = subject
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as srv:
            srv.login(gmail_user, gmail_pass)
            srv.sendmail(gmail_user, [to], msg.as_string())
        return True
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending '%s' to %s: %s", subject, to, exc)
        return False


def send_welcome_email(to: str, name: str) -> bool:
    first = name.split()[0] if name else "investigador/a"
    body = (
        f"¡Hola {first}!\n\n"
        f"Tu cuenta en la plataforma de investigación CAL (Aural-Syncro Research Lab) "
        f"fue creada con éxito.\n\n"
        f"Próximo paso: el equipo te enviará una invitación con la fecha y hora de tu "
        f"sesión experimental. En esa fecha vas a ingresar con tu email y contraseña "
        f"para realizar la prueba.\n\n"
        f"Acceso: {_APP_URL}\n\n"
        f"Gracias por participar.\n"
        f"— Aural-Syncro CAL\n"
    )
    return _send(to, "CAL — Registro confirmado", body)


def send_invitation_email(to: str, name: str, scheduled_at: str) -> bool:
    first = name.split()[0] if name else "investigador/a"
    body = (
        f"¡Hola {first}!\n\n"
        f"Te invitamos a tu sesión experimental de la plataforma CAL.\n\n"
        f"Fecha y hora: {scheduled_at}\n"
        f"Acceso: {_APP_URL}/login\n\n"
        f"Ingresá con tu email y contraseña unos minutos antes. La sesión dura "
        f"aproximadamente 3 horas e incluye una pausa.\n\n"
        f"— Aural-Syncro CAL\n"
    )
    return _send(to, "CAL — Invitación a tu sesión experimental", body)
