# -*- coding: utf-8 -*-
"""
qmini - 按键精灵风格图像识别与鼠标操作库
基于 pyautogui + OpenCV 实现
提供 'Point', 'Screen', 'Rect', 'ImageTask', 'Execute' 类
"""

import time
import random
import os
import pyautogui
import cv2
import numpy as np
from typing import List,Optional

__all__= [
    'Point',
    'Screen',
    'Rect',
    'ImageTask',
    'Execute',
]

# ========== 'Point' 类 ==========
class Point:
    def __init__(self, x: int, y: int):
        if not(x >= 0 and y >= 0):
            raise ValueError("参数输入应满足:x>=0 and y>=0")

        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"

    __repr__ = __str__

# ========== 'Screen' 类 ==========
class Screen:
    WIDTH:int = pyautogui.size().width
    HEIGHT:int = pyautogui.size().height

# ========== 'Rect' 类 ==========
class Rect:
    def __init__(self, x: int, y: int, width: int, height: int):
        x = max(0, x)
        y = max(0, y)
        width = min(width, Screen.WIDTH - x)
        height = min(height, Screen.HEIGHT - y)
        if width <= 0 or height <= 0:
            raise ValueError("选择区域在屏幕中自适应裁剪后无有效范围")

        self.x, self.y, self.width, self.height = x, y, width, height

    def __str__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}, {self.height})"

    __repr__ = __str__

# ========== 'ImageTask' 类 ==========
class ImageTask:
    """图像查找任务:包含图像|相似度|屏幕查找区域"""
    def __init__(self, image_path: str, min_factor: float, search_rect: 'Rect'):
        if not os.path.exists(image_path):
            raise ValueError(f"图像路径不存在: {image_path}")

        if not os.path.isfile(image_path):
            raise ValueError(f"图像路径指向非文件类型: {image_path}")

        self.image_path = image_path

        if min_factor <= 0 or min_factor > 1.0:
            raise ValueError("参数输入应满足: min_factor>0 and min_factor<=1")

        self.min_factor = min_factor

        self.search_rect = search_rect

        template = cv2.imread(self.image_path, cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"无法加载图像: {self.image_path}")

        h, w = template.shape[:2]
        if h > self.search_rect.height or w > self.search_rect.width:
            raise ValueError(f"图像尺寸大于屏幕搜索区域尺寸: {self.image_path}")

        self.template = template
        self.image_width = w
        self.image_height = h

    def __str__(self) -> str:
        return (f"ImageTask{{image_path:{self.image_path},"
                f"image_width:{self.image_width},"
                f"image_height:{self.image_height},"
                f"min_factor:{self.min_factor},"
                f"search_rect:{self.search_rect}}}")

    __repr__ = __str__

    @staticmethod
    def make_default(image_path: str, min_factor: float = 0.8) -> 'ImageTask':
        search_rect = Rect(0, 0, Screen.WIDTH, Screen.HEIGHT)
        return ImageTask(image_path, min_factor, search_rect)

