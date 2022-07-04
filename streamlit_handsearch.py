import pandas as pd
import requests
import re
from automated_handsearch import automated_handsearch
import streamlit as st

#defining streamlit paarameters
semantic_scholar_key =  'KOh3wE4IBn21HkRsU49Ya4JT93KrwyPv4PV37Vry'

st.title('Automated Handsearch - Proof of Concept Demo - Part of the Automated Evidence Synthesis Stack')

st.write('Hi There! This is a web app that conducts automated handsearching as part of evidence retrieval in evidence synthesis tasks. For example, things like systematic reviews, scoping reviews and more.'
)
st.write('Handsearching involves looking through the reference section of an article (Backward citation) and also all papers that have cited the starting article (Forward citation) as a means to obtain potentiallly relevant articles for a given research question or evidence synthesis task. This is also known as snowballing.')
st.write('Under the hood we are querying the Semantic Scholar Application Programming Interface, which holds a database of over 200 million papers, from a range of sources, including PubMed, Preprint servers, and Microsoft Academic Graph')
st.write('This is part of an overarching protocol to develop and evaluate automated methods to streamline evidence synthesis : [Protocol here]')
st.write('If this tool is useful, we would love for you to cite us at [Link]. We are tracking the use of this tool as a means to understand whether handsearching should form best practice in evidence retrieval. We are developing software to extract data from PRISMA diagrams, and hope to release this publically soon. Citing us would mean that we can systematically study how citation based methods perform in combination with traditional search strategies.')


#preparing example seed articles
#move this to a separate demo class 
article_title = ['Systematic review automation technologies',
                      'Text mining for search term development in systematic reviewing: A discussion of some methods and challenges',
                      'Toward systematic review automation: a practical guide to using machine learning tools in research synthesis',
                      'Editorial: Systematic review automation thematic series',
                      'A question of trust: can we build an evidence base to gain trust in systematic review automation technologies?',
                      'Using text mining for study identification in systematic reviews: a systematic review of current approaches', 
                      'Automating data extraction in systematic reviews: a systematic review',
                      'Automation of systematic literature reviews: A systematic literature review'
                      'Data extraction methods for systematic review (semi)automation: A living systematic review'
                      'Tools to support the automation of systematic reviews: a scoping review'
                      ]

article_doi = ['10.1186/2046-4053-3-74','10.1002/jrsm.1250','10.1186/s13643-019-1074-9','10.1186/s13643-019-0974-z','10.1186/s13643-019-1062-0','10.1186/2046-4053-4-5',
                    '10.1186/s13643-015-0066-7','10.1016/j.infsof.2021.106589','10.12688/f1000research.51117.1','10.1016/j.jclinepi.2021.12.005'] 

@st.cache
def load_seed_article_data(seed_article_title,seed_article_doi): 

    seed_article_zip = list(zip(seed_article_doi,seed_article_title,))
    seed_article_demo = pd.DataFrame(seed_article_zip, columns = ['seed_Id','seed_Title'])
    return seed_article_demo

seed_article_df_example = load_seed_article_data(article_title,article_doi)

st.write('### Step 1 : Input Starting Set of Articles')
st.write('Instructions:')
st.write('1. Provide a CSV file with your initial starting set of articles, with article DOI and article Title.')
st.write('2. There must be 2 columns. Named seed_Id, and seed_Title')
st.write('3. We have prepared an example of required formatting as below.', seed_article_df_example)
st.write('*For best results, choose articles that you would expect to be influential in your research question. For example, influential trials, systematic reviews and perspective pieces.*')

def convert_df(df): 
    return df.to_csv().encode('utf-8')

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



# take out this chhunk of code out of this function to prevent app from ending prematurely 
    st.write('Handsearching done over', iter_num, ' iteration. We found a total of: ', len(result_dedupe), 'unique articles based on your initial sample size of ', len(seed_article_df), 'articles.')
    st.write('Results: ', result_dedupe)

    results_csv = convert_df(result_dedupe)

    st.write('Metadata retrieval done 🎉. Download ready as CSV file. For reference the encoding is in UTF-8. ', key='Download Results')
    st.download_button(
        label = 'Download results as CSV file',
        data = results_csv,
        file_name = 'automated_handsearch_results.csv',
        mime='text/csv',
    )
    
  

uploaded_file = st.file_uploader('Upload starting set of articles as CSV file', key='user_starting_article_input')
if st.button('Use demonstration starting articles', key='example_starting_article_input'): 
    st.write('Using demo startingf article set. Loading data in..')
    uploaded_file = seed_article_df_example
    seed_article_df = seed_article_df_example
    run_handsearch(seed_article_df)
    
elif uploaded_file is not None: 
    seed_article_df = pd.read_csv(uploaded_file)
    run_handsearch(seed_article_df)
