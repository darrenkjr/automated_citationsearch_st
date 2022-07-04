import pandas as pd
import re
from demo.demo_module import demo_article
from app_functions import run_handsearch
import streamlit as st

#defining streamlit parameters
demo_cls = demo_article()
seed_article_df_example = demo_cls.load_seed_article_data()

st.title('Automated Handsearch - Proof of Concept Demo - Part of the Automated Evidence Synthesis Stack')

st.write('Hi There! This is a web app that conducts automated handsearching as part of evidence retrieval in evidence synthesis tasks. For example, things like systematic reviews, scoping reviews and more.'
)
st.write('Handsearching involves looking through the reference section of an article (Backward citation) and also all papers that have cited the starting article (Forward citation) as a means to obtain potentiallly relevant articles for a given research question or evidence synthesis task. This is also known as snowballing.')
st.write('Under the hood we are querying the Semantic Scholar Application Programming Interface, which holds a database of over 200 million papers, from a range of sources, including PubMed, Preprint servers, and Microsoft Academic Graph')
st.write('This is part of an overarching protocol to develop and evaluate automated methods to streamline evidence synthesis : [Protocol here]')
st.write('If this tool is useful, we would love for you to cite us at [Link]. We are tracking the use of this tool as a means to understand whether handsearching should form best practice in evidence retrieval. We are developing software to extract data from PRISMA diagrams, and hope to release this publically soon. Citing us would mean that we can systematically study how citation based methods perform in combination with traditional search strategies.')
st.write('### Step 1 : Input Starting Set of Articles')
st.write('Instructions:')
st.write('1. Provide a CSV file with your initial starting set of articles, with article DOI and article Title.')
st.write('2. There must be 2 columns. Named seed_Id, and seed_Title')
st.write('3. We have prepared an example of required formatting as below.', seed_article_df_example)
st.write('*For best results, choose articles that you would expect to be influential in your research question. For example, influential trials, systematic reviews and perspective pieces.*')


uploaded_file = st.file_uploader('Upload starting set of articles as CSV file', key='user_starting_article_input')

iter_option =st.radio(
    "Select number of snowball / handsearch iterations you would like:", (1,2))

if iter_option == 1: 
    iter_num = 1
elif iter_option ==2: 
    iter_num = 2


if st.button('Use demonstration starting articles', key='example_starting_article_input'): 
    st.write('Using demo starting article set. Loading data in..')
    if iter_num ==1: 
        run_handsearch(seed_article_df_example)
    elif iter_num == 2:
        st.write('Conducting handsearch for 2 iterations. This may take a while.')
        ## implement loop 
    
if uploaded_file is not None: 

    if iter_num ==1: 
        seed_article_df = pd.read_csv(uploaded_file)
        run_handsearch(seed_article_df)
    elif iter_num == 2:
        print('Conducting handsearch for 2 iterations. This may take a while.')
        seed_article_df = pd.read_csv(uploaded_file) 
        ## implement loop 

