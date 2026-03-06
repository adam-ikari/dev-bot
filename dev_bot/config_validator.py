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
        return (
            f"[{self.error_code}] {self.field_path}: {self.message} "
            f"(error_type: {self.error_type}, expected: {self.expected}, got: {self.actual})"
        )


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
        "INVALID_SCHEMA": "E007",
        "CIRCULAR_INHERITANCE": "E008",
        "CUSTOM_VALIDATION_FAILED": "E009",
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
        self.custom_validators: Dict[str, Any] = {}

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

        for field_name in required_fields:
            if field_name not in config:
                missing_fields.append(field_name)

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

        for field_name, expected_type in field_types.items():
            if field_name not in config:
                continue

            actual_value = config[field_name]

            # 处理联合类型（支持多种类型）
            if isinstance(expected_type, tuple):
                if not isinstance(actual_value, expected_type):
                    expected_types = [t.__name__ for t in expected_type]
                    result.add_error(ValidationError(
                        field_path=field_name,
                        error_type="INVALID_FIELD_TYPE",
                        expected="或".join(expected_types),
                        actual=actual_value,
                        message=f"字段 '{field_name}' 类型错误，应为 {' 或 '.join(expected_types)}",
                        error_code=self.ERROR_CODES["INVALID_FIELD_TYPE"]
                    ))
            else:
                if not isinstance(actual_value, expected_type):
                    result.add_error(ValidationError(
                        field_path=field_name,
                        error_type="INVALID_FIELD_TYPE",
                        expected=expected_type.__name__,
                        actual=actual_value,
                        message=f"字段 '{field_name}' 类型错误，应为 {expected_type.__name__}",
                        error_code=self.ERROR_CODES["INVALID_FIELD_TYPE"]
                    ))

        # 验证自定义验证器
        custom_validators = schema.get("custom_validators", {})
        for field_name, validator_name in custom_validators.items():
            if field_name not in config:
                continue

            if validator_name not in self.custom_validators:
                result.add_error(ValidationError(
                    field_path=field_name,
                    error_type="CUSTOM_VALIDATION_FAILED",
                    expected=f"验证器 '{validator_name}'",
                    actual="未注册",
                    message=f"自定义验证器 '{validator_name}' 未注册",
                    error_code=self.ERROR_CODES["CUSTOM_VALIDATION_FAILED"]
                ))
                continue

            validator_func = self.custom_validators[validator_name]
            is_valid, error_message = validator_func(config[field_name], config)

            if not is_valid:
                result.add_error(ValidationError(
                    field_path=field_name,
                    error_type="CUSTOM_VALIDATION_FAILED",
                    expected=f"通过 '{validator_name}' 验证",
                    actual=config[field_name],
                    message=f"字段 '{field_name}' 自定义验证失败: {error_message}",
                    error_code=self.ERROR_CODES["CUSTOM_VALIDATION_FAILED"]
                ))

    def _validate_field_ranges(
        self,
        config: Dict,
        schema: Dict,
        result: ValidationResult
    ) -> None:
        """验证字段值范围"""
        field_ranges = schema.get("field_ranges", {})

        for field_name, range_config in field_ranges.items():
            if field_name not in config:
                continue

            value = config[field_name]

            if not isinstance(value, (int, float)):
                continue

            min_val = range_config.get("min")
            max_val = range_config.get("max")

            if min_val is not None and value < min_val:
                result.add_error(ValidationError(
                    field_path=field_name,
                    error_type="VALUE_OUT_OF_RANGE",
                    expected=f">= {min_val}",
                    actual=value,
                    message=f"字段 '{field_name}' 值 {value} 小于最小值 {min_val}",
                    error_code=self.ERROR_CODES["VALUE_OUT_OF_RANGE"]
                ))

            if max_val is not None and value > max_val:
                result.add_error(ValidationError(
                    field_path=field_name,
                    error_type="VALUE_OUT_OF_RANGE",
                    expected=f"<= {max_val}",
                    actual=value,
                    message=f"字段 '{field_name}' 值 {value} 大于最大值 {max_val}",
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
            "CIRCULAR_INHERITANCE": "❌ 循环继承",
            "CUSTOM_VALIDATION_FAILED": "❌ 自定义验证失败",
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

    def register_validator(self, name: str, validator_func: Any) -> None:
        """注册自定义验证器

        Args:
            name: 验证器名称
            validator_func: 验证函数，签名应为 (value, config) -> (bool, str)
                          返回 (is_valid, error_message)
        """
        self.custom_validators[name] = validator_func

    def resolve_env_vars(self, config: Dict) -> Dict:
        """解析配置中的环境变量占位符

        支持 ${VAR_NAME} 和 ${VAR_NAME:default_value} 格式

        Args:
            config: 配置字典

        Returns:
            解析后的配置字典
        """
        import os
        import re

        def resolve_value(value: Any) -> Any:
            """递归解析值中的环境变量"""
            if isinstance(value, str):
                # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default}
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

                def replace_env_var(match):
                    var_name = match.group(1)
                    default_value = match.group(2) if match.group(2) is not None else None
                    return os.environ.get(var_name, default_value)

                return re.sub(pattern, replace_env_var, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value

        return resolve_value(config)

    def calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """计算文件的校验和

        Args:
            file_path: 文件路径
            algorithm: 哈希算法，支持 md5, sha1, sha256, sha512

        Returns:
            十六进制格式的校验和字符串
        """
        import hashlib

        hash_func = getattr(hashlib, algorithm, hashlib.sha256)()

        with open(file_path, 'rb') as f:
            # 分块读取文件，避免大文件内存问题
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def verify_checksum(self, file_path: Path, checksum: str, algorithm: str = "sha256") -> bool:
        """验证文件的校验和

        Args:
            file_path: 文件路径
            checksum: 期望的校验和
            algorithm: 哈希算法

        Returns:
            校验和是否匹配
        """
        calculated_checksum = self.calculate_checksum(file_path, algorithm)
        return calculated_checksum.lower() == checksum.lower()

    def format_config(self, config: Dict, indent: int = 2) -> str:
        """格式化配置为 JSON 字符串

        Args:
            config: 配置字典
            indent: 缩进空格数

        Returns:
            格式化后的 JSON 字符串
        """
        return json.dumps(config, indent=indent, ensure_ascii=False, sort_keys=True)

    def format_config_file(self, file_path: Path, indent: int = 2) -> None:
        """格式化配置文件

        Args:
            file_path: 配置文件路径
            indent: 缩进空格数
        """
        # 读取配置
        with open(file_path, encoding='utf-8') as f:
            config = json.load(f)

        # 格式化并写回
        formatted = self.format_config(config, indent)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted)

    def merge_configs(
        self,
        base_config: Dict,
        override_config: Dict,
        result: ValidationResult,
        visited: set = None
    ) -> Dict:
        """合并配置，支持嵌套结构

        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            result: 验证结果对象，用于记录错误
            visited: 已访问的配置对象 ID 集合，用于检测循环引用

        Returns:
            合并后的配置
        """
        if visited is None:
            visited = set()

        # 检测循环继承
        base_id = id(base_config)
        override_id = id(override_config)

        if base_id in visited or override_id in visited:
            result.add_error(ValidationError(
                field_path="",
                error_type="CIRCULAR_INHERITANCE",
                expected="无循环引用",
                actual="检测到循环继承",
                message="配置合并中检测到循环继承",
                error_code=self.ERROR_CODES["CIRCULAR_INHERITANCE"]
            ))
            return base_config.copy()

        # 添加当前对象到已访问集合
        visited.add(base_id)
        visited.add(override_id)

        # 创建合并结果的副本
        merged = base_config.copy()

        for key, override_value in override_config.items():
            if key in merged:
                base_value = merged[key]

                # 如果都是字典，递归合并
                if isinstance(base_value, dict) and isinstance(override_value, dict):
                    merged[key] = self.merge_configs(
                        base_value,
                        override_value,
                        result,
                        visited.copy()
                    )
                else:
                    # 非字典类型，直接覆盖
                    merged[key] = override_value
            else:
                # 新增字段
                merged[key] = override_value

        return merged


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
