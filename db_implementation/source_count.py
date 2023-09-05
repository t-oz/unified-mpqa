# tyler osborne
# tgosborne@cs.stonybrook.edu
# 4 September 2023

import pathlib
import pprint

pp = pprint.PrettyPrinter()
mpqa = pathlib.Path('database.mpqa.2.0/man_anns')
count = 0

for file in mpqa.rglob("gateman*"):
    with file.open() as f:
        for line in f:
            pieces = line.split()
            for chunk in pieces:
                if chunk in ['GATE_expressive-subjectivity', 'GATE_objective-speech-event']:
                    count += 1
                    break
                elif 'target-link' in chunk:
                    count += chunk.count(',') + 1
                    break


print(count)
