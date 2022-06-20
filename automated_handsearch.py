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

    def retrieve_paper_details(self, seed_article_df):
        #
        return self


    @limits(calls=100,period=1)
    def obtain_paper_citation(self):

        self.error_list = []
        paper_citation_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/citations?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        paper_reference_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/references?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        self.seed_article_data = pd.DataFrame()

        for i in self.seed_article_id:
            print(self.seed_article_id)
            
            try:
                #defning api paths
                paper_reference_path_1 = re.sub('(?<=paper/).*?(?=/references)',str(i),paper_reference_endpoint)
                paper_citation_path_1 = re.sub('(?<=paper/).*?(?=/citations)',str(i),paper_citation_endpoint)
                
                #conducting backwards and forwards snowballing, and retrieving paper ids
                print('Retrieving results for paper with ID: ',i)
                api_response_paper_ref = requests.get(paper_reference_path_1, headers = {'x-api-key':self.api_key})
                api_response_paper_cite = requests.get(paper_citation_path_1, headers = {'x-api-key':self.api_key})

                #convert json response for cited papers into pandas dataframe
                flat_json_ref = pd.json_normalize(api_response_paper_ref.json(),record_path=['data'])

                #normalizing column names - removes distinction between cited papers and citing papers

                flat_json_ref.columns = ['paper_Id','paper_Title', 'paper_Abstract', 'paper_Venue', 'paper_Year', 'paper_citation_count','paper_field', 'paper_author' ]

                
                #convert json respone for citing papers into pandas dataframe
                flat_json_citedby = pd.json_normalize(api_response_paper_cite.json(),record_path=['data'])

                #normalizing column names 
                flat_json_citedby.columns = flat_json_ref.columns
                
                #create result dataframe 
                self.seed_article_data = pd.concat([self.seed_article_data,flat_json_ref,flat_json_citedby],ignore_index=True)

            
            except: 
                self.error_log.append([i,api_response_paper_cite,api_response_paper_ref])
        
        
    
        #drop results with no id
        self.seed_article_data.dropna(subset =['paper_Id'], inplace=True)
        self.results_no_na = self.seed_article_data
        print(len(self.seed_article_data))
        #deduplicate
        self.results_no_dupe= self.seed_article_data.drop_duplicates(subset=['paper_Id'])
        print(len(self.results_no_dupe))
            
        return  self.results_no_dupe, self.error_list


    @limits(calls=100,period=1)
    def obtain_reference_paper_data(self):



        paper_info_path = 'https://partner.semanticscholar.org/graph/v1/paper/{paperid}?fields=title,abstract,year,citationCount,fieldsOfStudy,authors,venue'
        data_1 = pd.DataFrame()
        for i in self.snowball_data_no_dupe_id:

            print('Retrieving article details for paper with ID: ',i)
            paper_info_path_1 = re.sub('(?<=paper/).*?(?=\?fields)',str(i),paper_info_path)

            try:
                response_1 = requests.get(paper_info_path_1,headers = {'x-api-key':self.api_key})
                response_1.raise_for_status()
                paper_info = pd.json_normalize(response_1.json())
                data_1 = pd.concat([data_1,paper_info], ignore_index=True)

            except requests.HTTPError as e:
                #note: implement error handling properly
                error_string = e 
                error_collection = error_collection.append([error_string])

        self.handsearch_results = data_1

        return self.handsearch_results, self.error_log

        