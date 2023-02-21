import pandas as pd
import re
from demo.demo_module import demo_article
from app_functions import run_handsearch
import streamlit as st

#defining streamlit parameters
demo_cls = demo_article()
seed_article_df_example = demo_cls.load_seed_article_data()

st.title('Automated Handsearch - Proof of Concept Demo - Part of the Automated Evidence Synthesis Stack')

st.write('Hi There! This is a web app (note: Highly Experimental!) that conducts automated handsearching as part of evidence retrieval in evidence synthesis tasks. For example, for systematic reviews, evidence based guideline development etc.'
)
st.write('Handsearching involves looking through the reference section of an article (Backward citation) and also all papers that have cited the starting article (Forward citation) as a means to obtain potentiallly relevant articles for a given research question or evidence synthesis task. This is also known as snowballing.')
st.write('Under the hood we are querying the Semantic Scholar Application Programming Interface, which holds a database of over 200 million papers, from a range of sources, including PubMed, Preprint servers, and Microsoft Academic Graph. We recently added support for OpenAlex as well which has comparable coverage.')
st.write('This is part of a doctoral project investigating how to incorporate AI and automation into evidence synthesis, and work is underway in emperically investigating best practice in utilising automated citation searching during evidence retrieval.')
st.write('If this tool is useful, we would love for you to cite us at [Link]. Feedback is always welcome, alongside bug / issue reports. Please send these to darren.rajit1@monash.edu')
st.write('---')
st.write('### Step 1: Select your database of choice')

api =st.radio(
    "Choice of database:", ('Semantic Scholar','OpenAlex - New!'))


st.write('---')

st.write('### Step 2a : Input Starting Set of Articles (Pearls) / Seed Articles)')
st.write('1. Provide a CSV file with your initial starting set of articles, with article DOI and article Title.')
st.write('2. There must be 2 columns. Named seed_Id, and seed_Title (case-sensitive)')



st.write('3. We have prepared an example of required formatting as below.', seed_article_df_example)
st.write('*For best results, choose articles that you would expect to be influential in your research question. For example, influential trials, systematic reviews and perspective pieces.*')

uploaded_file = st.file_uploader('Upload CSV file', key='user_starting_article_input')

st.write('---')
st.write('### Step 2b. Alternatively, you can try out our demo set of articles:')


input_df = pd.DataFrame()
if st.button('Use demo articles.', key='example_starting_article_input'): 
    st.write('Using demo starting article set. Loading data in..')
    input_df = seed_article_df_example
    run_handsearch(api,input_df)
    # if iter_num ==1: 
    #     
    # elif iter_num == 2:
    #     st.write('Conducting handsearch for 2 iterations. This may take a while.')
    #     ## implement loop 
    
if uploaded_file is not None: 

    # if iter_num ==1: 
    input_df = pd.read_csv(uploaded_file)
    run_handsearch(api, input_df)
    # elif iter_num == 2:
        # print('Conducting handsearch for 2 iterations. This may take a while.')
        # seed_article_df = pd.read_csv(uploaded_file) 
        ## implement loop 

