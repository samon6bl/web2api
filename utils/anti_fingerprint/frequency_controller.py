"""
智能频率控制模块
基于时间窗口的请求频率控制，自适应延迟调整，智能退避策略
"""
import asyncio
import logging
import time
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class FrequencyController:
    """智能频率控制器"""

    def __init__(
        self,
        max_requests_per_minute: int = 30,
        min_request_interval: float = 2.0,
        adaptive_backoff_enabled: bool = True,
        backoff_multiplier: float = 1.5,
        max_backoff_interval: float = 60.0,
    ):
        """
        初始化频率控制器

        Args:
            max_requests_per_minute: 每分钟最大请求数
            min_request_interval: 最小请求间隔（秒）
            adaptive_backoff_enabled: 是否启用自适应退避
            backoff_multiplier: 退避倍数
            max_backoff_interval: 最大退避间隔（秒）
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.min_request_interval = min_request_interval
        self.adaptive_backoff_enabled = adaptive_backoff_enabled
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff_interval = max_backoff_interval

        # 请求时间记录（使用滑动窗口）
        self.request_times: deque = deque()
        self.last_request_time: float = 0.0

        # 自适应退避状态
        self.current_backoff_interval: float = min_request_interval
        self.consecutive_errors: int = 0
        self.last_error_time: float = 0.0

        # 锁，确保线程安全
        self._lock = asyncio.Lock()

    async def should_throttle(self) -> bool:
        """
        判断是否需要限流

        Returns:
            如果需要限流返回 True，否则返回 False
        """
        async with self._lock:
            current_time = time.time()

            # 清理超过1分钟的请求记录
            cutoff_time = current_time - 60.0
            while self.request_times and self.request_times[0] < cutoff_time:
                self.request_times.popleft()

            # 检查是否超过每分钟最大请求数
            if len(self.request_times) >= self.max_requests_per_minute:
                return True

            # 检查是否满足最小请求间隔
            if (
                self.last_request_time > 0
                and current_time - self.last_request_time < self.min_request_interval
            ):
                return True

            return False

    async def calculate_delay(self) -> float:
        """
        计算需要延迟的时间

        Returns:
            延迟时间（秒）
        """
        async with self._lock:
            current_time = time.time()

            # 基础延迟：最小请求间隔
            base_delay = self.min_request_interval

            # 如果距离上次请求时间不足，计算需要等待的时间
            if self.last_request_time > 0:
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.min_request_interval:
                    base_delay = self.min_request_interval - time_since_last

            # 自适应退避延迟
            if self.adaptive_backoff_enabled:
                backoff_delay = self.current_backoff_interval
                total_delay = max(base_delay, backoff_delay)
            else:
                total_delay = base_delay

            # 添加小量随机延迟，避免时间模式化
            random_delay = asyncio.get_event_loop().time() % 0.5
            total_delay += random_delay

            return total_delay

    async def record_request(self, success: bool = True, response_time: Optional[float] = None) -> None:
        """
        记录请求完成

        Args:
            success: 请求是否成功
            response_time: 响应时间（秒），如果提供则用于自适应调整
        """
        async with self._lock:
            current_time = time.time()
            self.request_times.append(current_time)
            self.last_request_time = current_time

            if success:
                # 请求成功，重置错误计数和退避间隔
                if self.consecutive_errors > 0:
                    self.consecutive_errors = 0
                    self.current_backoff_interval = self.min_request_interval
            else:
                # 请求失败，增加退避间隔
                self.consecutive_errors += 1
                if self.adaptive_backoff_enabled:
                    self.current_backoff_interval = min(
                        self.current_backoff_interval * self.backoff_multiplier,
                        self.max_backoff_interval,
                    )
                    logger.warning(
                        f"请求失败，增加退避间隔至 {self.current_backoff_interval:.2f} 秒"
                    )

            # 如果响应时间过长，轻微增加延迟
            if response_time and response_time > 5.0:
                self.current_backoff_interval = min(
                    self.current_backoff_interval * 1.1, self.max_backoff_interval
                )

    async def adaptive_backoff(self, error_type: Optional[str] = None) -> None:
        """
        自适应退避策略

        Args:
            error_type: 错误类型（如 'rate_limit', 'quota', 'timeout'）
        """
        async with self._lock:
            self.consecutive_errors += 1

            # 根据错误类型调整退避策略
            if error_type == "rate_limit":
                # 限流错误，快速增加退避
                self.current_backoff_interval = min(
                    self.current_backoff_interval * 2.0, self.max_backoff_interval
                )
            elif error_type == "quota":
                # 配额错误，大幅增加退避
                self.current_backoff_interval = min(
                    self.current_backoff_interval * 3.0, self.max_backoff_interval
                )
            else:
                # 其他错误，正常退避
                self.current_backoff_interval = min(
                    self.current_backoff_interval * self.backoff_multiplier,
                    self.max_backoff_interval,
                )

            logger.info(
                f"自适应退避：错误类型={error_type}, "
                f"连续错误={self.consecutive_errors}, "
                f"退避间隔={self.current_backoff_interval:.2f}秒"
            )

    async def wait_if_needed(self) -> None:
        """
        如果需要，等待直到可以发送请求
        """
        while await self.should_throttle():
            delay = await self.calculate_delay()
            if delay > 0:
                logger.debug(f"频率控制：等待 {delay:.2f} 秒")
                await asyncio.sleep(delay)

    def reset(self) -> None:
        """重置频率控制器状态"""
        self.request_times.clear()
        self.last_request_time = 0.0
        self.current_backoff_interval = self.min_request_interval
        self.consecutive_errors = 0
        self.last_error_time = 0.0

