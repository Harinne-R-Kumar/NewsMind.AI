"""
NewsMind AI - Email Utilities
Reusable SMTP email functions.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings
from backend.utils.logging import setup_logger

logger = setup_logger("email")


async def send_verification_email(
    to_email: str,
    verification_link: str,
) -> bool:
    """
    Send account verification email.
    """

    try:

        msg = MIMEMultipart("alternative")

        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = "Verify your NewsMind AI Account"

        html = f"""
        <html>
        <body>

        <h2>Welcome to NewsMind AI!</h2>

        <p>
        Thank you for creating your account.
        </p>

        <p>
        Click the button below to verify your email address.
        </p>

        <p>
            <a href="{verification_link}"
               style="
               background:#2563eb;
               color:white;
               padding:12px 20px;
               text-decoration:none;
               border-radius:6px;">
               Verify Email
            </a>
        </p>

        <br>

        <p>
        Or copy this link into your browser:
        </p>

        <p>{verification_link}</p>

        <br>

        <p>
        Thanks,<br>
        NewsMind AI Team
        </p>

        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:

            server.starttls()

            server.login(
                settings.SMTP_USER,
                settings.SMTP_PASSWORD
            )

            server.sendmail(
                settings.EMAIL_FROM,
                to_email,
                msg.as_string()
            )

        logger.info(f"Verification email sent to {to_email}")

        return True

    except Exception as e:

        logger.error(f"Failed to send verification email: {e}")

        return False