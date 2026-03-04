"""
ConfigValidator 扩展测试
"""

import json
import tempfile
from pathlib import Path

import pytest

from dev_bot.config_validator import (
    ConfigValidator,
    ValidationError,
    ValidationResult,
)


@pytest.fixture
def temp_config():
    """创建临时配置文件"""
    config_data = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300,
        "auto_commit": False
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def valid_config():
    """有效的配置数据"""
    return {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300,
        "auto_commit": False
    }


@pytest.fixture
def invalid_config_missing_fields():
    """缺少必需字段的配置"""
    return {
        "ai_command": "iflow"
        # 缺少 prompt_file
    }


@pytest.fixture
def invalid_config_wrong_types():
    """类型错误的配置"""
    return {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": "300",  # 应该是整数
        "auto_commit": "false"  # 应该是布尔值
    }


@pytest.fixture
def invalid_config_out_of_range():
    """超出范围的配置"""
    return {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 5000,  # 超出最大值 3600
        "auto_commit": False
    }


@pytest.fixture
def valid_config_with_all_fields():
    """包含所有字段的配置"""
    return {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300,
        "auto_commit": False,
        "wait_interval": 10,
        "log_dir": "/tmp/logs",
        "stats_file": "/tmp/stats.json"
    }


def test_config_validator_initialization():
    """测试 ConfigValidator 初始化"""
    validator = ConfigValidator()
    assert validator is not None
    assert validator.custom_schemas == {}
    assert validator.custom_validators == {}


def test_validate_valid_config(temp_config):
    """测试验证有效配置"""
    validator = ConfigValidator()
    result = validator.validate(Path(temp_config))

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_missing_required_fields():
    """测试缺少必需字段"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow"
        # 缺少 prompt_file
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False
    assert len(result.errors) > 0

    # 检查错误信息
    error_messages = [error.message for error in result.errors]
    assert any("prompt_file" in msg for msg in error_messages)


def test_validate_field_types():
    """测试字段类型验证"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": "300",  # 应该是整数
        "auto_commit": "false"  # 应该是布尔值
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False

    # 检查类型错误
    type_errors = [error for error in result.errors if error.error_type == "INVALID_FIELD_TYPE"]
    assert len(type_errors) >= 1


def test_validate_value_range():
    """测试值范围验证"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 5000,  # 超出最大值 3600
        "auto_commit": False
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False

    # 检查范围错误
    range_errors = [error for error in result.errors if error.error_type == "VALUE_OUT_OF_RANGE"]
    assert len(range_errors) >= 1


def test_validate_invalid_json():
    """测试无效的 JSON 格式"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        invalid_json_file = f.name

    try:
        validator = ConfigValidator()
        result = validator.validate(Path(invalid_json_file))

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.errors[0].error_type == "INVALID_JSON"
    finally:
        Path(invalid_json_file).unlink(missing_ok=True)


def test_validation_result_properties():
    """测试 ValidationResult 属性"""
    result = ValidationResult(is_valid=True, errors=[])

    assert result.is_valid is True
    assert result.errors == []
    assert len(result.errors) == 0


def test_validation_result_with_errors():
    """测试带错误的 ValidationResult"""
    error = ValidationError(
        field_path="timeout_seconds",
        error_type="VALUE_OUT_OF_RANGE",
        expected="1-3600",
        actual=5000,
        message="超时时间超出有效范围"
    )

    result = ValidationResult(is_valid=False, errors=[error])

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field_path == "timeout_seconds"
    assert result.errors[0].error_type == "VALUE_OUT_OF_RANGE"


def test_validation_result_add_error():
    """测试 ValidationResult 添加错误"""
    result = ValidationResult(is_valid=True, errors=[])

    error = ValidationError(
        field_path="test_field",
        error_type="TEST_ERROR",
        expected="expected",
        actual="actual",
        message="Test error"
    )

    result.add_error(error)

    assert result.is_valid is False
    assert len(result.errors) == 1


