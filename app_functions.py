import pandas as pd
import requests
from libraries.automated_handsearch import automated_handsearch
import streamlit as st

def run_handsearch(api,seed_article_df): 

    try: 
        st.dataframe(seed_article_df)
    except: 
        st.write('Waiting on user input')

    st.write('---')
    st.write("Intitial starting articles (pearls) loaded sucessfully. ")
    st.write('### Step 3 : Conduct automated handsearching and deduplication based on your initial set of articles.')
    handsearch_instance = automated_handsearch(api)

    st.write('Now conducting automated handsearching. Give us a minute')
    #number of iterations 
    iter_num = 1
    for i in range(iter_num): 
        #obtain id of all cited papers and papers that cite the articles in seed dataset
        result_full = handsearch_instance.run_citation_search(seed_article_df)
        #drop duplicates
        result_dedupe = result_full.drop_duplicates(subset=['paper_Id'])


    st.write('Handsearching done over', iter_num, ' iteration. We found a total of: ', len(result_full), 'and ', len(result_dedupe), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')
    st.write('Results: ', result_dedupe)


    st.write('Metadata retrieval done 🎉. Download ready as CSV RIS file. For reference the encoding is in UTF-8. RIS File Support is comming imminently.')
    
    st.download_button(
        label = 'Download results as CSV file',
        data = result_dedupe.to_csv().encode('utf-8'),
        file_name = 'automated_handsearch_results.csv',
        mime='text/csv',
    )

    # st.download_button(
    #     label = 'Download results as RIS File', 
    #     data = handsearch_instance.to_ris(result_dedupe),
    #     file_name = 'automated_handsearch_results.ris',
    # )


    