import os
from dotenv import load_dotenv
from flask import Flask, request
import random
import string
import incosy
import json
import yaml
import requests

load_dotenv()


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


# scrape.scrape()
# vectorstore = incosy.get_vector_store()
chats = dict()
app = Flask(__name__)


@app.route("/chat/start", methods=['POST'])
def start_chat():
    chat_id = get_random_string(8)
    chats[chat_id] = incosy.open_chat()
    return chat_id


@app.route("/chat/query", methods=['POST'])
def query():
    input_text = request.args.get('query')
    if input_text is None:
        return "No query provided"
    chat_id = request.args.get('chat_id')
    if chat_id is None:
        return "No chat_id provided"
    if chat_id not in chats:
        return "No chat found for chat_id " + chat_id
    chat = chats[chat_id]
    print("asking chat"+chat_id+": "+input_text)
    response = chat({"input": input_text})
    print(json.dumps(response, indent=2))
    return response


@app.route("/chat/stop", methods=['POST'])
def stop_chat():
    chat_id = request.args.get('chat_id')
    if chat_id is None:
        return "No chat_id provided"
    del chats[chat_id]
    return "ok"


@app.route("/reset", methods=['POST'])
def reset_chats():
    global agents
    agents = dict()
    return "ok"


@app.route("/product", methods=['GET'])
def get_product():
    requested_product = request.args.get('product').strip()

    file = open("database.yml")
    database = yaml.load(file, Loader=yaml.FullLoader)
    for product in database['products']:
        if product['name'] == requested_product:
            return product

    return "Product not found"


@app.route("/product/suggest", methods=['POST'])
def suggest_product():
    baseUrl = "https://budibase.app/api/public/v1/"
    url = baseUrl + "tables/" + \
        os.getenv("BUDIBASE_SUGGESTIONS_TABLE_ID") + "/rows"

    data = {
        "problem": request.args.get('problem').strip(),
        "suggestion": request.args.get('suggestion').strip(),
        "status": "open",
    }

    headers = {
        'x-budibase-app-id': os.getenv("BUDIBASE_APP_ID"),
        'x-budibase-api-key': os.getenv("BUDIBASE_API_KEY"),
    }

    response = requests.post(url, json=data, headers=headers)
    print(response.status_code)
    return "ok"
