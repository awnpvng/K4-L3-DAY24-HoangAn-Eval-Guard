"""Shared configuration for K4 / Track 3A: Eval + Guardrail Stack."""

# ⚠️ Phải import torch SỚM NHẤT, trước ragas/nemoguardrails/presidio_analyzer.
# Trên Windows, nếu onnxruntime/fastembed (kéo qua ragas/nemoguardrails) nạp
# trước, torch sẽ lỗi "DLL initialization routine failed" khi load c10.dll.
try:
    import torch  # noqa: F401
except ImportError:
    pass

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # Gemini — cả 2 key free tier đã cạn RPD, không còn dùng
GEMINI_API_KEY = GOOGLE_API_KEY  # Alias: m4_eval.py/m5_enrichment.py (từ bài Day 18) vẫn import tên này (không dùng giá trị)
OPENAI_API_KEY = "ollama"  # Alias: scripts/run_experiments.py (starter) chỉ check truthy; Ollama không check giá trị key
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Optional: for HuggingFace models

# --- Qdrant (same as Day 18) ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "lab24_production"
NAIVE_COLLECTION = "lab24_naive"

# --- Embedding (same as Day 18) ---
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# --- Chunking (same as Day 18) ---
HIERARCHICAL_PARENT_SIZE = 2048
HIERARCHICAL_CHILD_SIZE = 256
SEMANTIC_THRESHOLD = 0.85

# --- Search (same as Day 18) ---
BM25_TOP_K = 20
DENSE_TOP_K = 20
HYBRID_TOP_K = 20
RERANK_TOP_K = 3

# --- Paths ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
FIXTURES_DIR = os.path.join(ROOT_DIR, "fixtures")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts")
TEST_SET_PATH = os.path.join(FIXTURES_DIR, "test_set_50q.json")
ANSWERS_PATH = os.path.join(ARTIFACTS_DIR, "answers_50q.json")
HUMAN_LABELS_PATH = os.path.join(FIXTURES_DIR, "human_labels_10q.json")
ADVERSARIAL_SET_PATH = os.path.join(FIXTURES_DIR, "adversarial_set_20.json")
CLEAN_SET_PATH = os.path.join(FIXTURES_DIR, "clean_set_8.json")
OUTPUT_SET_PATH = os.path.join(FIXTURES_DIR, "output_set_4.json")
GUARDRAILS_CONFIG_DIR = os.path.join(ROOT_DIR, "guardrails")
PAIR_QUESTION_IDS = (1, 5, 12, 21, 41)

# --- LLM (local, qua Ollama) ---
# Cả 2 Gemini API key free tier đã cạn quota RPD (500/ngày, reset ~24h) hai lần
# liên tiếp trong cùng buổi chạy — không còn cách nào dùng Gemini hôm nay mà
# không chờ cả nửa ngày. Chuyển hẳn sang LLM chạy local qua Ollama: không giới
# hạn request, nhưng chạy chậm hơn và model nhỏ (7B) suy luận yếu hơn Gemini.
GENERATION_MODEL = "qwen2.5:7b-instruct"
JUDGE_MODEL = "qwen2.5:7b-instruct"
GEMINI_MODEL = GENERATION_MODEL  # Alias: m4_eval.py/m5_enrichment.py (từ bài Day 18) dùng tên này
OLLAMA_EMBED_MODEL = "nomic-embed-text"  # RAGAS context_precision/recall cần embedding riêng
# Ollama expose OpenAI-compatible endpoint tại /v1 — cho phép dùng lại `openai`
# SDK/mock test gốc (tests/conftest.py mock module "openai") không cần sửa gì.
LLM_BASE_URL = "http://localhost:11434/v1"
OLLAMA_NATIVE_URL = "http://localhost:11434"  # cho ChatOllama/OllamaEmbeddings (API gốc, không qua /v1)

# --- Guardrail latency budget ---
LATENCY_BUDGET_P95_MS = 500  # Full guard target; Task 12 currently measures input guards only.
PRESIDIO_LANGUAGE = "en"    # Presidio base language; custom VN recognizers added via PatternRecognizer

# Một số file runner cung cấp sẵn (vd. experiment_runners.py, experiment_support.py)
# gọi `OpenAI()` không tham số — SDK tự đọc OPENAI_API_KEY/OPENAI_BASE_URL từ
# os.environ. Set các biến này trỏ sang Ollama local để những lệnh gọi đó cũng
# dùng đúng endpoint, không cần sửa từng nơi gọi `OpenAI()`.
os.environ.setdefault("OPENAI_API_KEY", OPENAI_API_KEY)
os.environ.setdefault("OPENAI_BASE_URL", LLM_BASE_URL)
