import pandas as pd 

class demo_article: 

    def __init__(self): 
        self.demo_title = ['Systematic review automation technologies']
                                  
        self.demo_doi = ['10.1186/2046-4053-3-74']
    def load_seed_article_data(self): 

        seed_article_zip = list(zip(self.demo_doi,self.demo_title,))
        seed_article_demo = pd.DataFrame(seed_article_zip, columns = ['seed_Id','seed_Title'])
        return seed_article_demo
  

#original demo amount of articles  
    

# self.demo_title = ['Systematic review automation technologies',
#                 'Text mining for search term development in systematic reviewing: A discussion of some methods and challenges',
#                 'Toward systematic review automation: a practical guide to using machine learning tools in research synthesis',
#                 'Editorial: Systematic review automation thematic series',
#                 'A question of trust: can we build an evidence base to gain trust in systematic review automation technologies?',
#                 'Using text mining for study identification in systematic reviews: a systematic review of current approaches', 
#                 'Automating data extraction in systematic reviews: a systematic review',
#                 'Automation of systematic literature reviews: A systematic literature review'
#                 'Data extraction methods for systematic review (semi)automation: A living systematic review'
#                 'Tools to support the automation of systematic reviews: a scoping review'
#                 ]
                
# self.demo_doi = ['10.1186/2046-4053-3-74','10.1002/jrsm.1250','10.1186/s13643-019-1074-9','10.1186/s13643-019-0974-z','10.1186/s13643-019-1062-0','10.1186/2046-4053-4-5',
#             '10.1186/s13643-015-0066-7','10.1016/j.infsof.2021.106589','10.12688/f1000research.51117.1','10.1016/j.jclinepi.2021.12.005'] 
