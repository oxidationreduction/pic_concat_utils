import os
import shutil
import sys
import threading
import glob
from datetime import datetime, timedelta

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
    def _remove_pics_single_dir(result_dir0: str):
        for filename in glob.glob(os.path.join(result_dir0, f'{model}_{album}*')):
            try:
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
            for pic in images:
                save_pic(Image.open(os.path.join(album_dir, pic)), model, album, index, threshold, result_dirs)
                index += 1
                pbar.update(1)
            pbar.close()
    else:
        reverse = "reverse" in album_dir
        remove_pics(model, album, result_dirs)
        images = [img for img in os.listdir(album_dir) if img.endswith((".jpg", ".jpeg", ".png"))]
        images.sort()
        try:
            assert (len(images) & 1) == 0
        except AssertionError:
            raise AssertionError(f"Odd number of pictures in {album_dir}: {len(images)}")

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
        days_ago = date.today() + timedelta(days=int(args.from_date))
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
            if args.reset:
                rm_pic_model_album(result_dirs, model)
            for album in os.listdir(model_dir):
                if not os.path.isdir(os.path.join(model_dir, album)):
                    continue
                if album in ["results", "logs", "checkpoints"]:
                    continue
                album_dir = os.path.join(model_dir, album)
                if datetime.fromtimestamp(os.path.getctime(album_dir)).date() < days_ago:
                    print_warning(f"Skip {album_dir} for {datetime.fromtimestamp(os.path.getctime(album_dir)).date()} "
                                  f"early than {days_ago}")
                    continue
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
    elif args.dirs is not None:
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
            mkdir_if_not_exist(result_dirs, args.reset)
            model, album = get_model_album_from_path(album_dir)
            rm_pic_model_album(result_dirs, model, album)
            pic_concat(album_dir, result_dirs, args.threshold)
    else:
        model, album = args.model, args.album

        def _concat_for_single_model(model0: str, album0: str = None):
            model_dir0 = os.path.join(args.base_dir, model0)
            result_dirs0 = [
                os.path.join(model_dir0, 'results', 'high_quality'),
                os.path.join(model_dir0, 'results', 'mid_quality'),
                os.path.join(model_dir0, 'results', 'low_quality')
            ]

            if album0 is not None:
                for album_dir_name in os.listdir(model_dir0):
                    if album0 in [album_dir_name, get_album_real_name(os.path.join(model_dir0, album_dir_name))]:
                        rm_pic_model_album(result_dirs0, model0, album_dir_name)
                        pic_concat(os.path.join(model_dir0, album_dir_name), result_dirs0, args.threshold)
                        break
            else:
                for album_dir_name in os.listdir(model_dir0):
                    rm_pic_model_album(result_dirs0, model0, album_dir_name)
                    pic_concat(os.path.join(model_dir0, album_dir_name), result_dirs0, args.threshold)

        if model is not None:
            _concat_for_single_model(model, album)
        else:
            if album is not None:
                for model in os.listdir(args.base_dir):
                    if not os.path.isdir(os.path.join(args.base_dir, model)) or model == "united_results":
                        continue
                    if album in os.listdir(os.path.join(args.base_dir, model)).extend(
                            [get_album_real_name(os.path.join(args.base_dir, model, album_name))
                             for album_name in os.listdir(os.path.join(args.base_dir, model))]):
                        _concat_for_single_model(model, album)
            else:
                raise RuntimeError("If you don't use --all or --dirs for --concat, then --model and --album cannot be "
                                   "None at the same time")


