"""
邮件发送模块 - 支持HTML邮件模板
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
import markdown


class EmailSender:
    """邮件发送器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化邮件发送器"""
        email_config = config.get('email', {})
        self.smtp_server = email_config.get('smtp_server', 'smtp.qq.com')
        self.smtp_port = email_config.get('smtp_port', 465)
        self.use_ssl = email_config.get('use_ssl', True)
        self.sender = email_config.get('sender', '')
        self.password = email_config.get('password', '')
        self.recipients = email_config.get('recipients', [])

        # 过滤掉空的收件人
        self.recipients = [r for r in self.recipients if r and 'example.com' not in r]

    def send_trending_email(self, trending_data: List[Dict[str, Any]], time_range: str) -> bool:
        """
        发送trending邮件
        :param trending_data: trending项目数据列表
        :param time_range: 时间范围 (daily/weekly/monthly)
        :return: 是否发送成功
        """
        if not self.recipients:
            logger.error("No valid email recipients configured")
            return False

        if not trending_data:
            logger.warning("No trending data to send")
            return False

        # 生成邮件内容
        subject = self._generate_subject(time_range)
        html_content = self._render_html(trending_data, time_range)

        return self._send_email(subject, html_content)

    def _generate_subject(self, time_range: str) -> str:
        """生成邮件主题"""
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        range_names = {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}
        range_name = range_names.get(time_range, 'Daily')

        return f"GitHub {range_name} Trending - {today}"

    def _render_html(self, data: List[Dict[str, Any]], time_range: str) -> str:
        """渲染HTML邮件内容"""
        # 尝试加载模板文件
        template_path = Path("templates/email_template.html")
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return self._fill_template(template, data, time_range)

        # 使用内置模板
        return self._generate_inline_html(data, time_range)

    def _fill_template(self, template: str, data: List[Dict[str, Any]], time_range: str) -> str:
        """填充HTML模板"""
        import datetime

        range_names = {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}
        range_names_cn = {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}

        # 生成项目卡片HTML
        cards_html = ""
        for idx, repo in enumerate(data[:25], 1):  # 限制最多25个项目
            stars_key = f'stars_{time_range}'
            stars_period = repo.get(stars_key, 0)

            # 将AI总结的Markdown转换为HTML
            ai_summary_md = repo.get('ai_summary', '')
            ai_summary_html = markdown.markdown(ai_summary_md)

            card = f'''
            <div style="background: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="background: #0366d6; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-right: 8px;">#{idx}</span>
                    <a href="{repo.get('url', '#')}" style="color: #0366d6; text-decoration: none; font-size: 18px; font-weight: 600;">{repo.get('name', 'Unknown')}</a>
                </div>
                <p style="color: #586069; margin: 8px 0; font-size: 14px;">{repo.get('description', 'No description')}</p>
                <div style="color: #24292e; margin: 12px 0; font-size: 14px; background-color: #f6f8fa; padding: 12px; border-radius: 4px;">
                    {ai_summary_html}
                </div>
                <div style="display: flex; gap: 16px; font-size: 12px; color: #586069;">
                    <span>Language: {repo.get('language', 'Unknown')}</span>
                    <span>Stars: {repo.get('stars', 0):,}</span>
                    <span>+{stars_period:,} this {time_range}</span>
                </div>
            </div>
            '''
            cards_html += card

        # 替换模板变量
        result = template.replace("{{TITLE}}", f"GitHub {range_names.get(time_range, 'Daily')} Trending")
        result = result.replace("{{TITLE_CN}}", f"GitHub {range_names_cn.get(time_range, '每日')}热门项目")
        result = result.replace("{{DATE}}", datetime.datetime.now().strftime("%Y-%m-%d"))
        result = result.replace("{{PROJECT_COUNT}}", str(len(data)))
        result = result.replace("{{PROJECT_CARDS}}", cards_html)

        return result

    def _generate_inline_html(self, data: List[Dict[str, Any]], time_range: str) -> str:
        """生成内联HTML（无模板时使用）"""
        import datetime

        range_names = {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}
        range_names_cn = {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f6f8fa; padding: 20px; margin: 0;">
            <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">GitHub {range_names.get(time_range, 'Daily')} Trending</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9;">{range_names_cn.get(time_range, '每日')}热门项目 - {datetime.datetime.now().strftime("%Y-%m-%d")}</p>
                </div>
                <div style="padding: 20px;">
                    <p style="color: #586069; margin-bottom: 20px;">Found {len(data)} trending repositories</p>
        '''

        for idx, repo in enumerate(data[:25], 1):
            stars_key = f'stars_{time_range}'
            stars_period = repo.get(stars_key, 0)

            # Markdown转HTML
            ai_summary_md = repo.get('ai_summary', '')
            ai_summary_html = markdown.markdown(ai_summary_md)

            html += f'''
                    <div style="background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                        <div style="margin-bottom: 8px;">
                            <span style="background: #0366d6; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-right: 8px;">#{idx}</span>
                            <a href="{repo.get('url', '#')}" style="color: #0366d6; text-decoration: none; font-size: 16px; font-weight: 600;">{repo.get('name', 'Unknown')}</a>
                        </div>
                        <p style="color: #24292e; margin: 8px 0; font-size: 14px;">{repo.get('description', 'No description')}</p>
                        <div style="color: #28a745; margin: 8px 0; font-size: 14px; font-style: italic;">{ai_summary_html}</div>
                        <div style="font-size: 12px; color: #586069;">
                            <span style="margin-right: 16px;">Language: {repo.get('language', 'Unknown')}</span>
                            <span style="margin-right: 16px;">Stars: {repo.get('stars', 0):,}</span>
                            <span>+{stars_period:,} stars</span>
                        </div>
                    </div>
            '''

        html += '''
                </div>
                <div style="background: #f6f8fa; padding: 16px; text-align: center; color: #586069; font-size: 12px;">
                    <p style="margin: 0;">Powered by GitHub Trending Push</p>
                </div>
            </div>
        </body>
        </html>
        '''

        return html

    def _send_email(self, subject: str, html_content: str) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)

            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")

            # 智能判断SSL/TLS模式
            if self.smtp_port == 465:
                # 端口465通常使用隐式SSL
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                # 端口587(Gmail等)使用显式TLS (STARTTLS)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_ssl: # 如果配置了use_ssl，尝试STARTTLS
                    server.starttls()

            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {len(self.recipients)} recipient(s)")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            logger.error("Please check your email credentials (use SMTP authorization code, not login password)")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


def create_mailer(config: Dict[str, Any]) -> EmailSender:
    """创建邮件发送器实例"""
    return EmailSender(config)
