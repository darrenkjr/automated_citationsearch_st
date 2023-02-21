import sys 
sys.path.append('../automated_evidence_retrieval_study')
import pandas as pd 
from libraries.simulation_study_functions import run_handsearch

from numpy import NaN

from urllib.error import HTTPError

#conducting automated handsearch from seed article 
def snowball_iteration_test(): 
    iter_num = 2
    seed_article_df = pd.read_csv('PCOS_seed_2iterations.csv')
    original_sys_review_id = ["326d25762fa7c0dd247de6b5e951a3f8b5309870"]
    result = run_handsearch(seed_article_df,iter_num,original_sys_review_id)
    return result 

result = snowball_iteration_test()
