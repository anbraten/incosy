import pickle
import os
import yaml

from langchain import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.tools import StructuredTool

from langchain.agents import initialize_agent, Tool, AgentType

from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader


def get_vector_store():
    if os.path.exists("vectorstore.pkl"):
        print("Loading vectorstore from file")
        with open("vectorstore.pkl", "rb") as f:
            return pickle.load(f)

    print("Creating vectorstore")
    loaders = [TextLoader("./data/patientenlifter.txt")]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save vectorstore
    with open("vectorstore.pkl", "wb") as f:
        pickle.dump(vectorstore, f)

    return vectorstore


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def get_best_product_prompt():
    file = open("database.yml", "r")
    database = yaml.load(file, Loader=yaml.FullLoader)

    product_list = []
    product_names = []
    for product in database['products']:
        if not 'use_cases' in product:
            print("Product " + product.get('name') +
                  " has no name or use_cases")
            continue
        product_names.append(product.get('name'))
        product_list.append(product.get('name') + ": " +
                            product.get('use_cases').replace('\n', ' ').replace('- ', ''))

    data = SafeDict(product_list='- ' + '\n- '.join(product_list),
                    product_names=', '.join(product_names))

    prompt = """
Suggest products for the following problem of a caregiver of a nursing home as best you can. You have access to the following products and their use cases:

{product_list}

Use the following format:

Question: the input problem to suggest products for
Thought: you should always think what would be the best products to suggest
Products: the products to suggest, should of [{product_names}]
Observation: the result of the suggestion
... (this Thought/Product/Observation can repeat N times)
Thought: I now know the best products to suggest
Final Answer: Maybe one of the following products could help you ...

Begin!

Question: {input}
Thought:
    """.format_map(data).strip()

    return prompt


def open_chat(vectorstore):
    # llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)
    # llm_chat = llm

    llm_chat = ChatOpenAI(
        temperature=0, model_name='gpt-3.5-turbo', verbose=True)
    llm = llm_chat

    product_qa = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            template=get_best_product_prompt(),
            input_variables=["input"],
        ),
    )

    describe = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            template="""You are an AI assistant for caregivers of a nursing home. You are asked to describe a product that can help with a problem in the daily caregiving job.
                You are given the following extracted parts of information about possible products.
                If you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer.
                Question: {input}
                """,
            # input_variables=["input", "chat_history", "agent_scratchpad"],
            input_variables=["input"],
        ),
    )

    buy = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            # template="""You are an AI assistant for caregivers of a nursing home. You are asked to suggest products that can help with a problem in the daily caregiving job.
            # You are given the following extracted parts of information about possible products.
            # If you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer.
            # Question: {input}
            # =========
            # {chat_history}
            # =========
            # Answer:
            # {agent_scratchpad}
            # """,
            template="""You are an AI assistant for caregivers of a nursing home. You are asked to suggest products that can help with a problem in the daily caregiving job.
            You are given the following extracted parts of information about possible products.
            If you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer.
            Question: {input}
            """,
            # input_variables=["input", "chat_history", "agent_scratchpad"],
            input_variables=["input"],
        ),
    )

    tools = [
        Tool(
            name="problem",
            func=product_qa.run,
            description="""useful for when the caregiver is telling us about a problem they have in caregiving""",
            return_direct=True,
        ),
        Tool(
            name="describe",
            func=describe.run,
            description="""useful for when the caregiver is interested in a product and wants to know more about it""",
            return_direct=True,
        ),
        Tool(
            name="buy",
            func=buy.run,
            description="""useful for when the caregiver wants to suggest a product to the home lead""",
            return_direct=True,
        ),
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history", output_key="output")
    memory.chat_memory.add_ai_message(
        "Did you had any problems in your last shift?")

    agent_chain = initialize_agent(
        tools, llm=llm_chat, agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, verbose=True, memory=memory, return_intermediate_steps=True,)

    return agent_chain