# ========== Screen 类 ==========
class Execute:
    @staticmethod
    def move_to(pos: Optional['Point']) -> None:
        if pos is None:
            raise RuntimeError("光标无法移动到无效位置")

        pyautogui.moveTo(pos.x, pos.y)

    @staticmethod
    def left_click(pos: Optional['Point'], clicks: int = 1) -> None:
        if clicks <= 0:
            return
        if pos is None:
            raise RuntimeError("鼠标左键无法点击无效位置")

        Execute.move_to(pos)
        pyautogui.click(button='left', clicks=clicks)

    @staticmethod
    def find_image(image_task: 'ImageTask') -> Optional['Point']:
        """
        在当前屏幕指定区域内查找图像
        查找的方向为从左到右,从上到下,返回找到的第一个对象的位置
        返回 'Point' 对象:找到返回中心点坐标,未找到返回无效的'Point'对象
        """
        # 截取屏幕指定区域
        region = (image_task.search_rect.x, image_task.search_rect.y,
                  image_task.search_rect.width, image_task.search_rect.height)
        screenshot = pyautogui.screenshot(region=region)
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        result = cv2.matchTemplate(screenshot_cv, image_task.template, cv2.TM_CCOEFF_NORMED)
        # 找到所有相似度 >= 阈值的位置
        locations = np.where(result >= image_task.min_factor)
        if len(locations[0]) > 0:
            # locations 是 (y坐标数组, x坐标数组),按行主序(先y后x)排列
            y = locations[0][0]   # 第一个满足条件的 y
            x = locations[1][0]   # 对应的 x
            h, w = image_task.template.shape[:2]
            center_x = image_task.search_rect.x + x + w // 2
            center_y = image_task.search_rect.y + y + h // 2
            return Point(center_x, center_y)

        return None

    @staticmethod
    def exists_image(image_task: 'ImageTask') -> bool:
        """
        在当前屏幕指定区域内查找图像,找到返回true
        """
        return Execute.find_image(image_task) is not None

    @staticmethod
    def until_find_image(image_task: 'ImageTask', interval_s: float = 0.2, timeout_s: float = 30.0) -> 'Point':
        """
        在当前屏幕指定区域内查找图像
        循环查找直到找到有效点,interval 为每次查找间隔(秒)
        返回 'Point' 对象:找到返回中心点坐标
        """
        start = time.time()
        while True:
            pos = Execute.find_image(image_task)
            if pos is not None:
                return pos

            if time.time() - start > timeout_s:
                raise TimeoutError(f"图片任务 {image_task} 超时 {timeout_s} 秒")

            time.sleep(interval_s)

    @staticmethod
    def find_images(image_task_list: List['ImageTask']) -> Optional['Point']:
        """
        依次查找多个 'ImageTask',返回第一个找到的有效点
        :param image_task_list: 'ImageTask' 列表
        :return: 'Point' 对象(未找到返回空点)
        """
        for image_task in image_task_list:
            pos = Execute.find_image(image_task)
            if pos is not None:
                return pos

        return None

    @staticmethod
    def exists_images(image_task_list: List['ImageTask']) -> bool:
        """
        在当前屏幕指定区域内查找多个图像,只要找到其中一个就返回true
        """
        return Execute.find_images(image_task_list) is not None

    @staticmethod
    def until_find_images(image_task_list: List['ImageTask'], interval_s: float = 0.2, timeout_s: float = 30.0) -> 'Point':
        """
        循环查找多个 'ImageTask',直到找到任意一个有效点
        :param image_task_list: 'ImageTask' 列表
        :param interval_s: 每次循环间隔(秒)
        :return: 找到的第一个有效点
        """
        if len(image_task_list) == 0:
            raise ValueError("图像任务列表无任务")

        start = time.time()
        while True:
            pos = Execute.find_images(image_task_list)
            if pos is not None:
                return pos

            if time.time() - start > timeout_s:
                raise TimeoutError(f"图片任务列表 {image_task_list} 超时 {timeout_s} 秒")

            time.sleep(interval_s)

    @staticmethod
    def delay_ms(milliseconds: float) -> None:
        """毫秒级延迟"""
        if milliseconds > 0:
            time.sleep(milliseconds / 1000.0)

    @staticmethod
    def random_delay(base_ms: float, extra_max_ms: float = 500.0) -> None:
        """
        固定延迟 + 随机额外延迟
        :param base_ms: 基础延迟毫秒数
        :param extra_max_ms: 额外随机延迟最大值(毫秒)
        """
        extra_ms = random.uniform(0.001, extra_max_ms) if extra_max_ms > 0 else 0
        Execute.delay_ms(base_ms + extra_ms)

    @staticmethod
    def mouse_wheel_smooth(distance: float, duration_sec: float) -> None:
        """
        平滑滚动鼠标滚轮
        :param distance: 总滚动距离(正数向下,负数向上)
        :param duration_sec: 滚动总时长(秒)
        """
        if distance == 0:
            return

        steps = max(1, int(abs(distance) * 2))  # 每步滚动0.5个单位，更平滑
        step_dist = distance / steps
        step_delay = duration_sec / steps
        remaining = 0.0
        for _ in range(steps):
            remaining += step_dist
            delta = int(round(remaining))
            if delta != 0:
                pyautogui.scroll(delta)
                remaining -= delta
            time.sleep(step_delay)

