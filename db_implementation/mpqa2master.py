# author: tyler osborne
# tyler.osborne@stonybrook.edu

import pprint
import random
import sqlite3
from time import time

import orjson
from progress.bar import Bar

from ddl import DDL
from offsets_correction import OffsetsCorrection


# direct objective, expressive & direct subjective annotations
class MPQA2MASTER:

    def __init__(self):
        self.create_tables()
        self.con = sqlite3.connect("mpqa_master.db")
        self.cur = self.con.cursor()

        self.master_sentences = []
        self.master_mentions = []
        self.master_sources = []
        self.master_attitudes = []

        self.agents = {}
        self.csds = []
        self.targets = {}

        self.csds_expr_subj = []
        self.encountered_sentences = {}
        self.encountered_sources = {}
        self.assembled_tokens = {}

        self.next_global_sentence_id = 1
        self.next_global_token_id = 1
        self.next_global_source_id = 1
        self.next_global_attitude_id = 1

        self.pp = pprint.PrettyPrinter()
        self.oc = OffsetsCorrection()

        self.errors = []

    # initializing the DDL for the master schema
    @staticmethod
    def create_tables():
        db = DDL('mpqa')
        db.create_tables()
        db.close()

    # modular methods to read in JSON data
    def load_csds(self):
        f = open("json_corpus/mpqa_csds.json", "r", encoding="utf-8")
        self.csds = orjson.loads(f.read())
        f.close()

    def load_agents(self):
        f = open("json_corpus/mpqa_agent.json", "r", encoding="utf-8")
        self.agents = orjson.loads(f.read())
        f.close()

    def load_targets(self):
        f = open("json_corpus/mpqa_target.json", "r", encoding="utf-8")
        self.targets = orjson.loads(f.read())
        f.close()

    def generate_database(self):
        print("Loading MPQA JSON data into Python data structures...")
        bar = Bar("Data Imported", max=3)
        self.load_csds()
        bar.next()
        self.load_agents()
        bar.next()
        self.load_targets()
        bar.next()
        bar.finish()

        # self.run_tests()
        # exit()

        print("\nLoading Python data into master schema...")
        self.load_data()
        self.exec_sql()

        self.dump_errors()

        self.con.commit()
        self.con.close()

    def dump_errors(self):
        f = open('error_annotations.txt', 'wb')
        f.write(orjson.dumps(self.errors))
        f.close()

    def run_tests(self):
        ghost_agent_annotations = []
        for annotation in self.csds:
            try:
                for agent_id in list(reversed(annotation['nested_source_link'])):
                    if agent_id not in self.agents:
                        ghost_agent_annotations.append(annotation)
                        break
            except:
                continue
        sample = random.sample(ghost_agent_annotations, 10)
        self.pp.pprint(len(ghost_agent_annotations))
        return

    def is_ghost_annotation(self, annotation):
        try:
            for agent_id in list(reversed(annotation['nested_source_link'])):
                if agent_id not in self.agents:
                    return True
            return False
        except:
            return True
    def exec_sql(self):
        self.con.executemany('INSERT INTO SENTENCES (sentence_id, file, file_sentence_id, sentence)'
                             'VALUES (?, ?, ?, ?);', self.master_sentences)
        self.con.executemany('INSERT INTO mentions '
                             '(token_id, sentence_id, token_text, token_offset_start, '
                             'token_offset_end, phrase_text, phrase_offset_start, phrase_offset_end) '
                             'VALUES (?, ?, ?, ?, ?, ?, ?, ?);', self.master_mentions)
        self.con.executemany('INSERT INTO sources '
                             '(source_id, sentence_id, token_id, parent_source_id, nesting_level, [source]) '
                             'VALUES (?, ?, ?, ?, ?, ?);', self.master_sources)
        self.con.executemany('INSERT INTO attitudes '
                             '(attitude_id, source_id, anchor_token_id, target_token_id, is_expression, '
                             'is_implicit, is_insubstantial, label, polarity, intensity, label_type) '
                             'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', self.master_attitudes)

    """
    inputs: annotation
    output: most relevant source entry
    
    this function takes in an annotation and processes the entire tree of sources associated with the annotation.
    a dictionary, encountered_sources, is used to ensure duplicate sources are not inserted.
    encountered_sources: unique_agent_id -> unique_source_id
    
    pseudo:
    start at the most nested source. check if it has been encountered.
        if it has, retrieve the unique_source_id from the dictionary. we are done.
        if not, move up the tree until either:
            (a) we encounter a source already present in the dictionary.
            (b) we reach the top of the tree.
    
    (a): work backwards -- go back to the previous source in the tree and
         create mention/source entries (source encountered in (a) = first parent source), 
         and create entry in encountered_sources
    (b): same as (a), except insert the source at the top of the tree first
    
    continue working backwards, inserting mention/source entries at each level of the tree, using previous iterations of
    the loop as parent source IDs
    
    return the source ID for the source most immediate to the annotation in question
        
    """
    # BUG: nested source link's data corresponds to the FIRST mention of a source, not the one for THIS SENTENCE... that
    # data comes from the "convenient" nested_source LIST
    def process_sources(self, annotation, global_sentence_id):
        # skipping useless annotations
        # if type(annotation['nested_source_link']) is NoneType or len(annotation['nested_source_link']) == 0:
        #     return -1

        # looping over sources in reverse
        agents = list(reversed(annotation['nested_source_link']))
        try:
            nesting_level = len(agents) - 1
        except Exception:
            return -1

        relevant_global_source_id = None

        agent_stack = []

        # first loop: traverse tree leaf -> root, until we find an encountered source or reach the root
        for agent_id in agents:
            # disambiguating agent-w's to be sentence-based, not file-based
            if agent_id[-7:] == 'agent-w':
                key = (agent_id + str(global_sentence_id), nesting_level)
            else:
                key = (agent_id, nesting_level)

            if key in self.encountered_sources:
                relevant_global_source_id = self.encountered_sources[key]

                # annoying edge case
                if len(agents) == 1:
                    agent_stack.append((agent_id, nesting_level, relevant_global_source_id))
                break
            else:
                # self.encountered_sources[key] = self.next_global_source_id
                # relevant_global_source_id = self.encountered_sources[key]
                relevant_global_source_id = self.next_global_source_id
                self.next_global_source_id += 1

                agent_stack.append((agent_id, nesting_level, relevant_global_source_id))
                nesting_level -= 1

        # no parent source if we made it all the way to the top of the tree in the first loop
        if len(agents) == len(agent_stack):
            global_parent_source_id = None
        else:
            global_parent_source_id = relevant_global_source_id

        # second loop: traverse stack of un-encountered sources, creating DB entries as needed
        useful_global_source_id = None
        for agent_id, nesting_level, global_source_id in list(reversed(agent_stack)):
            # create mentions entry
            global_token_id = self.next_global_token_id
            self.next_global_token_id += 1

            # some agents... don't exist? not sure why
            if agent_id not in self.agents:
                continue
            agent_annotation = self.agents[agent_id]

            # disambiguating agent-w's to be sentence-based, not file-based
            # also customizing author-only mentions
            if agent_id[-7:] == 'agent-w':
                mentions_entry = [global_token_id, global_sentence_id, 'AUTHOR', -1, -1, None, None, None]
                key = (agent_id + str(global_sentence_id), nesting_level)
            else:
                # mentions_entry = [global_token_id, global_sentence_id, agent_annotation['head'],
                #                   agent_annotation['head_start'], agent_annotation['head_end'], None, None, None]
                # use LOCAL mention for insertion
                nested_source = list(annotation['nested_source'])[nesting_level]

                if 'w_head_span' not in tuple(nested_source):
                    continue

                w_head_start, w_head_end = tuple(nested_source['w_head_span'])

                _, offset_list = self.assembled_tokens[global_sentence_id]
                if offset_list is not None and (w_head_end == 0 or w_head_end < len(offset_list)):
                    mentions_entry = [global_token_id, global_sentence_id, nested_source['clean_head'],
                                      offset_list[w_head_start], offset_list[w_head_end], None, None, None]
                else:
                    mentions_entry = [global_token_id, global_sentence_id, nested_source['clean_head'],
                                      None, None, None, None, None]

                key = (agent_id, nesting_level)

            self.master_mentions.append(mentions_entry)

            if key in self.encountered_sources:
                global_source_id = self.encountered_sources[key]
            else:
                self.encountered_sources[key] = global_source_id
                sources_entry = [global_source_id, global_sentence_id, global_token_id,
                                 global_parent_source_id, nesting_level, agent_annotation['head']]
                self.master_sources.append(sources_entry)

            # saving out global source id for this entry for return, since the last one processed in this loop
            # is what we want
            useful_global_source_id = global_source_id

            # replacing parent source with this source to prep for next iteration
            global_parent_source_id = global_source_id

        return useful_global_source_id

    # creating mentions entry for anchor
    def catalog_anchor(self, annotation, global_sentence_id):
        anchor_token_id = self.next_global_token_id
        self.next_global_token_id += 1

        clean_text, offset_list = self.assembled_tokens[global_sentence_id]
        w_head_start, w_head_end = tuple(annotation['w_head_span'])

        if offset_list is not None and (w_head_end == 0 or w_head_end < len(offset_list)):
            self.master_mentions.append([anchor_token_id, global_sentence_id,
                                         clean_text[offset_list[w_head_start]:offset_list[w_head_end]],
                                         offset_list[w_head_start], offset_list[w_head_end],
                                         None, None, None])
        else:
            self.master_mentions.append([anchor_token_id, global_sentence_id, None, None, None, None, None, None])

        return anchor_token_id

    # intensity: 'intensity'
    # anchor: new mention using head
    # no target
    # is_expression: no
    # is_implicit: 'implicit'
    # is_insubstantial: no
    # label: no
    # label_type: 'expressive subjective'

    def proc_expr_subj(self, annotation, global_sentence_id):
        global_source_id = self.process_sources(annotation, global_sentence_id)
        global_anchor_token_id = self.catalog_anchor(annotation, global_sentence_id)

        global_attitude_id = self.next_global_attitude_id
        self.next_global_attitude_id += 1

        # inserting attitude
        self.master_attitudes.append([global_attitude_id, global_source_id, global_anchor_token_id,
                                      None, None, annotation['implicit'], None, None, annotation['polarity'],
                                      annotation['intensity'], 'Expressive Subjective'])

    # process a single direct subjective annotation
    def proc_dir_subj(self, annotation):
        pass

    # process a single direct objective annotation
    def proc_dir_obj(self, annotation):
        pass

    def load_data(self):
        # loop over all annotations, executing different functions for each respective annotation type
        bar = Bar("Annotations Processed", max=len(self.csds))
        for annotation in self.csds:

            # skipping useless annotations
            if self.is_ghost_annotation(annotation):
                self.errors.append(annotation)
                continue

            # all annotation types will require identical processing in many areas
            file = annotation['doc_id']
            sentence = annotation['text']

            # careful to add only unique sentences to the DB
            if annotation['sentence_id'] not in self.encountered_sentences:
                global_sentence_id = self.next_global_sentence_id
                self.encountered_sentences[annotation['sentence_id']] = self.next_global_sentence_id
                self.next_global_sentence_id += 1
                new_sentence_insert = True
            else:
                global_sentence_id = self.encountered_sentences[annotation['sentence_id']]
                new_sentence_insert = False

            # extracting file sentence id
            file_sentence_id = int(annotation['sentence_id'].split('&&')[1].split('-')[1])

            # if it is a new sentence, prep it for SQL insertion
            if new_sentence_insert:
                clean_text, offset_list = None, None
                try:
                    # note: use justin's clean head!
                    clean_text, offset_list = self.oc.assemble_tokens(annotation['w_text'], annotation['w_head'])
                except:
                    pass


                # memoize!
                self.assembled_tokens[global_sentence_id] = (clean_text, offset_list)

                self.master_sentences.append([global_sentence_id, file, file_sentence_id, clean_text])

            # past sentences, the code's behavior diverges depending on the annotation type
            bar.next()

            # disambiguating sources?

            if annotation['annotation_type'] == 'expressive_subjectivity':
                self.proc_expr_subj(annotation, global_sentence_id)
            elif annotation['annotation_type'] == 'direct_subjective':
                self.proc_dir_subj(annotation)
            elif annotation['annotation_type'] == 'objective_speech_event':
                self.proc_dir_obj(annotation)
            else:
                continue

        bar.finish()


if __name__ == "__main__":
    print("mpqa2master.py version 1.0\n\n")
    START_TIME = time()
    test = MPQA2MASTER()
    test.generate_database()
    print('\n\nDone.')
    RUN_TIME = time() - START_TIME
    print("Runtime:", round(RUN_TIME, 3), 'sec')
