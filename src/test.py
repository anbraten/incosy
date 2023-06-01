import incosy
import dotenv
import json

dotenv.load_dotenv()


def main():
    # vectorstore = incosy.get_vector_store()
    chat = incosy.open_chat()
    print("Type 'exit' to exit, 'reset' to reset the chatbot.")

    print("Bot: Did you had any problems in your last shift?")
    while True:
        input_text = input("You: ")
        if input_text == "exit":
            break
        if input_text == "reset":
            chat.reset()
            continue
        if input_text == "":
            input_text = "I often have back pain when lifting patients from their beds into a wheelchair."
            print("You: " + input_text)
        response = chat({"input": input_text})
        # prompt = incosy.get_best_product_prompt()
        # response = prompt.format(input=input_text)
        # print(response)
        print("Bot: ")
        print(json.dumps(response, indent=2))


if __name__ == '__main__':
    main()
