import pandas as pd
from libraries.automated_handsearch import automated_handsearch
import streamlit as st

#move this somewhere else (probably as environment variable) 
semantic_scholar_key =  'KOh3wE4IBn21HkRsU49Ya4JT93KrwyPv4PV37Vry'

def run_handsearch(seed_article_df,iter_num): 

    try: 
        st.dataframe(seed_article_df)
        seed_id = seed_article_df['seed_Id']
        print(seed_id)
        st.write("Intitial starting articles (pearls) loaded sucessfully. ")
    except Exception as e:
        print(e) 

    st.write('---')
    st.write('### Step 3 : Conduct automated handsearching and deduplication based on your initial set of articles.')
    st.write('Conducting automated handsearching for', iter_num,'iteratons, for following seed ids:',seed_id)
    
    
    #add parallelism here
    for i in range(iter_num): 
        handsearch_instance = automated_handsearch(semantic_scholar_key)
        result_dedupe = handsearch_instance.backwards_forwards_citation(seed_id)
        st.write('Iteration complete')
        if iter_num >1:
            seed_id = result_dedupe['paper_Id'] 
            st.write('Now retrieving for next iteration, for following seed_ids: ', seed_id)
            print('Now retrieving for next iteration, for following seed_ids: ', seed_id)
    
    #add parallelism here
            
    #check whether we have any missing abstracts, and fix if possible via obtaining DOI from semantic scholar and contacting OpenAlex
    if result_dedupe['paper_Abstract'].isnull().values.any() == True: 
        print('missing abstracts found from Semantic Scholar API. Retrieving DOIs')
        
        #obtain DOI from semantic scholar 
        missing_abs_semantic_scholar_ID= handsearch_instance.obtain_doi_missing_abs(result_dedupe)
        #retrieve abstracts from OpenAlex 
        print('Contacting OpenAlex to retrieve abstracts for a total of ', len(missing_abs_semantic_scholar_ID), 'articles')
        missing_abs_semantic_scholar_ID['abstract']=missing_abs_semantic_scholar_ID['DOI'].apply(handsearch_instance.retrieve_openalex_abs)
        fixed_article_df = missing_abs_semantic_scholar_ID
        retrieved_abs = fixed_article_df
        retrieved_abs_index_list = retrieved_abs.index.tolist()
        retrieved_abs_abstract_list = retrieved_abs['abstract'].tolist()
        result_dedupe.loc[retrieved_abs_index_list,"paper_Abstract"] = retrieved_abs_abstract_list


    st.write('Handsearching done over', iter_num, ' iteration(s). We found a total of: ', len(result_dedupe), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')
    st.write('Results: ', result_dedupe)

    results_csv = result_dedupe.to_csv().encode('utf-8')

    st.write('Metadata retrieval done 🎉. Download ready as CSV file. For reference the encoding is in UTF-8. ', key='Download Results')
    st.download_button(
        label = 'Download results as CSV file',
        data = results_csv,
        file_name = 'automated_handsearch_results.csv',
        mime='text/csv',
    )
    