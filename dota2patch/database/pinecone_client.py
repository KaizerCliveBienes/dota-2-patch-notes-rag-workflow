from langchain_pinecone import Pinecone as LangchainPinecone
from pinecone import ServerlessSpec
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
import time


class PineconeClient:
    def __init__(self, pinecone_client, embeddings_client, llm_client):
        self.pinecone_client = pinecone_client
        self.embeddings_client = embeddings_client
        self.llm_client = llm_client
        self.pinecone_index_name = "dota2-patches-rag"
        self.embedding_dimensions = 1536
        self.pinecone_cloud = "aws"
        self.pinecone_region = "us-east-1"

    def insert(self, all_patch_documents):
        if self.pinecone_index_name not in self.pinecone_client.list_indexes().names():
            print(f"Creating Pinecone index: {self.pinecone_index_name}")
            self.pinecone_client.create_index(
                name=self.pinecone_index_name,
                # Dimension of OpenAI's text-embedding-ada-002 or
                # text-embedding-3-small
                dimension=self.embedding_dimensions,
                metric="cosine",      # Common metric for semantic similarity
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

            print(f"Waiting for index '{
                  self.pinecone_index_name}' to become ready...")
            # Use describe_index to poll for readiness status
            while not self.pinecone_client.describe_index(
                    self.pinecone_index_name).status['ready']:
                time.sleep(1)
                print(f"Waiting for index {
                      self.pinecone_index_name} to be ready")
            print(f"Index {self.pinecone_index_name} created successfully.")
        else:
            print(f"Pinecone index {self.pinecone_index_name} already exists.")

        try:
            vector_store = LangchainPinecone.from_existing_index(
                index_name=self.pinecone_index_name,
                embedding=self.embeddings_client,
                namespace="dota2-patches-v1"
            )
        except Exception as e:
            raise RuntimeError(f"Cannot connect to langchain index: {e}")

        for document in all_patch_documents:
            vector_store.add_documents(documents=document)

        print("Documents embedded and loaded into Pinecone.")

        return vector_store

    def retrieve(self, vector_store):
        retriever = vector_store.as_retriever(
            search_kwargs={
                'k': 3,  # Number of documents to retrieve
                # Example filter:
                # 'filter': {'type': 'heroes', 'patch_number': '7.38c'}
            }
        )

        return retriever

    def get_vector_store(self):
        print(f"Connecting to existing Pinecone index: {
              self.pinecone_index_name}")
        vector_store = LangchainPinecone(
            index_name=self.pinecone_index_name,
            embedding=self.embeddings_client,
            namespace="dota2-patches-v1",
        )

        print("Successfully connected to existing Pinecone index via Langchain.")

        return vector_store

    def get_retriever_from_self_query_retriever(self, vector_store):
        metadata_field_info = [
            AttributeInfo(
                name="patch_name",
                description="The name of the patch. Formatted as <major version>.<minor version><patch version> e.g. 7.38c",
                type="string",
            ),
            AttributeInfo(
                name="patch_number",
                description="The official patch number, usually the same as patch_name.Formatted as <major version>.<minor version><patch version> e.g. 7.38c",
                type="string",
            ),
            AttributeInfo(
                name="skill_name",
                description="(Optional) The name of the skill that is being patched. The format is \"<name of skill> (<code name>)\"",
                type="string",
            ),
            AttributeInfo(
                name="type", description="The type of the patch change. One of the following: ['heroes', 'items', 'generic']", type="string"
            ),
            AttributeInfo(
                name="subtype", description="The subtype of the patch change. The \"heroes\" type can be ['abilities', 'facets'] while the \"items\" type can be [\"hero_items\", \"neutral_items\"]", type="string"
            ),
            AttributeInfo(
                name="title", description="The name of the hero or item. The format is <hero or item name> (<code name>).", type="string"
            ),
        ]

        document_content_description = "Patch notes from the game, Dota 2"

        return SelfQueryRetriever.from_llm(
            self.llm_client,
            vector_store,
            document_content_description,
            metadata_field_info,
        )
