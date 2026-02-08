"""
Collectors 共享工具函数
"""
import re


def parse_github_number(text: str) -> int:
    """
    解析 GitHub 上的数字格式
    支持格式: 1.2k -> 1200, 3,456 -> 3456, 1.5m -> 1500000

    :param text: 包含数字的文本
    :return: 整数
    """
    if not text:
        return 0

    text = text.replace(',', '').strip()

    try:
        lower_text = text.lower()
        if 'k' in lower_text:
            return int(float(lower_text.replace('k', '')) * 1000)
        elif 'm' in lower_text:
            return int(float(lower_text.replace('m', '')) * 1000000)
        else:
            numbers = re.findall(r'[\d.]+', text)
            if numbers:
                return int(float(numbers[0]))
            return 0
    except (ValueError, AttributeError, TypeError):
        return 0
