import os, streamlit as st

from llama_index import SimpleDirectoryReader, LLMPredictor, PromptHelper, ServiceContext, GPTVectorStoreIndex, StorageContext, load_index_from_storage
from langchain.llms.openai import OpenAI
import os
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

index_dir = "./index"

def initialize_index():
    if os.path.exists(index_dir+"/docstore.json"):
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        return load_index_from_storage(storage_context)
    else:
        storage_context = StorageContext.from_defaults()
        llm = OpenAI(temperature=0, model_name="text-davinci-003")
        llm_predictor = LLMPredictor(llm=llm)

        # Configure prompt parameters and initialise helper
        max_input_size = 4096
        num_output = 256
        max_chunk_overlap = 20
        prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)

        documents = SimpleDirectoryReader("./data").load_data()
        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
        index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context, service_context=service_context)
        storage_context.persist(index_dir)
        return index

index = initialize_index()


app = Flask(__name__)

@app.route("/query", methods=['POST'])
def query():
    print(request)
    input_text = request.form['query']
    query_engine = index.as_query_engine()
    response = query_engine.query("Please suggest a comma separated list of products helping with the following problem in a nursing home:" + input_text)
    return response
