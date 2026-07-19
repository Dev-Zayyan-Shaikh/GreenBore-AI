import logging

from backend.prompts.manager import PromptManager
from backend.rag.llm import LLMProvider
from backend.rag.schema import Citation, RAGResponse
from backend.rag.vector_store import DBVectorStore

logger = logging.getLogger("greenbore.rag.pipeline")


class RAGPipeline:
    """
    Retrieval-Augmented Generation (RAG) pipeline coordinating vector search,
    context prompt assembly, and response generation with cited sources.
    """

    def __init__(
        self,
        vector_store: DBVectorStore,
        llm_provider: LLMProvider,
        prompt_manager: PromptManager,
    ) -> None:
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.prompt_manager = prompt_manager

    async def query(self, user_query: str, k: int = 3) -> RAGResponse:
        """
        Processes a user question: retrieves relevant chunks,
        formats the prompt template, queries the LLM, and formats citations.
        """
        logger.info(f"RAG query received: '{user_query}' (k={k})")

        # 1. Similarity Search
        retrieved_chunks = await self.vector_store.similarity_search(user_query, k=k)

        if not retrieved_chunks:
            logger.info("No relevant document chunks retrieved.")
            return RAGResponse(
                query=user_query,
                answer=(
                    "I do not have enough geological record information "
                    "to answer this question."
                ),
                citations=[],
            )

        # 2. Context Assembly
        context_parts = []
        for chunk in retrieved_chunks:
            part = (
                f"Title: {chunk['title']}\n"
                f"Category: {chunk['category']}\n"
                f"Content: {chunk['content']}"
            )
            context_parts.append(part)

        context_str = "\n\n".join(context_parts)

        # 3. Format Prompt
        formatted_prompt = self.prompt_manager.format_prompt(
            "rag_assistant.txt", context=context_str, query=user_query
        )

        # 4. Generate Answer via LLM
        answer = self.llm_provider.generate(formatted_prompt, retrieved_chunks)

        # 5. Extract Citations
        citations = []
        seen_titles = set()
        for chunk in retrieved_chunks:
            title = chunk["title"]
            if title not in seen_titles:
                citations.append(
                    Citation(
                        title=title,
                        category=chunk["category"],
                        content_preview=chunk["content"][:150].strip() + "...",
                    )
                )
                seen_titles.add(title)

        return RAGResponse(query=user_query, answer=answer.strip(), citations=citations)
