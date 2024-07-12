
"""
construct a semantic search index using the vector embeddings of articles downloaded
from the arxiv

"""

import os
import openai
from pinecone import Pinecone, ServerlessSpec


import PyPDF2
import pdfplumber

openai.api_key = os.getenv("OPENAI_API_KEY")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "tao-search"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    ) #dimension for text-embedding-3-small

index = pc.Index(index_name)
def extract_text_from_pdf(file_path):
    pypdf2_text = ""
    pdfplumber_text = ""

    # Using PyPDF2 to extract text
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            pypdf2_text += page.extract_text() or ""

    # Using pdfplumber to extract text
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pdfplumber_text += page.extract_text() or ""

    # Determine the best text extraction
    if len(pdfplumber_text) > len(pypdf2_text):
        return pdfplumber_text
    else:
        return pypdf2_text

def divide_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_embeddings(text_chunks):
    embeddings = []
    for chunk in text_chunks:
        response = openai.embeddings.create(input=[chunk], model="text-embedding-3-small")
        embeddings.append(response.data[0].embedding)
    return embeddings


def read_file_in_chunks(file_path, chunk_size=500):
    with open(file_path, 'r') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

def create_semantic_search_index(directory_path):
    n = 0
    for file_name in os.listdir(directory_path):
        print(file_name, n)
        n +=1
        file_path = os.path.join(directory_path + '/' + file_name)
        text = extract_text_from_pdf(file_path)
        chunks = divide_text(text)
        print('number of chunks', len(chunks))
        embeddings= get_embeddings(chunks)
        vectors = [(f"{file_name}_{i}", embedding) for i, embedding in enumerate(embeddings)]
        index.upsert(vectors, namespace="ns2")

def search_pinecone(query):
    query_embedding = get_embeddings([query])[0]
    result = index.query(namespace="ns2", vector=[query_embedding], top_k=5)
    return result

def get_text_snippet(query_result):
    files = [result['id'] for result in query_result['matches']]
    results = {'matches':[]}
    for result in query_result['matches']:
        filename, number = result['id'].split('_') #important don't delete the newline
        number = int(number)
        dirpath = 'text_files/terence_tao'
        text = extract_text_from_pdf(dirpath + '/' + filename)
        snippet = divide_text(text)[number]
        obj = {
            'filename': filename,
            'number': number,
            'text': text
        }
        results['matches'].append(obj)
    return results

def main():
    directory_path = 'text_files/terence_tao'
    #create_semantic_search_index(directory_path)
    query = "what is the Navier-stokes equation? Does it relate to black holes and the black scholes equation conjecture?"
    # time.sleep(30)
    search_result = search_pinecone(query)
    results = get_text_snippet(search_result)
    print(query)
    print(search_result)
    print(results)

if __name__ == "__main__":
    main()