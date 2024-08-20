import pandas as pd
import requests
from libraries.automated_handsearch import automated_handsearch
import streamlit as st

async def run_handsearch(api,seed_article_df): 

    st.write('---')
    
    st.write('### Step 3 : Conduct automated handsearching and deduplication based on your initial set of articles.')
    
    try: 
        st.write('Now conducting automated handsearching. Give us a minute')
    except: 
        st.write('Waiting on user input')

    handsearch_instance = automated_handsearch(api)

    #number of iterations 
    iter_num = 1

    citations_progress = st.progress(0, text="Initializing citation retrieval...")
    citations = await handsearch_instance.retrieve_citations(seed_article_df, citations_progress)
    
    references_progress = st.progress(0, text="Initializing reference retrieval...")
    references = await handsearch_instance.retrieve_references(seed_article_df, references_progress)

    result_full = pd.concat([citations, references], ignore_index=True)
    result_dedupe = result_full.drop_duplicates(subset=['paper_Id'])

    st.write('Handsearching done over', iter_num, ' iteration. We found a total of: ', len(result_full), 'and ', len(result_dedupe), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')

    st.write('Metadata retrieval done 🎉. Download ready as CSV RIS file. For reference the encoding is in UTF-8. RIS File Support is comming imminently.')
    st.download_button(
        label = 'Download results as CSV file',
        data = result_dedupe.to_csv().encode('utf-8'),
        file_name = 'automated_handsearch_results.csv',
        mime='text/csv',
    )

    return result_dedupe

    # st.download_button(
    #     label = 'Download results as RIS File', 
    #     data = handsearch_instance.to_ris(result_dedupe),
    #     file_name = 'automated_handsearch_results.ris',
    # )


    