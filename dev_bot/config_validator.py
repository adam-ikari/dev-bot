#!/usr/bin/env python3

"""
配置验证系统 - 验证配置文件的格式、必需字段和字段类型

功能:
1. 配置文件格式验证 (JSON 格式检查)
2. 必需字段检查
3. 字段类型验证
4. 字段值范围验证
5. 友好的错误提示
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union


@dataclass
class ValidationError:
    """验证错误"""
    field_path: str
    error_type: str
    expected: Any
    actual: Any
    message: str
    error_code: str = ""

    def __str__(self) -> str:
        """格式化错误信息"""
        return f"[{self.error_code}] {self.field_path}: {self.message} (error_type: {self.error_type}, expected: {self.expected}, got: {self.actual})"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(self, error: ValidationError) -> None:
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False

    def get_errors_by_type(self, error_type: str) -> List[ValidationError]:
        """按类型获取错误"""
        return [e for e in self.errors if e.error_type == error_type]

    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if self.is_valid:
            return "✓ 配置验证通过"

        summary = f"✗ 配置验证失败，发现 {len(self.errors)} 个错误:\n"
        for i, error in enumerate(self.errors, 1):
            summary += f"  {i}. {error}\n"
        return summary


class ConfigValidator:
    """配置验证器"""

    # 错误代码定义
    ERROR_CODES = {
        "INVALID_JSON": "E001",
        "MISSING_REQUIRED_FIELD": "E002",
        "INVALID_FIELD_TYPE": "E003",
        "VALUE_OUT_OF_RANGE": "E004",
        "INVALID_VALUE": "E005",
        "FILE_NOT_FOUND": "E006",
    }

    # 预定义的配置 Schema
    CONFIG_SCHEMAS = {
        "dev-bot": {
            "required_fields": [
                "ai_command",
                "prompt_file"
            ],
            "field_types": {
                "ai_command": str,
                "prompt_file": str,
                "timeout_seconds": int,
                "wait_interval": (int, float),
                "auto_commit": bool,
                "log_dir": str,
                "stats_file": str,
                "session_counter_file": str,
                "git_commit_template": str,
            },
            "field_ranges": {
                "timeout_seconds": {"min": 1, "max": 3600},
                "wait_interval": {"min": 0.1, "max": 60},
            }
        },
        "sdd": {
            "required_fields": [
                "name",
                "type",
                "version"
            ],
            "field_types": {
                "name": str,
                "type": str,
                "version": str,
                "description": str,
            }
        },
        "spec": {
            "required_fields": [
                "spec_version",
                "metadata",
                "description"
            ],
            "field_types": {
                "spec_version": str,
                "metadata": dict,
                "description": str,
                "requirements": list,
                "user_stories": list,
                "acceptance_criteria": list,
            }
        }
    }

    def __init__(self):
        """初始化配置验证器"""
        self.custom_schemas: Dict[str, Dict] = {}

    def register_schema(self, name: str, schema: Dict) -> None:
        """注册自定义 Schema"""
        self.custom_schemas[name] = schema

    def get_schema(self, name: str) -> Dict:
        """获取 Schema"""
        return self.custom_schemas.get(name, self.CONFIG_SCHEMAS.get(name, {}))

    def validate(self, config_path: Path) -> ValidationResult:
        """验证配置文件"""
        result = ValidationResult(is_valid=True)

        # 检查文件是否存在
        if not config_path.exists():
            result.add_error(ValidationError(
                field_path="",
                error_type="FILE_NOT_FOUND",
                expected=f"文件 {config_path}",
                actual="不存在",
                message=f"配置文件不存在: {config_path}",
                error_code=self.ERROR_CODES["FILE_NOT_FOUND"]
            ))
            return result

        # 读取并解析 JSON
        try:
            with open(config_path, encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(ValidationError(
                field_path="",
                error_type="INVALID_JSON",
                expected="有效的 JSON 格式",
                actual=f"语法错误在第 {e.lineno} 行，第 {e.colno} 列",
                message=f"JSON 格式错误: {e.msg}",
                error_code=self.ERROR_CODES["INVALID_JSON"]
            ))
            return result
        except Exception as e:
            result.add_error(ValidationError(
                field_path="",
                error_type="INVALID_JSON",
                expected="可读取的文件",
                actual=str(e),
                message=f"读取配置文件失败: {e}",
                error_code=self.ERROR_CODES["INVALID_JSON"]
            ))
            return result

        # 验证配置内容
        return self.validate_config(config, "dev-bot")

    def validate_config(self, config: Dict, schema_name: str) -> ValidationResult:
        """验证配置字典"""
        result = ValidationResult(is_valid=True)
        schema = self.get_schema(schema_name)

        if not schema:
            result.add_error(ValidationError(
                field_path="",
                error_type="INVALID_SCHEMA",
                expected=f"Schema '{schema_name}'",
                actual="不存在",
                message=f"未找到 Schema: {schema_name}",
                error_code="E007"
            ))
            return result

        # 验证必需字段
        self._validate_required_fields(config, schema, result)

        # 验证字段类型
        self._validate_field_types(config, schema, result)

        # 验证字段值范围
        self._validate_field_ranges(config, schema, result)

        return result

    def _validate_required_fields(
        self,
        config: Dict,
        schema: Dict,
        result: ValidationResult
    ) -> None:
        """验证必需字段"""
        required_fields = schema.get("required_fields", [])
        missing_fields = []

        for field in required_fields:
            if field not in config:
                missing_fields.append(field)

        if missing_fields:
            result.add_error(ValidationError(
                field_path="",
                error_type="MISSING_REQUIRED_FIELD",
                expected=f"必需字段: {', '.join(required_fields)}",
                actual=f"缺少: {', '.join(missing_fields)}",
                message=f"缺少必需字段: {', '.join(missing_fields)}",
                error_code=self.ERROR_CODES["MISSING_REQUIRED_FIELD"]
            ))

    def _validate_field_types(
        self,
        config: Dict,
        schema: Dict,
        result: ValidationResult
    ) -> None:
        """验证字段类型"""
        field_types = schema.get("field_types", {})

        for field, expected_type in field_types.items():
            if field not in config:
                continue

            actual_value = config[field]
            actual_type = type(actual_value)

            # 处理联合类型（支持多种类型）
            if isinstance(expected_type, tuple):
                if not isinstance(actual_value, expected_type):
                    expected_types = [t.__name__ for t in expected_type]
                    result.add_error(ValidationError(
                        field_path=field,
                        error_type="INVALID_FIELD_TYPE",
                        expected="或".join(expected_types),
                        actual=actual_value,
                        message=f"字段 '{field}' 类型错误，应为 {' 或 '.join(expected_types)}",
                        error_code=self.ERROR_CODES["INVALID_FIELD_TYPE"]
                    ))
            else:
                if not isinstance(actual_value, expected_type):
                    result.add_error(ValidationError(
                        field_path=field,
                        error_type="INVALID_FIELD_TYPE",
                        expected=expected_type.__name__,
                        actual=actual_value,
                        message=f"字段 '{field}' 类型错误，应为 {expected_type.__name__}",
                        error_code=self.ERROR_CODES["INVALID_FIELD_TYPE"]
                    ))

    def _validate_field_ranges(
        self,
        config: Dict,
        schema: Dict,
        result: ValidationResult
    ) -> None:
        """验证字段值范围"""
        field_ranges = schema.get("field_ranges", {})

        for field, range_config in field_ranges.items():
            if field not in config:
                continue

            value = config[field]

            if not isinstance(value, (int, float)):
                continue

            min_val = range_config.get("min")
            max_val = range_config.get("max")

            if min_val is not None and value < min_val:
                result.add_error(ValidationError(
                    field_path=field,
                    error_type="VALUE_OUT_OF_RANGE",
                    expected=f">= {min_val}",
                    actual=value,
                    message=f"字段 '{field}' 值 {value} 小于最小值 {min_val}",
                    error_code=self.ERROR_CODES["VALUE_OUT_OF_RANGE"]
                ))

            if max_val is not None and value > max_val:
                result.add_error(ValidationError(
                    field_path=field,
                    error_type="VALUE_OUT_OF_RANGE",
                    expected=f"<= {max_val}",
                    actual=value,
                    message=f"字段 '{field}' 值 {value} 大于最大值 {max_val}",
                    error_code=self.ERROR_CODES["VALUE_OUT_OF_RANGE"]
                ))

    def format_error(self, error: ValidationError) -> str:
        """格式化错误信息"""
        error_type_messages = {
            "INVALID_JSON": "❌ 配置文件格式错误",
            "MISSING_REQUIRED_FIELD": "❌ 缺少必需字段",
            "INVALID_FIELD_TYPE": "❌ 字段类型错误",
            "VALUE_OUT_OF_RANGE": "❌ 字段值超出范围",
            "INVALID_VALUE": "❌ 字段值无效",
            "FILE_NOT_FOUND": "❌ 文件不存在",
            "INVALID_SCHEMA": "❌ Schema 不存在",
        }

        prefix = error_type_messages.get(error.error_type, "❌ 配置验证错误")

        # 构建详细错误信息
        details = []
        if error.error_code:
            details.append(f"错误代码: {error.error_code}")
        if error.field_path:
            details.append(f"字段: {error.field_path}")
        if error.actual is not None:
            details.append(f"当前值: {error.actual}")
        if error.expected is not None:
            details.append(f"期望: {error.expected}")

        detail_str = ", ".join(details) if details else ""

        return f"{prefix}: {error.message}\n  {detail_str}"


# ============================================================================
# 便捷函数
# ============================================================================

def validate_config_file(config_path: Union[str, Path]) -> ValidationResult:
    """便捷函数：验证配置文件"""
    validator = ConfigValidator()
    return validator.validate(Path(config_path))


def validate_config_dict(config: Dict, schema_name: str = "dev-bot") -> ValidationResult:
    """便捷函数：验证配置字典"""
    validator = ConfigValidator()
    return validator.validate_config(config, schema_name)
