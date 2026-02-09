import logging
import smtplib
import re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal, Optional

from admitplus.config import settings

# Email constants
EMAIL_PURPOSES = {
    "SIGN_UP": "sign_up_verification",
    "RESET_PASSWORD": "reset_password_verification",
}

# Email configuration
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
EMAIL_TIMEOUT = 10  # seconds


class EmailTemplate:
    """Email template class for consistent styling and structure."""

    @staticmethod
    def get_base_html(title: str, message: str, code: str, action_text: str) -> str:
        """Generate base HTML template for verification emails."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);">
                <h2 style="color: #333333; margin-top: 0;">🔐 {title}</h2>
                <p>Dear user,</p>
                <p>{message}</p>
                <div style="text-align: center; margin: 20px 0;">
                    <p style="font-size: 16px; color: #000000; margin-bottom: 10px;">
                        <strong>Your verification code is:</strong>
                    </p>
                    <div style="font-size: 24px; font-weight: bold; background-color: #f0f0f0; padding: 15px 25px; border-radius: 6px; letter-spacing: 3px; display: inline-block; color: #333;">
                        {code}
                    </div>
                </div>
                <p>Please enter this code within <strong>5 minutes</strong> to {action_text}.</p>
                <p style="color: #666; font-size: 14px;">If you did not request this, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="margin-bottom: 0;">Best regards,<br><strong>AdmitPlus Team</strong></p>
            </div>
        </body>
        </html>
        """


def build_email_content(
    purpose: Literal["SIGN_UP", "RESET_PASSWORD"], code: str
) -> tuple[str, str]:
    """
    Build email subject and HTML body based on purpose.

    Args:
        purpose: Email purpose - "SIGN_UP" or "RESET_PASSWORD"
        code: Verification code to include in email

    Returns:
        Tuple of (subject, html_body)
    """
    email_configs = {
        "SIGN_UP": {
            "subject": "[AdmitPlus] Sign-up Verification Code",
            "title": "Email Verification",
            "message": "You are receiving this email to verify your auth.",
            "action": "proceed",
        },
        "RESET_PASSWORD": {
            "subject": "[AdmitPlus] Password Reset Verification Code",
            "title": "Password Reset Verification",
            "message": "You are receiving this email to reset your password.",
            "action": "proceed with resetting your password",
        },
    }

    config = email_configs[purpose]
    html_body = EmailTemplate.get_base_html(
        title=config["title"],
        message=config["message"],
        code=code,
        action_text=config["action"],
    )

    return config["subject"], html_body


class EmailSender:
    """Email sender class with connection management and error handling."""

    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.email = settings.ZOHO_EMAIL
        self.password = settings.ZOHO_APP_PASSWORD

    def _create_message(
        self, to_email: str, subject: str, html_body: str
    ) -> MIMEMultipart:
        """Create email message with proper headers and content."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.email
        msg["To"] = to_email
        msg["Subject"] = subject

        # Attach HTML content
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        return msg

    def _send_email(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Send email using SMTP connection."""
        try:
            with smtplib.SMTP(
                self.smtp_server, self.smtp_port, timeout=EMAIL_TIMEOUT
            ) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
                logging.info(f"Email sent successfully to {to_email}")
                return True

        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logging.error(f"Recipient email refused: {to_email}, error: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logging.error(f"SMTP server disconnected: {e}")
            return False
        except smtplib.SMTPException as e:
            logging.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending email to {to_email}: {e}")
            return False


def send_verification_email(
    receiver_email: str, code: str, purpose: Literal["SIGN_UP", "RESET_PASSWORD"]
) -> bool:
    """
    Send verification email to the specified receiver.

    Args:
        receiver_email: Email address to send to
        code: Verification code to include in email
        purpose: Email purpose - "SIGN_UP" or "RESET_PASSWORD"

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Build email content
        subject, html_body = build_email_content(purpose, code)

        # Create and send email
        sender = EmailSender()
        msg = sender._create_message(receiver_email, subject, html_body)

        return sender._send_email(msg, receiver_email)

    except Exception as e:
        logging.error(f"Failed to send verification email to {receiver_email}: {e}")
        return False


# Legacy function for backward compatibility
def build_sign_up_email_body_html(code: str) -> tuple[str, str]:
    """Legacy function - use send_verification_email instead."""
    return build_email_content("SIGN_UP", code)


def build_reset_password_email_body_html(code: str) -> tuple[str, str]:
    """Legacy function - use send_verification_email instead."""
    return build_email_content("RESET_PASSWORD", code)


def generate_email_from_name(name: str, domain: str = "example.com") -> str:
    """
    根据中文姓名生成邮箱地址
    """
    try:
        # 移除空格和特殊字符
        clean_name = re.sub(r"[^\u4e00-\u9fa5a-zA-Z]", "", name)

        if not clean_name:
            raise ValueError("姓名不能为空")

        # 如果是中文姓名，转换为拼音
        if any("\u4e00" <= char <= "\u9fff" for char in clean_name):
            from pypinyin import pinyin, Style

            # 获取拼音
            pinyin_list = pinyin(clean_name, style=Style.NORMAL)
            # 拼接拼音
            email_local = "".join([p[0] for p in pinyin_list])
        else:
            # 如果是英文姓名，直接使用
            email_local = clean_name.lower()

        # 添加随机后缀避免重复
        import random
        import string

        random_suffix = "".join(random.choices(string.digits, k=4))

        email = f"{email_local}{random_suffix}@{domain}"
        return email

    except Exception as e:
        # 如果转换失败，使用备用方案
        logging.warning(
            f"Failed to generate email from name {name}: {e}, using fallback"
        )
        import random
        import string

        random_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"student{random_id}@{domain}"
