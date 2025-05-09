import click
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

@click.command()
@click.option('--insert', default=False, help='Flag to insert vector embeddings into pinecone')
@click.option('--patch-version', default='', help='Patch version to insert. Must be with --insert')
def get_data(insert, patch_version):
    if (insert and patch_version == ''):
        raise RuntimeError("must include patch version (--patch-version) if you are going to insert something.")

    patch_fetcher = PatchFetcher()

    llm_client = ChatOpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"), model_name="gpt-4.1-mini",temperature=0)

    pinecone_instance = PineconeClient(
        Pinecone(api_key=os.environ.get("PINECONE_API_KEY")),
        OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"), model="text-embedding-3-small"),
        llm_client,
    )

    vector_store = None
    if insert:
        vector_store = pinecone_instance.insert(patch_fetcher.construct_all_patch_documents(patch_version))
    else:
        vector_store = pinecone_instance.get_vector_store()

    # retriever = pinecone_instance.retrieve(vector_store)
    retriever = pinecone_instance.get_retriever_from_self_query_retriever(vector_store)

    retrieval_chain = RetrievalChain(llm_client)
    qa_chain = retrieval_chain.get_qa_chain(retriever)

    chat_query = ChatQuery(qa_chain)
    continually_query_user(chat_query)
