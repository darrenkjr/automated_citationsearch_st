import sys 
sys.path.append('../automated_evidence_retrieval_study')
from main import experiment

experiment = experiment()
original_review_data = experiment.review_prep()
print(original_review_data)


