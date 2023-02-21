import sys
sys.path.append('../automated_citationsearch_st')
import rispy
import pandas as pd 
import os 
import json
from libraries.openalex import openalex_interface

file_path = os.path.join(os.path.dirname(__file__),'test_data/openalex_forwardsnowball_test.csv')
result_df_openalex = pd.read_csv(file_path)

print(result_df_openalex['paper_Id'])

openalex_interface_cls = openalex_interface()
ris_path = 'oa_results_fromcsv.ris'
openalex_interface_cls.to_ris(result_df_openalex,ris_path)
