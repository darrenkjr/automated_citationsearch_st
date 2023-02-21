import pandas as pd 
import asyncio 
from libraries.simulation_study_functions import study_functions

class original_review:

    '''class for original review included as part of testing of automated handsearch. Instantiating the class will
    create a dataframe with IDs / DOIs of potential seed articles that have been extracted from the background section of the review,
    IDs/DOIs of the final included articles that were included in the original review, and details on search strategy
    sufficient to compute recall, precision, and f1 score
    ''' 

    def __init__(self,file_name):

        self.file_name = file_name
        self.workbook_dict = pd.read_excel(file_name,sheet_name=None)
        print(self.workbook_dict)
        self.data = self.workbook_dict['sys_rev_data']
        self.included_article = self.workbook_dict['sys_rev_included_data']
        self.seed_candidates = self.workbook_dict['sys_rev_seed_candidates']
        self.recall = len(self.included_article) / len(self.included_article)
        self.precision = len(self.included_article) / self.data['original_search_retrieved'].loc[0]
        
    def prepare_seed_candidates(self):
        sf = study_functions()
        self.seed_candidates = asyncio.run(sf.retrieve_paper_details(self.seed_candidates))
        #retrieve articles and obtain embeddings for each article
        return self.seed_candidates
        #for a given selection strategy, and number of seed articles, return seed articles to then run automated handsearch

    def generate_embeddings(self): 
        seed_embeddings = None
        return seed_embeddings

