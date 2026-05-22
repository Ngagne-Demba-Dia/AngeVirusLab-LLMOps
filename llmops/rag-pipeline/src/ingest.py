import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCS_DIR = Path(__file__).parent.parent / "docs"
CHROMA_DIR = str(Path(__file__).parent.parent / "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "hardware_security"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_pdfs(docs_dir: Path) -> list:
    docs = []
    pdf_files = sorted(docs_dir.glob("*.pdf"))
    print(f"  Chargement de {len(pdf_files)} PDFs...")
    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            docs.extend(pages)
            print(f"    + {pdf_path.name[:55]:<55} ({len(pages):>4} pages)")
        except Exception as e:
            print(f"    ! Erreur {pdf_path.name}: {e}")
    return docs


def ingest():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — RAG Pipeline · Ingestion")
    print("  Ngagne Demba Dia · Master SSE · UCAD · Dakar")
    print("=" * 65)

    raw_docs = load_pdfs(DOCS_DIR)
    print(f"\n  Total pages chargees  : {len(raw_docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(raw_docs)
    print(f"  Total chunks crees    : {len(chunks)}")
    print(f"  Taille chunk          : {CHUNK_SIZE} chars, overlap {CHUNK_OVERLAP}")

    print(f"\n  Modele embeddings     : {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print(f"  Vectorstore ChromaDB  : {CHROMA_DIR}")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )

    print(f"\n  Ingestion complete : {vectorstore._collection.count()} chunks dans ChromaDB")
    print("=" * 65 + "\n")
    return vectorstore


if __name__ == "__main__":
    ingest()
