import pandas as pd 
import pickle 

with open('doc_embedding_seeds_SPECTER.pickle', 'rb') as pkl:
    SPECTER_seed_embedding = pickle.load(pkl) 
with open('doc_embedding_seeds.pickle', 'rb') as pkl:
    sPubmedBert_seed_embedding = pickle.load(pkl)   
with open('doc_embedding_snowball_results_SPECTER.pickle', 'rb') as pkl:
    SPECTER_snowball_result_embedding = pickle.load(pkl)
with open('doc_embedding_snowball_results.pickle', 'rb') as pkl:
    sPubmedBERT_snowball_result_embedding = pickle.load(pkl)
    
#SPECTER
from sentence_transformers import util
import numpy as np

column_score = []
cosine_scores = pd.DataFrame(columns = df_seeds['paper_Id'])

for count, i in enumerate(SPECTER_seed_embedding):
    cosine_score_column = []
    for j in SPECTER_snowball_result_embedding: 
        cosine_similarity = util.cos_sim(i,j)
        cosine_score_column.append(cosine_similarity.numpy())
    cosine_scores[cosine_scores.columns[count]] = cosine_score_column
        
#compute average semantic similarity for each seed article and each retrieved article
cosine_scores['average_cosine_similarity_SPECTER'] = cosine_scores.mean(axis=1)
cosine_scores.rename(index = {'paper_Id':'index'}, inplace = True)
cosine_scores['paper_Id'] = df_snowball_results['paper_Id']

cosine_scores