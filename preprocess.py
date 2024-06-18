import os
import json
import random
import pickle
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import streamlit as st

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

file_path = os.path.join(os.getcwd(), "dataset", "all_docs.json")

RELATED_DOCUMENTS = ["2385", "3212", "3740", "3040", "3662", "4080", "1785", "3435", "1878", "1030", "1038", "3295"]
FALSE_LEADS = ["0926", "3630", "0783", "1088", "0383", "0129", "0639", "1671", "3231", "2287", "4293", "2395", "0499", "4312", "3232", "2243", "3665", "0878", "3375", "4156", "1482", "1594", "2696", "0432", "4314", "0008", "3563", "1750", "2900", "1243", "0274", "3772", "3874", "2664", "3237"]


with open(file_path, 'r') as json_file:
    data_dict = json.load(json_file)

n = 200  # generating random numbers
RAND_DOCS = random.sample(list(data_dict.keys()), n - len(RELATED_DOCUMENTS) - len(FALSE_LEADS))

filtered_docs = ["VAST 2011 Mini-Challenge 3 Dataset"]

for k, v in data_dict.items():
    if k in set(RELATED_DOCUMENTS + RAND_DOCS + FALSE_LEADS):
        v = f"Document ID: {str(k)}\n{v}"
        filtered_docs.append(v)

print(f"Total Number of documents: {len(filtered_docs)-1}")


# Assuming OPENAI_API_KEY is defined somewhere in your environment or code
db = FAISS.from_texts(
    filtered_docs, embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
)


# Save the db object to a file
db.save_local("./dataset/faiss_index_low")


