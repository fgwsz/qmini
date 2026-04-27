# -*- coding: utf-8 -*-
from qmini import Point,ImageTask,Execute,Screen

if __name__ == "__main__":
    # 示例:查找单张图片
    image_task = ImageTask.make_default("./images/test.png")
    Execute.left_click(Execute.until_find_image(image_task))
    print("点击了目标按钮")
    Execute.left_click(Point(Screen.WIDTH/2,Screen.HEIGHT/2))
