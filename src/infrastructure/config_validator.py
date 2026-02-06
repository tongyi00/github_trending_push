"""
配置验证模块 - 纯YAML配置，使用loguru日志
"""

import sys
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any
from loguru import logger


class ConfigValidator:
    """配置验证器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化验证器"""
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
                return self.config
        except yaml.YAMLError as e:
            self.errors.append(f"Config file format error: {e}")
            return {}
        except Exception as e:
            self.errors.append(f"Failed to read config file: {e}")
            return {}

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        验证所有配置

        Returns:
            (是否通过, 错误列表, 警告列表)
        """
        self.errors.clear()
        self.warnings.clear()

        # 加载配置文件
        self.load_config()
        if self.errors:
            return False, self.errors, self.warnings

        # 验证各部分配置
        self._validate_github()
        self._validate_ai_models()
        self._validate_email()
        self._validate_scheduler()
        self._validate_logging()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_github(self):
        """验证GitHub配置"""
        github = self.config.get('github', {})
        token = github.get('token', '')

        if not token:
            self.warnings.append("GitHub token not configured - API rate limit will be 60 requests/hour (5000/hour with token)")
        elif token.startswith('ghp_xxx') or token.startswith('YOUR_'):
            self.errors.append("GitHub token not properly configured (still using example value)")

    def _validate_ai_models(self):
        """验证AI模型配置"""
        ai_config = self.config.get('ai_models', {})
        enabled = ai_config.get('enabled', [])

        if not enabled:
            self.errors.append("No AI models enabled in configuration")
            return

        configured_models = []
        for model_name in enabled:
            model_config = ai_config.get(model_name, {})
            api_key = model_config.get('api_key', '')

            if api_key and not api_key.startswith('YOUR_') and not api_key.startswith('sk-xxx') and not api_key.startswith('nvapi-xxx'):
                configured_models.append(model_name)

        if not configured_models:
            self.errors.append("No AI model API keys configured")
            self.errors.append(f"Please configure at least one of: {', '.join(enabled)}")
        else:
            self.warnings.append(f"Configured AI models: {', '.join(configured_models)}")

    def _validate_email(self):
        """验证邮件配置"""
        email = self.config.get('email', {})

        sender = email.get('sender', '')
        password = email.get('password', '')
        recipients = email.get('recipients', [])

        if not sender or sender.startswith('your_'):
            self.errors.append("Email sender not configured")

        if not password or password.startswith('your_'):
            self.errors.append("Email password (SMTP authorization code) not configured")
            self.warnings.append("Note: Use SMTP authorization code, not login password")

        if not recipients or not any(r and 'example.com' not in r for r in recipients):
            self.errors.append("Email recipients not configured or still using example values")

    def _validate_scheduler(self):
        """验证调度器配置"""
        scheduler = self.config.get('scheduler', {})

        if not scheduler:
            self.warnings.append("Scheduler configuration not found, using defaults")
            return

        timezone = scheduler.get('timezone', '')
        if not timezone:
            self.warnings.append("Timezone not configured, defaulting to Asia/Shanghai")

        # 验证时间格式
        for period in ['daily', 'weekly', 'monthly']:
            period_config = scheduler.get(period, {})
            time_str = period_config.get('time', '')
            if time_str and ':' in time_str:
                try:
                    hour, minute = time_str.split(':')
                    int(hour), int(minute)
                except ValueError:
                    self.errors.append(f"Invalid time format for {period}: {time_str}")

    def _validate_logging(self):
        """验证日志配置"""
        logging_config = self.config.get('logging', {})

        if not logging_config:
            self.warnings.append("Logging configuration not found, using defaults")

    def print_results(self):
        """打印验证结果"""
        try:
            from colorama import Fore, Style, init
            init(autoreset=True)
        except ImportError:
            # 如果没有colorama，使用空字符串
            class Fore:
                CYAN = RED = YELLOW = GREEN = ''
            class Style:
                RESET_ALL = ''

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}Configuration Validation Results")
        print(f"{Fore.CYAN}{'='*60}\n")

        if self.errors:
            print(f"{Fore.RED}[ERROR] Found {len(self.errors)} error(s):{Style.RESET_ALL}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print(f"{Fore.YELLOW}[WARNING] Found {len(self.warnings)} warning(s):{Style.RESET_ALL}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        if not self.errors and not self.warnings:
            print(f"{Fore.GREEN}[SUCCESS] All configuration validation passed!{Style.RESET_ALL}\n")
        elif not self.errors:
            print(f"{Fore.GREEN}[SUCCESS] Configuration validation passed (with warnings){Style.RESET_ALL}\n")
        else:
            print(f"{Fore.RED}[FAILED] Configuration validation failed, please fix the errors above{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}{'='*60}\n{Style.RESET_ALL}")

    def get_config(self) -> Dict[str, Any]:
        """获取已加载的配置"""
        if not self.config:
            self.load_config()
        return self.config


def validate_config(config_path: str = "config/config.yaml") -> bool:
    """
    快捷验证函数

    Returns:
        是否通过验证
    """
    validator = ConfigValidator(config_path)
    success, errors, warnings = validator.validate_all()
    validator.print_results()
    return success


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    加载并验证配置

    Returns:
        配置字典，如果验证失败则退出程序
    """
    validator = ConfigValidator(config_path)
    success, errors, warnings = validator.validate_all()

    if not success:
        validator.print_results()
        logger.error("Configuration validation failed, exiting")
        sys.exit(1)

    if warnings:
        for warning in warnings:
            logger.warning(warning)

    return validator.get_config()


if __name__ == "__main__":
    import colorama
    colorama.init(autoreset=True)

    success = validate_config()
    sys.exit(0 if success else 1)
