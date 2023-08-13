import argparse
from add import add
from search import search
from pic_cat import pic_cat
from unite_files import unite_files
from utils import days_since


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', help='Function: Add a model or a album', action='store_true')
    parser.add_argument('--search', help='Function: Search by album name', action='store_true')
    parser.add_argument('--concat', help='Function: Concat files', action='store_true')
    parser.add_argument('--model', help='Model name', default='')
    parser.add_argument('--album', help='Album name, will stored in the name file', default='')
    parser.add_argument('--all', help='include all dirs', default=False, action='store_true')
    parser.add_argument('--dirs', help='dirs to concat', nargs='+', default=[])
    parser.add_argument('--reset', help='override processed dirs, re-process all pics', default=False, action='store_true')
    parser.add_argument('--base_dir', help='base directory of all pictures', default='pic_concat')
    parser.add_argument('--unite', help='copy all processed results to one dir', default=False, action='store_true')
    parser.add_argument('--threshold', help='height threshold of high and mid qualities (in pixel)',
                        default=[1600, 1080], type=float)
    parser.add_argument('--from_date', help='a zero or negative integer indicates the number of days before today, '
                                            'e.g. 0 means only apply to files added today, '
                                            '-1 means only apply to files added after yesterday (included)',
                        default=days_since(1970, 1, 1), type=int)
    args = parser.parse_args()

    if args.add:
        add(args)
    elif args.search:
        search(args)
    elif args.concat:
        pic_cat(args)
    else:
        raise RuntimeError(f"Undefined function, only allow 'add', 'search' and 'concat'")

    if args.unite:
        unite_files(args)


if __name__ == '__main__':
    main()
