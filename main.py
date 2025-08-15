import pandas as pd
import re
from demo.demo_module import demo_article
from app_functions import run_handsearch
import streamlit as st
import asyncio

#defining streamlit parameters
demo_cls = demo_article()
seed_article_df_example = demo_cls.load_seed_article_data()
results = pd.DataFrame()

st.title('Automated Citation Searching - Proof of Concept Demo')

st.write('Hi There! This is a web app (**note: Highly Experimental!**) that conducts automated citation searching as part of evidence retrieval in evidence synthesis tasks. For example, for systematic reviews, evidence based guideline development etc.'
)
st.write('Citation searching involves looking through the reference section of an article (Backward citation) and also all papers that have cited the starting article (Forward citation) as a means to obtain potentiallly relevant articles for a given research question or evidence synthesis task. This is also known as snowballing.')
st.markdown('The following bibliographic databases are supported: OpenAlex [1], and Semantic Scholar [2], both of which have coverage of over 200 million articles.')

st.write('This is part of a doctoral project investigating how to incorporate AI and automation into evidence synthesis, and work is underway in emperically investigating best practice in utilising automated citation searching during evidence retrieval [3].')

st.write('If you find this tool useful, we would love for you to cite us at: https://doi.org/10.26180/26785558.v2. Feedback is always welcome, alongside bug / issue reports. Please send these to darren.rajit1@monash.edu')

# display warning header for rate limits and potential instability 
st.warning('Please note that there are rate limits on the APIs we are using. If you encounter any issues or instability, please try again later.')
st.write('---')
st.write('### Step 1: Select your database of choice')

api =st.radio(
    "Choice of database:", ('OpenAlex','Semantic Scholar'))


st.write('---')

st.write('### Step 2: Provide Seed Articles')

# Show example of required formatting
st.write('#### Required CSV Format:')
st.write('Your CSV file should have two columns: "seed_Id" and "seed_Title" (case-sensitive).')
demo_cls = demo_article()
example_df = demo_cls.load_seed_article_data().head(3)  # Show only first 3 rows as an example
st.write('Example format:')
st.dataframe(example_df)
st.write('*For best results, choose articles that you would expect to be influential in your research question. For example, influential trials, systematic reviews and perspective pieces.*')

input_option = st.radio(
    "Choose your input method:",
    ("Upload your own CSV file", "Use demo articles")
)

input_df = pd.DataFrame()

if input_option == "Upload your own CSV file":
    uploaded_file = st.file_uploader('Upload CSV file', key='user_starting_article_input')
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)
        if set(input_df.columns) != set(['seed_Id', 'seed_Title']):
            st.error("Error: Your CSV file doesn't have the correct columns. Please ensure it has 'seed_Id' and 'seed_Title' columns.")
        else:
            st.write("Uploaded file preview:")
            st.dataframe(input_df)
elif input_option == "Use demo articles":
    input_df = demo_cls.load_seed_article_data()
    st.write("Demo articles:")
    st.dataframe(input_df)


st.write('---') 
st.write('### Step 3 : Conduct automated citation searching and deduplication based on your initial set of articles.')

if not input_df.empty:

    if st.button('Run citation search', disabled=False):
        #placeholder for iteration number - multiple iterations are coming soon (but this will require some extensive testing)
        iter_num = 1
        st.session_state.results = asyncio.run(run_handsearch(api, input_df, iter_num))
        
        st.write("Results:")
        st.dataframe(st.session_state.results)
else: 
    st.button('Run citation search', disabled=True)


st.write('---')
st.write('### Step 4: Download results')

#if results is a non empty dataframe, then download results 
if 'results' in st.session_state and not st.session_state.results.empty:

    st.write('Citation searching done over', iter_num, ' iteration. We found a total of: ', len(st.session_state.results), 'unique articles based on your initial sample size of ', len(input_df), 'articles.')

    st.write('Metadata retrieval sucessful 🎉. Download now ready as CSV file. For reference the encoding is in UTF-8. RIS File Support is comming imminently.')
    st.download_button(
        disabled = False,
        label = 'Download results as CSV file',
        data = st.session_state.results.to_csv().encode('utf-8'),
        file_name = 'automated_citation search_results.csv',
        mime='text/csv',)
    
else:
    st.write('No results available for download yet. Please run the citation search first.')
    st.download_button(
        label='Download results as CSV file',
        data='',
        file_name='automated_citation_search_results.csv',
        mime='text/csv',
        disabled=True
    )
    



st.markdown("""
---
### References
[1] Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. ArXiv. https://arxiv.org/abs/2205.01833

[2] Kyle Lo, Lucy Lu Wang, Mark Neumann, Rodney Kinney, Dan S. Weld (2020). S2ORC: The Semantic Scholar Open Research Corpus. ArXiv. https://arxiv.org/abs/1911.02782

[3] Rajit D, Du L, Teede H, Callander E, Enticott J. Automated Citation Searching in Systematic Review Production: A Simulation Study Protocol and Framework. Authorea Preprints; 2023. DOI: 10.22541/au.169028985.56828301/v1. 
""")
