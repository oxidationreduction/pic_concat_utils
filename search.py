import os
import sys
import argparse
import traceback

from utils import *


def _search_album(album_name: str, BASE_DIR: str):
    results = []
    for dir in os.listdir(BASE_DIR):
        # For macOS
        if dir in [".DS_Store", "united_results"] or not os.path.isdir(os.path.join(BASE_DIR, dir)):
            continue
        try:
            with open(os.path.join(BASE_DIR, dir, "name"), "r") as f:
                name = f.readline()
                if album_name in name:
                    results.append((os.path.join(BASE_DIR, dir, "name"), name))
        except FileNotFoundError:
            pass
    return results


def search(args: argparse.Namespace):
    if args.album is None:
        args.album = ''

    album_name = standardize_album_name(args.album)
    BASE_DIR = args.base_dir

    results = _search_album(album_name, BASE_DIR)
    if len(results) == 0:
        print_warning(f"Album not found: {album_name}")
    else:
        print(f"{len(results)} album(s) found:")
        for dir, name in results:
            print(f"{name[:-1]}:\t\t{dir}")
