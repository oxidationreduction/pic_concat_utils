import os
import shutil
import sys
import threading
import glob

from PIL import Image
from multiprocessing import Process
import time
from tqdm import tqdm
import argparse
from utils import *

'''
将两张图片拼接成一张图片
@:param img1: 第一张图片
@:param img1name: 第一张图片的文件名
@:param img2: 第二张图片
@:param img2name: 第二张图片的文件名
@:param BASE_DIR: 保存拼接后的图片的目录
@:param person_name: 人名
@:param count: 图片计数
@:param pbar: 进度条
'''


def single_thread(img1, img1name, img2, img2name, album_dir, count, pbar, threshold, result_dirs):
    model, album = album_dir.split('/')[-2:]
    # 确保两张图片的尺寸一致
    # try:
    #     assert img1.height == img2.height
    # except AssertionError:
    #     print_warning(f'Picture height error in {album_dir}: {img1name}-{img1.height} and {img2name}-{img2.height}')
    # 创建一个新的空白图片，尺寸为原图片的两倍宽度
    new_img = Image.new('RGB', (img1.width + img2.width, min(img1.height, img2.height)))

    # 将原图片粘贴到新的空白图片上
    new_img.paste(img2, (0, 0))
    new_img.paste(img1, (img2.width, 0))

    # 保存拼接后的图片，文件名以两张原图片的文件名组合
    save_pic(new_img, model, album, count, threshold, result_dirs)

    pbar.update(1)


'''
删除当前目录下所有以 prefix 开头的文件
@:param BASE_DIR: 当前目录
@:param prefix: 文件名前缀
'''


def remove_pics(model: str, album: str, result_dirs: Union[list[str], tuple[str]]):
    def _remove_pics_single_dir(result_dir: str):
        for filename in glob.glob(os.path.join(result_dir, f'{model}_{album}*')):
            try:
                # 删除文件
                os.remove(filename)
            except OSError as e:
                print(f'Error: {filename} : {e.strerror}')
    for result_dir in result_dirs:
        _remove_pics_single_dir(result_dir)


'''
将当前目录下的所有jpg图片两两拼接
@:param BASE_DIR: 当前目录
@:param reverse: 是否反向拼接
'''


def pic_concat(album_dir: str,
               result_dirs: Union[list[str], tuple[str]], threshold: Union[list[int], tuple[int]]):
    # Origin means the pictures in this directory are all landscape direction photos.
    # Just copy these pictures to 'result' is OK.
    model = os.path.dirname(album_dir).split('/')[-1]
    album = os.path.dirname(os.path.join(album_dir, '..')).split('/')[-1].split('_')[0]
    origin = 'origin' in album_dir
    if origin:
        images = [img for img in os.listdir(album_dir) if img.endswith((".jpg", ".jpeg", ".png"))]
        with tqdm(total=len(images), leave=False) as pbar:
            pbar.set_description_str(f'Copy {model}/{album}')
            index = 0
            lock = threading.Lock()
            threads = []
            for pic in images:
                td = threading.Thread(target=save_pic,
                                      args=(os.path.join(album_dir, pic), model, album, index,
                                            threshold, result_dirs, lock))
                td.start()
                threads.append(td)
            for td in threads:
                td.join()
                pbar.update(1)
            pbar.close()
    else:
        reverse = "reverse" in album_dir
        remove_pics(model, album, result_dirs)
        images = [img for img in os.listdir(album_dir) if img.endswith((".jpg", ".jpeg", ".png"))]
        images.sort()
        assert len(images) % 2 == 0

        with tqdm(total=len(images) >> 1, leave=False) as pbar:
            pbar.set_description_str(f'Concat {model}/{album}')
            threads = []
            for i in range(0, len(images), 2):  # 每次取两张图片
                img1 = Image.open(os.path.join(album_dir, images[i]))
                img2 = Image.open(os.path.join(album_dir, images[i + 1]))
                if reverse:
                    img1, img2 = img2, img1

                td = threading.Thread(target=single_thread,
                                      args=(img1, images[i], img2, images[i + 1], album_dir, i >> 1, pbar,
                                            threshold, result_dirs))
                threads.append(td)
                td.start()
                # single_thread(img1, images[i], img2, images[i + 1], album_dir, i >> 1, pbar, threshold, result_dirs)

            for td in threads:
                td.join()
    if "processed" not in album_dir:
        os.rename(album_dir, album_dir + "_processed")


def pic_cat(args: argparse.Namespace):
    work_dirs = []
    results_dirs = []
    args.base_dir = os.path.abspath(args.base_dir)
    if args.all:
        
        for model in os.listdir(args.base_dir):
            if model in [".DS_Store", "united_results"] or not os.path.isdir(os.path.join(args.base_dir, model)):
                continue
            model_dir = os.path.join(args.base_dir, model)
            mkdir_if_not_exist(os.path.join(model_dir, 'results'), args.reset)
            result_dirs = [
                os.path.join(model_dir, 'results', 'high_quality'),
                os.path.join(model_dir, 'results', 'mid_quality'),
                os.path.join(model_dir, 'results', 'low_quality')
            ]
            mkdir_if_not_exist(result_dirs, args.reset)
            for album in os.listdir(model_dir):
                if not os.path.isdir(os.path.join(model_dir, album)):
                    continue
                if album in ["results", "logs", "checkpoints"]:
                    continue
                album_dir = os.path.join(model_dir, album)
                if os.path.isdir(album_dir) and "name" in os.listdir(album_dir):
                    if args.reset or (not args.reset and "processed" not in album_dir):
                        work_dirs.append(album_dir)
                        results_dirs.append(result_dirs)
        with tqdm(total=len(work_dirs)) as pbar:
            pbar.set_description_str(f'Total progress')
            for album_dir, result_dirs in zip(work_dirs, results_dirs):
                pic_concat(album_dir, result_dirs, args.threshold)
                pbar.update(1)
            pbar.close()
    else:
        work_dirs = args.dirs
        for album_dir in work_dirs:
            if not os.path.isdir(album_dir):
                continue
            if not args.reset and "processed" in album_dir:
                continue
            model_dir = os.path.join(album_dir, "..")
            mkdir_if_not_exist(os.path.join(model_dir, 'results'), args.reset)
            result_dirs = [
                os.path.join(model_dir, 'results', 'high_quality'),
                os.path.join(model_dir, 'results', 'mid_quality'),
                os.path.join(model_dir, 'results', 'low_quality')
            ]
            pic_concat(album_dir, result_dirs, args.threshold)
