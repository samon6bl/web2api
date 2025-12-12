"""
反指纹管理器
统一管理所有反指纹检测模块
"""
import logging
from typing import Optional

from playwright.async_api import Page as AsyncPage

from .behavior_simulator import BehaviorSimulator
from .frequency_controller import FrequencyController
from .header_manager import HeaderManager
from .interaction_simulator import InteractionSimulator

logger = logging.getLogger(__name__)


class AntiFingerprintManager:
    """反指纹管理器"""

    def __init__(
        self,
        enable_behavior_simulation: bool = True,
        enable_interaction_simulation: bool = True,
        enable_frequency_control: bool = True,
        enable_header_management: bool = True,
        os_family: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化反指纹管理器

        Args:
            enable_behavior_simulation: 是否启用行为模拟
            enable_interaction_simulation: 是否启用交互模拟
            enable_frequency_control: 是否启用频率控制
            enable_header_management: 是否启用头部管理
            os_family: 操作系统类型
            **kwargs: 其他配置参数
        """
        self.enable_behavior_simulation = enable_behavior_simulation
        self.enable_interaction_simulation = enable_interaction_simulation
        self.enable_frequency_control = enable_frequency_control
        self.enable_header_management = enable_header_management

        # 初始化各个模块
        self.behavior_simulator: Optional[BehaviorSimulator] = None
        self.interaction_simulator: Optional[InteractionSimulator] = None
        self.frequency_controller: Optional[FrequencyController] = None
        self.header_manager: Optional[HeaderManager] = None

        if enable_behavior_simulation:
            self.behavior_simulator = BehaviorSimulator(
                mouse_speed_min=kwargs.get("mouse_speed_min", 50.0),
                mouse_speed_max=kwargs.get("mouse_speed_max", 200.0),
                click_delay_min=kwargs.get("click_delay_min", 0.1),
                click_delay_max=kwargs.get("click_delay_max", 0.5),
                scroll_smoothness=kwargs.get("scroll_smoothness", 0.8),
            )

        if enable_interaction_simulation:
            self.interaction_simulator = InteractionSimulator(
                browsing_duration_min=kwargs.get("browsing_duration_min", 1.0),
                browsing_duration_max=kwargs.get("browsing_duration_max", 3.0),
                random_click_probability=kwargs.get("random_click_probability", 0.3),
                page_transition_delay_min=kwargs.get("page_transition_delay_min", 0.5),
                page_transition_delay_max=kwargs.get("page_transition_delay_max", 2.0),
            )

        if enable_frequency_control:
            self.frequency_controller = FrequencyController(
                max_requests_per_minute=kwargs.get("max_requests_per_minute", 30),
                min_request_interval=kwargs.get("min_request_interval", 2.0),
                adaptive_backoff_enabled=kwargs.get("adaptive_backoff_enabled", True),
                backoff_multiplier=kwargs.get("backoff_multiplier", 1.5),
                max_backoff_interval=kwargs.get("max_backoff_interval", 60.0),
            )

        if enable_header_management:
            self.header_manager = HeaderManager(os_family=os_family)

        logger.info(
            f"反指纹管理器初始化完成: "
            f"行为模拟={enable_behavior_simulation}, "
            f"交互模拟={enable_interaction_simulation}, "
            f"频率控制={enable_frequency_control}, "
            f"头部管理={enable_header_management}"
        )

    async def before_request(self) -> None:
        """
        请求前的处理（频率控制）
        """
        if self.enable_frequency_control and self.frequency_controller:
            await self.frequency_controller.wait_if_needed()

    async def after_request(self, success: bool = True, response_time: Optional[float] = None) -> None:
        """
        请求后的处理（记录请求）

        Args:
            success: 请求是否成功
            response_time: 响应时间
        """
        if self.enable_frequency_control and self.frequency_controller:
            await self.frequency_controller.record_request(success, response_time)

    async def on_error(self, error_type: Optional[str] = None) -> None:
        """
        错误处理（自适应退避）

        Args:
            error_type: 错误类型
        """
        if self.enable_frequency_control and self.frequency_controller:
            await self.frequency_controller.adaptive_backoff(error_type)

    async def on_page_loaded(self, page: AsyncPage) -> None:
        """
        页面加载后的处理（交互模拟）

        Args:
            page: 页面对象
        """
        if self.enable_interaction_simulation and self.interaction_simulator:
            await self.interaction_simulator.simulate_browsing(page)

    def get_behavior_simulator(self) -> Optional[BehaviorSimulator]:
        """获取行为模拟器"""
        return self.behavior_simulator

    def get_frequency_controller(self) -> Optional[FrequencyController]:
        """获取频率控制器"""
        return self.frequency_controller

    def get_headers(self) -> Optional[dict]:
        """获取生成的 HTTP 头"""
        if self.enable_header_management and self.header_manager:
            return self.header_manager.generate_headers()
        return None

