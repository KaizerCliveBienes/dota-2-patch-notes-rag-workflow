import os
import json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# Renamed to avoid conflict
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from pinecone import Pinecone, ServerRelativeOption  # For Pinecone client
# from pinecone import PodSpec # If using pod-based indexes

# --- Configuration ---
# Best practice: Use environment variables for API keys
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
# PINECONE_ENVIRONMENT = "..." # e.g., "gcp-starter" or your Pinecone environment for pod-based. Not needed for serverless with just API key.
# PINECONE_INDEX_NAME = "dota2-patches-rag"

# Hardcoded for example purposes, replace with environment variables or
# secure key management
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
PINECONE_API_KEY = "YOUR_PINECONE_API_KEY"
# For Pinecone Serverless, you don't specify an environment during client initialization,
# but you do specify cloud and region during index creation.
PINECONE_INDEX_NAME = "dota2-patches-rag"
PINECONE_CLOUD = "aws"  # Or "gcp", "azure"
PINECONE_REGION = "us-east-1"  # Your chosen region

# --- 1. Load and Process Your JSON Data ---


def load_and_process_data(json_file_path):
    """Loads JSON data and converts entries into Langchain Documents."""
    documents = []
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle cases where data might be a single dict or a list of dicts
    if isinstance(data, dict):
        data = [data]

    for entry in data:
        page_content = entry.get("changes")
        if not page_content:
            print(
                f"Skipping entry due to missing 'changes' field: {
                    entry.get('title')}")
            continue

        metadata = {
            "patch_number": entry.get("patch_metadata", {}).get("patch_number", "N/A"),
            "patch_name": entry.get("patch_metadata", {}).get("patch_name", "N/A"),
            "type": entry.get("type", "N/A"),
            "subtype": entry.get("subtype", "N/A"),
            "title": entry.get("title", "N/A"),
            # Storing the original text is good practice
            "original_change_text": page_content
        }
        if "skill_name" in entry:
            metadata["skill_name"] = entry["skill_name"]

        documents.append(
            Document(
                page_content=page_content,
                metadata=metadata))
    return documents


# Example: Assuming you have two files as per your examples
# Create dummy files for the example to run
item_data_example = [{
    "patch_metadata": {"patch_number": "7.38c", "patch_name": "7.38c"},
    "type": "items", "subtype": "hero_items",
    "changes": "Dominated creep is now considered a creep-hero (It cannot be dominated, persuaded or enchanted, and it isn't instantly killed by Hand of Midas, Mirana's Sacred Arrow, etc.).",
    "title": "Helm of the Overlord (item_helm_of_the_overlord)"
}]
with open('item_changes.json', 'w') as f:
    json.dump(item_data_example, f)

hero_data_example = [{
    "patch_metadata": {"patch_number": "7.38c", "patch_name": "7.38c"},
    "type": "heroes", "subtype": "facets", "skill_name": "Ofrenda",
    "changes": "Ofrenda (muerta_ofrenda): Attack Speed Bonus increased from 15/25/35/45 to 20/30/40/50.",
    "title": "Muerta (npc_dota_hero_muerta)"
}]
with open('hero_changes.json', 'w') as f:
    json.dump(hero_data_example, f)

all_patch_documents = []
all_patch_documents.extend(load_and_process_data('item_changes.json'))
all_patch_documents.extend(load_and_process_data('hero_changes.json'))

# --- 2. Initialize Embeddings Model ---
# Using one of OpenAI's text embedding models
embeddings = OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY,
    model="text-embedding-3-small")  # "text-embedding-ada-002" is older
# text-embedding-3-small has dimension 1536 by default. text-embedding-ada-002 is 1536.
# text-embedding-3-large has dimension 3072.
EMBEDDING_DIMENSION = 1536  # for text-embedding-3-small or text-embedding-ada-002

# --- 3. Initialize Pinecone ---
# Initialize Pinecone client (this is the newer client syntax)
pinecone = Pinecone(api_key=PINECONE_API_KEY)

