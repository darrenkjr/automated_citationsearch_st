## script adapted from: https://github.com/svidmar/OpenAlex2RIS/blob/main/ris_from_doi.py

openalex_to_ris_type_mapping = {
    'article': 'JOUR',
    'book-chapter': 'CHAP',
    'book': 'BOOK',
    'dissertation': 'THES',
    'report': 'RPRT',
    'editorial': 'JOUR',
    'letter': 'JOUR',
}

def reconstruct_abstract_from_inverted_index(inverted_index):
    """Reconstruct abstract text from an inverted index if available."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return "" 
    
    word_positions = [(word, pos) for word, positions in inverted_index.items() for pos in positions]
    sorted_word_positions = sorted(word_positions, key=lambda x: x[1])
    
    words_in_order = [word for word, pos in sorted_word_positions]
    return " ".join(words_in_order)

def format_ris(metadata):
    """Format an OpenAlex metadata dictionary into an RIS string."""
    ris_type = openalex_to_ris_type_mapping.get(metadata.get('type', ''), 'GEN') 
    ris_content = f"TY  - {ris_type}\n"
    ris_content += f"T1  - {metadata.get('title', 'No title available')}\n"
    
    primary_location = metadata.get('primary_location', {})
    source = primary_location.get('source', {}) if isinstance(primary_location, dict) else None
    
    if isinstance(source, dict):
        journal_name = source.get('display_name', '')
        if journal_name:
            ris_content += f"T2  - {journal_name}\n"
        
        issn_l = source.get('issn_l', '')
        if issn_l:
            ris_content += f"SN  - {issn_l}\n"
        else:
            issns = source.get('issn', [])
            if issns:
                ris_content += f"SN  - {issns[0]}\n"
    
    for author in metadata.get('authorships', []):
        author_name = author.get('author', {}).get('display_name', 'No author name')
        ris_content += f"A1  - {author_name}\n"
    
    if 'publication_year' in metadata:
        ris_content += f"PY  - {metadata['publication_year']}\n"
    

    biblio = metadata.get('biblio', {})
    if biblio:
        if biblio.get('volume'):
            ris_content += f"VL  - {biblio.get('volume')}\n"
        if biblio.get('issue'):
            ris_content += f"IS  - {biblio.get('issue')}\n"
        if biblio.get('first_page') and biblio.get('last_page'):
            ris_content += f"SP  - {biblio.get('first_page')}\n"
            ris_content += f"EP  - {biblio.get('last_page')}\n"
    
    if 'doi' in metadata and metadata['doi']:

        ris_content += f"DO  - {metadata.get('doi', '')}\n"
    
    if 'language' in metadata and metadata['language']:
        ris_content += f"LA  - {metadata.get('language', '')}\n"
    
    for keyword in metadata.get('keywords', []):
        keyword_text = keyword.get('keyword', '')
        if keyword_text:
            ris_content += f"KW  - {keyword_text}\n"
    
    oa_url = metadata.get('open_access', {}).get('oa_url', '')
    if oa_url:
        ris_content += f"L2  - {oa_url}\n"
    

    if metadata.get('abstract') and isinstance(metadata['abstract'], str):
         ris_content += f"AB  - {metadata['abstract']}\n"
    elif 'abstract_inverted_index' in metadata:
        abstract = reconstruct_abstract_from_inverted_index(metadata['abstract_inverted_index'])
        if abstract:
            ris_content += f"AB  - {abstract}\n"
    
    ris_content += "ER  - \n"
    return ris_content