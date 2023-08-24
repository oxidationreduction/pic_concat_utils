import os
import shutil

from utils import *
import argparse


def unite_files(args: argparse.Namespace):
    root_dir_for_base = os.path.dirname(os.path.join(args.base_dir, ".."))
    mkdir_if_not_exist(os.path.join(root_dir_for_base, "united_results"))
    results = [
        os.path.join(root_dir_for_base, "united_results", "high_quality"),
        os.path.join(root_dir_for_base, "united_results", "mid_quality"),
        os.path.join(root_dir_for_base, "united_results", "low_quality")
    ]
    mkdir_if_not_exist(results, cleanup_exist=False)
    print("Uniting files...", end="")
    for model in os.listdir(args.base_dir):
        if model in [".DS_Store", "united_results"] or not os.path.isdir(os.path.join(args.base_dir, model)):
            continue
        if "results" not in os.listdir(os.path.join(args.base_dir, model)):
            print_warning(f"You need to process this model first: {model}")
            continue
        for pic in os.listdir(os.path.join(args.base_dir, model, "results", "high_quality")):
            if not is_image(pic):
                continue
            safe_copy(os.path.join(args.base_dir, model, "results", "high_quality", pic),
                      os.path.join(results[0], pic))
        for pic in os.listdir(os.path.join(args.base_dir, model, "results", "mid_quality")):
            if not is_image(pic):
                continue
            safe_copy(os.path.join(args.base_dir, model, "results", "mid_quality", pic),
                      os.path.join(results[1], pic))
        for pic in os.listdir(os.path.join(args.base_dir, model, "results", "low_quality")):
            if not is_image(pic):
                continue
            safe_copy(os.path.join(args.base_dir, model, "results", "low_quality", pic),
                      os.path.join(results[2], pic))
    print("Done")
