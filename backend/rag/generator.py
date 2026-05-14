import os
from typing import List, Dict, AsyncGenerator
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

MODELS = {
    "gemini-flash":  ("google",    "gemini-1.5-flash"),
    "gemini-pro":    ("google",    "gemini-1.5-pro"),
    "claude-haiku":  ("anthropic", "claude-3-haiku-20240307"),
    "gpt-4o-mini":   ("openai",    "gpt-4o-mini"),
}

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are DevFlow, an expert technical assistant.
Answer using ONLY the provided context. Be precise and structured.
Use markdown formatting. Include code blocks with language tags where relevant.
If context is insufficient, say so clearly.
IMPORTANT: Always respond in the same language as the question. \
If the question is in Spanish, answer in Spanish. \
If in French, answer in French. Match the language of the question exactly.

Context:
{context}

Conversation history:
{history}

Question: {question}

Answer (markdown):"""
)


def _format_context(documents: List[str], metadatas: List[Dict]) -> str:
    parts = []
    for i, (doc, meta) in enumerate(zip(documents[:5], metadatas[:5])):
        parts.append(f"[Source {i+1}: {meta.get('title', 'Unknown')}]\n{doc}")
    return "\n\n---\n\n".join(parts)


def _format_history(history: List[Dict]) -> str:
    if not history:
        return "None"
    return "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:])


def _get_llm(model_key: str):
    provider, model_name = MODELS.get(model_key, MODELS["gemini-flash"])
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name, google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1, max_tokens=2048,
        )
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1, max_tokens=2048,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1, max_tokens=2048,
        )
    raise ValueError(f"Unknown model: {model_key}")


class GeminiRAG:
    def __init__(self):
        self.default_llm = _get_llm("gemini-flash")
        self.chain = RAG_PROMPT | self.default_llm | StrOutputParser()

    def generate_answer(
        self,
        query: str,
        context: List[str],
        sources: List[Dict],
        history: List[Dict] = None,
        model: str = "gemini-flash",
    ) -> Dict:
        if not context:
            return {"answer": "No relevant documents found.", "sources": [], "model": model}

        llm = _get_llm(model) if model != "gemini-flash" else self.default_llm
        chain = RAG_PROMPT | llm | StrOutputParser()

        try:
            answer = chain.invoke({
                "context": _format_context(context, sources),
                "question": query,
                "history": _format_history(history or []),
            })
        except Exception as e:
            answer = f"Generation error: {str(e)}"

        return {"answer": answer, "sources": sources[:5], "model": model}

    async def astream_answer(
        self,
        query: str,
        context: List[str],
        sources: List[Dict],
        history: List[Dict] = None,
        model: str = "gemini-flash",
    ) -> AsyncGenerator[str, None]:
        if not context:
            yield "No relevant documents found in your knowledge base."
            return

        llm = _get_llm(model)
        messages = RAG_PROMPT.format_messages(
            context=_format_context(context, sources),
            question=query,
            history=_format_history(history or []),
        )
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
