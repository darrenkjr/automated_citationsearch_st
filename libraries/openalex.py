import asyncio
import aiohttp 
import pandas as pd
from aiolimiter import AsyncLimiter
import platform 
import re 
import rispy 
import streamlit as st
#test openalex API functionality 


class openalex_interface: 

    '''
    Convenience class for interacting with the openalex api interface. Main functionality at the moment is to conduct snowballing / citation mining. Must provide a 
    dataframe containing a column of article ids (either DOI or OpenAlex format).
    '''

    def __init__(self, oa_email_address): 

        self.oa_email_address = oa_email_address
        self.api_limit = AsyncLimiter(5,1) 
        self.pagination_limit = 200
        self.default_cursor = '*'
        self.batch_size = 10
        self.openalex_results_df = pd.DataFrame()
        self.citation_url = 'https://api.openalex.org/works?filter=cites:{}&per-page={}&cursor={}'

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


                        
    async def retrieve_references(self, article_df, progress_bar): 

        '''retrieves references from a given list of article IDs'''
        
        backward_snowball_tasks = []
        #divide entire ID list into list containing segments that are 50 entries long (list of lists) 
        
        completed_tasks = 0 
        #obtain paper details for each individual seed id chunk (50 seed ids at a time)
        async def fetch_with_progress(url): 
            nonlocal completed_tasks 
            result = await self.retrieve_paperdetails([url])
            completed_tasks += 1
            progress = completed_tasks / total_tasks
            progress_bar.progress(progress, text=f"Retrieving references: {completed_tasks}/{total_tasks} ({progress:.1%})")
            return result

        if self.openalex_results_df.empty: 
            seed_detail_tasks = [] 
            id_list = article_df['seed_Id'].tolist()
            id_chunks = [self.chunk_id_list(id_list)]
            total_tasks = len(id_list)
            for i in id_chunks:
                openalex_api_path_list = self.generate_default_api_path(i)
                seed_detail_tasks.append(self.retrieve_paperdetails(openalex_api_path_list))

            st.write('Retrieving paper details for seed articles and extract references')
            openalex_results = await asyncio.gather(*seed_detail_tasks)
            openalex_results_df = openalex_results[0]

        #retrieve referenced works for each seed id (openalex id)
        references_openalex = self.openalex_results_df[['id','referenced_works']].copy()
        #for each batch of openalex ids, perform backwards snowballing 
        references_openalex_chunked = references_openalex.apply(lambda x: self.chunk_id_list(x['referenced_works']), axis=1)

        st.write('Retrieving paper details for references')
        references_results = [] 
        total_tasks = sum(len(self.generate_default_api_path(chunk)) for chunk in references_openalex_chunked)
        completed_tasks = 0
        progress_bar.progress(0, text=f"Retrieving references: 0/{total_tasks} (0%)")
        for j in references_openalex_chunked:
            references_api_path_list = self.generate_default_api_path(j)
            for i in range(0, len(references_api_path_list), self.batch_size):
                batch = references_api_path_list[i:i+self.batch_size]
                batch_tasks = [fetch_with_progress(url) for url in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                references_results.extend([r for r in batch_results if r is not None])


        final_reference_results = pd.concat(references_results)
        #change column names from id to paper_Id to match semantic scholar interface 
        final_reference_results.rename(columns={'id':'paper_Id'}, inplace=True)
        return final_reference_results

    async def retrieve_citations(self,article_df): 

        '''retrieve citations from a given list of article IDs. OpenAlex structure is a bit different as citation urls are their own thing'''

        seed_detail_tasks = [] 
        citation_results_full = pd.DataFrame()
        id_list = article_df['seed_Id'].tolist()
        id_chunks = [self.chunk_id_list(id_list)]

        for i in id_chunks: 
            openalex_api_path_list = self.generate_default_api_path(i)
            

        total_seed_article_tasks = len(openalex_api_path_list)
        completed_seed_article_tasks = 0
        st.write('Retrieving paper details for seed articles initially in batches. Each batch contains max 50 seed ids.')
        seed_progress_bar = st.progress(0, text="Initializing seed article retrieval...")
        #obtain paper details for each seed id from openalex 
        async def fetch_seed_with_progress(url): 
            nonlocal completed_seed_article_tasks 
            result = await self.retrieve_paperdetails([url])
            completed_seed_article_tasks += 1
            progress = completed_seed_article_tasks / total_seed_article_tasks
            seed_progress_bar.progress(progress, text=f"Retrieving seed article details: {completed_seed_article_tasks}/{total_seed_article_tasks} ({progress:.1%})")
            return result
        #batching 
        openalex_results = []
        for i in range(0, len(openalex_api_path_list), self.batch_size):
            batch = openalex_api_path_list[i:i+self.batch_size]
            batch_tasks = [fetch_seed_with_progress(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            openalex_results.extend([r for r in batch_results if r is not None])

        self.openalex_results_df = pd.concat(openalex_results)

        
        #extract citation url path for each seed id (openalex id), and add to list
        seed_oa_id_list = self.openalex_results_df['id'].tolist()
        citation_url_list = [self.citation_url.format(i,self.pagination_limit,self.default_cursor) for i in seed_oa_id_list]
        

        st.write('Retrieving citations for seed articles')
        
        #reset tasks number
        #reset progress bar 
        completed_citation_tasks = 0
        total_citation_tasks = len(citation_url_list)
        citation_progress_bar = st.progress(0, text="Initializing citation retrieval...")
        async def fetch_citation_with_progress(url): 
            nonlocal completed_citation_tasks 
            result = await self.retrieve_paperdetails([url])
            completed_citation_tasks += 1
            progress = completed_citation_tasks / total_citation_tasks
            citation_progress_bar.progress(progress, text=f"Retrieving citations: {completed_citation_tasks}/{total_citation_tasks} ({progress:.1%})")
            return result

        citation_results = []
        for i in range(0, len(citation_url_list), self.batch_size):
            batch = citation_url_list[i:i+self.batch_size]
            batch_tasks = [fetch_citation_with_progress(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            citation_results.extend([r for r in batch_results if r is not None])
            
        citation_results_full = pd.concat(citation_results)
        #change column names from id to paper_Id to match semantic scholar interface 
        citation_results_full.rename(columns={'id':'paper_Id'}, inplace=True)
        return citation_results_full
    
    async def retrieve_paperdetails(self,api_path_list): 

        ''' Takes a list of OpenAlex API URLs and returns OpenAlex api response as a dataframe.'''
        openalex_results_full = pd.DataFrame() 
        cursor = self.default_cursor
        for api_path in api_path_list:
            
            async with aiohttp.ClientSession() as session:
                # await self.semaphore.acquire()
                async with self.api_limit: 
                    async with session.get(api_path, headers={"mailto":self.oa_email_address}) as resp: 
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
                                    async with session.get(api_path, headers={"mailto":self.oa_email_address}) as pagination_resp: 
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

                                
        return openalex_results_full


    def to_ris(self, df, path):
        """
        Export OpenAlex results to RIS format.
        """
        try:
            result_df_openalex = df.copy()
            
            # Check if required columns exist
            required_columns = ['paper_Id', 'doi', 'title', 'abstract', 'publication_year', 'publication_date', 'authorships', 'primary_location', 'type', 'biblio']
            missing_columns = [col for col in required_columns if col not in result_df_openalex.columns]
            
            if missing_columns:
                print(f"Warning: Missing columns: {missing_columns}")
                # Fill missing columns with empty values
                for col in missing_columns:
                    result_df_openalex[col] = ''
            
            # Select and rename columns safely
            entries = result_df_openalex[required_columns].copy()
            entries['database_provider'] = 'OpenAlex'
            entries['journal_name'] = entries['primary_location'].apply(
                lambda x: x.get('source',{}).get('display_name') if x is not None else ''
            )
            entries[['volume','issue','first_page','last_page']] = entries['biblio'].apply(
                lambda x: pd.json_normalize(x).loc[:,['volume','issue','start_page','end_page']] if x is not None else pd.Series([None]*4, index=['volume','issue','first_page','last_page'])
            )

            
            
            # Rename columns
            column_mapping = {
                'type': 'type_of_reference',
                'publication_year': 'year',
                'publication_date': 'date',
                'authorships': 'authorship_data',
                'paper_Id': 'id'
            }
            entries.rename(columns=column_mapping, inplace=True)
            
            print('Writing RIS File..')
            
            # Safely handle authorship data
            try:
                # Use ast.literal_eval instead of eval for safety
                import ast
                author_data = pd.json_normalize(
                    entries['authorship_data'].apply(
                        lambda x: ast.literal_eval(str(x)) if pd.notna(x) and str(x) != 'nan' else {}
                    )
                )
                
                if not author_data.empty:
                    # Process author names safely
                    colname_range = range(1, len(author_data.columns) + 1)
                    new_cols = ['A' + str(i) for i in colname_range]
                    author_data.columns = new_cols
                    
                    author_names = author_data.apply(
                        lambda x: x.str.get('author.display_name', ''), axis=1
                    )
                    author_names = author_names.apply(
                        lambda x: [name for name in x.tolist() if pd.notna(name) and name != ''], axis=1
                    )
                    author_names.name = 'authors'
                    
                    # Join author names with entries
                    entries_flat_authors = entries.join(author_names).reset_index(drop=True)
                    entries_flat_authors = entries_flat_authors.drop(['authorship_data'], axis=1)
                else:
                    # No author data, create empty authors column
                    entries_flat_authors = entries.copy()
                    entries_flat_authors['authors'] = ''
                    
            except Exception as e:
                print(f"Warning: Error processing authors: {e}")
                # Fallback: create empty authors column
                entries_flat_authors = entries.copy()
                entries_flat_authors['authors'] = ''
            
            # Convert to records for rispy
            entries_ris = entries_flat_authors.to_dict('records')
            
            # Write RIS file
            with open(path, 'w', encoding='utf-8') as f:
                rispy.dump(entries_ris, f)
                
            print(f"RIS file successfully written to: {path}")
            return True
            
        except Exception as e:
            print(f"Error writing RIS file: {e}")
            raise e

