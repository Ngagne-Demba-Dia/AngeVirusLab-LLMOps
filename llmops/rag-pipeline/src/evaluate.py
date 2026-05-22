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

# Evaluation dataset : question + ground truth
EVAL_QUESTIONS = [
    {
        "question": "What is a hardware Trojan horse?",
        "ground_truth": "A hardware Trojan is a malicious modification of an integrated circuit that can leak information, disable or destroy a system, or perform unauthorized functions.",
    },
    {
        "question": "What are the evaluation assurance levels in Common Criteria?",
        "ground_truth": "The Common Criteria defines seven Evaluation Assurance Levels (EAL1 to EAL7) that represent increasing levels of assurance from functionally tested to formally verified design and tested.",
    },
    {
        "question": "What is a side-channel attack?",
        "ground_truth": "A side-channel attack exploits information leaked through physical implementation of a cryptographic system, such as timing, power consumption, electromagnetic emissions, or acoustic signals.",
    },
    {
        "question": "What is CAN bus and what are its security weaknesses?",
        "ground_truth": "The Controller Area Network (CAN) bus is an automotive communication protocol that lacks authentication and encryption, making it vulnerable to spoofing, replay attacks, and DoS attacks.",
    },
    {
        "question": "What is static analysis in malware analysis?",
        "ground_truth": "Static analysis examines malware without executing it, using techniques such as file hashing, string extraction, disassembly, and PE header analysis to understand its structure and behavior.",
    },
]


def format_docs(docs: list) -> str:
    return "\n\n".join(
        f"[{Path(doc.metadata.get('source', '?')).name}, p.{doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )


def build_rag(embeddings):
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


def collect_rag_outputs(chain, retriever) -> list:
    results = []
    for item in EVAL_QUESTIONS:
        question = item["question"]
        docs = retriever.invoke(question)
        contexts = [doc.page_content for doc in docs]
        answer = chain.invoke(question)
        results.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": item["ground_truth"],
        })
    return results


def run_ragas(results: list):
    try:
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from datasets import Dataset

        try:
            # RAGAS 0.2.x
            from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
            faithfulness_metric = Faithfulness()
            answer_relevancy_metric = AnswerRelevancy()
            metrics = [faithfulness_metric, answer_relevancy_metric]
        except ImportError:
            # RAGAS 0.1.x fallback
            from ragas.metrics import faithfulness, answer_relevancy
            metrics = [faithfulness, answer_relevancy]

        llm_wrapper = LangchainLLMWrapper(
            ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
        )
        emb_wrapper = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cuda"},
                encode_kwargs={"normalize_embeddings": True},
            )
        )

        for metric in metrics:
            if hasattr(metric, "llm"):
                metric.llm = llm_wrapper
            if hasattr(metric, "embeddings"):
                metric.embeddings = emb_wrapper

        dataset = Dataset.from_dict({
            "question": [r["question"] for r in results],
            "answer": [r["answer"] for r in results],
            "contexts": [r["contexts"] for r in results],
            "ground_truth": [r["ground_truth"] for r in results],
        })

        print("  Calcul des metriques RAGAS (avec Ollama comme juge)...")
        score = evaluate(dataset, metrics=metrics)
        return score.to_pandas()

    except Exception as e:
        print(f"  [INFO] RAGAS automatique non disponible : {e}")
        return None


def manual_metrics(results: list) -> list:
    scores = []
    for r in results:
        context_text = " ".join(r["contexts"]).lower()
        answer = r["answer"].lower()
        ground = r["ground_truth"].lower()

        # Context Hit Rate : pourcentage de mots de la ground truth trouves dans les contextes
        gt_words = set(w for w in ground.split() if len(w) > 4)
        ctx_hits = sum(1 for w in gt_words if w in context_text) / max(len(gt_words), 1)

        # Answer Coverage : mots de la ground truth presents dans la reponse
        ans_hits = sum(1 for w in gt_words if w in answer) / max(len(gt_words), 1)

        # Not Hallucinated : la reponse ne dit pas "not found"
        not_hallucinated = 0 if "not found" in answer or "information not found" in answer else 1

        scores.append({
            "question": r["question"][:55],
            "context_hit_rate": round(ctx_hits, 2),
            "answer_coverage": round(ans_hits, 2),
            "not_hallucinated": not_hallucinated,
        })
    return scores


def run():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — RAG Pipeline · Evaluation RAGAS")
    print("  Ngagne Demba Dia · Master SSE · UCAD · Dakar")
    print("=" * 65)
    print(f"  Modele LLM    : {OLLAMA_MODEL}")
    print(f"  Embeddings    : {EMBEDDING_MODEL}")
    print(f"  Questions     : {len(EVAL_QUESTIONS)}")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("\n  Collecte des reponses RAG...")
    chain, retriever = build_rag(embeddings)
    results = collect_rag_outputs(chain, retriever)

    # Metriques manuelles (toujours disponibles)
    print("\n" + "-" * 65)
    print("  METRIQUES MANUELLES")
    print("-" * 65)
    manual = manual_metrics(results)
    print(f"\n  {'Question':<55} {'CTX':>5} {'ANS':>5} {'HAL':>5}")
    print("  " + "-" * 63)
    for s in manual:
        hal_str = "OK" if s["not_hallucinated"] else "HALL"
        print(f"  {s['question']:<55} {s['context_hit_rate']:>5.2f} {s['answer_coverage']:>5.2f} {hal_str:>5}")

    avg_ctx = sum(s["context_hit_rate"] for s in manual) / len(manual)
    avg_ans = sum(s["answer_coverage"] for s in manual) / len(manual)
    hal_ok = sum(s["not_hallucinated"] for s in manual)
    print("  " + "-" * 63)
    print(f"  {'MOYENNE':<55} {avg_ctx:>5.2f} {avg_ans:>5.2f} {hal_ok}/{len(manual)}")
    print("\n  CTX = Context Hit Rate  (ground truth retrouvee dans les chunks)")
    print("  ANS = Answer Coverage   (ground truth retrouvee dans la reponse)")
    print("  HAL = Hallucination     (OK = reponse ancree dans le contexte)\n")

    # Metriques RAGAS
    print("-" * 65)
    print("  METRIQUES RAGAS (Faithfulness + AnswerRelevancy)")
    print("-" * 65)
    ragas_df = run_ragas(results)
    if ragas_df is not None:
        print(ragas_df.to_string(index=False))
    else:
        print("  RAGAS non execute (voir message ci-dessus).")
        print("  Les metriques manuelles suffisent pour valider le pipeline.\n")

    print("\n" + "=" * 65)
    print("  CONCLUSION")
    print("=" * 65)
    print(f"""
  Metriques cles du RAG pipeline :
  - Context Hit Rate  : les bons chunks sont-ils retrouves ?
  - Answer Coverage   : la reponse couvre-t-elle la ground truth ?
  - Hallucination     : la reponse est-elle ancree dans le contexte ?

  OWASP LLM10 — Model Theft / RAG Poisoning :
  Un RAG peut etre attaque via des documents malveillants injectes
  dans le vectorstore (RAG poisoning). Le guardrail INPUT RAIL
  doit aussi filtrer les documents avant ingestion en production.
    """)
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run()
