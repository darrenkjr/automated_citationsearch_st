import pandas as pd 
import asyncio
import sys 
sys.path.append('../automated_evidence_retrieval_study')
from libraries.simulation_study_functions import retrieve_paper_details
from sentence_transformers import SentenceTransformers

class original_review:

    '''class for original review included as part of testing of automated handsearch. Instantiating the class will
    create a dataframe with IDs / DOIs of potential seed articles that have been extracted from the background section of the review
    IDs/DOIs of the final included articles that were included in the final version of the original review, and details on search strategy
    sufficient to compute recall, precision, and f1 score
    ''' 

    def __init__(self,file_name):

        self.file_name = file_name
        self.workbook_dict = pd.read_excel(file_name,sheet_name=None)
        self.data = self.workbook_dict['sys_rev_data']
        self.included_article = self.workbook_dict['sys_rev_included_data']
        self.seed_candidates = self.workbook_dict['sys_rev_seed_candidates']
        self.recall = len(self.included_article) / len(self.included_article)
        self.precision = len(self.included_article) / self.data['original_search_retrieved'].loc[0]
        
    async def prepare_seed_candidates(self,number_of_seed_articles,selection_strategy):
        self.seed_candidates = asyncio.run(retrieve_paper_details(self.seed_candidates))
        #retrieve articles and obtain embeddings for each article
        return self.seed_candidates
        #for a given selection strategy, and number of seed articles, return seed articles to then run automated handsearch

    def generate_embeddings(self): 
        seed_embeddings = None
        return seed_embeddings

    def prepare_seed_articles(self,selection_strategy):
        return None
        #for a given selection strategy, and number of seed articles, return seed articles to then run automated handsearch 
        
path = "review_data\sysreview_1.xlsx" 

review_cls = original_review(path)
print(review_cls.data)