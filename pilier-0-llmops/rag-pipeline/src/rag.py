import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

CHROMA_DIR = str(Path(__file__).parent.parent / "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "hardware_security"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
TOP_K = 4

RAG_PROMPT = ChatPromptTemplate.from_template("""You are a hardware security expert assistant. \
Answer the question using ONLY the provided context extracted from security documents.
If the answer is not found in the context, say "Information not found in the provided documents."

Context:
{context}

Question: {question}

Answer:""")

TEST_QUESTIONS = [
    "What is a hardware Trojan horse and how can it be detected?",
    "What are the main principles of the Common Criteria (ISO/IEC 15408)?",
    "How does side-channel analysis work in cryptographic attacks?",
    "What are the main vulnerabilities in automotive CAN bus systems?",
    "What techniques are used for static malware analysis?",
]


def format_docs(docs: list) -> str:
    return "\n\n".join(
        f"[{Path(doc.metadata.get('source', '?')).name}, p.{doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )


def build_chain():
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def run():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — RAG Pipeline · Generation")
    print("  Ngagne Demba Dia · Master SSE · UCAD · Dakar")
    print("=" * 65)
    print(f"  Modele LLM    : {OLLAMA_MODEL}")
    print(f"  Embeddings    : {EMBEDDING_MODEL}")
    print(f"  Retrieval k   : {TOP_K} chunks")

    chain, retriever = build_chain()

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'#' * 65}")
        print(f"  Q{i} : {question}")
        print("#" * 65)

        docs = retriever.invoke(question)
        print(f"\n  Sources ({len(docs)} chunks retrieved) :")
        for doc in docs:
            src = Path(doc.metadata.get("source", "?")).name
            page = doc.metadata.get("page", "?")
            print(f"    - {src[:50]:<50} p.{page}")

        answer = chain.invoke(question)
        print(f"\n  Reponse :")
        print(f"  {answer[:600]}{'...' if len(answer) > 600 else ''}")

    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    run()
