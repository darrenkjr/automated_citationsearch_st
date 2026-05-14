import asyncio
import pandas as pd
import streamlit as st
import pyalex
from pyalex import Works
import random
from itertools import chain
from libraries.oa_to_ris import format_ris

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class openalex_interface:
    '''
    Convenience class for interacting with the openalex api interface using pyalex.
    Main functionality is to conduct snowballing / citation mining.
    '''

    def __init__(self, oa_email_address):
        self.oa_email_address = oa_email_address
        pyalex.config.email = self.oa_email_address
        self.batch_size = 50
        self.semaphore = asyncio.Semaphore(8)

    def extract_id_from_url(self, url):
        if pd.isna(url) or not isinstance(url, str):
            return None
        url = url.strip()
        if url.startswith('https://openalex.org/'):
            return url.replace('https://openalex.org/', '')
        elif url.startswith('https://doi.org/'):
            return url.replace('https://doi.org/', '')
        return url

    async def fetch_citations_with_backoff(self, id_batch, max_retries=5):
        """Fetch forward citations (works citing the seed batch)"""
        async with self.semaphore:
            retries = 0
            while retries < max_retries:
                try:
                    def get_all_pages():
                        local_records = {}
                        page_query = Works().filter_or(cites=id_batch)
                        for record in chain(*page_query.paginate(per_page=200, n_max=None)):
                            local_records[record["id"]] = record
                        return local_records

                    batch_records = await asyncio.to_thread(get_all_pages)
                    return batch_records
                    
                except Exception as e:
                    error_msg = str(e)
                    if any(err in error_msg for err in ['429', '503', '502']):
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        print(f"Rate limited. Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        retries += 1
                    else:
                        print(f"Error fetching citations: {error_msg}")
                        return {}
                        
            return {}

    async def fetch_works_with_backoff(self, id_batch, max_retries=5):
        """Fetch specific works by ID"""
        dois = [i for i in id_batch if i.startswith('10.')]
        oa_ids = [i for i in id_batch if i.startswith('W')]
        
        async with self.semaphore:
            retries = 0
            while retries < max_retries:
                try:
                    def get_all_pages():
                        local_records = {}
                        if dois:
                            page_query = Works().filter_or(doi=dois)
                            for record in chain(*page_query.paginate(per_page=200, n_max=None)):
                                local_records[record["id"]] = record
                        if oa_ids:
                            page_query = Works().filter_or(openalex=oa_ids)
                            for record in chain(*page_query.paginate(per_page=200, n_max=None)):
                                local_records[record["id"]] = record
                        return local_records

                    batch_records = await asyncio.to_thread(get_all_pages)
                    return batch_records
                    
                except Exception as e:
                    error_msg = str(e)
                    if any(err in error_msg for err in ['429', '503', '502']):
                        wait_time = (2 ** retries) + random.uniform(0, 1)
                        print(f"Rate limited. Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        retries += 1
                    else:
                        print(f"Error fetching works: {error_msg}")
                        return {}
                        
            return {}

    async def fetch_seed_articles(self, article_df):
        """Fetch the seed articles to standardize IDs to OpenAlex IDs and get their references"""
        id_list = article_df['seed_Id'].dropna().tolist()
        clean_ids = [self.extract_id_from_url(i) for i in id_list]
        clean_ids = [i for i in clean_ids if i is not None]
        
        seed_batches = list(chunk_list(clean_ids, self.batch_size))
        seed_tasks = [self.fetch_works_with_backoff(batch) for batch in seed_batches]
        
        all_seed_records = {}
        for task in asyncio.as_completed(seed_tasks):
            batch_result = await task
            all_seed_records.update(batch_result)
            
        return all_seed_records

    async def retrieve_citations(self, article_df):
        st.write('Retrieving citations for seed articles...')
        citations_progress = st.progress(0, text="Fetching seed articles to identify OpenAlex IDs...")
        
        # Fetch seeds first to ensure we have pure OpenAlex IDs
        all_seed_records = await self.fetch_seed_articles(article_df)
        
        # Use the OpenAlex IDs (e.g. W12345678)
        oa_ids = [self.extract_id_from_url(record['id']) for record in all_seed_records.values()]
        oa_ids = [i for i in oa_ids if i is not None]
        
        batches = list(chunk_list(oa_ids, self.batch_size))
        total_batches = len(batches)
        
        all_citation_records = {}
        
        tasks = [self.fetch_citations_with_backoff(batch) for batch in batches]
        
        completed = 0
        for task in asyncio.as_completed(tasks):
            batch_result = await task
            all_citation_records.update(batch_result)
            completed += 1
            progress = completed / total_batches if total_batches > 0 else 1.0
            citations_progress.progress(progress, text=f"Retrieving citations: {completed}/{total_batches} batches ({progress:.1%})")

        return self.records_to_dataframe(all_citation_records)

    async def retrieve_references(self, article_df, progress_bar):
        st.write('Retrieving references for seed articles...')
        
        progress_bar.progress(0, text="Fetching seed articles to extract reference lists...")
        all_seed_records = await self.fetch_seed_articles(article_df)
            
        # Extract referenced works
        referenced_works = set()
        for record in all_seed_records.values():
            refs = record.get('referenced_works', [])
            referenced_works.update(refs)
            
        referenced_works_list = list(referenced_works)
        ref_clean_ids = [self.extract_id_from_url(i) for i in referenced_works_list]
        ref_clean_ids = [i for i in ref_clean_ids if i is not None]
        
        ref_batches = list(chunk_list(ref_clean_ids, self.batch_size))
        total_batches = len(ref_batches)
        
        all_reference_records = {}
        tasks = [self.fetch_works_with_backoff(batch) for batch in ref_batches]
        
        completed = 0
        if total_batches == 0:
            progress_bar.progress(1.0, text="No references found for seed articles.")
        
        for task in asyncio.as_completed(tasks):
            batch_result = await task
            all_reference_records.update(batch_result)
            completed += 1
            progress = completed / total_batches if total_batches > 0 else 1.0
            progress_bar.progress(progress, text=f"Retrieving references: {completed}/{total_batches} batches ({progress:.1%})")

        return self.records_to_dataframe(all_reference_records)

    def records_to_dataframe(self, records_dict):
        """Convert OpenAlex raw dictionaries into a DataFrame with required columns for the app."""
        data = []
        for paper_id, record in records_dict.items():
            # Process authors into a neat string for CSV export display
            authorships = record.get('authorships', [])
            author_names = [a.get('author', {}).get('display_name') for a in authorships if a.get('author')]
            author_str = "; ".join(filter(None, author_names))

            row = {
                'paper_Id': paper_id,
                'title': record.get('title'),
                'doi': record.get('doi'),
                'publication_year': record.get('publication_year'),
                'type': record.get('type'),
                'authors': author_str,
                'raw_oa_dict': record
            }
            data.append(row)
        
        if not data:
            return pd.DataFrame(columns=['paper_Id', 'title', 'doi', 'publication_year', 'type', 'authors', 'raw_oa_dict'])
            
        return pd.DataFrame(data)

    def to_ris(self, df, path):
        """
        Export OpenAlex results to RIS format.
        """
        try:
            print('Writing RIS File..')
            ris_content = ""
            for _, row in df.iterrows():
                # Extract the raw dictionary saved during retrieval
                if 'raw_oa_dict' in row and isinstance(row['raw_oa_dict'], dict):
                    ris_content += format_ris(row['raw_oa_dict']) + "\n"
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(ris_content)
                
            print(f"RIS file successfully written to: {path}")
            return True
            
        except Exception as e:
            print(f"Error writing RIS file: {e}")
            raise e

