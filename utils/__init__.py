"""
工具模块
"""
from .user_data_pool import ChromeUserDataPool, get_user_data_pool

# 导出反指纹检测模块
from .anti_fingerprint import (
    AntiFingerprintManager,
    BehaviorSimulator,
    FrequencyController,
    HeaderManager,
    InteractionSimulator,
)

__all__ = [
    "ChromeUserDataPool",
    "get_user_data_pool",
    "AntiFingerprintManager",
    "BehaviorSimulator",
    "FrequencyController",
    "HeaderManager",
    "InteractionSimulator",
]

