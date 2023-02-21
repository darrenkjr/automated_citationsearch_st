import pandas as pd 
import sys 
sys.path.append('../automated_evidence_retrieval_study')
from libraries.simulation_study_functions import study_functions
from numpy import NaN
import asyncio
import sys
import mlflow 



experiment_name = 'automated_handsearch_test'

current_experiment = mlflow.get_experiment_by_name(experiment_name)

with mlflow.start_run(experiment_id = current_experiment.experiment_id) as run: 
    run_id = run.info.run_id
    seed_path = 'PCOS_test_automated_handsearch_seed_8.csv'
    included_article_path = 'PCOS_sex_func_included.csv'
    seed_article_df = pd.read_csv(seed_path, dtype = object)
    df_included = pd.read_csv(included_article_path, dtype = object)
    
    mlflow.log_artifact(seed_path, 'seed articles')
    mlflow.log_artifact(included_article_path, 'included articles')
    
    
    iter_num = 1
    seed_num = len(seed_article_df)  
    original_sys_review_id = ["326d25762fa7c0dd247de6b5e951a3f8b5309870"]
    seed_id = seed_article_df['seed_Id']
    mlflow.log_param("iteration_num", iter_num)
    mlflow.log_param("seed_article_num", seed_num)
    mlflow.log_param("source_review_semantic_scholar_id", original_sys_review_id)
    
    sf = study_functions()
    result = asyncio.run(sf.run_handsearch(seed_article_df,iter_num,original_sys_review_id))
    result_filename = 'results/result_raw_{}.csv'.format(run_id)
    result.to_csv(result_filename)
    mlflow.log_artifact(result_filename,'raw_result')
    

    df_semantic_scholar_id = asyncio.run(sf.retrieve_included_id(df_included))
    recall,precision, f1_score = sf.eval_metrics(df_semantic_scholar_id,result)

    mlflow.log_metric(key = "recall_raw",value= recall)
    mlflow.log_metric(key = "precision_raw", value = precision)
    mlflow.log_metric(key = "f1_score_raw", value = f1_score)
    
    df_automated_results_year_restriction = result[result['paper_Year']<=2018]
    restricted_result_filename = 'results/result_year_restriction_{}.csv'.format(run_id)
    df_automated_results_year_restriction.to_csv(restricted_result_filename)
    mlflow.log_artifact(restricted_result_filename,"results_restricted_by_year")
    recall_year_restriction, precision_year_restriction, f1_score_year_restriction = sf.eval_metrics(df_semantic_scholar_id,df_automated_results_year_restriction)
    mlflow.log_metric("recall_year_restriction", recall_year_restriction)
    mlflow.log_metric("precision_year_restriction", precision_year_restriction)
    mlflow.log_metric("f1_score_year_restriction", f1_score_year_restriction)



