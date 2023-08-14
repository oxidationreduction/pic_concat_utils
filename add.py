import os
import sys
import argparse

from utils import *
from search import _search_album


def add(args: argparse.Namespace):
    model = standardize_model_name(args.model)
    album = standardize_album_name(args.album)
    BASE_DIR = args.base_dir

    if model not in os.listdir(BASE_DIR):
        model_dir = os.path.join(BASE_DIR, model)
        os.mkdir(model_dir)
        mkdir_if_not_exist(os.path.join(model_dir, 'results'))
        result_dirs = [
            os.path.join(model_dir, 'results', 'high_quality'),
            os.path.join(model_dir, 'results', 'mid_quality'),
            os.path.join(model_dir, 'results', 'low_quality')
        ]
        mkdir_if_not_exist(result_dirs)
        print("Model created:", model)
    else:
        print_warning(f"Model already exist, override: {model}")
    if album == '':
        return
    BASE_DIR = os.path.join(BASE_DIR, model)
    results = _search_album(album, BASE_DIR)
    if len(results) == 0:
        BASE_DIR = os.path.join(BASE_DIR,
                                str(len(os.listdir(BASE_DIR))
                                    + (0 if ".ds_store" in [file.lower() for file in os.listdir(BASE_DIR)] else 1)))
        os.mkdir(BASE_DIR)
        with open(os.path.join(BASE_DIR, "name"), "w") as f:
            f.write(album)
        print("Album created:", album)
    else:
        print_warning(f"Album already exists, override: {results}")


