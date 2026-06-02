import pandas as pd
import re
import datetime
from demo.demo_module import demo_article
from app_functions import run_handsearch
import streamlit as st
import asyncio
from libraries.oa_to_ris import *

#defining streamlit parameters
demo_cls = demo_article()
seed_article_df_example = demo_cls.load_seed_article_data()
results = pd.DataFrame()

st.title('Automated Citation Searching - Proof of Concept Demo')

st.write('Hi There! This is a web app (**note: Highly Experimental!**) that conducts automated citation searching as part of evidence retrieval in evidence synthesis tasks. For example, for systematic reviews, evidence based guideline development etc.'
)
st.write('Citation searching involves looking through the reference section of an article (Backward citation) and also all papers that have cited the starting article (Forward citation) as a means to obtain potentiallly relevant articles for a given research question or evidence synthesis task. This is also known as snowballing.')
st.markdown('The following bibliographic databases are supported: OpenAlex [1], and Semantic Scholar [2], both of which have coverage of over 200 million articles.')

st.write('This is part of a doctoral project investigating how to incorporate AI and automation into evidence synthesis, including investigating best practice in utilising automated citation searching during evidence retrieval [3].')

st.write('If you find this tool useful, we would love for you to cite us at: https://doi.org/10.1017/rsm.2024.15. Feedback is always welcome, alongside bug / issue reports. Please send these to darren.rajit1@monash.edu')

# display warning header for rate limits and potential instability 
st.warning('Please note that there are rate limits on the APIs we are using. If you encounter any issues or instability, please try again later.')
st.write('---')
st.write('### Step 1: Select your database of choice')

col1, col2 = st.columns(2)
with col1:
    st.button("OpenAlex (Active)", use_container_width=True, type="primary")
with col2:
    st.button("Semantic Scholar (Disabled)", use_container_width=True, disabled=True, help="Semantic Scholar is currently disabled.")

api = 'OpenAlex'


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
    ("Upload your own CSV file", "Upload your own RIS file", "Use demo articles")
)

input_df = pd.DataFrame()

if input_option == "Upload your own CSV file":
    uploaded_file = st.file_uploader('Upload CSV file', key='user_starting_article_input', type=['csv'])
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)
        if set(input_df.columns) != set(['seed_Id', 'seed_Title']):
            st.error("Error: Your CSV file doesn't have the correct columns. Please ensure it has 'seed_Id' and 'seed_Title' columns.")
        else:
            st.write("Uploaded file preview:")
            st.dataframe(input_df)
elif input_option == "Upload your own RIS file":
    uploaded_file = st.file_uploader('Upload RIS file', key='user_starting_article_input_ris', type=['ris', 'txt'])
    if uploaded_file is not None:
        import rispy
        import io
        
        try:
            # Read and parse RIS file
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8", errors='replace'))
            entries = rispy.load(stringio)
            
            # Extract DOI and Title
            data = []
            for entry in entries:
                doi = entry.get('doi', '')
                title = entry.get('title', '')
                
                # Clean up the DOI if it's formatted as a URL
                if doi and doi.startswith('http'):
                    # e.g., https://doi.org/10.1016/j...
                    doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
                
                # We need an ID. DOI is required for citation searching if no OpenAlex ID is present.
                if doi:
                    data.append({'seed_Id': doi, 'seed_Title': title})
            
            input_df = pd.DataFrame(data)
            
            if input_df.empty:
                st.error("No valid DOIs found in the uploaded RIS file. Automated citation search currently requires DOIs to identify seed articles.")
            else:
                st.success(f"Successfully extracted {len(input_df)} articles with DOIs from the RIS file.")
                st.write("Extracted file preview:")
                st.dataframe(input_df)
                
        except Exception as e:
            st.error(f"Error parsing RIS file: {str(e)}")
elif input_option == "Use demo articles":
    input_df = demo_cls.load_seed_article_data()
    st.write("Demo articles:")
    st.dataframe(input_df)


st.write('---') 
st.write('### Step 3 : Conduct automated citation searching and deduplication based on your initial set of articles.')

