import asyncio
import sys 
sys.path.append('../automated_evidence_retrieval_study')
import pandas as pd
from libraries.openalex import openalex_interface 
import os 

def openalex_backwardsnowball_test():
    file_path = os.path.join(os.path.dirname(__file__),'test_data/scoping_review_seed_article_data.csv')
    id_df = pd.read_csv(file_path)
    openalex_cls = openalex_interface()
    result_df = asyncio.run(openalex_cls.retrieve_references(id_df))
    return result_df

result_df = openalex_backwardsnowball_test()
result_df = result_df.sort_values(by=['title'], ascending=False) 
print('Number of results:', len(result_df.index)) 
print('Number of unique results:', len(result_df['id'].unique()))

result_df_unique_oa = result_df.drop_duplicates(subset=['id'])
result_df_unique_oa.to_csv('openalex_backwardsnowball_test_unique.csv')
result_df.to_csv('openalex_backwardsnowball_test.csv', encoding = 'utf-8')

