from urllib.error import HTTPError
from json.decoder import JSONDecodeError
import pandas as pd
import asyncio
import os 
import streamlit as st 
from libraries.openalex import openalex_interface
from libraries.semanticscholar import semanticscholar_interface

class automated_handsearch: 

    def __init__(self,api): 

        self.error_log = []
        self.api = api

        if api == 'semanticscholar':
            #get api key from streamlit secretes 

            semanticscholar_api_key =  st.secrets['semanticscholar_api_key']
            self.api_interface = semanticscholar_interface(semanticscholar_api_key)

        if api == 'openalex':
            self.api_interface = openalex_interface(a)

    
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


    