import os, streamlit as st

from llama_index import SimpleDirectoryReader, LLMPredictor, PromptHelper, ServiceContext, GPTVectorStoreIndex, StorageContext, load_index_from_storage
from langchain.llms.openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

index = None
index_dir = "./index"

def initialize_index():
    global index

    if index is not None:
        return

    storage_context = StorageContext.from_defaults(persist_dir=index_dir)
    if os.path.exists(index_dir):
        index = load_index_from_storage(storage_context)
    else:
        llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003"))

        # Configure prompt parameters and initialise helper
        max_input_size = 4096
        num_output = 256
        max_chunk_overlap = 20
        prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)

        documents = SimpleDirectoryReader("./data").load_data()
        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
        index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context, service_context=service_context)
        storage_context.persist(index_dir)

st.title("InCosy")
query = st.text_input("How was your last shift?", "")

# If the 'Submit' button is clicked
if st.button("Submit"):
    if not query.strip():
        st.error(f"Please provide the search query.")
    else:
        try:
            initialize_index()
            query_engine = index.as_query_engine()
            response = query_engine.query(query)
            st.success(response)
        except Exception as e:
            st.error(f"An error occurred: {e}")