#!/usr/bin/env python3

"""
测试配置验证系统 (config_validator.py)
"""

import json
import tempfile
from pathlib import Path

import pytest

from dev_bot.config_validator import (
    ConfigValidator,
    ValidationError,
    ValidationResult,
    validate_config_dict,
    validate_config_file,
)


class TestValidationError:
    """测试 ValidationError 类"""

    def test_validation_error_creation(self):
        """测试创建验证错误"""
        error = ValidationError(
            field_path="ai_command",
            error_type="INVALID_FIELD_TYPE",
            expected=str,
            actual=123,
            message="字段类型错误"
        )

        assert error.field_path == "ai_command"
        assert error.error_type == "INVALID_FIELD_TYPE"
        assert error.expected == str
        assert error.actual == 123
        assert error.message == "字段类型错误"

    def test_validation_error_str(self):
        """测试验证错误的字符串表示"""
        error = ValidationError(
            field_path="timeout",
            error_type="VALUE_OUT_OF_RANGE",
            expected=">= 1",
            actual=0,
            message="超时时间必须大于0",
            error_code="E004"
        )

        error_str = str(error)
        assert "timeout" in error_str
        assert "E004" in error_str
        assert ">= 1" in error_str
        assert "0" in error_str


class TestValidationResult:
    """测试 ValidationResult 类"""

    def test_validation_result_initial_valid(self):
        """测试初始验证结果为有效"""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validation_result_add_error(self):
        """测试添加错误"""
        result = ValidationResult(is_valid=True)
        error = ValidationError(
            field_path="test",
            error_type="TEST_ERROR",
            expected="value",
            actual="wrong",
            message="测试错误"
        )

        result.add_error(error)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == error

    def test_validation_result_get_errors_by_type(self):
        """测试按类型获取错误"""
        result = ValidationResult(is_valid=True)

        error1 = ValidationError("f1", "TYPE_ERROR", str, 1, "类型错误")
        error2 = ValidationError("f2", "RANGE_ERROR", 10, 5, "范围错误")
        error3 = ValidationError("f3", "TYPE_ERROR", int, "x", "类型错误2")

        result.add_error(error1)
        result.add_error(error2)
        result.add_error(error3)

        type_errors = result.get_errors_by_type("TYPE_ERROR")
        assert len(type_errors) == 2
        assert error1 in type_errors
        assert error3 in type_errors

    def test_validation_result_get_error_summary_valid(self):
        """测试获取有效结果的错误摘要"""
        result = ValidationResult(is_valid=True)
        summary = result.get_error_summary()
        assert "✓ 配置验证通过" in summary

    def test_validation_result_get_error_summary_invalid(self):
        """测试获取无效结果的错误摘要"""
        result = ValidationResult(is_valid=True)
        error1 = ValidationError("f1", "ERROR1", "e1", "a1", "错误1")
        error2 = ValidationError("f2", "ERROR2", "e2", "a2", "错误2")

        result.add_error(error1)
        result.add_error(error2)

        summary = result.get_error_summary()
        assert "✗ 配置验证失败" in summary
        assert "2 个错误" in summary
        assert "f1" in summary
        assert "f2" in summary


