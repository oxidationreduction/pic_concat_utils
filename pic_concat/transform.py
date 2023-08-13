import os
from pyth.plugins.plaintext.writer import PlaintextWriter
from pyth.plugins.rtf15.reader import Rtf15Reader


def convert_rtf_to_plain_text(rtf_path):
    with open(rtf_path, 'rb') as rtf_file:
        doc = Rtf15Reader.read(rtf_file)
        plain_text = PlaintextWriter.write(doc).getvalue()

        # 构建纯文本文件的路径
        plain_text_path = os.path.splitext(rtf_path)[0] + '.txt'

        # 将纯文本内容写入文件
        with open(plain_text_path, 'w') as txt_file:
            txt_file.write(plain_text)

        print(f'Converted {rtf_path} to {plain_text_path}')

        # 删除原RTF文件
        os.remove(rtf_path)


def convert_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith('.rtf'):
                rtf_path = os.path.join(root, file_name)
                convert_rtf_to_plain_text(rtf_path)


if __name__ == '__main__':
    input_folder = '.'

    convert_folder(input_folder)
