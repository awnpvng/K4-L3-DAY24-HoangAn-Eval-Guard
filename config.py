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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # Gemini
GEMINI_API_KEY = GOOGLE_API_KEY  # Alias: m4_eval.py/m5_enrichment.py (từ bài Day 18) dùng tên này
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

# --- LLM (Gemini) ---
# gemini-2.0-flash đã bị Google retired (404). gemini-3.8-flash free tier chỉ
# 20 requests/NGÀY — cạn ngay ở bước enrichment. Dùng gemini-3.1-flash-lite
# (quota free tier riêng, cao hơn nhiều) cho generation/judge/enrichment.
GENERATION_MODEL = "gemini-3.1-flash-lite"
JUDGE_MODEL = "gemini-3.1-flash-lite"
GEMINI_MODEL = GENERATION_MODEL  # Alias: m4_eval.py/m5_enrichment.py (từ bài Day 18) dùng tên này
# OpenAI-compatible endpoint của Gemini — cho phép dùng lại `openai` SDK/mock
# test gốc (tests/conftest.py mock module "openai") thay vì đổi hẳn sang
# google.generativeai (sẽ phá mock, khiến unit test gọi API thật).
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# --- Guardrail latency budget ---
LATENCY_BUDGET_P95_MS = 500  # Full guard target; Task 12 currently measures input guards only.
PRESIDIO_LANGUAGE = "en"    # Presidio base language; custom VN recognizers added via PatternRecognizer