# Search filters expander
filters = {}
with st.expander("🔍 Search Filters (Optional)", expanded=False):
    st.write("Apply filters to narrow down the retrieved citations and references. (Note: These filters are applied to OpenAlex; Semantic Scholar remains unfiltered).")
    
    # 1. Date Filter
    enable_date_filter = st.checkbox("Filter by Publication Date (From)", value=False, help="Only retrieve papers published on or after the specified date.")
    if enable_date_filter:
        from_date = st.date_input("From Publication Date", value=datetime.date(2022, 8, 1))
        filters['from_publication_date'] = from_date.strftime("%Y-%m-%d")
        
    # 2. Language Filter
    enable_lang_filter = st.checkbox("Filter by Language", value=False, help="Only retrieve papers in the specified language.")
    if enable_lang_filter:
        lang_options = {
            "English (en)": "en",
            "Spanish (es)": "es",
            "French (fr)": "fr",
            "German (de)": "de",
            "Chinese (zh)": "zh",
            "Other (specify code)": "custom"
        }
        selected_lang = st.selectbox("Select Language", list(lang_options.keys()))
        if lang_options[selected_lang] == "custom":
            custom_lang = st.text_input("Enter 2-letter language code (e.g. en, es, fr):", value="en", max_chars=2)
            filters['language'] = custom_lang.strip().lower()
        else:
            filters['language'] = lang_options[selected_lang]
            
    # 3. Work Type Filter
    enable_type_filter = st.checkbox("Filter by Work Type", value=False, help="Restrict retrieval to certain types of works (e.g., articles).")
    if enable_type_filter:
        type_options = ["article", "book-chapter", "book", "preprint", "dataset", "report"]
        filters['type'] = st.selectbox("Select Work Type", type_options, index=0)
    else:
        filters['type'] = "Any"
        
    # 4. Require Abstract
    require_abstract = st.checkbox("Require Abstract", value=False, help="Only retrieve papers that have an abstract available.")
    filters['has_abstract'] = True if require_abstract else None

if not input_df.empty:
    if st.button('Run citation search', disabled=False):
        #placeholder for iteration number - multiple iterations are coming soon (but this will require some extensive testing)
        st.session_state.iter_num = 1
        st.session_state.results = asyncio.run(run_handsearch(api, input_df, st.session_state.iter_num, filters=filters))
        
        st.write("Results:")
        display_df = st.session_state.results.drop(columns=['raw_oa_dict'], errors='ignore')
        st.dataframe(display_df)
else: 
    st.button('Run citation search', disabled=True)


st.write('---')
st.write('### Step 4: Download results')

if 'results' in st.session_state and not st.session_state.results.empty:
    
    st.write('Citation searching done over',  st.session_state.iter_num, ' iteration. We found a total of: ', len(st.session_state.results), 'unique articles based on your initial sample size of ', len(input_df), 'articles.')

    st.write('Metadata retrieval successful 🎉. Download now ready!')

    # Create two columns for the download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download (always available)
        csv_df = st.session_state.results.drop(columns=['raw_oa_dict'], errors='ignore')
        st.download_button(
            disabled=False,
            label='Download as CSV',
            data=csv_df.to_csv(index=False).encode('utf-8'),
            file_name='automated_citation_search_results.csv',
            mime='text/csv',
            help='Download results as CSV file (compatible with Excel, Google Sheets, etc.)'
        )
    
    with col2:
        # RIS download (conditional)
        if api == 'OpenAlex':
            from app_functions import export_to_ris
            ris_content = export_to_ris(st.session_state.results, api)
            
            if ris_content:
                st.download_button(
                    disabled=False,
                    label='Download as RIS',
                    data=ris_content.encode('utf-8'),
                    file_name='automated_citation_search_results.ris',
                    mime='text/plain',
                    help='Download results as RIS file (compatible with EndNote, Zotero, Mendeley, etc.)'
                )
            else:
                st.download_button(
                    disabled=True,
                    label='Download as RIS',
                    data='',
                    file_name='automated_citation_search_results.ris',
                    mime='text/plain',
                    help='RIS generation failed. Please try again.'
                )
        else:  # Semantic Scholar
            st.download_button(
                disabled=True,
                label='Download as RIS',
                data='',
                file_name='automated_citation_search_results.ris',
                mime='text/plain',
                help='RIS export not yet supported for Semantic Scholar. Please use CSV download instead.'
            )
    
    # Add explanatory text below the buttons
    if api == 'Semantic Scholar':
        st.info("**Note:** RIS export is not yet supported for Semantic Scholar. Please use the CSV download option, which you can import into reference management software.")

else:
    st.write('No results available for download yet. Please run the citation search first.')
    
    # Show disabled download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label='Download as CSV',
            data='',
            file_name='automated_citation_search_results.csv',
            mime='text/csv',
            disabled=True
        )
    
    with col2:
        st.download_button(
            label='Download as RIS',
            data='',
            file_name='automated_citation_search_results.ris',
            mime='text/plain',
            disabled=True
        )

# Add this in a sidebar
with st.sidebar:
    st.header("App Controls")
    
    if st.button('🔄 Reset App & Run New Search'):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Show current status
    if 'results' in st.session_state:
        st.info(f"Current results: {len(st.session_state.results)} articles")
    else:
        st.info("No results yet")

st.markdown("""
---
### References
[1] Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. ArXiv. https://arxiv.org/abs/2205.01833

[2] Kyle Lo, Lucy Lu Wang, Mark Neumann, Rodney Kinney, Dan S. Weld (2020). S2ORC: The Semantic Scholar Open Research Corpus. ArXiv. https://arxiv.org/abs/1911.02782

[3] Rajit D, Du L, Teede H, Enticott J. Automated citation searching in systematic review production: A simulation study. Research Synthesis Methods. 2025;16(1):211-227. doi:10.1017/rsm.2024.15 
""")
