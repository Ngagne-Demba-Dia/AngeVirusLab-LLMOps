import os
import re
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse

load_dotenv()

CHROMA_DIR = str(Path(__file__).parent.parent.parent / "rag-pipeline" / "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "hardware_security"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
TOP_K = 4

# ── Guardrails ────────────────────────────────────────────────────

class RailDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"

@dataclass
class RailResult:
    decision: RailDecision
    reason: Optional[str] = None
    threat_type: Optional[str] = None

INJECTION_PATTERNS = [
    (r"ignore\s+(tes|les|vos|previous|your|all)\s+(instructions|directives|règles|rules)", "instruction_override"),
    (r"(tu es|you are|vous êtes)\s+maintenant", "identity_override"),
    (r"\bDAN\b", "dan_jailbreak"),
    (r"(oublie|forget|ignore)\s+(tout|everything|all|previous)", "context_wipe"),
    (r"(pretend|fais semblant|act as|agis comme).{0,40}(no restriction|sans restriction|unrestricted)", "persona_jailbreak"),
    (r"\[\s*(system|SYSTEM|INST)\s*\]", "instruction_tag_injection"),
    (r"<\s*(system|assistant|user)\s*>", "role_tag_injection"),
    (r"(new\s+instructions?|nouvelles?\s+instructions?)\s*:", "instruction_hijack"),
]

HARMFUL_CONTENT_PATTERNS = [
    (r"(crée|créer|développer|coder|écrire|ecri[rst]|génère|genere|fais|make|write|create).{0,40}(virus|malware|ransomware|trojan|keylogger|botnet)", "malware_creation"),
    (r"(ransomware|malware|virus|keylogger).{0,50}(python|complet|fonctionnel|qui crypte|qui chiffre|encrypt)", "malware_creation"),
    (r"(pirater|hacker|hack|compromettre).{0,50}(wifi|réseau|serveur|compte|système)", "unauthorized_hacking"),
    (r"(bombe|explosif|détonateur|TNT|IED|engin explosif)", "explosive_device"),
    (r"(synthèse|fabriquer|créer).{0,40}(drogue|stupéfiant|poison)", "illegal_substance"),
    (r"(ransomware|cryptolocker).{0,40}(déployer|lancer|créer)", "ransomware_deployment"),
    (r"(ddos|déni de service).{0,30}(lancer|attaquer|cibler)", "ddos_attack"),
    (r"(scanner|scan).{0,30}(ports?).{0,40}(ip|cible)", "port_scanner"),
    (r"(brute\s*force).{0,40}(connexion|login|mot de passe)", "brute_force"),
    (r"(keylogger|capturer.{0,20}touches)", "keylogger"),
]

DANGEROUS_OUTPUT_PATTERNS = [
    (r"\brm\s+-rf\b", "destructive_command"),
    (r"\b(DELETE|DROP|TRUNCATE)\s+(FROM|TABLE|DATABASE)\b", "sql_destructive"),
    (r"\b(sk-|pk-lf-|ghp_|AKIA)[A-Za-z0-9]{10,}", "api_key_leak"),
    (r"(password|passwd)\s*[:=]\s*\S{4,}", "credential_leak"),
    (r"wget\s+.{0,60}\|\s*(sh|bash|python)", "remote_execution"),
    (r"os\.system\s*\(", "os_command_injection"),
]


class InputRail:
    def check(self, text: str) -> RailResult:
        for pattern, threat in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return RailResult(RailDecision.BLOCK, f"Injection : {threat}", threat)
        for pattern, threat in HARMFUL_CONTENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return RailResult(RailDecision.BLOCK, f"Contenu dangereux : {threat}", threat)
        return RailResult(RailDecision.ALLOW)


class OutputRail:
    def check(self, text: str) -> RailResult:
        for pattern, threat in DANGEROUS_OUTPUT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return RailResult(RailDecision.BLOCK, f"Output dangereux : {threat}", threat)
        return RailResult(RailDecision.ALLOW)


# ── RAG chain ─────────────────────────────────────────────────────

RAG_PROMPT = ChatPromptTemplate.from_template("""You are a hardware security expert assistant. \
Answer the question using ONLY the provided context extracted from security documents.
If the answer is not found in the context, say "Information not found in the provided documents."

Context:
{context}

Question: {question}

Answer:""")


def format_docs(docs: list) -> str:
    return "\n\n".join(
        f"[{Path(doc.metadata.get('source', '?')).name}, p.{doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    )


# ── Pipeline integre ─────────────────────────────────────────────

class SecureRAGPipeline:
    def __init__(self):
        self.input_rail = InputRail()
        self.output_rail = OutputRail()
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )

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
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | llm
            | StrOutputParser()
        )

    def invoke(self, user_input: str, run_name: str = "secure_rag") -> dict:
        # Stage 1 — Input Rail
        input_check = self.input_rail.check(user_input)
        if input_check.decision == RailDecision.BLOCK:
            return {
                "status": "BLOCKED",
                "stage": "input",
                "threat": input_check.threat_type,
                "reason": input_check.reason,
                "response": "Requete bloquee : tentative de manipulation detectee.",
            }

        # Stage 2 — RAG + LLM avec LangFuse
        handler = CallbackHandler()
        docs = self.retriever.invoke(user_input)
        sources = [
            f"{Path(d.metadata.get('source','?')).name} p.{d.metadata.get('page','?')}"
            for d in docs
        ]
        response = self.rag_chain.invoke(
            user_input,
            config={"callbacks": [handler], "run_name": run_name},
        )

        # Stage 3 — Output Rail
        output_check = self.output_rail.check(response)
        if output_check.decision == RailDecision.BLOCK:
            return {
                "status": "BLOCKED",
                "stage": "output",
                "threat": output_check.threat_type,
                "reason": output_check.reason,
                "response": "Reponse bloquee : contenu dangereux detecte dans l'output.",
            }

        return {
            "status": "ALLOWED",
            "response": response,
            "sources": sources,
        }
