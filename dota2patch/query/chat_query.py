import json


class ChatQuery:
    def __init__(self, qa_chain):
        self.qa_chain = qa_chain

    def ask_question(self, query, verbose, metadata_filter=None):
        current_search_kwargs = {'k': 3}
        if metadata_filter:
            current_search_kwargs['filter'] = metadata_filter

        if verbose:
            print(f"\nQuery: {query}")
            if metadata_filter:
                print(f"With filter: {metadata_filter}")

        # Langchain LCEL uses invoke
        result = self.qa_chain.invoke({"query": query})
        print(">" + result["result"])

        if verbose:
            print("\nSource Documents:")
            for doc in result["source_documents"]:
                print(f"  Content: {doc.page_content}")
                print(f"  Metadata: {json.dumps(doc.metadata, indent=4)}")

        return result
