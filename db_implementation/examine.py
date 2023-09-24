import orjson
import pprint
import pandas as pd
import random

def dir_subj_no_attitudes():
    f = open('dir_subj_no_attitudes.txt', 'r', encoding='utf-8')
    data = orjson.loads(f.read())
    f.close()

    pp = pprint.PrettyPrinter(stream=open('dir_subj_heads_when_no_attitudes.txt', 'w'))

    for i, annotation in enumerate(data):
        pp.pprint(i)
        pp.pprint(annotation['text'])
        pp.pprint(f'HEAD: {annotation["head"]}')
        pp.pprint('-------------')

def attitudes_no_targets():
    f = open('dir_subj_no_targets.txt', 'r', encoding='utf-8')
    data = orjson.loads(f.read())
    f.close()

    sample_space = range(len(data))
    owen = random.sample(sample_space, 25)
    tyler = random.sample(sample_space, 25)
    amittai = random.sample(sample_space, 25)

    print(owen)
    print(tyler)
    print(amittai)

    df = pd.DataFrame(columns=['sentence', 'head', 'annotation_type', 'intensity',
                               'polarity', 'Owen', 'Amittai', 'Tyler'])

    for attitude in data:
        if len(df.index) in owen:
            df.loc[len(df.index)] = [attitude['text'], attitude['head'], attitude['annotation_type'],
                                     attitude['intensity'], attitude['polarity'], 'X', None, None]
        elif len(df.index) in amittai:
            df.loc[len(df.index)] = [attitude['text'], attitude['head'], attitude['annotation_type'],
                                     attitude['intensity'], attitude['polarity'], None, 'X', None]
        elif len(df.index) in tyler:
            df.loc[len(df.index)] = [attitude['text'], attitude['head'], attitude['annotation_type'],
                                     attitude['intensity'], attitude['polarity'], None, None, 'X']
        else:
            df.loc[len(df.index)] = [attitude['text'], attitude['head'], attitude['annotation_type'],
                                     attitude['intensity'], attitude['polarity'], None, None, None]

    df.to_csv('attitudes_without_targets.csv')

if __name__ == '__main__':
    attitudes_no_targets()