# Check if the index exists, create it if it doesn't
if PINECONE_INDEX_NAME not in pinecone.list_indexes().names:
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
    pinecone.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        # Dimension of OpenAI's text-embedding-ada-002 or
        # text-embedding-3-small
        metric="cosine",      # Common metric for semantic similarity
        spec=ServerRelativeOption(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION)  # For serverless indexes
        # For pod-based indexes, use:
        # spec=PodSpec(environment=PINECONE_ENVIRONMENT, pod_type="p1.x1") #
        # Choose appropriate pod_type
    )
    print(f"Index {PINECONE_INDEX_NAME} created successfully.")
else:
    print(f"Pinecone index {PINECONE_INDEX_NAME} already exists.")

# Connect to your Pinecone index using Langchain's integration
# Ensure you have the `langchain-pinecone` package installed: pip install langchain-pinecone
# and the `pinecone-client` package: pip install pinecone-client~=3.0 (or
# latest v3+)
vector_store = LangchainPinecone.from_documents(
    documents=all_patch_documents,
    embedding=embeddings,
    index_name=PINECONE_INDEX_NAME
    # namespace="dota2-patches-v1" # Optional: if you want to partition data
    # within an index
)
print("Documents embedded and loaded into Pinecone.")

# Alternative, if index already has data or for more control:
# index = pinecone.Index(PINECONE_INDEX_NAME)
# vector_store = LangchainPinecone(index, embeddings, "text") # "text" is the default text key
# vector_store.add_documents(all_patch_documents)


# --- 4. Setting up the Retriever with Metadata Filtering ---
# The retriever will fetch relevant documents from Pinecone
# We can specify metadata filters in `search_kwargs`
retriever = vector_store.as_retriever(
    search_kwargs={
        'k': 3,  # Number of documents to retrieve
        # Example filter:
        # 'filter': {'type': 'heroes', 'patch_number': '7.38c'}
    }
)

# --- 5. Setting up the RAG Chain (LLM for Generation) ---
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                 model_name="gpt-3.5-turbo")  # Or "gpt-4"

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # "stuff" puts all retrieved docs into the prompt.
    # Other types: "map_reduce", "refine", "map_rerank"
    retriever=retriever,
    return_source_documents=True  # To see which documents were retrieved
)

# --- 6. Asking Questions ---


def ask_question(query, metadata_filter=None):
    """Asks a question to the RAG chain, optionally with a metadata filter."""
    current_search_kwargs = {'k': 3}
    if metadata_filter:
        current_search_kwargs['filter'] = metadata_filter

    # Update the retriever's search_kwargs for this specific query
    # Note: A more robust way might involve creating a new retriever or
    # using a more advanced retrieval mechanism if filters change frequently.
    # For simplicity, we re-assign here.
    qa_chain.retriever.search_kwargs = current_search_kwargs

    print(f"\nQuery: {query}")
    if metadata_filter:
        print(f"With filter: {metadata_filter}")

    result = qa_chain.invoke({"query": query})  # Langchain LCEL uses invoke
    print("\nAnswer:")
    print(result["result"])
    print("\nSource Documents:")
    for doc in result["source_documents"]:
        print(f"  - Content: {doc.page_content}")
        print(f"    Metadata: {doc.metadata}")
    return result


# Example Queries:
query1 = "What changed for Helm of the Overlord?"
ask_question(
    query1, metadata_filter={
        'title': 'Helm of the Overlord (item_helm_of_the_overlord)'})

query2 = "Tell me about Muerta's Ofrenda in patch 7.38c."
# Note: Pinecone filtering is exact by default. For partial matches on title or skill_name,
# you might need more advanced text processing before metadata creation or use regex if supported by Pinecone's filter syntax for your setup.
# For exact match using the 'title' field for the hero:
ask_question(query2, metadata_filter={
    'title': 'Muerta (npc_dota_hero_muerta)',
    'patch_number': '7.38c',
    # 'skill_name': 'Ofrenda' # This would make it even more specific
    'type': 'heroes'
})

query3 = "What were the item changes in patch 7.38c?"
ask_question(
    query3,
    metadata_filter={
        'type': 'items',
        'patch_number': '7.38c'})

# --- Cleanup (Optional: Delete dummy files) ---
# os.remove('item_changes.json')
# os.remove('hero_changes.json')
