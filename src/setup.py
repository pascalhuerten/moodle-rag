from langchain_community.vectorstores import Chroma
from chromadb.config import Settings
from chromadb import PersistentClient
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.docstore.document import Document
from .scrape_moodle import scrape_moodle_data, MoodleSiteInfo
import os


def load_embedding_function():
    return HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-large",
        query_instruction="Represent the user query for retriving relevant documents: ",
        embed_instruction="Represent the document for retrieval: ",
    )


def load_vectorstore(embedding):
    persist_directory = "data\stores\moodlestore"
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
        # Scrape Moodle data
        print("Scraping Moodle data")
        site = scrape_moodle_data()
        print("Moodle data scraped")

        # Load Moodle data into documents
        documents = []
        documents.append(site)
        for course in site.courses:
            documents.append(course)
            for section in course.sections:
                documents.append(section)
                for module in section.modules:
                    documents.append(module)
                    for content in module.contents:
                        documents.append(content)

        documents = [
            Document(
                page_content=str(doc),
                metadata=doc.asdict(),
            )
            for doc in documents
        ]

        print("Embedding documents")
        # Load documents into Vecorstore
        db = Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            collection_metadata={"hnsw:space": "cosine"},
            persist_directory=persist_directory,
        )

        print("Vectorstore loaded")

        print(str(len(db.get()["metadatas"])) + " documents loaded")

        return db
    else:
        return Chroma(
            client=PersistentClient(persist_directory),
            embedding_function=embedding,
            client_settings=Settings(anonymized_telemetry=False),
            collection_metadata={"hnsw:space": "cosine"},
        )
