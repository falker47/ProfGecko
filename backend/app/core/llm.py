from langchain_core.language_models import BaseChatModel


def get_llm(provider: str = "gemini", **kwargs) -> BaseChatModel:
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=kwargs.get("model", "gemini-2.0-flash"),
            temperature=kwargs.get("temperature", 0.7),
            streaming=True,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=kwargs.get("model", "gpt-4o-mini"),
            temperature=kwargs.get("temperature", 0.7),
            streaming=True,
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=kwargs.get("model", "gemma3:4b"),
            temperature=kwargs.get("temperature", 0.7),
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
