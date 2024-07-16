from langchain_openai import ChatOpenAI

def create_chat_openai_with_base(openai_api_base, openai_api_key="-", max_tokens=512):
    return ChatOpenAI(
        model="-",
        openai_api_base=openai_api_base,
        openai_api_key="-",
        temperature=0.1,
        max_tokens=max_tokens,
        model_kwargs={"seed": 42},
    )