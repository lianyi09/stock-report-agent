"""邮件发送模块 - 通过 Resend HTTP API 发送 HTML 邮件（非 SMTP）"""
import os
import logging

import resend

logger = logging.getLogger(__name__)


def send_email(subject, html_content, recipient=None):
    """
    通过 Resend API 发送 HTML 邮件（HTTP API，不是 SMTP）

    参数:
        subject: 邮件标题
        html_content: HTML 邮件正文
        recipient: 收件人邮箱（默认从环境变量 RESEND_RECIPIENT 读取）

    环境变量:
        RESEND_API_KEY: Resend API Key（从 https://resend.com 获取）
        RESEND_FROM_EMAIL: 发件人地址（需在 Resend 中验证的域名邮箱）
        RESEND_FROM_NAME: 发件人名称
        RESEND_RECIPIENT: 收件人邮箱地址
    """
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    from_name = os.getenv("RESEND_FROM_NAME", "美股日报")
    to_email = recipient or os.getenv("RESEND_RECIPIENT")

    if not api_key:
        logger.error("RESEND_API_KEY 未配置，请在环境变量或 GitHub Secrets 中设置")
        return False

    if not to_email:
        logger.error("收件人邮箱未配置，请设置 RESEND_RECIPIENT 环境变量")
        return False

    try:
        resend.api_key = api_key

        params = {
            "from": f"{from_name} <{from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        result = resend.Emails.send(params)
        logger.info(f"邮件发送成功: id={result.id}, subject={subject}")
        return True

    except resend.exceptions.ResendError as e:
        logger.error(f"Resend API 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"邮件发送异常: {e}")
        return False