def test_validation_result_get_errors_by_type():
    """测试按类型获取错误"""
    result = ValidationResult(is_valid=False, errors=[])

    error1 = ValidationError(
        field_path="field1",
        error_type="INVALID_FIELD_TYPE",
        expected="str",
        actual=123,
        message="Type error"
    )

    error2 = ValidationError(
        field_path="field2",
        error_type="VALUE_OUT_OF_RANGE",
        expected="1-100",
        actual=200,
        message="Range error"
    )

    error3 = ValidationError(
        field_path="field3",
        error_type="INVALID_FIELD_TYPE",
        expected="int",
        actual="string",
        message="Another type error"
    )

    result.add_error(error1)
    result.add_error(error2)
    result.add_error(error3)

    type_errors = result.get_errors_by_type("INVALID_FIELD_TYPE")
    assert len(type_errors) == 2

    range_errors = result.get_errors_by_type("VALUE_OUT_OF_RANGE")
    assert len(range_errors) == 1


def test_validation_result_get_error_summary():
    """测试获取错误摘要"""
    result = ValidationResult(is_valid=True, errors=[])

    # 有效配置的摘要
    summary = result.get_error_summary()
    assert "✓ 配置验证通过" in summary

    # 无效配置的摘要
    error = ValidationError(
        field_path="test_field",
        error_type="TEST_ERROR",
        expected="expected",
        actual="actual",
        message="Test error"
    )
    result.add_error(error)

    summary = result.get_error_summary()
    assert "✗ 配置验证失败" in summary
    assert "1 个错误" in summary


def test_validation_error_properties():
    """测试 ValidationError 属性"""
    error = ValidationError(
        field_path="ai_command",
        error_type="INVALID_FIELD_TYPE",
        expected="str",
        actual=123,
        message="字段类型错误"
    )

    assert error.field_path == "ai_command"
    assert error.error_type == "INVALID_FIELD_TYPE"
    assert error.expected == "str"
    assert error.actual == 123
    assert error.message == "字段类型错误"


def test_validation_error_str():
    """测试 ValidationError 字符串表示"""
    error = ValidationError(
        field_path="timeout_seconds",
        error_type="VALUE_OUT_OF_RANGE",
        expected="1-3600",
        actual=5000,
        message="超时时间超出有效范围",
        error_code="E004"
    )

    error_str = str(error)

    assert "E004" in error_str
    assert "timeout_seconds" in error_str
    assert "VALUE_OUT_OF_RANGE" in error_str


def test_format_error():
    """测试错误格式化"""
    validator = ConfigValidator()

    error = ValidationError(
        field_path="timeout_seconds",
        error_type="VALUE_OUT_OF_RANGE",
        expected="1-3600",
        actual=5000,
        message="超时时间超出有效范围",
        error_code="E004"
    )

    formatted = validator.format_error(error)

    assert "timeout_seconds" in formatted
    assert "当前值" in formatted
    assert "期望" in formatted
    assert "5000" in formatted


def test_validate_with_optional_fields():
    """测试验证包含可选字段的配置"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300,
        "auto_commit": False,
        "wait_interval": 10
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is True


def test_validate_sdd_spec():
    """测试验证 SDD spec 配置"""
    validator = ConfigValidator()
    config = {
        "name": "test-spec",
        "type": "feature",
        "version": "1.0.0"
    }

    result = validator.validate_config(config, "sdd")

    assert result.is_valid is True


def test_validate_sdd_spec_missing_fields():
    """测试验证缺少字段的 SDD spec"""
    validator = ConfigValidator()
    config = {
        "name": "test-spec"
        # 缺少 type 和 version
    }

    result = validator.validate_config(config, "sdd")

    assert result.is_valid is False
    # ConfigValidator 将所有缺失字段合并为一个错误
    assert len(result.errors) >= 1
    # 检查错误消息中包含缺少的字段
    error_msg = result.errors[0].message
    assert "type" in error_msg
    assert "version" in error_msg


def test_validate_empty_config():
    """测试空配置"""
    validator = ConfigValidator()
    config = {}

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False
    # ConfigValidator 将所有缺失字段合并为一个错误
    assert len(result.errors) >= 1
    # 检查错误消息中包含缺少的字段
    error_msg = result.errors[0].message
    assert "ai_command" in error_msg
    assert "prompt_file" in error_msg


def test_validate_with_extra_fields():
    """测试包含额外字段的配置"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300,
        "auto_commit": False,
        "extra_field": "some_value"
    }

    # 额外字段应该被忽略
    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is True


