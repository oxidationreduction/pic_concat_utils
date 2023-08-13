import threading
import warnings
import os
from datetime import date
from typing import Union

from PIL import Image


def print_warning(message: str):
    warnings.formatwarning = lambda message, category, filename, lineno, line="": \
        '\033[91m' + category.__name__ + ': ' + str(message) + '\033[0m'
    warnings.warn(message, UserWarning)


def standardize_album_name(album_name: str) -> str:
    return (album_name.replace(":", "-").replace("：", "-").
            replace(" ", "").replace("　", ""))


def standardize_model_name(album_name: str) -> str:
    return album_name.replace(" ", "_").replace("　", "_").lower()


def mkdir_if_not_exist(path: Union[str, tuple[str], list[str]], cleanup_exist: bool = False):
    if isinstance(path, str):
        path = (path,)
    for p in path:
        if not os.path.exists(p):
            os.mkdir(p)
        elif cleanup_exist:
            for file in os.listdir(p):
                if file != ".DS_Store" and file != "Thumbs.db" and not os.path.isdir(os.path.join(p, file)):
                    try:
                        os.remove(os.path.join(p, file))
                    except PermissionError:
                        raise PermissionError(f"Permission denied: {os.path.join(p, file)}")


def generate_file_name(model: str, album: str, index: Union[int, str]) -> str:
    return f"{model}_{album}_{format_count_idx(index)}.png"


def is_image(file_name: str) -> bool:
    return file_name.endswith((".jpg", ".jpeg", ".png"))


def save_pic(pic: Union[str, Image.Image], model: str, album: str,
             index: Union[int, str], threshold: list[int], result_dirs: list[str], lock: threading.Lock = None):
    if isinstance(pic, str) and is_image(pic):
        img = Image.open(pic)
    elif isinstance(pic, Image.Image):
        img = pic
    else:
        raise TypeError(f"Unsupported type or file format for pic {pic}: {type(pic)}")

    def _save_fig():
        if img.height >= threshold[0]:
            img.save(os.path.join(result_dirs[0], generate_file_name(model, album, index)))
        elif img.height >= threshold[1]:
            img.save(os.path.join(result_dirs[1], generate_file_name(model, album, index)))
        else:
            img.save(os.path.join(result_dirs[2], generate_file_name(model, album, index)))

    if lock is not None:
        lock.acquire()
        _save_fig()
        lock.release()
    else:
        _save_fig()


'''
将数字转换为5位字符串，不足5位的在前面补0
@:param count: 数字
'''


def format_count_idx(count):
    return ("0" * (5 - len(str(count)))) + str(count)


def days_since(year: int, month: int, day: int) -> int:
    start_date = date(year, month, day)
    today = date.today()
    delta = today - start_date
    return delta.days
