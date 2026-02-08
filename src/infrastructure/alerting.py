#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
告警通知模块
"""

import smtplib
import threading
from datetime import datetime
from typing import Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from loguru import logger

from .config_manager import ConfigManager


class AlertLevel:
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alerting:
    """告警通知管理器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        config_manager = ConfigManager.get_instance(config_path)
        self.config = config_manager.get_all()

        self.email_config = self.config.get('email', {})
        self.alert_config = self.config.get('alerting', {})
        self._smtp_server = None
        self._lock = threading.Lock()

    def send_email_alert(self, subject: str, body: str, level: str = AlertLevel.ERROR) -> bool:
        """发送邮件告警"""
        try:
            smtp_server = self.email_config.get('smtp_server', '')
            smtp_port = self.email_config.get('smtp_port', 465)
            sender = self.email_config.get('sender', '')
            password = self.email_config.get('password', '')
            recipients = self.email_config.get('recipients', [])
            use_ssl = self.email_config.get('use_ssl', True)

            if not all([smtp_server, sender, password, recipients]):
                logger.error("Email configuration incomplete, cannot send alert")
                return False

            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{level_emoji.get(level, '📧')} [{level.upper()}] {subject}"
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)

            text_body = f"""
GitHub Trending Push - 系统告警

告警级别: {level.upper()}
告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}

---
此邮件由 GitHub Trending Push 系统自动发送
"""

            level_colors = {
                'info': '#17a2b8',
                'warning': '#ffc107',
                'error': '#dc3545',
                'critical': '#6f42c1'
            }
            alert_color = level_colors.get(level, '#6c757d')

            html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-box {{ background-color: #f8f9fa; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; }}
        .alert-{level} {{ border-left-color: {alert_color}; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h2>{level_emoji.get(level, '📧')} GitHub Trending Push - 系统告警</h2>
    <div class="alert-box alert-{level}">
        <p><strong>告警级别:</strong> {level.upper()}</p>
        <p class="timestamp"><strong>告警时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <div>{body.replace(chr(10), '<br>')}</div>
    </div>
    <p style="color: #6c757d; font-size: 0.85em;">此邮件由 GitHub Trending Push 系统自动发送</p>
</body>
</html>
"""

            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            server = self._get_smtp_connection()
            server.sendmail(sender, recipients, msg.as_string())

            logger.info(f"Alert email sent successfully: {subject}")
            return True

        except Exception as e:
            sanitized_error = self._sanitize_error_message(str(e))
            logger.error(f"Failed to send email alert: {sanitized_error}")
            return False

    def _sanitize_error_message(self, message: str) -> str:
        """Remove sensitive information from error messages"""
        import re
        message = re.sub(r'password[=:\s]+\S+', 'password=***', message, flags=re.IGNORECASE)
        message = re.sub(r'auth[=:\s]+\S+', 'auth=***', message, flags=re.IGNORECASE)
        message = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***@***.***', message)
        return message

    def send_wechat_alert(self, message: str, webhook_url: Optional[str] = None) -> bool:
        """发送企业微信告警"""
        try:
            webhook_url = webhook_url or self.alert_config.get('wechat_webhook', '')

            if not webhook_url:
                logger.warning("WeChat webhook URL not configured, skipping WeChat alert")
                return False

            data = {
                "msgtype": "text",
                "text": {
                    "content": f"【GitHub Trending Push 告警】\n{message}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }

            response = requests.post(webhook_url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info("WeChat alert sent successfully")
                return True
            else:
                logger.error(f"Failed to send WeChat alert: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send WeChat alert: {e}")
            return False

    def send_telegram_alert(self, message: str, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
        """发送 Telegram 告警"""
        try:
            bot_token = bot_token or self.alert_config.get('telegram_bot_token', '')
            chat_id = chat_id or self.alert_config.get('telegram_chat_id', '')

            if not all([bot_token, chat_id]):
                logger.warning("Telegram configuration incomplete, skipping Telegram alert")
                return False

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": f"🔔 *GitHub Trending Push 告警*\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.info("Telegram alert sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram alert: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def alert_health_check_failure(self, health_result: Dict) -> bool:
        """健康检查失败告警"""
        unhealthy_checks = [
            check for check in health_result.get('checks', [])
            if check['status'] in ['unhealthy', 'degraded']
        ]

        if not unhealthy_checks:
            return True

        subject = f"系统健康检查异常 ({len(unhealthy_checks)} 项)"

        body_lines = [
            f"整体状态: {health_result.get('status', 'unknown').upper()}",
            "",
            "异常项目:"
        ]

        for check in unhealthy_checks:
            body_lines.append(f"- {check['name']}: {check['status'].upper()}")
            body_lines.append(f"  消息: {check['message']}")
            if check.get('details'):
                body_lines.append(f"  详情: {check['details']}")
            body_lines.append("")

        body = "\n".join(body_lines)

        level = AlertLevel.CRITICAL if health_result.get('status') == 'unhealthy' else AlertLevel.WARNING

        success = self.send_email_alert(subject, body, level)

        wechat_message = f"{subject}\n\n{body}"
        self.send_wechat_alert(wechat_message)

        return success

    def alert_task_failure(self, task_name: str, error_message: str) -> bool:
        """任务执行失败告警"""
        subject = f"任务执行失败: {task_name}"
        body = f"任务名称: {task_name}\n错误信息: {error_message}"

        return self.send_email_alert(subject, body, AlertLevel.ERROR)

    def _get_smtp_connection(self):
        """获取SMTP连接（复用连接，线程安全）"""
        with self._lock:
            smtp_server = self.email_config.get('smtp_server', '')
            smtp_port = self.email_config.get('smtp_port', 465)
            sender = self.email_config.get('sender', '')
            password = self.email_config.get('password', '')
            use_ssl = self.email_config.get('use_ssl', True)

            try:
                if self._smtp_server is not None:
                    self._smtp_server.noop()
                    return self._smtp_server
            except Exception:
                logger.debug("Existing SMTP connection invalid, creating new one")
                self._smtp_server = None

            if use_ssl:
                self._smtp_server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                self._smtp_server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

            self._smtp_server.login(sender, password)
            logger.debug("SMTP connection established")
            return self._smtp_server

    def close(self):
        """关闭SMTP连接"""
        with self._lock:
            if self._smtp_server:
                try:
                    self._smtp_server.quit()
                    logger.debug("SMTP connection closed")
                except Exception as e:
                    logger.warning(f"Error closing SMTP connection: {e}")
                finally:
                    self._smtp_server = None
