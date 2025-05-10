# Dota 2 Simple Patch Notes RAG Pipeline

This project provides a Python script to build a simple Retrieval Augmented Generation (RAG) pipeline specifically for information contained within **Dota 2 patch notes**. It leverages Langchain, Pinecone, and OpenAI's text embeddings to create a searchable knowledge base from historical and recent patch data, allowing you to ask questions about changes in specific patches and receive answers based on the retrieved context. The pipeline utilizes a `SelfQueryRetriever` to enable sophisticated filtering of information based on metadata, such as the patch version.

## Workflow

The script follows these steps:

1.  **Patch Data Pull:** Extracts data specifically from Dota 2 patch note sources (details of the specific source and extraction method would be in the script), focusing on the changes introduced in each patch.
2.  **Vector Database Creation:** Uses Langchain to process the extracted patch data and create vector embeddings using OpenAI's text embedding model. These embeddings are then stored in a Pinecone vector database. Metadata associated with the patch notes (crucially, the patch version, and potentially details about heroes, items, or mechanics changed) is also stored.
3.  **Self-Querying Retrieval:** When a query is provided (e.g., "What changed for Pudge in patch 7.35b?"), the `SelfQueryRetriever` intelligently parses the query to identify potential metadata filters (like the patch version "7.35b" and the hero "Pudge"). It then uses these filters in conjunction with semantic search to retrieve the most relevant sections of patch notes from the Pinecone database.
4.  **Answer Generation:** The retrieved context from the RAG pipeline (the relevant patch note sections) is fed into a ChatGPT model (via Langchain) to generate a coherent and informative answer to the original query about the patch changes.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up environment variables:**
    You will need to set up the following environment variables:
    * `OPENAI_API_KEY`: Your API key for OpenAI.
    * `PINECONE_API_KEY`: Your API key for Pinecone.
    * `PINECONE_INDEX_NAME`: The name for your Pinecone index.
    * `PINECONE_INDEX_NAMESPACE`: Your Pinecone index's namespace.

    You can do this by creating a `.env` file by copying from `.env.example`
    ```bash
    cp .env.example .env
    ```

## Usage

The script `init.py` is the main entry point.

```bash
python init.py [OPTIONS]
```

### Options:

* `--insert`: Flag to trigger the insertion of vector embeddings into Pinecone. This is required when you want to build or update the vector database with patch data.
* `--patch-version TEXT`: Specifies the Dota 2 patch version to insert. The script will attempt to pull and process data for this specific patch. This option **must** be used with the `--insert` flag.
* `--verbose`: Enables verbose output, showing the retrieved documents (sections of patch notes) before generating the answer.
* `--help`: Show the help message and exit.

### Example Runs:

* **Insert data for a specific patch version (e.g., 7.38):**
    ```bash
    python init.py --insert --patch-version 7.38
    ```
* **Query the RAG pipeline (after patch data has been inserted):**
    ```bash
    python init.py
    ```
    (The script will then likely prompt you for a query related to patch changes.)
* **Query with verbose output:**
    ```bash
    python init.py --verbose
    ```

## To-Do List

* Add unit tests for key functionalities (data parsing specifically for patch notes, embedding, retrieval).
* Add a command-line option for specifying the query directly.
* Implement support for incremental data updates for new patches in Pinecone.
* Expand data sources to include starting from a specific patch version.
* Improve the natural language understanding of the `SelfQueryRetriever` for more complex queries about patch changes (e.g., comparing changes across multiple patches).
* Quantify the performance of the RAG pipeline for patch note retrieval and answer generation.
* Investigate extracting and utilizing more granular metadata from patch notes (e.g., specific hero/item names, ability changes, number values).
* Explore using a fine-tuned language model specifically for summarizing patch changes.
* **Future Improvement:** Extend to include other types of Dota 2 information beyond just patch notes.
