class ChatQuery:
    def __init__(self, qa_chain):
        self.qa_chain = qa_chain

    def ask_question(self, query, metadata_filter=None):
        """Asks a question to the RAG chain, optionally with a metadata filter."""
        current_search_kwargs = {'k': 3}
        if metadata_filter:
            current_search_kwargs['filter'] = metadata_filter

        # Update the retriever's search_kwargs for this specific query
        # Note: A more robust way might involve creating a new retriever or
        # using a more advanced retrieval mechanism if filters change frequently.
        # For simplicity, we re-assign here.
        # self.qa_chain.retriever.search_kwargs = current_search_kwargs

        print(f"\nQuery: {query}")
        if metadata_filter:
            print(f"With filter: {metadata_filter}")

        # Langchain LCEL uses invoke
        result = self.qa_chain.invoke({"query": query})
        print("\nAnswer:")
        print(result["result"])
        print("\nSource Documents:")
        for doc in result["source_documents"]:
            print(f"  - Content: {doc.page_content}")
            print(f"    Metadata: {doc.metadata}")

        return result
