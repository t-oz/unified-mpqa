# author: tyler osborne
# tyler.osborne@stonybrook.edu

import orjson
import time
import pprint
import glob
import os

if __name__ == '__main__':
    print("Splitting MPQA JSON into bite-sized pieces...")
    start = time.time()
    pp = pprint.PrettyPrinter()

    # removing existing files
    for f in glob.glob("mpqa_*.json"):
        os.remove(f)

    # starting with big file
    f = open('mpqa.json', 'r', encoding='utf-8')
    content = f.read()
    js = orjson.loads(content)

    # freeing memory
    del content
    f.close()

    for name in ["csds", "target", "agent"]:
        content = js[f"{name}_objects"]

        f_full = open(f"mpqa_{name}.json", "wb")

        # only split csds objects in two; targets and agents aren't very large
        if name == "csds":

            f_first = open(f"mpqa_{name}_1.json", "wb")
            f_second = open(f"mpqa_{name}_2.json", "wb")

            first = content[:len(content) // 2]
            second = content[(len(content) // 2) + 1:]

            f_first.write(orjson.dumps(first))
            f_second.write(orjson.dumps(second))

            f_first.close()
            f_second.close()

        f_full.write(orjson.dumps(content))
        f_full.close()

    print("Done.")
    print(f"Time: {round(time.time() - start, 2)} sec")

