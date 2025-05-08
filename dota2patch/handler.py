import json
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone
from dotenv import load_dotenv


from .fetcher.patch_fetcher import PatchFetcher
from .parser.parse_patch_general_notes import ParsePatchGeneralNotes
from .parser.parse_patch_items import ParsePatchItems
from .parser.parse_patch_heroes import ParsePatchHeroes
from .database.process_data import ProcessData
from .database.pinecone_client import PineconeClient
from .ragchain.retrieval_chain import RetrievalChain
from .query.chat_query import ChatQuery

load_dotenv()


def continually_query_user(chat_query):
    print("Enter your query. Press Ctrl+C to exit.")
    print("\tExample: Tell me about changes to the neutral item Ripper's Lash in patch 7.38c.")
    while True:
        try:
            user_input = input("> ")

            if user_input.strip(): # Check if the input is not just whitespace
                print(f"You entered: '{user_input}'")
                chat_query.ask_question(user_input)
            else:
                print("Please enter a query.")
        except KeyboardInterrupt:
            print("\nCancelled. Exiting program.")
            break

        except EOFError:
            print("\nInput stream closed. Exiting.")
            break

        except Exception as e:
            print(f"An error occurred: {e}")

def get_data():
    patch_fetcher = PatchFetcher()
    parse_patch_general_notes = ParsePatchGeneralNotes()

    patch_api_url = "https://www.dota2.com/datafeed/patchnotes?version=7.38b&language=english"
    patch_data = patch_fetcher.fetch_and_parse_json(patch_api_url)

    item_api_url = "https://www.dota2.com/datafeed/itemlist?language=english"
    item_data = patch_fetcher.fetch_and_parse_json(item_api_url)

    hero_api_url = "https://www.dota2.com/datafeed/herolist?language=english"
    hero_data = patch_fetcher.fetch_and_parse_json(hero_api_url)

    ability_api_url = "https://www.dota2.com/datafeed/abilitylist?language=english"
    ability_data = patch_fetcher.fetch_and_parse_json(ability_api_url)

    patch_metadata = {
        'patch_number': patch_data['patch_number'],
        'patch_name': patch_data['patch_name'],
    }

    parse_patch_items = ParsePatchItems(item_data)
    parse_patch_heroes = ParsePatchHeroes(hero_data, ability_data)

    general_notes = list(map(lambda note: parse_patch_general_notes.parse(note, patch_metadata), patch_data['general_notes']))
    item_notes = list(
        filter(
            lambda x: x is not None,
            map(
                lambda item: parse_patch_items.parse(item, patch_metadata, 'hero_items'),
                patch_data['items'],
            )
        )
    )

    neutral_item_notes = list(
        filter(
            lambda x: x is not None,
            map(
                lambda item: parse_patch_items.parse(item, patch_metadata, 'neutral_items'),
                patch_data['neutral_items'],
            )
        )
    )

    hero_notes = list(
        filter(
            lambda x: x is not None,
            map(
                lambda item: parse_patch_heroes.parse(item, patch_metadata),
                patch_data['heroes'],
            )
        )
    )

    # print("general_notes")
    # print(json.dumps(general_notes, indent=4))
    # print("item_notes")
    # print(json.dumps(item_notes, indent=4))
    # print("neutral_item_notes")
    # print(json.dumps(neutral_item_notes, indent=4))
    # print("hero_notes")
    # print(json.dumps(hero_notes, indent=4))


    process_data = ProcessData()
    all_patch_documents = []
    all_patch_documents.extend(process_data.load_and_process_data(general_notes))
    all_patch_documents.extend(process_data.load_and_process_data(item_notes))
    all_patch_documents.extend(process_data.load_and_process_data(neutral_item_notes))
    all_patch_documents.extend(process_data.load_and_process_hero_data(hero_notes))

    embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"), model="text-embedding-3-small")
    pinecone = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

    llm_client = ChatOpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"), model_name="gpt-3.5-turbo",temperature=0)
    pinecone_instance = PineconeClient(pinecone, embeddings, llm_client)
    vector_store = pinecone_instance.insert(all_patch_documents) # if inserting new documents
    # vector_store = pinecone_instance.get_vector_store() # if retrieving vector store only

    # retriever = pinecone_instance.retrieve(vector_store)
    retriever = pinecone_instance.get_retriever_from_self_query_retriever(vector_store)

    retrieval_chain = RetrievalChain(llm_client)
    qa_chain = retrieval_chain.get_qa_chain(retriever)

    chat_query = ChatQuery(qa_chain)
    continually_query_user(chat_query)
