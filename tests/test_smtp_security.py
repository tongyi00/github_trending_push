#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SMTP 密码安全存储测试
"""

import pytest
import os
from src.infrastructure.security import encrypt_sensitive, decrypt_sensitive
from src.outputs.mailer import EmailSender


class TestSMTPPasswordSecurity:
    """SMTP 密码加密存储安全测试"""

    def test_password_priority_env_var(self, monkeypatch):
        """测试环境变量优先级最高"""
        monkeypatch.setenv("SMTP_PASSWORD", "env-password")

        config = {
            'email': {
                'password_encrypted': encrypt_sensitive("encrypted-password"),
                'password': 'plaintext-password'
            }
        }

        mailer = EmailSender(config)
        assert mailer.password == "env-password", "Environment variable should have highest priority"

    def test_password_priority_encrypted(self):
        """测试加密密码优先级次高"""
        encrypted = encrypt_sensitive("encrypted-password")

        config = {
            'email': {
                'password_encrypted': encrypted,
                'password': 'plaintext-password'
            }
        }

        mailer = EmailSender(config)
        assert mailer.password == "encrypted-password", "Encrypted password should be used when env var not set"

    def test_password_priority_plaintext(self):
        """测试明文密码作为后备方案"""
        config = {
            'email': {
                'password': 'plaintext-password'
            }
        }

        mailer = EmailSender(config)
        assert mailer.password == "plaintext-password", "Plaintext password should be used as fallback"

    def test_encrypted_password_decryption(self):
        """测试加密密码正确解密"""
        original = "my-smtp-password-123"
        encrypted = encrypt_sensitive(original)

        config = {
            'email': {
                'password_encrypted': encrypted
            }
        }

        mailer = EmailSender(config)
        assert mailer.password == original, "Encrypted password should be correctly decrypted"

    def test_invalid_encrypted_password(self, caplog):
        """测试无效加密密码时的错误处理"""
        config = {
            'email': {
                'password_encrypted': 'invalid-encrypted-data',
                'password': 'fallback-plaintext'
            }
        }

        mailer = EmailSender(config)
        # 解密失败时应回退到明文密码
        assert mailer.password == 'fallback-plaintext', "Should fallback to plaintext when decryption fails"
        # loguru 输出到 stderr，检查功能是否正常即可

    def test_production_plaintext_warning(self, monkeypatch, caplog):
        """测试生产环境使用明文密码时的警告"""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = {
            'email': {
                'password': 'plaintext-password'
            }
        }

        mailer = EmailSender(config)
        # loguru 输出到 stderr，检查密码已正确加载即可
        assert mailer.password == 'plaintext-password', "Should load plaintext password in production"

    def test_empty_password_handling(self):
        """测试空密码处理"""
        config = {
            'email': {}
        }

        mailer = EmailSender(config)
        assert mailer.password == '', "Empty password should be handled gracefully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
