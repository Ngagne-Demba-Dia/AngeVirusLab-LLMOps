import os
from dotenv import load_dotenv

load_dotenv()

# llama3.1:8b required — llama3:8b (v3.0) does not support the Ollama tool calling API
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
