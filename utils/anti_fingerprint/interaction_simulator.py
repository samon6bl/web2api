"""
交互模式模拟模块
模拟真实的浏览交互模式，如随机停留、随机滚动、随机点击等
"""
import asyncio
import logging
import random
from typing import Optional

from playwright.async_api import Page as AsyncPage

logger = logging.getLogger(__name__)


class InteractionSimulator:
    """交互模式模拟器"""

    def __init__(
        self,
        browsing_duration_min: float = 1.0,
        browsing_duration_max: float = 3.0,
        random_click_probability: float = 0.3,
        page_transition_delay_min: float = 0.5,
        page_transition_delay_max: float = 2.0,
    ):
        """
        初始化交互模拟器

        Args:
            browsing_duration_min: 浏览最小持续时间（秒）
            browsing_duration_max: 浏览最大持续时间（秒）
            random_click_probability: 随机点击概率 (0-1)
            page_transition_delay_min: 页面跳转最小延迟（秒）
            page_transition_delay_max: 页面跳转最大延迟（秒）
        """
        self.browsing_duration_min = browsing_duration_min
        self.browsing_duration_max = browsing_duration_max
        self.random_click_probability = random_click_probability
        self.page_transition_delay_min = page_transition_delay_min
        self.page_transition_delay_max = page_transition_delay_max

    async def simulate_browsing(self, page: AsyncPage) -> None:
        """
        模拟页面浏览行为

        Args:
            page: 页面对象
        """
        try:
            # 随机浏览持续时间
            duration = random.uniform(
                self.browsing_duration_min, self.browsing_duration_max
            )

            # 随机滚动
            scroll_count = random.randint(1, 3)
            for _ in range(scroll_count):
                scroll_amount = random.randint(100, 500)
                await page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.3, 0.8))

            # 随机停留
            await asyncio.sleep(duration)

            # 随机点击（避开关键功能元素）
            if random.random() < self.random_click_probability:
                await self._random_safe_click(page)

        except Exception as e:
            logger.debug(f"浏览行为模拟失败（可忽略）: {e}")

    async def _random_safe_click(self, page: AsyncPage) -> None:
        """
        随机点击页面安全区域（避开关键功能）

        Args:
            page: 页面对象
        """
        try:
            # 查找一些安全的点击目标（如文本、图片等，避开按钮和输入框）
            safe_selectors = [
                "p",
                "span",
                "div[role='text']",
                "img",
            ]

            for selector in safe_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        # 随机选择一个元素
                        element = random.choice(elements)
                        # 检查是否可见且不在关键区域
                        box = await element.bounding_box()
                        if box and box.get("width", 0) > 10 and box.get("height", 0) > 10:
                            # 轻微随机偏移，不精确点击
                            x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
                            await page.mouse.click(x, y)
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            return
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"随机点击模拟失败（可忽略）: {e}")

    async def simulate_page_transition(self, page: AsyncPage) -> None:
        """
        模拟页面跳转前的行为

        Args:
            page: 页面对象
        """
        try:
            # 随机延迟，模拟用户思考时间
            delay = random.uniform(
                self.page_transition_delay_min, self.page_transition_delay_max
            )
            await asyncio.sleep(delay)

            # 可能的小幅滚动
            if random.random() < 0.5:
                await page.mouse.wheel(0, random.randint(-200, 200))
                await asyncio.sleep(random.uniform(0.2, 0.5))

        except Exception as e:
            logger.debug(f"页面跳转模拟失败（可忽略）: {e}")

