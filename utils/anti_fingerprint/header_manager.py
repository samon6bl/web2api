"""
HTTP/TLS 头管理模块
使用 browserforge 生成真实的 HTTP 头，对齐 TLS 指纹参数
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 尝试导入 browserforge
try:
    from browserforge import FingerprintGenerator, HeadersGenerator
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    logger.warning("browserforge 未安装，HTTP 头管理功能将不可用")


class HeaderManager:
    """HTTP/TLS 头管理器"""

    def __init__(self, os_family: Optional[str] = None):
        """
        初始化头管理器

        Args:
            os_family: 操作系统类型 ('windows', 'macos', 'linux')，如果为 None 则随机选择
        """
        self.os_family = os_family
        self.fingerprint_generator: Optional[FingerprintGenerator] = None
        self.headers_generator: Optional[HeadersGenerator] = None
        self.current_headers: Optional[Dict[str, str]] = None

        if BROWSERFORGE_AVAILABLE:
            try:
                self.fingerprint_generator = FingerprintGenerator()
                self.headers_generator = HeadersGenerator()
                logger.info("HTTP 头管理器初始化成功")
            except Exception as e:
                logger.warning(f"HTTP 头管理器初始化失败: {e}")
        else:
            logger.warning("browserforge 未安装，HTTP 头管理功能不可用")

    def generate_headers(self, url: Optional[str] = None) -> Dict[str, str]:
        """
        生成真实的 HTTP 头

        Args:
            url: 目标 URL（可选，用于生成特定域名的头部）

        Returns:
            HTTP 头字典
        """
        if not BROWSERFORGE_AVAILABLE or not self.headers_generator:
            # 返回基础头部
            return self._get_default_headers()

        try:
            # 生成指纹
            fingerprint = self.fingerprint_generator.generate()

            # 根据操作系统过滤（如果指定）
            if self.os_family:
                # browserforge 的指纹可能包含 os 信息，这里简化处理
                pass

            # 生成头部
            headers = self.headers_generator.generate(fingerprint)

            # 转换为标准字典格式
            headers_dict = dict(headers)

            # 保存当前头部
            self.current_headers = headers_dict

            logger.debug(f"生成 HTTP 头: {list(headers_dict.keys())}")
            return headers_dict

        except Exception as e:
            logger.warning(f"生成 HTTP 头失败，使用默认头部: {e}")
            return self._get_default_headers()

    def _get_default_headers(self) -> Dict[str, str]:
        """
        获取默认 HTTP 头

        Returns:
            默认 HTTP 头字典
        """
        # 根据操作系统生成基础头部
        if self.os_family == "windows":
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        elif self.os_family == "macos":
            user_agent = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        elif self.os_family == "linux":
            user_agent = (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            # 默认使用 Windows
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    def get_current_headers(self) -> Optional[Dict[str, str]]:
        """
        获取当前使用的 HTTP 头

        Returns:
            当前 HTTP 头字典，如果未生成则返回 None
        """
        return self.current_headers

