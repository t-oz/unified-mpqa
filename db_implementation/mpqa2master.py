# author: tyler osborne
# tyler.osborne@stonybrook.edu

from ddl import DDL
import sqlite3
import orjson
from time import time
import pprint
import glob
import os
from progress.bar import Bar


# direct objective, expressive & direct subjective annotations
class MPQA2MASTER:

    def __init__(self):
        self.create_tables()
        self.con = sqlite3.connect("mpqa_master.db")
        self.cur = self.con.cursor()

        self.agents = {}
        self.csds = []
        self.targets = {}

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

        self.con.close()


    def load_data(self):
        i = annotation_types = set()
        for annotation in self.csds:
            annotation_types.add(annotation["annotation_type"])
        self.pp.pprint(annotation_types)

        self.con.commit()


if __name__ == "__main__":
    print("mpqa2master.py version 1.0\n\n")
    START_TIME = time()
    test = MPQA2MASTER()
    test.generate_database()
    print('\n\nDone.')
    RUN_TIME = time() - START_TIME
    print("Runtime:", round(RUN_TIME, 3), 'sec')
