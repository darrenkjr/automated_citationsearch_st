import pandas as pd
import requests
from libraries.automated_handsearch import automated_handsearch
import streamlit as st
import tempfile
import os 

async def run_handsearch(api,seed_article_df, iter_num): 

    
    
    try: 
        st.write('Now conducting automated handsearching. Give us a minute')
    except: 
        st.write('Waiting on user input')

    handsearch_instance = automated_handsearch(api)

    #number of iterations 
    #placeholder - future implementation will allow for multiple iterations, by wrapping this in a loop
    if api == 'Semantic Scholar':
        citations_progress = st.progress(0, text="Initializing citation retrieval...")
        citations = await handsearch_instance.retrieve_citations(seed_article_df, citations_progress)
    elif api == 'OpenAlex':
        seed_progress = st.progress(0, text="Initializing seed article retrieval...")
        citations = await handsearch_instance.retrieve_citations(seed_article_df, seed_progress)
    
    references_progress = st.progress(0, text="Initializing reference retrieval...")
    references = await handsearch_instance.retrieve_references(seed_article_df, references_progress)

    result_full = pd.concat([citations, references], ignore_index=True)
    result_dedupe = result_full.drop_duplicates(subset=['paper_Id'])

    return result_dedupe

    # st.download_button(
    #     label = 'Download results as RIS File', 
    #     data = handsearch_instance.to_ris(result_dedupe),
    #     file_name = 'automated_handsearch_results.ris',
    # )

def export_to_ris(results_df, api_choice):
    """
    Export results to RIS format based on the selected API.
    Returns the RIS content as a string.
    """
    if api_choice == 'OpenAlex':
        # Use the existing interface from session state
        if 'api_interface' in st.session_state and hasattr(st.session_state.api_interface, 'to_ris'):
            oa_interface = st.session_state.api_interface
        else:
            # Fallback: create new instance with email from secrets
            from libraries.openalex import openalex_interface
            oa_email = os.environ.get('oa_email_address') or st.secrets['oa_email_address']
            oa_interface = openalex_interface(oa_email)
        
        # Create temporary file for RIS generation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ris', delete=False, encoding='utf-8') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            success = oa_interface.to_ris(results_df, tmp_path)
            
            if success:
                # Read the generated RIS file
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    ris_content = f.read()
            else:
                ris_content = ""
                
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return ris_content
        
    elif api_choice == 'Semantic Scholar':
        from libraries.semanticscholar import semanticscholar_interface
        from dotenv import load_dotenv
        
        load_dotenv()
        ss_api_key = os.getenv('semantic_scholar_api_key')
        
        # Create temporary file for RIS generation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ris', delete=False, encoding='utf-8') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            ss_interface = semanticscholar_interface(ss_api_key)
            
            # The Semantic Scholar to_ris method saves to 'result.ris' by default
            # We need to modify it to use our temp path or handle the file reading
            ss_interface.to_ris(results_df)
            
            # Read the generated RIS file (assuming it saves to 'result.ris')
            if os.path.exists('result.ris'):
                with open('result.ris', 'r', encoding='utf-8') as f:
                    ris_content = f.read()
                os.unlink('result.ris')  # Clean up
            else:
                ris_content = ""
                
        except Exception as e:
            st.error(f"Error generating RIS file: {str(e)}")
            ris_content = ""
            
        return ris_content
    
    else:
        return ""

    