class TestConfigValidator:
    """测试 ConfigValidator 类"""

    def test_validator_initialization(self):
        """测试验证器初始化"""
        validator = ConfigValidator()
        assert validator.custom_schemas == {}
        assert "dev-bot" in validator.CONFIG_SCHEMAS
        assert "sdd" in validator.CONFIG_SCHEMAS

    def test_register_schema(self):
        """测试注册自定义 Schema"""
        validator = ConfigValidator()
        custom_schema = {
            "required_fields": ["field1"],
            "field_types": {"field1": str}
        }

        validator.register_schema("custom", custom_schema)

        assert "custom" in validator.custom_schemas
        assert validator.custom_schemas["custom"] == custom_schema

    def test_get_schema_builtin(self):
        """测试获取内置 Schema"""
        validator = ConfigValidator()
        schema = validator.get_schema("dev-bot")

        assert schema == validator.CONFIG_SCHEMAS["dev-bot"]
        assert "required_fields" in schema
        assert "ai_command" in schema["required_fields"]

    def test_get_schema_custom(self):
        """测试获取自定义 Schema"""
        validator = ConfigValidator()
        custom_schema = {"test": "value"}
        validator.register_schema("my_schema", custom_schema)

        schema = validator.get_schema("my_schema")
        assert schema == custom_schema

    def test_get_schema_nonexistent(self):
        """测试获取不存在的 Schema"""
        validator = ConfigValidator()
        schema = validator.get_schema("nonexistent")
        assert schema == {}

    def test_validate_file_not_found(self):
        """测试验证不存在的文件"""
        validator = ConfigValidator()
        result = validator.validate(Path("/nonexistent/config.json"))

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "FILE_NOT_FOUND"

    def test_validate_invalid_json(self):
        """测试验证无效的 JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            validator = ConfigValidator()
            result = validator.validate(temp_path)

            assert result.is_valid is False
            assert len(result.errors) == 1
            assert result.errors[0].error_type == "INVALID_JSON"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_dev_bot_config_valid(self):
        """测试验证有效的 dev-bot 配置"""
        config_data = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md",
            "timeout_seconds": 300,
            "auto_commit": True
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            validator = ConfigValidator()
            result = validator.validate(temp_path)

            assert result.is_valid is True
            assert len(result.errors) == 0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_dev_bot_config_missing_required(self):
        """测试验证缺少必需字段的配置"""
        config_data = {
            "timeout_seconds": 300
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            validator = ConfigValidator()
            result = validator.validate(temp_path)

            assert result.is_valid is False
            errors = result.get_errors_by_type("MISSING_REQUIRED_FIELD")
            assert len(errors) > 0
            assert any("ai_command" in str(e) for e in errors)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_dev_bot_config_invalid_type(self):
        """测试验证类型错误的字段"""
        config_data = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md",
            "timeout_seconds": "300",  # 应该是 int，但是 str
            "auto_commit": "true"  # 应该是 bool，但是 str
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            validator = ConfigValidator()
            result = validator.validate(temp_path)

            assert result.is_valid is False
            type_errors = result.get_errors_by_type("INVALID_FIELD_TYPE")
            assert len(type_errors) >= 2
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_dev_bot_config_out_of_range(self):
        """测试验证超出范围的值"""
        config_data = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md",
            "timeout_seconds": 5000,  # 超出最大值 3600
            "wait_interval": 0.05  # 小于最小值 0.1
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            validator = ConfigValidator()
            result = validator.validate(temp_path)

            assert result.is_valid is False
            range_errors = result.get_errors_by_type("VALUE_OUT_OF_RANGE")
            assert len(range_errors) >= 2
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_config_dict_valid(self):
        """测试验证有效的配置字典"""
        config = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md",
            "timeout_seconds": 300
        }

        validator = ConfigValidator()
        result = validator.validate_config(config, "dev-bot")

        assert result.is_valid is True

    def test_validate_config_dict_invalid_schema(self):
        """测试验证使用无效 Schema 的配置"""
        config = {"test": "value"}

        validator = ConfigValidator()
        result = validator.validate_config(config, "nonexistent_schema")

        assert result.is_valid is False
        assert any(e.error_type == "INVALID_SCHEMA" for e in result.errors)

    def test_format_error(self):
        """测试格式化错误信息"""
        validator = ConfigValidator()
        error = ValidationError(
            field_path="timeout",
            error_type="VALUE_OUT_OF_RANGE",
            expected=">= 1",
            actual=0,
            message="超时时间必须大于0",
            error_code="E004"
        )

        formatted = validator.format_error(error)
        assert "❌" in formatted
        assert "timeout" in formatted
        assert "E004" in formatted

    def test_validate_spec_config(self):
        """测试验证 spec 配置"""
        config = {
            "spec_version": "1.0",
            "metadata": {
                "name": "test",
                "type": "feature",
                "version": "1.0.0"
            },
            "description": "测试 spec"
        }

        validator = ConfigValidator()
        result = validator.validate_config(config, "spec")

        assert result.is_valid is True


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_validate_config_file_valid(self):
        """测试便捷函数验证有效配置文件"""
        config_data = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            result = validate_config_file(temp_path)
            assert result.is_valid is True
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_config_dict_valid(self):
        """测试便捷函数验证有效配置字典"""
        config = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md"
        }

        result = validate_config_dict(config, "dev-bot")
        assert result.is_valid is True

    def test_validate_config_dict_default_schema(self):
        """测试便捷函数使用默认 Schema"""
        config = {
            "ai_command": "iflow",
            "prompt_file": "PROMPT.md"
        }

        result = validate_config_dict(config)
        assert result.is_valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
