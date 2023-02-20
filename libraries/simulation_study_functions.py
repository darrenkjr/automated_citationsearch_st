import pandas as pd
from libraries.automated_handsearch import automated_handsearch
from numpy import NaN
import re
import asyncio
import aiohttp
import os 
from dotenv import load_dotenv
import platform
import rispy 

class simulation_study_functions: 
    
    '''class containing convenience functions for various parts of the evaluation study'''

    def __init__(self):
        load_dotenv()
        print('Loading environment variables')
        print(self.semantic_scholar_key)
        if platform.system()=='Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def run_handsearch(self,seed_article_df,iter_num, api_choice, original_sys_review): 

        '''Runs full automated handsearch (both backwards and forwards snowballing) on a dataframe of seed articles, and returns a dataframe of the results. 
        Takes in number of iterations to run, and the id of the original systematic review. 
        The original systematic review will be removed to prevent it from being included in iterations and results.
        '''
        try: 
            handsearch_instance = automated_handsearch(api_choice,article_df=seed_article_df)
        except Exception as e:
            print(e) 
        
        #number of iterations to the run the handsearch for 
        for i in range(iter_num): 
            result = await handsearch_instance.run_citation_search()
            #check for seed semantic scholar id and remove entry fronm results
            print('Length of result dataframe Before removing original sys review:', len(result))
            result = result[~result['paper_Id'].isin(original_sys_review)]
            print('Length of result dataframe After removing original sys review:',len(result))

            if iter_num >1:
                seed_article_df = result 
                handsearch_instance = automated_handsearch(api_choice,seed_article_df)
                print('Now retrieving for next iteration')

        
        #result checker - checking for missing abstracts, and imperfect data. 
        if result['paper_Abstract'].isnull().values.any() == True: 
            fixed_article_df = await self.fix_missing_abstract(result,handsearch_instance)
            retrieved_abs = fixed_article_df
            retrieved_abs_index_list = retrieved_abs.index.tolist()
            retrieved_abs_abstract_list = retrieved_abs['abstract'].tolist()
            result.loc[retrieved_abs_index_list,"paper_Abstract"] = retrieved_abs_abstract_list

        print('Handsearching done over', iter_num, ' iteration(s). We found a total of: ', len(result), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')
        print('Results: ', result)

        #export to both RIS file and CSV
        result.to_csv().encode('utf-8')
        return result

    async def fix_missing_abstract(self,dataframe,handsearch_cls): 
        '''Retrieves the DOI of articles that are missing abstracts, and returns a dataframe with the abstracts., through querying OpenAlex'''

        print('missing abstracts found from Semantic Scholar API. Retrieving DOIs')
        #get the DOIs of articles that are missing abstracts from the Semantic Scholar API 
        missing_abs_semantic_scholar_ID= await handsearch_cls.obtain_doi_missing_abs(dataframe)
        #retrieve abstracts from OpenAlex 
        print('Contacting OpenAlex to retrieve abstracts for a total of ', len(missing_abs_semantic_scholar_ID), 'articles')
        tasks = []
        #chunk the list of DOIs into smaller lists of 50 DOI batches 
        for i in missing_abs_semantic_scholar_ID['DOI']:
            tasks.append(handsearch_cls.retrieve_openalex_abs(i)) 
        missing_abs_semantic_scholar_ID['abstract'] = await asyncio.gather(*tasks)
        # retrieved_abstract = await handsearch_cls.retrieve_openalex_abs(missing_abs_semantic_scholar_ID['DOI'])
        print(missing_abs_semantic_scholar_ID)

        fixed_article_df = missing_abs_semantic_scholar_ID
        return fixed_article_df
        
    def get_included_id_task(self,session,df_included):
        paper_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/'
        tasks = [] 
        for count,i in enumerate(df_included['included_doi']): 
            if i is NaN:
                print('DOI is NaN, retrieving from PMID instead')
                print(str(df_included['included_pmid'].loc[count]))
                paper_reference_path_1 = re.sub('{.*?}','PMID:'+str(df_included['included_pmid'].loc[count]),paper_endpoint)
            else:  
                paper_reference_path_1 = re.sub('{.*?}',str(i),paper_endpoint)
            tasks.append(session.get(paper_reference_path_1, headers = {'x-api-key': self.semantic_scholar_key}))
        return tasks 
                

    async def retrieve_included_id(self,df_included):
        '''
        Retrieve included article IDs from Semantic Scholar API
        '''
        async with aiohttp.ClientSession() as diff_session:
            tasks = self.get_included_id_task(diff_session,df_included)
            responses = await asyncio.gather(*tasks)
            df_semantic_scholar_id = pd.DataFrame()
            error_log = []
            for response in responses: 
                json_response = await response.json()
                flat_json_ref = pd.json_normalize(json_response)
                print(flat_json_ref)
                flat_json_ref.columns = ['paper_Id','paper_Title']
                #create result dataframe 
                df_semantic_scholar_id = pd.concat([df_semantic_scholar_id,flat_json_ref],ignore_index=True)

        df_semantic_scholar_id.to_csv('included_article.csv')
        return df_semantic_scholar_id 

    def get_paper_details_tasks(self,session, paper_id): 
        '''
        takes in paper_id as a list of strings and returns a tasks list of aiohttp requests
        '''
        paper_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        tasks = [] 
        for count,i in enumerate(paper_id):
            paper_endpoint_1 = paper_endpoint.format(paper_id=i)
            tasks.append(session.get(paper_endpoint_1, headers = {'x-api-key': self.semantic_scholar_key})) 
        return tasks 

    async def retrieve_paper_details(self,paper_id):
        '''
        retrieve paper details from semantic scholar api given paper id 
        '''
        async with aiohttp.ClientSession() as session: 
            tasks = self.get_paper_details_tasks(session,paper_id)
            print(tasks)
            responses = await asyncio.gather(*tasks)
            df_paper_details = pd.DataFrame()
            for response in responses: 
                json_response = await response.json()
                flat_json_ref = pd.json_normalize(json_response)
                print(flat_json_ref)
                flat_json_ref.columns = ['paper_Id','paper_Title','paper_Abstract','paper_venue','paper_year','paper_citation_count','paper_fieldofstudy','paper_author']
                #create result dataframe 
                df_paper_details = pd.concat([df_paper_details,flat_json_ref],ignore_index=True)
        return df_paper_details
                    

    def f_beta_score (self,recall, precision, beta):
        return (1+beta**2)*(recall*precision)/((beta**2)*recall+precision)


    def eval_metrics(self,original,retrieved):
        f1_score = 0 
        if len(set(retrieved['paper_Id']).intersection(set(original['paper_Id']))) == 0: 
            recall = 0 
            precision = 0 
            f1_score = 0
        else: 
            recall = len(set(retrieved['paper_Id']).intersection(set(original['paper_Id'])))/len(original['paper_Id'])
            precision = len(set(retrieved['paper_Id']).intersection(set(original['paper_Id'])))/len(retrieved['paper_Id'])
            f1_score = 2*(recall*precision)/(recall+precision)
            # print(set(retrieved['paper_Id']).intersection(set(original['paper_Id'])))
            
        return recall,precision,f1_score



    



            

            