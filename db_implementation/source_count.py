# tyler osborne
# tgosborne@cs.stonybrook.edu
# 4 September 2023

import pathlib
import pprint

pp = pprint.PrettyPrinter()


"""
annotation_types = 
{'GATE_agent',
 'GATE_attitude',               
 'GATE_direct-subjective',      
 'GATE_expressive-subjectivity',
 'GATE_inside',                 
 'GATE_intention-pos',          
 'GATE_objective-speech-event', 
 'GATE_on',
 'GATE_split',
 'GATE_target',
 'GATE_target-speech'}
"""

source_verification = {}

def verify_sources(f, f_name):
    sources = []
    for line in f:
        pieces = line.split()
        if 'GATE_agent' not in line:
            continue

        for chunk in pieces:
            if 'id=' in chunk and chunk != 'id=""':
                # pp.pprint(chunk)
                source_id = chunk[4:-1]
                sources.append(source_id)
    source_verification[f_name] = sources

def check_this_source(f_name, pieces):
    true_sources = source_verification[f_name]
    for chunk in pieces:
        if 'nested-source' in chunk:
            test_sources = chunk[chunk.index('"'):-1].split(',')
            print(true_sources, test_sources)

def count_orig():
    mpqa = pathlib.Path('database.mpqa.2.0/man_anns')

    annotation_types = \
    ['GATE_agent',
     'GATE_attitude',
     'GATE_direct-subjective',
     'GATE_expressive-subjectivity',
     'GATE_intention-pos',
     'GATE_objective-speech-event',
     'GATE_on',
     'GATE_target']

    type_to_list = {}

    for anno_type in annotation_types:
        type_to_list[anno_type] = []

    no_target_link = 0
    target_link_none = 0
    target_link_empty = 0

    no_attitude_link = 0
    attitude_link_none = 0
    attitude_link_empty = 0

    ghost_references = 0

    for file in mpqa.rglob("gateman*"):
        with file.open() as f:
            verify_sources(f, str(file))
            for line in f:
                pieces = line.split()

                if 'nested-source' in line:
                    print(line)
                    check_this_source(str(file), pieces)

                for chunk in pieces:
                    if "GATE_" in chunk and chunk in annotation_types:
                        type_to_list[chunk].append(line)
                        break

    total_annotations = 0
    total_agents_targets = 0

    for anno_type in annotation_types:

        if anno_type in ['GATE_target', 'GATE_agent']:
            total_agents_targets += len(type_to_list[anno_type])

        elif anno_type == 'GATE_attitude':
            attitudes = type_to_list[anno_type]

            for attitude in attitudes:
                pieces = attitude.split()
                target_link_found = False

                for chunk in pieces:
                    if 'target-link' in chunk:
                        target_link_found = True

                        if chunk == 'target-link=""':
                            target_link_empty += 1
                        elif chunk == 'target-link="none"':
                            target_link_none += 1
                        else:
                            total_annotations += chunk.count(",") + 1

                        break

                if not target_link_found:
                    no_target_link += 1
        elif anno_type == 'GATE_direct-subjective':
            dir_subjs = type_to_list[anno_type]

            for dir_subj in dir_subjs:
                pieces = dir_subj.split()

                attitude_link_found = False
                skip = False

                for chunk in pieces:
                    if '0,0' in chunk:
                        skip = True
                        break

                    if 'attitude-link' in chunk:
                        attitude_link_found = True

                        if chunk == 'attitude-link=""':
                            attitude_link_empty += 1
                        elif chunk == 'target-link="none"':
                            attitude_link_none += 1
                if not attitude_link_found and not skip:
                    # pp.pprint(pieces)
                    no_attitude_link += 1

        else:
            total_annotations += len(type_to_list[anno_type])

        print(f'{anno_type}: {len(type_to_list[anno_type])}')

    print(f'Total annotations: {total_annotations}')
    print(f'Total agents and targets: {total_agents_targets}')
    print(f'Total attitudes with \'target-link\' literally not appearing in the text: {no_target_link}')
    print(f'Total attitudes with \'target-link=""\': {target_link_empty}')
    print(f'Total attitudes with \'target-link="none"\': {target_link_none})')
    print(f'Total of previous 3 lines dealing with target-link irregularities: '
          f'{no_target_link + target_link_empty + target_link_none}')
    print(f'Total annotations and irregular target-link cases: '
          f'{no_target_link + target_link_empty + target_link_none + total_annotations}')

    print(f'Total dir-subjs with \'attitude-link\' literally not appearing in the text: {no_attitude_link}')
    print(f'Total dir-subjs with \'attitude-link=""\': {attitude_link_empty}')
    print(f'Total dir-subjs with \'target-link="none"\': {attitude_link_none})')
    print(f'Total of previous 3 lines dealing with attitude-link irregularities: '
          f'{no_attitude_link + attitude_link_empty + attitude_link_none}')


if __name__ == '__main__':
    count_orig()


# if 'target-link=""' in line or ("GATE_attitude" in line and "target-link" not in line):
#     count_empties += 1
# pieces = line.split()
# for chunk in pieces:
#     if chunk in ['GATE_expressive-subjectivity', 'GATE_objective-speech-event']:
#         count += 1
#         break
#     elif 'target-link' in chunk:
#         count += chunk.count(',') + 1
#         break