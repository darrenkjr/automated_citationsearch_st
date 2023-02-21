import asyncio
import sys 
sys.path.append('../automated_evidence_retrieval_study')
import pandas as pd
from libraries.semanticscholar import semanticscholar_interface 
import os 
from dotenv import load_dotenv


def semanticscholar_backwardsnowball_test():
    load_dotenv() 
    semanticscholar_api_key =  os.getenv('semantic_scholar_api_key')
    file_path = os.path.join(os.path.dirname(__file__),'test_data/scoping_review_seed_article_data.csv')
    article_df = pd.read_csv(file_path)
    semanticscholar_cls = semanticscholar_interface(semanticscholar_api_key,)
    result_df = asyncio.run(semanticscholar_cls.retrieve_references(article_df))
    return result_df 

result_df = semanticscholar_backwardsnowball_test() 
print('Number of results:', len(result_df.index)) 
print('Number of unique results:', len(result_df['paper_Id'].unique()))

#sort dataframe with titles first, and drop duplicates after
result_df = result_df.sort_values(by=['paper_Title'], ascending=False) 
result_df_unique_ss = result_df.drop_duplicates(subset=['paper_Id'])
result_df_unique_ss.to_csv('ss_backward_snowball_test_unique.csv', encoding = 'utf-8')
result_df.to_csv('ss_backward_snowball_test.csv')
