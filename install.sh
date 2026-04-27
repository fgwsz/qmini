pip install opencv-python pyautogui numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

#File "python3.10/site-packages/pyscreeze/__init__.py", line 628, in _screenshot_linux
#raise Exception(
#Exception: To take screenshots, you must install Pillow version 9.2.0 or greater 
#           and gnome-screenshot by running `sudo apt install gnome-screenshot`
#)
pip install --upgrade Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
sudo apt install gnome-screenshot
