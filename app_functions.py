import pandas as pd
import requests
from libraries.automated_handsearch import automated_handsearch
import streamlit as st

semantic_scholar_key =  'KOh3wE4IBn21HkRsU49Ya4JT93KrwyPv4PV37Vry'

def run_handsearch(seed_article_df): 

    try: 
        st.dataframe(seed_article_df)
    except: 
        st.write('Waiting on user input')

    st.write("Intitial starting articles (pearls) loaded sucessfully. ")
    st.write('### Step 2 : Conduct automated handsearching and deduplication based on your initial set of articles.')
    handsearch_instance = automated_handsearch(seed_article_df,semantic_scholar_key)

    st.write('Now conducting automated handsearching. Give us a minute')
    #number of iterations 
    iter_num = 1
    for i in range(iter_num): 
        #obtain id of all cited papers and papers that cite the articles in seed dataset
        result_dedupe = handsearch_instance.backwards_forwards_citation()

    st.write('Handsearching done over', iter_num, ' iteration. We found a total of: ', len(result_dedupe), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')
    st.write('Results: ', result_dedupe)

    results_csv = result_dedupe.to_csv().encode('utf-8')

    st.write('Metadata retrieval done 🎉. Download ready as CSV file. For reference the encoding is in UTF-8. ', key='Download Results')
    st.download_button(
        label = 'Download results as CSV file',
        data = results_csv,
        file_name = 'automated_handsearch_results.csv',
        mime='text/csv',
    )
    