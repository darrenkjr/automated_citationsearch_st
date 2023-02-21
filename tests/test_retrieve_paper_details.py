import sys 
sys.path.append('../automated_evidence_retrieval_study')
from libraries.simulation_study_functions import study_functions 
import pandas as pd 
import asyncio
from libraries.automated_handsearch import automated_handsearch
import os 
from dotenv import load_dotenv

sf = study_functions()
load_dotenv()
key =  os.getenv('semantic_scholar_api_key')

df_scoping_review_seeds = pd.read_csv('PCOS_test_automated_handsearch_seed_4.csv')
handsearch_cls = automated_handsearch(key,df_scoping_review_seeds['seed_Id'].tolist())
df_paper_details = asyncio.run(sf.retrieve_paper_details(df_scoping_review_seeds['seed_Id'].tolist()))
#check if paper details of abstract are missing and if so, retrieve them from OpenAlex

async def main(df_paper_details_doi):
    print('Attempting fix with OpenAlex')
    df_missing_paper_details_doi['abstract'] = await asyncio.gather(*[handsearch_cls.retrieve_openalex_abs(i) for i in df_paper_details_doi['DOI']])
    return df_missing_paper_details_doi


if df_paper_details['paper_Abstract'].isnull().values.any() == True: 

    df_missing_paper_details_doi = asyncio.run(handsearch_cls.obtain_doi_missing_abs(df_paper_details))
    print(df_paper_details)
    df_missing_paper_details_doi = asyncio.run(main(df_missing_paper_details_doi))
    fixed_article_df = df_missing_paper_details_doi
    retrieved_abs = fixed_article_df
    retrieved_abs_index_list = retrieved_abs.index.tolist() 
    retrieved_abs_abstract_list = retrieved_abs['abstract'].tolist()
    df_paper_details.loc[retrieved_abs_index_list,"paper_Abstract"] = retrieved_abs_abstract_list

df_paper_details.to_csv('PCOS_test_automated_handsearch_seed_4_testing_results.csv')
