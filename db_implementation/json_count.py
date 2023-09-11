# tyler osborne
# tgosborne@cs.stonybrook.edu
# 10 September 2023

import orjson
import pprint

pp = pprint.PrettyPrinter()


def count_json():
    f = open("json_corpus/mpqa.json", "r", encoding="utf-8")
    mpqa = orjson.loads(f.read())
    f.close()

    csds = mpqa['csds_objects']
    targets = mpqa['target_objects']
    agents = mpqa['agent_objects']

    del mpqa

    annotation_types = \
    ['agreement',
     'arguing',
     'direct_subjective',
     'expressive_subjectivity',
     'intention',
     'objective_speech_event',
     'other_attitude',
     'sentence',
     'sentiment',
     'speculation',
     'unknown']

    type_to_list = {}

    total_annotations = 0
    total_attitudes = 0
    missing_targets = 0
    missing_attitudes = 0
    missing_agents = 0
    dir_subj_offsets = 0

    for anno_type in annotation_types:
        type_to_list[anno_type] = []

    for anno in csds:
        if 'attitude' in anno['unique_id']:

            total_attitudes += 1

            if len(list(anno['target_link'])) == 0:
                missing_targets += 1
                total_annotations += 1

            for t_link in list(anno['target_link']):
                if not t_link or t_link not in targets:
                    missing_targets += 1

                else:
                    total_annotations += 1

        elif anno['annotation_type'] == 'direct_subjective':

            if tuple(anno['w_head_span']) == (0, 0):
                dir_subj_offsets += 1

            for attitude in list(anno['attitude']):
                if not attitude:
                    missing_attitudes += 1
                    continue
                for target in list(attitude['target']):
                    if target:
                        total_annotations += 1

        type_to_list[anno['annotation_type']].append(anno)

    for anno_type in annotation_types:
        if anno_type in ['sentence', 'direct_subjective']:
            continue
        for anno in type_to_list[anno_type]:
            if 'attitude' in anno['unique_id']:
                continue
            total_annotations += 1

    print(f'Total annotations: {total_annotations}')
    print(f'Total attitudes: {total_attitudes}')
    print(f'Total agents and targets: {len(targets) + len(agents)}')
    print(f'Missing attitudes: {missing_attitudes}')
    print(f'Missing targets: {missing_targets}')
    print(dir_subj_offsets)

    for anno_type in annotation_types:
        print(f'{anno_type}: {len(type_to_list[anno_type])}')


if __name__ == '__main__':
    count_json()
