import orjson
import pprint

f = open('dir_subj_no_attitudes.txt', 'r', encoding='utf-8')
data = orjson.loads(f.read())
f.close()

pp = pprint.PrettyPrinter(stream=open('dir_subj_heads_when_no_attitudes.txt', 'w'))

for i, annotation in enumerate(data):
    pp.pprint(i)
    pp.pprint(annotation['text'])
    pp.pprint(annotation['head'])
    pp.pprint('-------------')
