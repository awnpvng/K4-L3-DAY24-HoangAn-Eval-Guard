from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, GEMINI_MODEL, TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation.

    Checkpoint/resume theo BATCH nhỏ: gọi ragas.evaluate() nhiều lần (mỗi lần
    1 batch nhỏ) thay vì 1 lần cho toàn bộ 50 câu, và lưu kết quả ngay sau mỗi
    batch thành công vào artifacts/ragas_eval.checkpoint.json. Nếu quota/crash
    giữa chừng, gọi lại hàm này (từ Task 2, vẫn đúng 1 lần theo hợp đồng) sẽ
    tự đọc checkpoint và chỉ evaluate các câu còn thiếu — không mất phần đã
    chạy xong, không tốn lại quota cho câu đã có kết quả.
    """
    n = len(questions)
    try:
        from datasets import Dataset
        from ragas import evaluate, RunConfig
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        # Cả 2 Gemini API key free tier đã cạn quota RPD (500/ngày) hai lần
        # liên tiếp → chuyển sang LLM/embedding chạy local qua Ollama, không
        # giới hạn số request (chỉ giới hạn bởi tốc độ GPU).
        from langchain_community.chat_models import ChatOllama
        from langchain_community.embeddings import OllamaEmbeddings
        from config import OLLAMA_EMBED_MODEL, OLLAMA_NATIVE_URL

        llm = ChatOllama(model=GEMINI_MODEL, base_url=OLLAMA_NATIVE_URL, temperature=0)
        embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_NATIVE_URL)

        # Ollama server mặc định xử lý tuần tự (không có quota ngày/phút để sợ
        # dội) — vẫn giữ concurrency thấp vì GPU 4GB chỉ nên chạy 1-2 request
        # cùng lúc, cao hơn chỉ gây hàng đợi chứ không nhanh hơn.
        run_config = RunConfig(max_workers=2, max_wait=180, max_retries=3)
        evaluator_models = [GEMINI_MODEL, OLLAMA_EMBED_MODEL]

        checkpoint_path = os.path.join(os.path.dirname(TEST_SET_PATH), "..", "artifacts", "ragas_eval.checkpoint.json")
        checkpoint_path = os.path.normpath(checkpoint_path)
        rows_by_index: dict[int, dict] = {}
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, encoding="utf-8") as f:
                saved = json.load(f)
            if saved.get("n") == n:  # chỉ resume nếu đúng số câu của lượt chạy này
                rows_by_index = {int(k): v for k, v in saved.get("rows", {}).items()}
                if rows_by_index:
                    print(f"  ↻ Resume RAGAS từ checkpoint: {len(rows_by_index)}/{n} câu đã có sẵn")

        def _save_checkpoint():
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump({"n": n, "rows": {str(k): v for k, v in rows_by_index.items()}}, f, ensure_ascii=False)

        import math
        metric_keys = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")

        def _is_valid(row):
            return all(math.isfinite(row[k]) for k in metric_keys)

        batch_size = 5
        max_rounds = 3  # tránh vòng lặp vô hạn nếu liên tục dính quota/NaN
        for round_num in range(max_rounds):
            remaining_idx = [i for i in range(n) if i not in rows_by_index]
            if not remaining_idx:
                break
            if round_num > 0:
                print(f"  RAGAS: vòng {round_num + 1}/{max_rounds}, thử lại {len(remaining_idx)} câu bị NaN/lỗi")
            for start in range(0, len(remaining_idx), batch_size):
                batch_idx = remaining_idx[start:start + batch_size]
                dataset = Dataset.from_dict({
                    "question":     [questions[i]     for i in batch_idx],
                    "answer":       [answers[i]       for i in batch_idx],
                    "contexts":     [contexts[i]       for i in batch_idx],
                    "ground_truth": [ground_truths[i] for i in batch_idx],
                })
                result = evaluate(dataset, metrics=[faithfulness, answer_relevancy,
                                                    context_precision, context_recall],
                                   llm=llm, embeddings=embeddings, run_config=run_config)
                df = result.to_pandas()
                for i, (_, row) in zip(batch_idx, df.iterrows()):
                    candidate = {
                        "question": row["question"], "answer": row["answer"],
                        "contexts": list(row["contexts"]), "ground_truth": row["ground_truth"],
                        "faithfulness": float(row.get("faithfulness", float("nan"))),
                        "answer_relevancy": float(row.get("answer_relevancy", float("nan"))),
                        "context_precision": float(row.get("context_precision", float("nan"))),
                        "context_recall": float(row.get("context_recall", float("nan"))),
                    }
                    if _is_valid(candidate):
                        rows_by_index[i] = candidate
                    else:
                        print(f"  ⚠️  Câu idx={i} có metric NaN (job lỗi/quota) — giữ lại cho vòng sau, KHÔNG lưu vào checkpoint")
                # Chỉ lưu các row ĐÃ VALID — không bao giờ checkpoint 1 record NaN,
                # để lần resume sau coi đúng các câu còn thiếu là "remaining".
                _save_checkpoint()
                print(f"  RAGAS: {len(rows_by_index)}/{n} câu hợp lệ đã evaluate")

        still_missing = [i for i in range(n) if i not in rows_by_index]
        if still_missing:
            raise ValueError(
                f"RAGAS: {len(still_missing)}/{n} câu vẫn lỗi/NaN sau {max_rounds} vòng thử lại "
                f"(thường do quota). {len(rows_by_index)} câu hợp lệ đã được giữ trong checkpoint "
                f"'{checkpoint_path}' — chạy lại khi có quota để resume, không mất phần đã xong.")

        per_question = [EvalResult(**rows_by_index[i]) for i in range(n)]
        means = {
            m: sum(r[m] for r in rows_by_index.values()) / n
            for m in metric_keys
        }
        # Đủ n/n câu hợp lệ, không còn gì để resume — dọn checkpoint.
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
        return {**means, "per_question": per_question,
                # PIPELINE_INTERFACE.md: evaluator_models phải là model ID thật đã dùng
                # trong lượt evaluate này (LLM judge + embedding), tách khỏi GENERATION_MODEL/JUDGE_MODEL.
                "metadata": {"evaluator_models": evaluator_models}}
    except ValueError:
        # Lỗi "còn thiếu câu sau max_rounds" ở trên — để hiện rõ nguyên nhân
        # thật (quota) thay vì bị khối except chung dưới đây nuốt mất và trả
        # fallback rỗng. Checkpoint đã được giữ an toàn trước khi raise.
        raise
    except Exception as e:
        print(f"  ⚠️  RAGAS evaluation failed: {e}")
        return {"faithfulness": 0.0, "answer_relevancy": 0.0,
                "context_precision": 0.0, "context_recall": 0.0, "per_question": [],
                "metadata": {"evaluator_models": []}}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    }

    scored = []
    for r in eval_results:
        metrics = {
            "faithfulness": r.faithfulness,
            "answer_relevancy": r.answer_relevancy,
            "context_precision": r.context_precision,
            "context_recall": r.context_recall,
        }
        avg = sum(metrics.values()) / len(metrics)
        worst_metric = min(metrics, key=metrics.get)
        scored.append((avg, worst_metric, metrics[worst_metric], r))

    scored.sort(key=lambda x: x[0])

    results = []
    for avg, worst_metric, worst_score, r in scored[:bottom_n]:
        diagnosis, fix = diagnostic_tree[worst_metric]
        results.append({
            "question": r.question,
            "worst_metric": worst_metric,
            "score": worst_score,
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })
    return results


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