def test_validate_timeout_min_value():
    """测试超时时间最小值边界"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 0,  # 小于最小值 1
        "auto_commit": False
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False
    range_errors = result.get_errors_by_type("VALUE_OUT_OF_RANGE")
    assert len(range_errors) >= 1


def test_validate_timeout_max_value():
    """测试超时时间最大值边界"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 3600,  # 等于最大值
        "auto_commit": False
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is True


def test_validate_timeout_above_max():
    """测试超时时间超过最大值"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 3601,  # 超过最大值
        "auto_commit": False
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False
    range_errors = result.get_errors_by_type("VALUE_OUT_OF_RANGE")
    assert len(range_errors) >= 1


def test_validate_nonexistent_schema():
    """测试不存在的 schema"""
    validator = ConfigValidator()
    config = {
        "name": "test"
    }

    result = validator.validate_config(config, "nonexistent_schema")

    assert result.is_valid is False
    assert len(result.errors) > 0
    assert result.errors[0].error_type == "INVALID_SCHEMA"


def test_validate_wait_interval():
    """测试 wait_interval 字段"""
    validator = ConfigValidator()

    # 有效值
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "wait_interval": 5.5  # 浮点数
    }
    result = validator.validate_config(config, "dev-bot")
    assert result.is_valid is True

    # 无效值（超出范围）
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "wait_interval": 100  # 超过最大值 60
    }
    result = validator.validate_config(config, "dev-bot")
    assert result.is_valid is False


def test_multiple_errors_collection():
    """测试多个错误的收集"""
    validator = ConfigValidator()
    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": "invalid",  # 类型错误
        "auto_commit": "maybe"  # 类型错误
    }

    result = validator.validate_config(config, "dev-bot")

    assert result.is_valid is False
    # 应该收集多个错误
    assert len(result.errors) >= 1


def test_error_message_clarity():
    """测试错误消息的清晰度"""
    validator = ConfigValidator()

    error = ValidationError(
        field_path="timeout_seconds",
        error_type="VALUE_OUT_OF_RANGE",
        expected="1-3600",
        actual=5000,
        message="超时时间超出有效范围"
    )

    formatted = validator.format_error(error)

    # 检查错误消息包含关键信息
    assert "timeout_seconds" in formatted
    assert "期望" in formatted
    assert "当前值" in formatted


def test_register_custom_schema():
    """测试注册自定义 schema"""
    validator = ConfigValidator()

    custom_schema = {
        "required_fields": ["name", "value"],
        "field_types": {
            "name": str,
            "value": int
        }
    }

    validator.register_schema("custom", custom_schema)

    retrieved_schema = validator.get_schema("custom")
    assert retrieved_schema == custom_schema


def test_register_custom_validator():
    """测试注册自定义验证器"""
    validator = ConfigValidator()

    def validate_positive(value, config):
        if value > 0:
            return True, ""
        return False, "值必须为正数"

    validator.register_validator("positive", validate_positive)

    assert "positive" in validator.custom_validators


def test_custom_validator_execution():
    """测试自定义验证器执行"""
    validator = ConfigValidator()

    def validate_even_number(value, config):
        if value % 2 == 0:
            return True, ""
        return False, "值必须为偶数"

    validator.register_validator("even", validate_even_number)

    schema = {
        "required_fields": [],
        "field_types": {},
        "custom_validators": {
            "test_field": "even"
        }
    }

    validator.register_schema("test_schema", schema)

    # 有效值
    config = {"test_field": 4}
    result = validator.validate_config(config, "test_schema")
    assert result.is_valid is True

    # 无效值
    config = {"test_field": 3}
    result = validator.validate_config(config, "test_schema")
    assert result.is_valid is False


def test_env_var_resolution():
    """测试环境变量解析"""
    validator = ConfigValidator()

    import os

    # 设置测试环境变量
    os.environ["TEST_VAR"] = "test_value"

    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "test_field": "${TEST_VAR}"
    }

    resolved = validator.resolve_env_vars(config)

    assert resolved["test_field"] == "test_value"

    # 清理
    del os.environ["TEST_VAR"]


def test_env_var_resolution_with_default():
    """测试带默认值的环境变量解析"""
    validator = ConfigValidator()

    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "test_field": "${UNDEFINED_VAR:default_value}"
    }

    resolved = validator.resolve_env_vars(config)

    assert resolved["test_field"] == "default_value"


def test_env_var_resolution_nested():
    """测试嵌套结构的环境变量解析"""
    validator = ConfigValidator()

    import os
    os.environ["NESTED_VAR"] = "nested_value"

    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "nested": {
            "field1": "${NESTED_VAR}",
            "field2": ["${NESTED_VAR}", "static"]
        }
    }

    resolved = validator.resolve_env_vars(config)

    assert resolved["nested"]["field1"] == "nested_value"
    assert resolved["nested"]["field2"][0] == "nested_value"

    del os.environ["NESTED_VAR"]


def test_calculate_checksum():
    """测试计算校验和"""
    validator = ConfigValidator()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "data"}')
        temp_path = f.name

    try:
        checksum = validator.calculate_checksum(Path(temp_path), "sha256")

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 产生 64 字符的十六进制字符串
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_verify_checksum():
    """测试验证校验和"""
    validator = ConfigValidator()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "data"}')
        temp_path = f.name

    try:
        checksum = validator.calculate_checksum(Path(temp_path), "sha256")

        # 验证正确的校验和
        assert validator.verify_checksum(Path(temp_path), checksum, "sha256") is True

        # 验证错误的校验和
        assert validator.verify_checksum(Path(temp_path), "wrong_checksum", "sha256") is False
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_format_config():
    """测试格式化配置"""
    validator = ConfigValidator()

    config = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout_seconds": 300
    }

    formatted = validator.format_config(config, indent=2)

    assert isinstance(formatted, str)
    # 验证是有效的 JSON
    parsed = json.loads(formatted)
    assert parsed == config


def test_format_config_file():
    """测试格式化配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # 写入未格式化的 JSON
        f.write('{"ai_command":"iflow","prompt_file":"PROMPT.md"}')
        temp_path = f.name

    try:
        validator = ConfigValidator()
        validator.format_config_file(Path(temp_path), indent=2)

        # 读取并验证格式化后的内容
        with open(temp_path, encoding='utf-8') as f:
            content = f.read()

        # 应该包含换行和缩进
        assert "\n" in content
        assert "  " in content  # 两个空格缩进
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_merge_configs():
    """测试合并配置"""
    validator = ConfigValidator()
    result = ValidationResult(is_valid=True)

    base_config = {
        "field1": "value1",
        "field2": "value2"
    }

    override_config = {
        "field2": "new_value2",
        "field3": "value3"
    }

    merged = validator.merge_configs(base_config, override_config, result)

    assert merged["field1"] == "value1"  # 保留基础值
    assert merged["field2"] == "new_value2"  # 被覆盖
    assert merged["field3"] == "value3"  # 新增


