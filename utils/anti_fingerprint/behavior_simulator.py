"""
行为轨迹模拟模块
生成人类级鼠标/滚动/点击轨迹，模拟真实用户行为
"""
import asyncio
import logging
import random
import math
from typing import Optional, Tuple

from playwright.async_api import Locator, Page as AsyncPage

logger = logging.getLogger(__name__)


class BehaviorSimulator:
    """行为轨迹模拟器"""

    def __init__(
        self,
        mouse_speed_min: float = 50.0,
        mouse_speed_max: float = 200.0,
        click_delay_min: float = 0.1,
        click_delay_max: float = 0.5,
        scroll_smoothness: float = 0.8,
    ):
        """
        初始化行为模拟器

        Args:
            mouse_speed_min: 鼠标移动最小速度 (像素/秒)
            mouse_speed_max: 鼠标移动最大速度 (像素/秒)
            click_delay_min: 点击前最小延迟 (秒)
            click_delay_max: 点击前最大延迟 (秒)
            scroll_smoothness: 滚动平滑度 (0-1)
        """
        self.mouse_speed_min = mouse_speed_min
        self.mouse_speed_max = mouse_speed_max
        self.click_delay_min = click_delay_min
        self.click_delay_max = click_delay_max
        self.scroll_smoothness = scroll_smoothness

    def _generate_bezier_curve(
        self, start: Tuple[float, float], end: Tuple[float, float], num_points: int = 20
    ) -> list[Tuple[float, float]]:
        """
        生成贝塞尔曲线轨迹点

        Args:
            start: 起始点 (x, y)
            end: 结束点 (x, y)
            num_points: 轨迹点数量

        Returns:
            轨迹点列表
        """
        # 生成控制点，增加随机性
        control1_x = start[0] + (end[0] - start[0]) * random.uniform(0.2, 0.4)
        control1_y = start[1] + (end[1] - start[1]) * random.uniform(0.2, 0.4)
        control2_x = start[0] + (end[0] - start[0]) * random.uniform(0.6, 0.8)
        control2_y = start[1] + (end[1] - start[1]) * random.uniform(0.6, 0.8)

        points = []
        for i in range(num_points + 1):
            t = i / num_points
            # 三次贝塞尔曲线
            x = (
                (1 - t) ** 3 * start[0]
                + 3 * (1 - t) ** 2 * t * control1_x
                + 3 * (1 - t) * t ** 2 * control2_x
                + t ** 3 * end[0]
            )
            y = (
                (1 - t) ** 3 * start[1]
                + 3 * (1 - t) ** 2 * t * control1_y
                + 3 * (1 - t) * t ** 2 * control2_y
                + t ** 3 * end[1]
            )
            points.append((x, y))

        return points

    async def human_click(
        self, locator: Locator, timeout: Optional[float] = None, force: bool = False
    ) -> None:
        """
        模拟人类点击行为

        Args:
            locator: 要点击的元素定位器
            timeout: 超时时间（毫秒）
            force: 是否强制点击
        """
        try:
            # 等待元素可见
            await locator.wait_for(state="visible", timeout=timeout or 5000)

            # 获取元素位置
            box = await locator.bounding_box()
            if not box:
                # 如果无法获取位置，使用标准点击
                await locator.click(timeout=timeout, force=force)
                return

            # 计算目标位置（添加小范围随机偏移，模拟点击不精确）
            target_x = box["x"] + box["width"] / 2 + random.uniform(-2, 2)
            target_y = box["y"] + box["height"] / 2 + random.uniform(-2, 2)

            # 获取当前鼠标位置（假设在页面中心）
            page = locator.page
            viewport = page.viewport_size
            if viewport:
                current_x = viewport["width"] / 2
                current_y = viewport["height"] / 2
            else:
                current_x, current_y = 0, 0

            # 生成鼠标移动轨迹
            trajectory = self._generate_bezier_curve(
                (current_x, current_y), (target_x, target_y)
            )

            # 计算移动时间（基于距离和速度）
            distance = math.sqrt(
                (target_x - current_x) ** 2 + (target_y - current_y) ** 2
            )
            speed = random.uniform(self.mouse_speed_min, self.mouse_speed_max)
            move_duration = distance / speed

            # 执行鼠标移动
            for i, (x, y) in enumerate(trajectory):
                await page.mouse.move(x, y)
                if i < len(trajectory) - 1:
                    await asyncio.sleep(move_duration / len(trajectory))

            # 点击前随机延迟
            click_delay = random.uniform(self.click_delay_min, self.click_delay_max)
            await asyncio.sleep(click_delay)

            # 执行点击
            await locator.click(timeout=timeout, force=force)

        except Exception as e:
            logger.warning(f"人类点击模拟失败，回退到标准点击: {e}")
            await locator.click(timeout=timeout, force=force)

    async def human_hover(
        self, locator: Locator, timeout: Optional[float] = None
    ) -> None:
        """
        模拟人类悬停行为

        Args:
            locator: 要悬停的元素定位器
            timeout: 超时时间（毫秒）
        """
        try:
            await locator.wait_for(state="visible", timeout=timeout or 5000)

            box = await locator.bounding_box()
            if not box:
                await locator.hover(timeout=timeout)
                return

            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2

            page = locator.page
            viewport = page.viewport_size
            if viewport:
                current_x = viewport["width"] / 2
                current_y = viewport["height"] / 2
            else:
                current_x, current_y = 0, 0

            trajectory = self._generate_bezier_curve(
                (current_x, current_y), (target_x, target_y)
            )

            distance = math.sqrt(
                (target_x - current_x) ** 2 + (target_y - current_y) ** 2
            )
            speed = random.uniform(self.mouse_speed_min, self.mouse_speed_max)
            move_duration = distance / speed

            for i, (x, y) in enumerate(trajectory):
                await page.mouse.move(x, y)
                if i < len(trajectory) - 1:
                    await asyncio.sleep(move_duration / len(trajectory))

            await locator.hover(timeout=timeout)

        except Exception as e:
            logger.warning(f"人类悬停模拟失败，回退到标准悬停: {e}")
            await locator.hover(timeout=timeout)

    async def human_scroll(
        self,
        page: AsyncPage,
        delta_x: int = 0,
        delta_y: int = 0,
        steps: Optional[int] = None,
    ) -> None:
        """
        模拟人类滚动行为

        Args:
            page: 页面对象
            delta_x: 水平滚动距离
            delta_y: 垂直滚动距离
            steps: 滚动步数（如果为 None，则根据距离自动计算）
        """
        try:
            if steps is None:
                # 根据滚动距离计算步数
                total_distance = abs(delta_x) + abs(delta_y)
                steps = max(5, int(total_distance / 50))

            # 平滑滚动
            step_x = delta_x / steps
            step_y = delta_y / steps

            for i in range(steps):
                await page.mouse.wheel(step_x, step_y)
                # 随机延迟，模拟人类滚动的不规律性
                delay = random.uniform(0.01, 0.03) * (1 - self.scroll_smoothness)
                await asyncio.sleep(delay)

        except Exception as e:
            logger.warning(f"人类滚动模拟失败，回退到标准滚动: {e}")
            await page.mouse.wheel(delta_x, delta_y)

