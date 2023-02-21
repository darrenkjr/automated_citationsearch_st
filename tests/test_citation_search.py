import sys 
import os 
sys.path.append('../automated_evidence_retrieval_study')
from libraries.automated_handsearch import automated_handsearch
import pandas as pd 


def citation_search_test(): 
    file_path = os.path.join(os.path.dirname(__file__),'test_data/openalex_snowball_test_short.csv')
    article_df = pd.read_csv(file_path)
    handsearch_cls = automated_handsearch('semanticscholar',article_df)
    full_results = handsearch_cls.run_citation_search()
    return full_results


results = citation_search_test()
print(results)

