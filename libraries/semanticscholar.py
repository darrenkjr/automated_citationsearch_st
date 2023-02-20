import asyncio
import aiohttp 
import pandas as pd
from aiolimiter import AsyncLimiter
import platform 
import rispy 
#test semantic scholar API functionality
# 

class semanticscholar_interface: 

    def __init__(self,article_df,api_key): 

        self.semaphore = asyncio.Semaphore(value=100)
        self.api_limit = AsyncLimiter(50,1)
        self.article_df = article_df 
        self.session_timeout = aiohttp.ClientTimeout(total=600)
        self.pagination_limit = 500
        self.default_pagination_offset = 0
        self.api_key = api_key
        self.error_log = []
        self.fields = 'title,abstract,year,citationCount,fieldsOfStudy,authors,venue,publicationTypes,publicationDate,externalIds'

        if platform.system()=='Windows':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def retrieve_references(self): 
        results_full = pd.DataFrame() 
        async with aiohttp.ClientSession(timeout = self.session_timeout) as session:
            article_id = self.article_df['seed_Id']
            tasks = [self.retrieve_references_task(i, session) for i in article_id]
            results = await asyncio.gather(*tasks)
        for x in results: 
            results_full = pd.concat([results_full,x],ignore_index=True)
             
        print(results_full)
        return  results_full
            
    async def retrieve_references_task(self,seed_id,session): 
        async with self.api_limit: 
            self.pagination_limit = 1000
            self.default_pagination_offset = 0 
            print('Queueing backwards snowballing task for paper: ', seed_id)
            paper_reference_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{id}/references?offset={offset}&limit={limit}&fields={fields}'
            paper_reference_path_1 = paper_reference_endpoint.format(id =seed_id,offset =self.default_pagination_offset,limit =self.pagination_limit, fields = self.fields)
            print(paper_reference_path_1) 
            async with session.get(paper_reference_path_1, headers = {'x-api-key':self.api_key}, ssl=False) as resp: 
                if resp.status == 200: 
                    paper_reference_json = await resp.json()
                    try: 
                        flat_json = pd.json_normalize(paper_reference_json,record_path=['data'])
                        flat_json.columns = flat_json.columns.str.replace('citedPaper.', '')
                        flat_json.columns = flat_json.columns.str.replace('externalIds.', '')
                        print(flat_json.columns)
                        flat_json.rename(columns = {
                            'paperId' : 'paper_Id', 'title':'paper_Title','abstract':'paper_Abstract','year':'paper_Year','citationCount':'paper_citation_count','fieldsOfStudy':'paper_field','authors':'paper_author'
                        }, inplace=True)
                        print('Request successful for paper: ', seed_id)
                        print('Length of response', len(flat_json))
                        if len(flat_json) >= self.pagination_limit: 
                            print('Pagination detected for paper: ', seed_id)
                            ## pagination not fully done here btw
                    except ValueError as e: 
                        print(e, 'No data found for paper: ', seed_id)
                        self.error_log.append(e)
                    print(flat_json.columns)
                    return flat_json
                else: 
                    print('Error: ', resp.status)
                    self.error_log.append(resp.status)
                    return None
                
    async def retrieve_citations(self): 
        results_full = pd.DataFrame() 
        async with aiohttp.ClientSession(timeout = self.session_timeout) as session:
            article_id = self.article_df['seed_Id']
            tasks = [self.retrieve_citations_task(i, session) for i in article_id]
            results = await asyncio.gather(*tasks)
        for x in results: 
            results_full = pd.concat([results_full,x],ignore_index=True)   
        print(results_full)
        return results_full
    
    async def retrieve_citations_task(self, seed_id, session):
        async with self.api_limit: 
            print('Queueing forward snowballing task for paper: ', seed_id)
            paper_citation_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{id}/citations?offset={offset}&limit={limit}&fields={fields}'
            paper_citation_path_1 = paper_citation_endpoint.format(id =seed_id,offset =self.default_pagination_offset,limit =self.pagination_limit, fields = self.fields) 
            async with session.get(paper_citation_path_1, headers = {'x-api-key':self.api_key}, ssl=False) as resp: 
                print(paper_citation_path_1)
                if resp.status == 200: 
                    paper_citation_json = await resp.json()
                    flat_json = pd.json_normalize(paper_citation_json,record_path=['data'])
                    flat_json.columns = flat_json.columns.str.replace('citingPaper.', '')
                    flat_json.columns = flat_json.columns.str.replace('externalIds.', '')
                    flat_json.rename(columns = {
                        'paperId' : 'paper_Id', 'title':'paper_Title','abstract':'paper_Abstract','year':'paper_Year','citationCount':'paper_citation_count','fieldsOfStudy':'paper_field','authors':'paper_author'
                    }, inplace=True)

                    pagination_check = len(flat_json)
                    print('Length of response',pagination_check)    
                    if pagination_check >= self.pagination_limit: 
                        print('Pagination detected for paper: ', seed_id)
                        pagination_offset = self.default_pagination_offset
                        while pagination_check >= self.pagination_limit: 
                            pagination_offset += self.pagination_limit 
                            paper_citation_path_pagination = paper_citation_endpoint.format(id = seed_id,offset = pagination_offset,limit = self.pagination_limit, fields = self.fields)
                            async with session.get(paper_citation_path_pagination, headers =  {'x-api-key':self.api_key}, ssl=False) as resp:
                                if resp.status == 200: 
                                    paper_citaton_json = await resp.json()
                                    flat_json_pagination = pd.json_normalize(paper_citaton_json,record_path=['data'])
                                    if flat_json_pagination.empty == True:
                                        print('Reached end of pagination. No extra data was found')
                                        break
                                    else: 
                                        print(flat_json_pagination.columns)
                                        print(flat_json_pagination.head)

                                        flat_json_pagination.columns = flat_json_pagination.columns.str.replace('citingPaper.', '')
                                        flat_json_pagination.columns = flat_json_pagination.columns.str.replace('externalIds.', '')
                                        flat_json_pagination.rename(columns = {
                                            'paperId' : 'paper_Id', 'title':'paper_Title','abstract':'paper_Abstract','year':'paper_Year','citationCount':'paper_citation_count','fieldsOfStudy':'paper_field','authors':'paper_author'
                                        }, inplace=True)
                                        print('Request successful for paper with pagination: ' + seed_id + 'at offset: ' + str(pagination_offset))  
                                        print('Appending data to results')
                                        flat_json = pd.concat([flat_json,flat_json_pagination],ignore_index=True)                     

                                if self.default_pagination_offset > 5000: 
                                    break 
                            pagination_check = len(flat_json)
                    return flat_json
                else: 
                    print('Error: ', resp.status)
                    self.error_log.append(resp.status)
                    return None
    
    async def retrieve_citations_and_references(self):
        paper_ref = await self.retrieve_references()
        print('Backwards snowballing data retrieved.')
        paper_citation = await (self.retrieve_citations())
        results = pd.concat([paper_ref,paper_citation],ignore_index=True)
        results.dropna(subset =['paper_Id'], inplace=True)
        print('Raw results:', len(results))
        results_no_dupe= results.drop_duplicates(subset=['paper_Id'])
        print('Results after deduplication:', len(results_no_dupe))
        return  results_no_dupe 
                    
    def to_ris(self,df): 

        result_df_ss = df 
        entries = result_df_ss.copy() 
        entries['database_provider'] = 'Semantic Scholar'
        entries.rename(columns ={
            'paper_Id':'id',
            'paper_Title':'title',
            'paper_Abstract':'abstract',
            'paper_Venue':'journal_name',
            'paper_Year':'year',
            'paper_author':'authors',
        }, inplace=True)

        #unpack author column to get list of authors (nested dictionary)
        author_data = pd.json_normalize(entries['authors'].apply(lambda x : eval(x)))
        author_data = author_data.applymap(lambda x: {} if pd.isnull(x) else x)
        colname_range = range(1, len(list(author_data))+1)
        new_cols = ['A' + str(i) for i in colname_range]
        author_data.columns = new_cols
        author_names = author_data.apply(lambda x : x.str.get('name'), axis = 1)
        author_names = author_names.apply(lambda x : list(x.tolist()), axis = 1)
        author_names = author_names.apply( lambda x : list(filter(lambda item: item is not None, x)))
        author_names.name = 'authors'
        entries = pd.concat([entries, author_names], axis = 1)
        entries_ris = entries.to_dict('records')
        ris_export_path = 'result.ris'
        with open (ris_export_path, 'w', encoding = 'utf-8') as f: 
            rispy.dump(entries_ris,f)

    # async def create_missing_abs_task(self,session,paper_id): 
    #     article_externalID_endpoint = 'https://partner.semanticscholar.org/graph/v1/paper/{paper_id}/?fields=externalIds'
    #     async with self.api_limit_semanticscholar:
    #         print('Retrieving doi for paper:', paper_id)
    #         semantic_scholar_api_path = article_externalID_endpoint.format(paper_id=paper_id)
    #         async with session.get(semantic_scholar_api_path, headers = {'x-api-key':self.api_key}, ssl=False) as resp: 
    #             return await resp.json()

    # do some async stuff here
    # async def obtain_doi_missing_abs(self,df_missing_abs): 
    #     '''obtain DOIs for entries that are missing abstracts from semantic scholar'''
    #     async with aiohttp.ClientSession(timeout = self.session_timeout) as session:
            
    #         missing_abs_index= df_missing_abs[df_missing_abs['paper_Abstract'].isnull()].index.tolist()
    #         missing_abs_semantic_scholar_ID = df_missing_abs.loc[missing_abs_index]['paper_Id']
    #         responses = await asyncio.gather(*(self.create_missing_abs_task(session,i) for i in missing_abs_semantic_scholar_ID))
    #         # print(responses)
    #         external_id = pd.DataFrame()
    #         for response in responses:
    #             try: 
    #                 flat_json_ref = pd.json_normalize(response)
    #                 external_id = pd.concat([external_id,flat_json_ref])
    #             except AttributeError as err:
    #                 break 
    #         print('DOI retrieval completed')
    #         missing_abs_semantic_scholar_ID = missing_abs_semantic_scholar_ID.to_frame()
    #         missing_abs_semantic_scholar_ID = missing_abs_semantic_scholar_ID.assign(DOI=external_id['externalIds.DOI'].values)
    #         print(missing_abs_semantic_scholar_ID)
    #         return missing_abs_semantic_scholar_ID

    # async def create_open_alex_tasks(self,DOI): 
    #     '''create tasks for open alex API'''
    #     resp_status = await self.retrieve_openalex_abs(DOI)
    #     return resp_status

    # async def retrieve_openalex_abs(self,doi): 
    #     '''retrieve abstracts from OpenAlex given doi as a list'''
    #     openalex_api_endpoint = 'https://api.openalex.org/works/https://doi.org/{doi}?mailto=darren.rajit1@monash.edu' 

    #     async with aiohttp.ClientSession() as session:
    #         await self.semaphore_openalex.acquire()
    #         async with self.api_limit_openalex: 
    #             async with session.get(openalex_api_endpoint.format(doi=doi)) as resp: 
    #                 print('Retrieving for :', openalex_api_endpoint.format(doi=doi))
    #                 if resp.status == 200: 
    #                     content = await resp.json()
    #                     try: 
    #                         retrieved_abstract_inverted = content.get('abstract_inverted_index')
    #                         abstract_index = {}
    #                         # print(retrieved_abstract_inverted)
    #                         for k, vlist in retrieved_abstract_inverted.items():
    #                             for v in vlist:
    #                                 abstract_index[v] = k
    #                             abstract = ' '.join(abstract_index[k] for k in sorted(abstract_index.keys()))
    #                             self.semaphore_openalex.release() 
    #                         return abstract

    #                     except AttributeError as err: 
    #                         print(err)
    #                         self.semaphore_openalex.release() 
    #                         return 'No Abstract Found'
    #                 else: 
    #                     return resp.status
        

