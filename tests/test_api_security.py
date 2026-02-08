#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 安全测试 - 验证路径参数验证
"""

import pytest
from fastapi.testclient import TestClient
from src.web.api import app


client = TestClient(app)


class TestPathParameterValidation:
    """路径参数验证安全测试"""

    def test_time_range_invalid_value(self):
        """测试 time_range 参数拒绝无效值"""
        # 尝试注入无效值
        response = client.get("/api/trending/invalid")
        assert response.status_code == 422  # Validation error

    def test_time_range_injection_attempt(self):
        """测试 time_range 参数拒绝路径遍历攻击"""
        # 包含 / 的输入会被 FastAPI 路由系统拒绝（404）
        path_traversal_inputs = ["../etc/passwd", "../../secret"]
        for malicious in path_traversal_inputs:
            response = client.get(f"/api/trending/{malicious}")
            assert response.status_code == 404, f"Failed to block path traversal: {malicious}"

        # 所有无效输入（包括命令注入尝试）会触发 Literal 类型验证（422）
        invalid_inputs = ["invalid", "hourly", "yearly", "daily;rm -rf /", "daily' OR '1'='1"]
        for malicious in invalid_inputs:
            response = client.get(f"/api/trending/{malicious}")
            assert response.status_code == 422, f"Failed to block invalid value: {malicious}"

    def test_owner_repo_invalid_characters(self):
        """测试 owner/repo 参数拒绝危险字符"""
        # 包含 / 的输入会被路由系统拒绝（404）
        path_traversal = [("../etc", "passwd"), ("owner", "../../secret"), ("owner/nested", "repo")]
        for owner, repo in path_traversal:
            response = client.get(f"/api/analysis/{owner}/{repo}")
            assert response.status_code in [401, 404], f"Failed to block path traversal: {owner}/{repo}"

        # 不符合正则的字符会触发验证错误（422 或 401）或被路由系统拒绝（404）
        invalid_chars = [
            ("owner<script>", "repo", [401, 422]),  # XSS 尝试
            ("owner' OR '1'='1", "repo", [401, 422]),  # SQL 注入尝试
            ("owner;rm -rf", "repo", [401, 422]),  # 命令注入
            ("owner@", "repo", [401, 422]),  # 非法字符
            ("owner#hash", "repo", [401, 404, 422]),  # URL特殊字符（被路由系统拒绝）
        ]
        for owner, repo, expected_codes in invalid_chars:
            response = client.get(f"/api/analysis/{owner}/{repo}")
            assert response.status_code in expected_codes, f"Failed to block invalid chars: {owner}/{repo} (got {response.status_code})"

    def test_task_id_invalid_format(self):
        """测试 task_id 参数拒绝非 UUID 格式"""
        # 包含 / 的输入会被路由系统拒绝（404）
        response = client.get("/api/tasks/status/../etc/passwd")
        assert response.status_code == 404, "Failed to block path traversal"

        # 不符合 UUID 格式的输入会触发验证错误（422）
        invalid_uuids = [
            "not-a-uuid",
            "12345",
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee-extra",  # 太长
            "short",
            "aaaaaaaa-bbbb-cccc-dddd",  # 太短
            "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",  # 非十六进制
        ]
        for malicious in invalid_uuids:
            response = client.get(f"/api/tasks/status/{malicious}")
            assert response.status_code in [401, 422], f"Failed to block invalid UUID: {malicious}"

    def test_valid_parameters_accepted(self):
        """测试合法参数被正确接受（不会因参数验证失败）"""
        # 合法的 time_range - 会通过参数验证，但可能因其他原因失败（认证、业务逻辑等）
        response = client.get("/api/trending/daily")
        assert response.status_code != 422, "Valid time_range should not trigger validation error"

        # 合法的 owner/repo - 只包含允许的字符
        response = client.get("/api/analysis/microsoft/vscode")
        assert response.status_code != 422, "Valid owner/repo should not trigger validation error"

        # 合法的 UUID
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/tasks/status/{valid_uuid}")
        assert response.status_code != 422, "Valid UUID should not trigger validation error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
