import os
import json
import streamlit as st
import re


def split_text(text):
    # Split the text into lines
    lines = text.splitlines() 

    # Ensure there are at least two lines
    if len(lines) >= 3:
        first_line = "Document ID: " + lines[0].strip() + "\n" # Strip any leading/trailing whitespace
        second_line = "Title: " + lines[1].strip() + "\n"  # Strip any leading/trailing whitespace
        third_line = "Date: " + lines[2].strip() + "\n"
        other_lines = "Content: " + "\n".join(line.strip() for line in lines[3:])  # Join other lines with newline

        return first_line + second_line + third_line + other_lines
    
    else:
        return None  # Empty strings for all lines if no lines are present



# Implement the search_documents function
def search_documents(query):
    # Get the path to the JSON file
    file_path = os.path.join(os.getcwd(), "dataset", "all_docs.json")
    
    # Load the JSON data
    with open(file_path, "r") as json_file:
        data_dict = json.load(json_file)

    relevant_document = None
    for doc_id, doc_content in data_dict.items():
        
        if query == doc_id:
            relevant_document = doc_id + "\n" + doc_content
            relevant_document = split_text(relevant_document)
            break
    
    with st.container():
        if relevant_document:
            # Display the results in a text area to ensure uniform formatting and box
            st.text_area("Result", relevant_document, height=900)
        else:
            st.text_area("Result", "No relevant documents found.", height=50)

    # return ""
    
