import asyncio
import aiohttp 
import pandas as pd
from aiolimiter import AsyncLimiter
import platform 
import re 
import rispy 
#test openalex API functionality 


class openalex_interface: 

    '''
    Convenience class for interacting with the openalex api interface. Main functionality at the moment is to conduct snowballing / citation mining. Must provide a 
    dataframe containing a column of article ids (either DOI or OpenAlex format).
    '''

    def __init__(self): 

        self.semaphore = asyncio.Semaphore(value=100)
        self.api_limit = AsyncLimiter(9,1)
        # self.article_df = article_df 
        self.pagination_limit = 200
        self.default_cursor = '*'

        if platform.system()=='Windows':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def chunk_id_list(self,id_list): 
        '''OpenAlex has a limit of 50 ids per request, which can be concatenated together with the pipe operator.
        This function takes a list containing article ids returns a list of chunks with maximum length of 50
        '''
        max_list_length = 50
        id_chunks = [id_list[x:x+max_list_length] for x in range(0, len(id_list), max_list_length)]
        id_chunks = ['|'.join(map(str, l)) for l in id_chunks]
        return id_chunks 

    def decode_abstract(self, inverted_index_dict): 
        '''Takes the inverted index dictionary from the OpenAlex API and returns abstract in human readable form'''
        abstract_index = {}
        abstract_list = []
        
        for j in inverted_index_dict:
            if j is None:
                abstract_list.append('No Abstract Found')
            else: 
                for k, vlist in j.items():
                    for v in vlist:
                        abstract_index[v] = k
                        abstract = ' '.join(abstract_index[k] for k in sorted(abstract_index.keys()))
                abstract_list.append(abstract)
        return abstract_list

    def generate_default_api_path(self,id): 
        '''Checks if id is a DOI or OpenAlex ID and returns appropriate API endpoint(s). Pagination limit is set to 200, but this can
        be modified inside this function if needed.
        '''

        openalex_api_path_list = [] 

        for i in id: 
            if i is None or not i: 
                openalex_api_path = None
                return None
            elif i and i.startswith('10.'):
                openalex_api_endpoint = 'https://api.openalex.org/works?filter=doi:{}&per-page={}&cursor={}' 
                openalex_api_path = openalex_api_endpoint.format(i,self.pagination_limit,self.default_cursor)
                openalex_api_path_list.append(openalex_api_path)
            elif i and i.startswith('https://openalex.org/W'): 
                openalex_api_endpoint = 'https://api.openalex.org/works?filter=openalex:{}&per-page={}&cursor={}'
                openalex_api_path = openalex_api_endpoint.format(i,self.pagination_limit,self.default_cursor)
                openalex_api_path_list.append(openalex_api_path)
        print('wait')
        return openalex_api_path_list


                        
    async def retrieve_references(self, article_df): 

        '''retrieves references from a given list of article IDs'''
        seed_detail_tasks = [] 
        backward_snowball_tasks = []
        id_list = article_df['seed_Id'].tolist()
        #divide entire ID list into list containing segments that are 50 entries long (list of lists) 
        id_chunks = [self.chunk_id_list(id_list)]
        #obtain paper details for each individual seed id chunk (50 seed ids at a time)
        for i in id_chunks:
            openalex_api_path_list = self.generate_default_api_path(i)
            seed_detail_tasks.append(self.retrieve_paperdetails(openalex_api_path_list))

        print('Retrieving paper details for seed articles')
        openalex_results = await asyncio.gather(*seed_detail_tasks)
        openalex_results_df = openalex_results[0]

        #retrieve referenced works for each seed id (openalex id)
        references_openalex = openalex_results_df[['id','referenced_works']].copy()
        #for each batch of openalex ids, perform backwards snowballing 
        references_openalex_chunked = references_openalex.apply(lambda x: self.chunk_id_list(x['referenced_works']), axis=1)
        for j in references_openalex_chunked:
            references_api_path_list = self.generate_default_api_path(j)
            backward_snowball_tasks.append(self.retrieve_paperdetails(references_api_path_list))
        print('Retrieving paper details for references')
        references_full_detail_openalex = await asyncio.gather(*backward_snowball_tasks)
        final_reference_results = pd.concat(references_full_detail_openalex)
        print(final_reference_results.shape)
        #change column names from id to paper_Id to match semantic scholar interface 
        final_reference_results.rename(columns={'id':'paper_Id'}, inplace=True)
        return final_reference_results

    async def retrieve_citations(self,article_df): 

        '''retrieve citations from a given list of article IDs. OpenAlex structure is a bit different as citation urls are their own thing'''

        seed_detail_tasks = [] 
        citation_results_full = pd.DataFrame()
        id_list = article_df['seed_Id'].tolist()
        id_chunks = [self.chunk_id_list(id_list)]

        #obtain paper details for each seed id from openalex 
        for i in id_chunks:
            print(i)
            openalex_api_path_list = self.generate_default_api_path(i)
            seed_detail_tasks.append(self.retrieve_paperdetails(openalex_api_path_list))
        openalex_results = await asyncio.gather(*seed_detail_tasks)
        openalex_results_df = openalex_results[0]

        #extract citation url path for each seed id (openalex id), and add to list
        citation_openalex_path = openalex_results_df[['id','cited_by_api_url']].copy()
        citation_url_list = []
        for i in citation_openalex_path['cited_by_api_url']:
            path = i+('&per-page={}&cursor={}')
            full_path = path.format(self.pagination_limit,self.default_cursor)
            citation_url_list.append(full_path)
        print(citation_url_list)
        citation_tasks = []
        for citation_url in citation_url_list:
            citation_tasks.append(self.retrieve_paperdetails([citation_url]))
        citation_results = await asyncio.gather(*citation_tasks)
        citation_results_full = pd.concat(citation_results)
        #print shape of all dataframes in dataframe 
        for i in citation_results:
            print(i.shape)
        print(citation_results_full.shape)
        #change column names from id to paper_Id to match semantic scholar interface 
        citation_results_full.rename(columns={'id':'paper_Id'}, inplace=True)
        return citation_results_full
    
    async def retrieve_paperdetails(self,api_path_list): 

        ''' Takes a list of OpenAlex API URLs and returns OpenAlex api response as a dataframe.'''
        openalex_results_full = pd.DataFrame() 
        cursor = self.default_cursor
        for api_path in api_path_list:
            
            async with aiohttp.ClientSession() as session:
                await self.semaphore.acquire()
                async with self.api_limit: 
                    async with session.get(api_path, headers={"mailto":"darren.rajit1@monash.edu"}) as resp: 
                        if resp.status != 200: 
                            print('Appropriate Response not received for path:', api_path)
                            print('Response status:', resp.status)
                            print('Response reason:', resp.reason)

                        elif resp.status == 200: 
                            print('Response received for path:', api_path)
                            content = await resp.json()
                            openalex_results = pd.json_normalize(content, record_path = 'results', max_level=0)
                            
                            resp_meta = content.get('meta')

                            retrieved_abstract_inverted = openalex_results['abstract_inverted_index']
                            abstract_list = self.decode_abstract(retrieved_abstract_inverted)
                            openalex_results.drop(columns=['abstract_inverted_index'], inplace=True)
                            openalex_results['abstract'] = abstract_list
                            openalex_results_full = pd.concat([openalex_results_full,openalex_results])
                            print('Shape of results (after first page):', openalex_results_full.shape)
                            #pagination handling 
                            
                            # api_path = re.sub(r"(?<=cursor\=).*$",cursor, api_path)
                            while cursor is not None:
                                print('Pagination detected, retrieving next page')
                                async with self.api_limit:
                                    cursor = resp_meta['next_cursor']
                                    api_path = re.sub(r"(?<=cursor\=).*$",cursor, api_path)
                                    print('Pagination API path:', api_path)
                                    async with session.get(api_path, headers={"mailto":"darren.rajit1@monash.edu"}) as pagination_resp: 
                                        if pagination_resp.status == 200: 
                                            print('Pagination Response received')
                                            pagination_content = await pagination_resp.json()

                                            openalex_paginated_results = pd.json_normalize(pagination_content, record_path = 'results', max_level=0)
                                            print('Checking if pagination results are empty:', openalex_paginated_results.empty)
                                            if openalex_paginated_results.empty == True:
                                                print('Pagination results are empty, breaking loop')
                                                cursor = None
                                            elif openalex_paginated_results.empty == False:
                                                print('Pagination results are not empty, continuing loop')
                                                resp_meta = pagination_content.get('meta')
                                                retrieved_abstract_inverted = openalex_paginated_results['abstract_inverted_index']
                                                abstract_list = self.decode_abstract(retrieved_abstract_inverted)
                                                openalex_paginated_results.drop(columns=['abstract_inverted_index'], inplace=True)
                                                openalex_paginated_results['abstract'] = abstract_list
                                                openalex_results_full = pd.concat([openalex_results_full,openalex_paginated_results])
                                                print('Shape of results being added with pagination:', openalex_paginated_results.shape)
                                                print('Shape of consolidated results (afer pagination):', openalex_results_full.shape)
                                            
                                                cursor = resp_meta['next_cursor']

                                            
                        else: 
                            self.semaphore.release()
                                
        return openalex_results_full

        
        
        


        # async with aiohttp.ClientSession() as session:
        #         async with self.api_limit:
        #             async with session.get(full_path, headers={"mailto":"darren.rajit1@monash.edu"}) as resp: 
        #                 if resp.status == 200: 
        #                     content = await resp.json()
        #                     citation_results = pd.json_normalize(content, record_path = 'results', max_level=0)
        #                     resp_meta = content.get('meta')
        #                     citation_results_full = pd.concat([citation_results_full,citation_results])
        #                     #pagination handling 
        #                     cursor = resp_meta['next_cursor']
        #                     full_path = re.sub(r"(?<=cursor\=).*$",cursor,full_path)
        #                     while cursor is not None and citation_results.empty is False:
        #                         print('Pagination detected, retrieving next page')
        #                         async with self.api_limit:
        #                             full_path = re.sub(r"(?<=cursor\=).*$",cursor,full_path)
        #                             print(full_path)
        #                             async with session.get(full_path, headers={"mailto":"darren.rajit1@monash.edu"}) as resp: 
        #                                 if resp.status == 200: 
        #                                     content = await resp.json()
        #                                     citation_results = pd.json_normalize(content, record_path = 'results', max_level=0) 
        #                                     resp_meta = content.get('meta')
        #                                     retrieved_abstract_inverted = citation_results['abstract_inverted_index']
        #                                     abstract_list = self.decode_abstract(retrieved_abstract_inverted)
        #                                     citation_results.drop(columns=['abstract_inverted_index'], inplace=True)
        #                                     citation_results['abstract'] = abstract_list
        #                                     citation_results_full = pd.concat([citation_results_full,citation_results])
        #                                     cursor = resp_meta['next_cursor']
        #                                     print(resp_meta)

        # final_citation_results = citation_results_full 
        # return final_citation_results

    def to_ris(self, df, path):

        result_df_openalex = df 
        entries = result_df_openalex[['paper_Id', 'doi', 'title', 'abstract', 'publication_year', 'publication_date','authorships','host_venue', 'type']].copy()
        entries['database_provider'] = 'OpenAlex'
        entries.rename(columns = {'type' : 'type_of_reference'
                                ,'publication_year' : 'year'
                                ,'publication_date' : 'date'
                                ,'authorships' : 'authorship_data'
                                ,'host_venue' : 'journal_name'
                                ,'paper_Id' : 'id'
                                }, inplace = True)

        #unpacking dictionary of authors into a list of authors
        print('Writing RIS File..')

        author_data = pd.json_normalize(entries['authorship_data'].apply(lambda x : eval(str(x))))
        author_data = author_data.applymap(lambda x: {} if pd.isnull(x) else x)
        colname_range = range(1, len(list(author_data))+1)
        new_cols = ['A' + str(i) for i in colname_range]
        author_data.columns = new_cols

        author_names = author_data.apply(lambda x : x.str.get('author.display_name'), axis = 1)
        print(author_names)
        author_names = author_names.apply(lambda x : list(x.tolist()), axis = 1)
        print(author_names)
        author_names = author_names.apply(lambda x : list(filter(lambda item: item is not None, x)))
        print(author_names)
        
        author_names.name = 'authors'
        # entries_flat_authors = pd.concat([entries, author_names], axis = 1).reset_index(drop = True)
        entries_flat_authors = entries.join(author_names).reset_index(drop = True)
        entries_flat_authors = entries_flat_authors.drop(['authorship_data'], axis = 1)
        entries_ris = entries_flat_authors.to_dict('records')

        
        with open (path,'w', encoding = 'utf-8') as f:
            rispy.dump(entries_ris,f)

