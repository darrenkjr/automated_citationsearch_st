import pandas as pd
from automated_handsearch import automated_handsearch

semantic_scholar_key =  'KOh3wE4IBn21HkRsU49Ya4JT93KrwyPv4PV37Vry'
article_title = ['Systematic review automation technologies','Text mining for search term development in systematic reviewing: A discussion of some methods and challenges']
article_doi = ['10.1186/2046-4053-3-74','10.1002/jrsm.1250']
article_df = pd.DataFrame(list(zip(article_doi,article_title,)), columns = ['seed_Id','seed_Title'])

#test class instantiation, expected output seed IDs and articles 
def automated_handsearch_instance(article_df, semantic_scholar_key):
    handsearch_instance = automated_handsearch(article_df, semantic_scholar_key)
    print (handsearch_instance.seed_article_df)
    print('Test #1 Done')
automated_handsearch_instance(article_df, semantic_scholar_key)

#test class instantiation, and backwards and forwards citation mining. Expected output = deduplicated results, and printed output of missing abstracts
def automated_handsearch_instance(article_df, semantic_scholar_key):
    handsearch_instance = automated_handsearch(article_df, semantic_scholar_key)
    results = handsearch_instance.backwards_forwards_citation()
    results.to_csv('testing_2.csv')
    print('Test #2 done.')
automated_handsearch_instance(article_df, semantic_scholar_key)



