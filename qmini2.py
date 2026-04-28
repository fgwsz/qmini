# -*- coding: utf-8 -*-
"""
qmini2 - 极简图像识别与鼠标操作库
提供一行完成查找|点击|等待等常用操作
"""

import time
import random
from typing import List, Optional, Tuple, Union
import pyautogui

# 复用原库的核心类(用户通常不需要直接使用)
from qmini import Point, Screen, Rect, ImageTask, Execute

# 重新导出原库中可能需要的类型(但不强制用户使用)
__all__ = [
    'Point', 'Screen', 'Rect',           # 原类型
    'find', 'exists', 'wait', 'click', 'click_image', 'wait_and_click',
    'find_any', 'wait_any', 'sleep', 'scroll', 'move_to', 'region'
]

# ---------- 私有辅助函数 ----------
def _to_rect(
    left: Union[int, Tuple[int, int, int, int], 'Rect', None],
    top: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> 'Rect':
    """
    将各种区域表示统一转换为 Rect 对象.
    支持:
      - None -> 全屏 Rect
      - 四个独立整数
      - (x, y, w, h) 元组
      - Rect 对象
    """
    if left is None:
        return Rect.get_screen_rect()
    if isinstance(left, Rect):
        return left
    if isinstance(left, (tuple, list)) and len(left) == 4:
        return Rect(left[0], left[1], left[2], left[3])
    if top is not None and width is not None and height is not None:
        return Rect(left, top, width, height)
    raise TypeError("region 必须是 (x, y, w, h) 元组|Rect 对象或四个整数参数")

def _make_task(image_path: str, confidence: float, region_rect: 'Rect') -> 'ImageTask':
    """内部构造 ImageTask,自动校验图像存在性"""
    return ImageTask(image_path, confidence, region_rect)

# ---------- 全局状态:当前区域上下文 ----------
_current_region: Optional['Rect'] = None   # 可以是 Rect 或 None(表示全屏)

class _RegionContext:
    def __init__(self, region: 'Rect') -> None:
        self.region: 'Rect' = region
        self.old_region: Optional['Rect'] = None

    def __enter__(self) -> None:
        global _current_region
        self.old_region = _current_region
        _current_region = self.region

    def __exit__(self, *args) -> None:
        global _current_region
        _current_region = self.old_region

def region(
    x: Optional[int] = None,
    y: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> '_RegionContext':
    """
    设置全局区域上下文,返回上下文管理器.
    用法:
        with q.region(100, 100, 500, 400):
            q.click('button.png')   # 在此区域内查找
    若调用 region() 不带参数,则使用全屏区域.
    """
    if x is None and y is None and width is None and height is None:
        rect = Rect.get_screen_rect()
    else:
        rect = Rect(x, y, width, height)
    return _RegionContext(rect)

# ---------- 公开 API ----------
def find(
    image_path: str,
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None
) -> Optional['Point']:
    """
    在屏幕指定区域查找图片,返回中心点坐标 Point;未找到返回 None
    :param image_path: 图片路径
    :param confidence: 相似度 (0~1),默认 0.8
    :param region: 可选,搜索区域.可以是 (x,y,w,h) 元组|Rect 对象或 None(使用全局/全屏)
    """
    rect = region if region is not None else _current_region
    if rect is None:
        rect = Rect.get_screen_rect()
    else:
        rect = _to_rect(rect)
    task = _make_task(image_path, confidence, rect)
    return Execute.find_image(task)

def exists(
    image_path: str,
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None
) -> bool:
    """判断图片是否存在"""
    return find(image_path, confidence, region) is not None

def wait(
    image_path: str,
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None,
    timeout: float = 30,
    interval: float = 0.2
) -> 'Point':
    """
    等待图片出现,返回其中心点;超时则抛出 TimeoutError
    """
    rect = region if region is not None else _current_region
    if rect is None:
        rect = Rect.get_screen_rect()
    else:
        rect = _to_rect(rect)
    task = _make_task(image_path, confidence, rect)
    return Execute.until_find_image(task, interval_s=interval, timeout_s=timeout)

def click(pos: Optional[Union['Point', Tuple[int, int]]] = None) -> None:
    """
    点击某个坐标.若不传参数,则点击当前鼠标位置.
    :param pos: Point 对象或 (x, y) 元组
    """
    if pos is None:
        x, y = pyautogui.position()
        pos = Point(x, y)
    elif isinstance(pos, tuple):
        pos = Point(pos[0], pos[1])
    Execute.left_click(pos)

def click_image(
    image_path: str,
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None,
    wait_time: float = 0,
    raise_if_missing: bool = False
) -> bool:
    """
    查找并点击图片.
    :param wait_time: 若 >0,则等待最多 wait_time 秒出现后点击;若为0,则只查找一次
    :param raise_if_missing: 找不到时是否抛出异常
    :return: 是否成功点击(找不到或超时返回 False)
    """
    try:
        if wait_time > 0:
            pos = wait(image_path, confidence, region, timeout=wait_time)
        else:
            pos = find(image_path, confidence, region)
        if pos:
            click(pos)
            return True
        if raise_if_missing:
            raise RuntimeError(f"图片未找到: {image_path}")
        return False
    except TimeoutError:
        if raise_if_missing:
            raise
        return False

def wait_and_click(
    image_path: str,
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None,
    timeout: float = 30,
    interval: float = 0.2
) -> None:
    """等待图片出现并点击,超时抛异常"""
    pos = wait(image_path, confidence, region, timeout, interval)
    click(pos)

def find_any(
    image_paths: List[str],
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None
) -> Optional['Point']:
    """
    在列表中依次查找图片,返回第一个找到的中心点;未找到返回 None
    """
    rect = region if region is not None else _current_region
    if rect is None:
        rect = Rect.get_screen_rect()
    else:
        rect = _to_rect(rect)
    tasks = [_make_task(p, confidence, rect) for p in image_paths]
    return Execute.find_images(tasks)

def wait_any(
    image_paths: List[str],
    confidence: float = 0.8,
    region: Union['Rect', Tuple[int, int, int, int], None] = None,
    timeout: float = 30,
    interval: float = 0.2
) -> 'Point':
    """
    等待多个图片中的任意一个出现,返回其中心点;超时抛异常
    """
    rect = region if region is not None else _current_region
    if rect is None:
        rect = Rect.get_screen_rect()
    else:
        rect = _to_rect(rect)
    tasks = [_make_task(p, confidence, rect) for p in image_paths]
    return Execute.until_find_images(tasks, interval_s=interval, timeout_s=timeout)

def sleep(milliseconds: float, jitter: float = 0) -> None:
    """
    延迟(毫秒),支持随机抖动
    :param milliseconds: 基础毫秒数
    :param jitter: 随机波动范围 ±jitter 毫秒
    """
    if jitter > 0:
        milliseconds += random.uniform(-jitter, jitter)
    if milliseconds > 0:
        time.sleep(milliseconds / 1000.0)

def scroll(amount: int, duration: float = 0.2, x: Optional[int] = None, y: Optional[int] = None) -> None:
    """
    滚动鼠标滚轮
    :param amount: 正数向上,负数向下
    :param duration: 滚动时长(秒)
    :param x, y: 可选,移动到该坐标再滚动
    """
    if x is not None and y is not None:
        pyautogui.moveTo(x, y)
    # Execute.mouse_wheel_smooth 的参数 distance: 正数向下,负数向上
    # 我们让 amount 正数向上,所以取反
    Execute.mouse_wheel_smooth(-amount, duration)

def move_to(x: int, y: int) -> None:
    """移动鼠标到指定坐标"""
    Execute.move_to(Point(x, y))

