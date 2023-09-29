import pyconll
import pathlib

def count_annotations():
    directory = pathlib.Path('.')
    for file in directory.glob('*.conll'):
        data = pyconll.load_from_file(file)


if __name__ == '__main__':
    count_annotations()