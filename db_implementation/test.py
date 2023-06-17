import orjson
import time

if __name__ == '__main__':
    start = time.time()
    # f = open('mpqa.json', 'r', encoding='utf-8')
    # content = f.read()
    # js = orjson.loads(content)
    # f.close()
    # del content

    f = open('mpqa_csds.json', 'r', encoding='utf-8')
    content = orjson.loads(f.read())
    first = content[:len(content) // 2]
    second = content[(len(content) // 2) + 1:]
    f.close()

    f_first = open('mpqa_csds_1.json', 'wb')
    f_first.write(orjson.dumps(first))
    f_first.close()

    f_second = open('mpqa_csds_2.json', 'wb')
    f_second.write(orjson.dumps(second))
    f_second.close()

    print(round(time.time() - start, 2))

