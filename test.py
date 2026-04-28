# -*- coding: utf-8 -*-
import qmini2 as q

# 一行等待并点击
q.wait_and_click('./images/test.png')

# 在指定区域内查找(上下文管理)
with q.region(100, 100, 500, 400):
    if q.exists('icon.png'):
        q.click_image('icon.png')

# 多图任意等待
pos = q.wait_any(['ok.png', 'cancel.png'], timeout=5)
q.click(pos)

# 人机化延迟
q.sleep(800, jitter=150)

# 滚动并移动
q.scroll(-5, duration=0.3, x=500, y=500)