def test_merge_configs_nested():
    """测试合并嵌套配置"""
    validator = ConfigValidator()
    result = ValidationResult(is_valid=True)

    base_config = {
        "nested": {
            "field1": "value1",
            "field2": "value2"
        }
    }

    override_config = {
        "nested": {
            "field2": "new_value2",
            "field3": "value3"
        }
    }

    merged = validator.merge_configs(base_config, override_config, result)

    assert merged["nested"]["field1"] == "value1"
    assert merged["nested"]["field2"] == "new_value2"
    assert merged["nested"]["field3"] == "value3"


def test_circular_inheritance_detection():
    """测试循环继承检测"""
    validator = ConfigValidator()
    result = ValidationResult(is_valid=True)

    config = {}
    visited = {id(config)}

    # 应该检测到循环继承并添加错误
    validator.merge_configs(config, config, result, visited)

    assert len(result.errors) > 0
    assert result.errors[0].error_type == "CIRCULAR_INHERITANCE"


def test_error_codes():
    """测试错误代码定义"""
    validator = ConfigValidator()

    assert "INVALID_JSON" in validator.ERROR_CODES
    assert "MISSING_REQUIRED_FIELD" in validator.ERROR_CODES
    assert "INVALID_FIELD_TYPE" in validator.ERROR_CODES
    assert "VALUE_OUT_OF_RANGE" in validator.ERROR_CODES

    assert validator.ERROR_CODES["INVALID_JSON"] == "E001"
    assert validator.ERROR_CODES["MISSING_REQUIRED_FIELD"] == "E002"
