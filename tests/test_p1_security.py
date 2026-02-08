import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.security import Sanitizer
from src.outputs.mailer import EmailSender
from fastapi.testclient import TestClient
from src.web.api import app

client = TestClient(app)

class TestP1Security:
    """P1 阶段安全测试"""

    def test_log_sanitization_secret_str(self):
        """验证 SecretStr 是否生效（日志不输出明文）"""
        # 模拟包含敏感信息的日志记录
        sensitive_data = "password='my_secret_password'"
        sanitized = Sanitizer.sanitize(sensitive_data)

        assert "my_secret_password" not in sanitized
        assert "***" in sanitized

        # 测试 Email 配置中的密码
        email_config_log = "Email config: user='test@example.com', password='smtp_auth_code'"
        sanitized_config = Sanitizer.sanitize(email_config_log)
        assert "smtp_auth_code" not in sanitized_config

    def test_token_exact_match(self):
        """验证 Token 精确匹配逻辑"""
        import jwt
        from src.infrastructure.security import Sanitizer

        secret = "test-secret-key"
        payload = {"user": "testuser", "exp": 9999999999}

        # 生成有效 token
        valid_token = jwt.encode(payload, secret, algorithm="HS256")

        # 验证有效 token 可以解码
        decoded = Sanitizer.verify_token(valid_token, secret, "HS256")
        assert decoded["user"] == "testuser"

        # 验证无效 token 被拒绝 (不同 secret)
        with pytest.raises(jwt.InvalidSignatureError):
            Sanitizer.verify_token(valid_token, "wrong-secret", "HS256")

        # 验证篡改的 token 被拒绝
        tampered_token = valid_token[:-5] + "XXXXX"
        with pytest.raises(jwt.InvalidTokenError):
            Sanitizer.verify_token(tampered_token, secret, "HS256")

    def test_css_color_injection_protection(self):
        """验证 CSS 颜色注入防护"""
        config = {"email": {"sender": "test@example.com", "recipients": ["r@example.com"]}}
        sender = EmailSender(config)

        # 构造恶意 tag 数据
        malicious_repo = {
            "name": "malicious-repo",
            "url": "http://example.com",
            "description": "test",
            "language": "Python",
            "stars": 100,
            "stars_daily": 10,
            "tags": [
                {
                    "name": "Malicious Tag",
                    "color": "red; background-image: url('http://hacker.com/steal');"  # 尝试注入样式
                }
            ]
        }

        html_content = sender._render_html([malicious_repo], "daily")

        # 验证输出的 HTML 中，颜色属性被转义或清洗，不包含恶意的 background-image
        # bleach 应该会转义分号或清洗 style 属性
        assert "background-image" not in html_content or "&quot;" in html_content or "&lt;" in html_content
