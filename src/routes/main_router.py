from fastapi import APIRouter, Depends
from starlette.requests import Request
from pydantic import BaseModel
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import os
import re
from ..models.utils import create_chat_openai_with_base

router = APIRouter()

class Home(BaseModel):
    title: str = "MOODLE RAG CHAT API"
    description: str = "API for the MOODLE RAG CHAT project"
    docs_url: str = "/docs"


class Health(BaseModel):
    status: str


@router.get("/", response_model=Home)
def index():
    return Home()


@router.get("/health", response_model=Health)
def health():
    return Health(status="ok")


class Query(BaseModel):
    message: str
    course_id: Optional[str] = None
    usercontext: Optional[str] = "Dashboard"


class Response(BaseModel):
    response: str


def get_vectorstore(req: Request):
    return req.app.state.VECTORSTORE


@router.post("/chat", response_model=Response)
def chat(request: Query, vectorstore=Depends(get_vectorstore)):
    predicted_context = predict_context(request)
    response = process_query(request, vectorstore, predicted_context)
    return Response(response=response)


def process_query(request, vectorstore, predicted_context):
    # Retriever will search for the top_5 most similar documents to the query.
    search_kwargs={"k": 5}
    filters = []
    
    def get_filters_for_context(predicted_context, course_id):
        # Define a mapping of predicted_context to their respective filter functions
        context_filters = {
            "Site-Context": lambda: [{"doc_type": {"$in": ["site", "course"]}}],
            "Course-Context": lambda: [
                {"course_id": {"$eq": course_id}, "doc_type": {"$in": ["course", "module"]}}
            ] if course_id else []
        }

        # Get the filter function based on predicted_context, default to an empty list if context not found
        filters = context_filters.get(predicted_context, lambda: [])()

        return filters

    # Usage in your main_router.py
    filters = get_filters_for_context(predicted_context, request.course_id)

    if filters:
        search_kwargs["filter"] = {"$and": filters} if len(filters) > 1 else filters[0]
    
    print("Set retriever with filters: " + str(search_kwargs))
    
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "Du bist ein hilfreicher Assistent der dabei unterstützt, passende Kurse auf der Kursplattform FututreLearnLab zu finden und über die verfügbaren Lerninhalte zu informieren."
                )
            ),
            HumanMessagePromptTemplate.from_template(
                (   
                    "Nutze den folgenden Kontext, um die nachfolgende Nutzeranfrage zu beantworten\n"
                    "\n"
                    "Der Nutzer befindet sich momentan auf der Kursplatform in folgendem Kontext: {usercontext}\n"
                    "Bei Fragen zu bestimmten Kursinhalten oder verfügbaren Kursen, nutze auschließlich Infromationen aus dem nachgehenden Kontext, der auf Basis der Nutzeranfrage zusammengestellt wurde. Nicht alle Informationen sind relevant, entscheide also selbst, welche Informationen du teilen möchtest.\n"
                    "{context}\n"
                    "\n"
                    "Kontext Ende"
                    "\n"
                    "Der Nutzer hat folgende Nachricht geschrieben: {query}"
                    "\n"
                    "Antworte auf die Nutzeranfrage unter Berücksichtigung des Kontexts und der Nutzeranfrage. Wenn der Kontext keine relevanten Informationen enthält, antworte mit 'Ich habe keine Informationen zu diesem Thema'."
                )
            ),
        ]
    )
    
    # model = create_chat_openai_with_base(os.getenv("DEFAULT_CUSTOM_LLM_URL"))
    model = create_chat_openai_with_base(os.getenv("DEFAULT_CUSTOM_LLM_URL"), openai_api_key="lm-studio")

    chain = (
        {"context": itemgetter("query") | retriever, "query": itemgetter("query"), "usercontext" : itemgetter("usercontext")}
        | prompt
        | model
        | StrOutputParser()
    )

    print("Retrieving context")
    context = retriever.invoke(request.message)
    print("Context retrieved")

    print("Context: " + str(context))

    print("Processing query")
    print(prompt.format_prompt(query = request.message, usercontext = request.usercontext, context = context))

    return chain.invoke({"query": request.message, "usercontext": request.usercontext})

def predict_context(request):
    prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessagePromptTemplate.from_template(
                (   
                    "User Query: {query}\n"
                    "User Context: {usercontext}\n"
                    "\n"
                    "Based on the previous query choose which sources are most relevant to answer the user query.\n"
                    "\n"
                    "Choose one of the following options, by reffering to its name only:\n"
                    "[Site-Context]: Includes general information about the site, its features and course offerings.\n"
                    "[Course-Context]: Includes information about a single specific course and its contents.\n"
                    "[User-Context]: Includes information about the current user, its bio, learning activity and interests and goals."
                )
            ),
        ]
    )
    
    # model = create_chat_openai_with_base(os.getenv("DEFAULT_CUSTOM_LLM_URL"))
    model = create_chat_openai_with_base(os.getenv("MINI_CUSTOM_LLM_URL"), openai_api_key="lm-studio", max_tokens=128)

    chain = ( prompt | model | StrOutputParser() )

    print("Processing query")
    print(prompt.format_prompt(query = request.message, usercontext = request.usercontext))

    answer = chain.invoke({"query": request.message, "usercontext": request.usercontext})
    print("Answer: " + str(answer))
    # get only content that matches the desired output [Site-Context] or [Course-Context] or [User-Context]

    match = re.search(r"\[(.*?)\]", answer)
    if match:
        predicted_context = match.group(1)
    else:
        return None

    print("Predicted context: " + str(predicted_context))

    return predicted_context


# Query example for preselectioon relevant context for user query:

# Example 1:

# User Query: Welche Kurse kann ich auf dieser Plattform belegen?
# User Context: The user visits the site as a guest. The user currently views the homepage of the site.

# Based on the previous query choose which sources are most relevant to answer the user query.

# Choose one of the following options, by reffering to its name only:
# [Site-Context]: Includes general information about the site, its features and course offerings.
# [Course-Context]: Includes information about a single specific course and its contents.
# [User-Context]: Includes information about the current user.

# Example 2:

# User Query: Fasse das Feedback zum Kurs zusammen,
# User Context: The user is logged in as a teacher. The user currently views the course overview.

# Based on the previous query choose which sources are most relevant to answer the user query.

# Choose one of the following options, by reffering to its name only:
# [Site-Context]: Includes general information about the site, its features and course offerings.
# [Course-Context]: Includes information about a single specific course and its contents.
# [User-Context]: Includes information about the current user, its bio, learning activity and interests and goals.

# Example 3:

# User Query: Welche Kurse habe ich bereits abgeschlossen?
# User Context: The user is logged in as a student. The user currently views the dashboard.

# Based on the previous query choose which sources are most relevant to answer the user query.

# Choose one of the following options, by reffering to its name only:
# [Site-Context]: Includes general information about the site, its features and course offerings.
# [Course-Context]: Includes information about a single specific course and its contents.
# [User-Context]: Includes information about the current user, its bio, learning activity and interests and goals.