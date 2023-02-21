import sys
sys.path.append('../automated_evidence_retrieval_study')
import pandas as pd 
import os 
from libraries.semanticscholar import semanticscholar_interface
from dotenv import load_dotenv

load_dotenv()
ss_api_key = os.getenv('semantic_scholar_api_key')
file_path = os.path.join(os.path.dirname(__file__),'test_data/ss_backward_snowball_test.csv')
result_df_ss = pd.read_csv(file_path)

ss_instance = semanticscholar_interface(ss_api_key,result_df_ss)
ss_instance.to_ris(result_df_ss)