import os
from pic_utils.utils import *


for dir in os.listdir("."):
    if "." in dir:
        continue
    for sub_dir in os.listdir(dir):
        if sub_dir[0] == ".":
            continue
        if "name" not in os.listdir(os.path.join(dir, sub_dir)):
            continue
        file_path = os.path.join(dir, sub_dir, "name.rtf")
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
