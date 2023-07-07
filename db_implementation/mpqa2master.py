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
        self.exec_sql()

        self.con.commit()
        self.con.close()

    def exec_sql(self):
        self.con.executemany('INSERT INTO SENTENCES (sentence_id, file, file_sentence_id, sentence)'
                             'VALUES (?, ?, ?, ?);', self.master_sentences)

    # process a single expressive subjective annotation and its relevant source(s)
    def proc_expr_subj(self, annotation):
        pass

    def load_data(self):
        # i = annotation_types = set()
        # for annotation in self.csds:
        #     annotation_types.add(annotation["annotation_type"])
        # self.pp.pprint(annotation_types)
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

            # with sentences populated, the code's behavior diverges depending on the annotation type
            bar.next()
            continue

            if annotation['annotation_type'] == 'expressive_subjectivity':
                self.proc_expr_subj(annotation)
            else:
                continue

        bar.finish()
        print(len(test_sentences))


if __name__ == "__main__":
    print("mpqa2master.py version 1.0\n\n")
    START_TIME = time()
    test = MPQA2MASTER()
    test.generate_database()
    print('\n\nDone.')
    RUN_TIME = time() - START_TIME
    print("Runtime:", round(RUN_TIME, 3), 'sec')
