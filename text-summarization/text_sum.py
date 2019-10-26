import numpy as np
import string 

from bert_serving.client import BertClient
from sklearn.metrics.pairwise import cosine_similarity

import nltk
import networkx as nx
from nltk.tokenize import sent_tokenize
nltk.download('punkt')

with open('sample.txt') as text_sample:
    data = text_sample.read()

class TextSummarizer(object):
    def __init__(self, text):
        super().__init__()
        self.text = text
        # Split text into sentences 
        self.sentences = sent_tokenize(self.text) 
        self.length = len(self.sentences)
        self.bc = BertClient()

    def remove_punctuation(self, sentence):
        return sentence.translate(str.maketrans('', '', string.punctuation))

    def lowercase_text(self):
        # lower case all words in sentences 
        for idx,sentence in enumerate(self.sentences):
            lower_cased_tokens = [word.lower() for word in sentence.split()]
            lower_cased_sentence = " ".join([word for word in lower_cased_tokens])
            sent_without_punct = self.remove_punctuation(lower_cased_sentence)
            self.sentences[idx] = sent_without_punct.strip()
    
    def get_embeddings(self):
        self.embeddings = self.bc.encode(self.sentences)

    def build_similarity_matrix(self):
        self.similarity_matrix = np.zeros([self.length, self.length])
        for i in range(self.length):
            for j in range(self.length):
                if i != j:
                    self.similarity_matrix[i][j] = cosine_similarity([self.embeddings[i]], [self.embeddings[j]])

    def get_important_sentences(self):
        nx_graph = nx.from_numpy_array(self.similarity_matrix)
        print("Running pagerank")
        scores = nx.pagerank(nx_graph)
        ranked_sentences = sorted(((scores[i],s) for i,s in enumerate(self.sentences)), reverse=True)
        print("\n")
        for i in range(10):
            print("> "+ranked_sentences[i][1]+"\n")

    def get_summary(self):
        print("Cleaning text input")
        self.lowercase_text()
        print("Generating embeddings")
        self.get_embeddings()
        print("Building similarity matrix")
        self.build_similarity_matrix()
        print("Getting similarity scores")
        self.get_important_sentences()

ts = TextSummarizer(data)
ts.get_summary()