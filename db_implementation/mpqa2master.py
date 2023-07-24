# author: tyler osborne
# tyler.osborne@stonybrook.edu

from ddl import DDL
import sqlite3
import orjson
from time import time
import pprint
import glob
import os
import re
from progress.bar import Bar


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

        self.next_global_sentence_id = 1
        self.next_global_token_id = 1
        self.next_global_source_id = 1
        self.next_global_attitude_id = 1

        self.pp = pprint.PrettyPrinter()

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

        print("\nLoading Python data into master schema...")
        self.load_data()
        self.run_tests()
        self.exec_sql()

        self.con.commit()
        self.con.close()

    def run_tests(self):
        dupe_source_annotations = []
        for annotation in self.csds:
            if annotation['nested_source_link'] is not None \
                    and len(annotation['nested_source_link']) \
                    != len(set(annotation['nested_source_link'])):

                dupe_source_annotations.append(annotation)

        # self.pp.pprint(len(dupe_source_annotations))
        return

    def exec_sql(self):
        self.con.executemany('INSERT INTO SENTENCES (sentence_id, file, file_sentence_id, sentence)'
                             'VALUES (?, ?, ?, ?);', self.master_sentences)

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
    def process_sources(self, annotation):
        # skipping useless annotations
        if annotation['nested_source_link'] is None or len(annotation['nested_source_link']) == 0:
            return -1

        # looping over sources in reverse
        agents = annotation['nested_source_link'].reverse()
        nesting_level = len(agents) - 1
        relevant_global_source_id = None

        agent_stack = []

        # first loop: traverse tree leaf -> root, until we find an encountered source or reach the root
        for agent_id in agents:
            key = (agent_id, nesting_level)
            if key in self.encountered_sources:
                relevant_global_source_id = self.encountered_sources[key]
                break
            else:
                self.encountered_sources[key] = self.next_global_source_id
                relevant_global_source_id = self.encountered_sources[key]
                # if len(agents) == 1:
                #     relevant_global_source_id = self.next_global_source_id
                #     break
                # else:
                agent_stack.append(agent_id)

                self.next_global_source_id += 1
                nesting_level -= 1

        # second loop: traverse stack of un-encountered sources, creating DB entries as necessary
        global_parent_source_id = None
        for agent_id in reversed(agent_stack):




    def proc_expr_subj(self, annotation):
        # dealing with sources: if there is only one source, it is the author and we are done
        # otherwise, traverse the nested source links, processing each one from the agents list and linking
        # the parent_source IDs. traverse the nested source links in reverse
        global_source_id = self.process_sources(annotation)

    # process a single direct subjective annotation
    def proc_dir_subj(self, annotation):
        pass

    # process a single direct objective annotation
    def proc_dir_obj(self, annotation):
        pass

    def load_data(self):
        test_sentences = set()
        # loop over all annotations, executing different functions for each respective annotation type
        bar = Bar("Annotations Processed", max=len(self.csds))
        for annotation in self.csds:
            # all annotation types will require identical processing in many areas
            file = annotation['doc_id']
            sentence = annotation['text']

            test_sentences.add(sentence)

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
                self.master_sentences.append([global_sentence_id, file, file_sentence_id, sentence])

            # past sentences, the code's behavior diverges depending on the annotation type
            bar.next()

            if annotation['annotation_type'] == 'expressive_subjectivity':
                self.proc_expr_subj(annotation)
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
