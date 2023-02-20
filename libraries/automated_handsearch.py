from urllib.error import HTTPError
from json.decoder import JSONDecodeError
import pandas as pd
import asyncio
import os 
from dotenv import load_dotenv
from libraries.openalex import openalex_interface
from libraries.semanticscholar import semanticscholar_interface
import streamlit as st

class automated_handsearch: 

    def __init__(self,api): 
        print(api)
        self.error_log = []
        if api == "Semantic Scholar":
            
            semanticscholar_api_key =  st.secrets["semantic_scholar_api_key"]
            print(semanticscholar_api_key)
            self.api_interface = semanticscholar_interface(semanticscholar_api_key)

        if api == "OpenAlex":
            self.api_interface = openalex_interface()

    
    def run_citation_search(self, article_df): 

        references = asyncio.run(self.api_interface.retrieve_citations(article_df))
        citations = asyncio.run(self.api_interface.retrieve_references(article_df))

        #combine api results
        results_full = pd.concat([references,citations],ignore_index=True)
        return results_full 

    def to_ris(self,df): 
        #convert to ris format 
        ris = asyncio.run(self.api_interface.to_ris(df))
        return ris


    