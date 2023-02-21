import asyncio
import sys 
sys.path.append('../automated_citationsearch_st')
import pandas as pd
from libraries.openalex import openalex_interface 
import os 

def openalex_forwardsnowball_test():
    file_path = os.path.join(os.path.dirname(__file__),'test_data/scoping_review_seed_article_data.csv')
    article_df = pd.read_csv(file_path)
    openalex_cls = openalex_interface()
    result_df = asyncio.run(openalex_cls.retrieve_citations(article_df))
    result_ris = openalex_cls.to_ris(result_df)
    return result_df 

def openalex_write_ris_test(result_df): 
    openalex_cls = openalex_interface()
    result_ris = openalex_cls.to_ris(result_df)
    return result_ris


result_df = openalex_forwardsnowball_test() 
print('Number of results:', len(result_df.index)) 
print('Number of unique results:', len(result_df['paper_Id'].unique()))
ris_export_path = 'oa_result_direct.ris'
result_ris = openalex_write_ris_test(result_df, ris_export_path)
result_df.to_csv('openalex_forwardsnowball_test.csv',index=False)





