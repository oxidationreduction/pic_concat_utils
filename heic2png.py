import os
import threading

from PIL import Image
import pyheif
from tqdm import tqdm


def convert_heic_to_png(heic_file, png_file, pbar):
    heif_file = pyheif.read(heic_file)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    image.save(png_file, format="PNG")
    pbar.update(1)


def rename_if_exists(filename):
    root, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filename):
        filename = f"{root}_{counter}{ext}"
        counter += 1
    return filename


def process_directory(dir_path):
    raw_files = [(root, dirs, files) for root, dirs, files in os.walk(dir_path)]
    with tqdm(total=len(raw_files)) as pbar:
        pbar.set_description_str(f'Processing {dir_path}')
    for root, dirs, files in raw_files:
        threads = []
        for file in files:
            if file.endswith(".HEIC") or file.endswith(".heic"):
                full_path = os.path.join(root, file)
                png_file = full_path.rsplit('.', 1)[0] + ".png"
                png_file = rename_if_exists(png_file)
                td = threading.Thread(target=convert_heic_to_png, args=(full_path, png_file, pbar))
                threads.append(td)
                td.start()
        for td in threads:
            td.join()


if __name__ == "__main__":
    for dir in os.listdir(".."):
        if os.path.isdir(dir):
            process_directory(dir)
