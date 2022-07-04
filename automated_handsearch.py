from urllib.error import HTTPError
from json.decoder import JSONDecodeError
import pandas as pd
import requests
import re
from ratelimit import limits

class automated_handsearch: 

    def __init__(self,seed_article_df, api_key): 
        self.seed_num = len(seed_article_df)
        self.api_key = api_key
        self.seed_article_df = seed_article_df
        self.seed_article_id = seed_article_df.seed_Id
        self.error_log = []

    @limits(calls=100,period=1)
    def backwards_forwards_citation(self):

        paper_citation_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/citations?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        paper_reference_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/references?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        seed_article_data = pd.DataFrame()

        for i in self.seed_article_id:
            
            try:
                #defning api paths
                paper_reference_path_1 = re.sub('(?<=paper/).*?(?=/references)',str(i),paper_reference_endpoint)
                paper_citation_path_1 = re.sub('(?<=paper/).*?(?=/citations)',str(i),paper_citation_endpoint)
                
                #conducting backwards and forwards snowballing, and retrieving paper ids
                api_response_paper_ref = requests.get(paper_reference_path_1, headers = {'x-api-key':self.api_key})
                api_response_paper_cite = requests.get(paper_citation_path_1, headers = {'x-api-key':self.api_key})
                #convert json response for cited papers into pandas dataframe
                flat_json_ref = pd.json_normalize(api_response_paper_ref.json(),record_path=['data'])
                #normalizing column names - removes distinction between cited papers and citing papers
                flat_json_ref.columns = ['paper_Id','paper_Title', 'paper_Abstract', 'paper_Venue', 'paper_Year', 'paper_citation_count','paper_field', 'paper_author']
                #convert json respone for citing papers into pandas dataframe
                flat_json_citedby = pd.json_normalize(api_response_paper_cite.json(),record_path=['data'])
                #normalizing column names 
                flat_json_citedby.columns = flat_json_ref.columns
                #create result dataframe 
                seed_article_data = pd.concat([seed_article_data,flat_json_ref,flat_json_citedby],ignore_index=True)
            
            except HTTPError as err: 
                self.error_log.append([i,api_response_paper_cite,api_response_paper_ref])
                raise

        #drop results with no id
        seed_article_data.dropna(subset =['paper_Id'], inplace=True)
        results_no_na = seed_article_data
        print('Raw results:', len(seed_article_data))
        #deduplicate
        results_no_dupe= seed_article_data.drop_duplicates(subset=['paper_Id'])
        print('Results after deduplication:', len(results_no_dupe))
        #check for missing abstracts 
        
        #check whether we have any missing abstracts, and fix if possible via contacitng OpenAlex
        if results_no_dupe['paper_Abstract'].isnull().values.any() == True: 
            print('missing abstracts found from Semantic Scholar API. Attempting to fix via contacting OpenAlex.')
            retrieved_abs = self.obtain_doi_missing_abs(results_no_dupe)
            retrieved_abs_index_list = retrieved_abs.index.tolist()
            retrieved_abs_abstract_list = retrieved_abs['abstract'].tolist()
            results_no_dupe.loc[retrieved_abs_index_list,"paper_Abstract"] = retrieved_abs_abstract_list
            
        return  results_no_dupe 
    

    
    @limits(calls=100,period=1)
    def obtain_doi_missing_abs(self, df_missing_abs): 
        #obtain DOIs for entries that are missing abstracts
        missing_abs_index= df_missing_abs[df_missing_abs['paper_Abstract'].isnull()].index.tolist()
        missing_abs_semantic_scholar_ID = df_missing_abs.loc[missing_abs_index]['paper_Id']
        article_externalID_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/?fields=externalIds'
        
        print('Contacting semantic scholar to retrieve external DOIs') 
        external_id = pd.DataFrame()
        for i in missing_abs_semantic_scholar_ID:
            try: 
                semantic_scholar_api_path = re.sub('(?<=paper/).*?(?=/)',str(i),article_externalID_endpoint)
                semantic_scholar_req = requests.get(semantic_scholar_api_path, headers = {'x-api-key':self.api_key})
                flat_json_ref = pd.json_normalize(semantic_scholar_req.json())
                external_id = pd.concat([external_id,flat_json_ref])
            except HTTPError as err: 
                raise
        print(external_id['externalIds.DOI'])
        missing_abs_semantic_scholar_ID = missing_abs_semantic_scholar_ID.to_frame()
        missing_abs_semantic_scholar_ID = missing_abs_semantic_scholar_ID.assign(DOI=external_id['externalIds.DOI'].values)
        print(missing_abs_semantic_scholar_ID.columns)
        print('DOIs retrieved.') 
        
        missing_abs_semantic_scholar_ID['abstract']=missing_abs_semantic_scholar_ID['DOI'].apply(self.retrieve_openalex_abs)
        fixed_article_df = missing_abs_semantic_scholar_ID
        fixed_article_df.to_csv('open_alex_fix_attempt.csv')
        return fixed_article_df
    
                
    def retrieve_openalex_abs(self, DOI_list): 

        openalex_api_endpoint = 'https://api.openalex.org/works/https://doi.org/{doi}'
        open_alex_path = re.sub('{.*?}',str(DOI_list),openalex_api_endpoint)
        print('Retrieving for: ', DOI_list)
        try:
            open_alex_response = requests.get(open_alex_path, headers = {'mailto':'daren.rajit1@monash.edu'})
            abstract_inverted_index = open_alex_response.json().get('abstract_inverted_index') 
            abstract_index = {}
            for k, vlist in abstract_inverted_index.items():
                for v in vlist:
                    abstract_index[v] = k
                abstract = ' '.join(abstract_index[k] for k in sorted(abstract_index.keys()))
            return abstract
        
        except JSONDecodeError as err: 
            if DOI_list == 'NaN' or 'nan': 
                print('No DOI detected. Skipping')
                abstract = 'No DOI detected'
                return abstract
            pass
        
        except AttributeError as err: 
            if abstract_inverted_index is None: 
                print('OpenAlex does not have this abstract. Skipping')
                abstract = 'No abstract found'
                return abstract
            pass
    