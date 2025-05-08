from langchain.prompts import PromptTemplate

from langchain.chains import RetrievalQA

class RetrievalChain:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def get_qa_chain(self, retriever):

        prompt_template_str = """You are a helpful assistant for answering questions related to Dota 2 patches. If the user asks for a patch update for a specific hero / item, you should mention all of the patch updates from the retrieved contexts.

Use the following pieces of retrieved context to answer the question.
You must answer based **ONLY** on the provided context.
If you don't know the answer or the context doesn't contain the answer, just say "I'm sorry, I cannot answer this question based on the provided patch notes."
Do not make up an answer or use any external knowledge.

Include the patch name from the metadata to the responses enclosed in parentheses. If not known, no need to put the patch name.

CONTEXT:
{context}

QUESTION: {question}

ANSWER (based ONLY on the context):"""

        custom_prompt = PromptTemplate(
            template=prompt_template_str, input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm_client,
            chain_type="stuff", # "stuff" puts all retrieved docs into the prompt.
                                # Other types: "map_reduce", "refine", "map_rerank"
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": custom_prompt},
)

