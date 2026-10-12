# PLAN — K4 Track 3A: Production Eval + Guardrail Stack (nhóm 2 người)

Tick `[x]` khi xong. Mỗi bước có 3 nhãn: **người phụ trách** (`R1`/`R2`), **loại hoạt động**, **người hay AI làm**.

**Nhãn hoạt động:** `[setup]` cài đặt · `[code]` viết code · `[test]` chạy test/kiểm tra · `[run]` chạy thực nghiệm thật (tốn API) · `[report]` điền báo cáo · `[submit]` đóng gói/nộp · `[check]` rà soát
**Nhãn người làm:** `[manual]` người tự làm (key, máy, quyết định, đọc số liệu) · `[AI]` nhờ Claude làm · `[manual+AI]` AI soạn, người kiểm chứng

> Quy tắc sống còn (RULES/RUBRIC): không bịa số đo, không dùng ground_truth làm answer, không gửi `human_label`/`human_note` vào prompt judge, không commit `.env`/key. Báo cáo phải dựa trên artifacts thật. Ai dùng AI thì ghi vào mục INDIVIDUAL của mình trong `doc/TEAM.md`. **Mỗi người phải có commit riêng** trong repo chung.

---

## 2 role trong nhóm

> Điền tên thật vào bảng rồi chốt trong `doc/TEAM.md`. Trưởng nhóm = R1 (nộp link).

| Role                                                              | Tên                                    | Tóm tắt                                                                                                                                                                                                                                                                                                                                        | File/Task chính                                                                                                                               | Output                                                                                                       |
| ----------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **R1 — Trưởng nhóm / Integrator + Phase A + Blueprint** | Trương Hoàng Thành An (2A202602574) | Dựng môi trường chung, đưa m1–m5 vào, sinh 50 answers, làm Phase A (RAGAS), tổng hợp blueprint từ số liệu của cả hai người, kiểm tra và nộp bài. R2 phụ thuộc R1 ở khâu`answers_50q.json` (chỉ riêng chạy Phase B live), nên R1 cần xong CP0 sớm.                                                              | `src/m1..m5`, `scripts/setup_answers.py`, `src/phase_a_ragas.py` (Tasks 1–4), `doc/reports/blueprint.md`, `check_lab.py`, nộp link | `answers_50q.json`, `ragas_50q.json`, `failure_clusters.md`, `blueprint.md`, phần chung `TEAM.md` |
| **R2 — Phase B (LLM Judge) + Phase C (Guardrails)**        | {{Tên, MSSV}}                          | Làm toàn bộ phần "đánh giá judge" và "bảo vệ": judge A/B + swap + Cohen κ + bias (Phase B, code ngắn), rồi Presidio PII, NeMo input/output rail, 20 attacks + 8 clean + 4 output, đo latency (Phase C). Phase C độc lập với RAG nên làm trước trong lúc chờ R1 sinh answers; Phase B live chạy sau khi R1 push answers. | `src/phase_b_judge.py` (Tasks 5–8), `src/phase_c_guard.py` (Tasks 9a–12), `guardrails/config.yml`, `rails.co`                        | `judge_results.json`, `guard_results.json`, `bias_report.md`                                           |

**Phụ thuộc:** R1 CP0 (answers) → R2 chạy B live. R2 làm Phase C trước vì chỉ cần `.env`. R1 viết blueprint sau khi R2 có số liệu B và C. Mỗi role tự điền mục `INDIVIDUAL` của mình trong `TEAM.md`.

**Việc chung (cả 2):** cài venv riêng trên máy mình (bước 0.4), đọc `doc/ASSIGNMENT.md` và `doc/RUBRIC.md`, commit phần của mình, giải thích được phần mình khai.

---

## Hiện trạng repo (đã đọc)

- Có: `src/phase_a/b/c_*.py` (còn TODO), runner/checker/support, fixtures, corpus `data/`, schemas, guardrails config, docker-compose, tests.
- **Thiếu:** `src/m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`, `m5_enrichment.py` (lấy từ bài RAG Day 18); `.env`; `artifacts/*.json`.
- `doc/TEAM.md` và 3 báo cáo trong `doc/reports/` còn là mẫu `{{...}}`. Tiêu đề `### }-}` ở mục INDIVIDUAL là mẫu hỏng, mỗi người đổi thành `### TenKhongDau-MSSV`.

---

## CP0 — Chuẩn bị trước lớp

**Chung (R1, R2):**

- [ ] 0.1 `R1 R2` `[setup]` `[manual]` Cài Python 3.11 và Microsoft C++ Build Tools (workload *Desktop development with C++*, cần cho `annoy`); mở lại terminal.
- [ ] 0.2 `R1 R2` `[setup]` `[manual]` Tạo `.env` từ `.env.example`, điền `OPENAI_API_KEY` riêng (không commit). Thống nhất một key chung hoặc mỗi người một key với R1.
- [ ] 0.3 `R1 R2` `[setup]` `[AI]` (Full runtime, R1 làm bước này; R2 có thể bỏ qua nếu dùng venv-tests) Tạo venv và cài:
  ```powershell
  py -3.11 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\python.exe -m pip install -r requirements/requirements.txt -c requirements/constraints-core.txt
  .\.venv\Scripts\python.exe -m pip check
  ```
- [ ] 0.4 `R1` `[test]` `[AI]` (R1 chỉ) Kiểm import full: `.\.venv\Scripts\python.exe -c "import ragas, nemoguardrails, presidio_analyzer, spacy; print('imports OK')"` rồi `.\.venv\Scripts\python.exe -m spacy download en_core_web_lg`.
- [ ] 0.5 `R2` `[setup]` `[AI]` (tuỳ chọn, nhẹ hơn) Venv test: `py -3.11 -m venv .venv-tests` + `requirements-test.lock.txt`. Đủ cho việc viết code + mock test khi full stack chưa cài xong.
- [ ] 0.5b `R2` `[test]` `[AI]` Chạy `pytest tests/ -m support -q` để xác nhận venv-tests hoạt động. Cũng chạy `pytest tests/test_phase_b.py -q` và `pytest tests/test_phase_c.py -q` để xác nhận test fail hiện tại (fail là bình thường, vì hàm TODO chưa implement).

**Riêng R1:**

- [x] 0.6a `R1` `[setup]` `[manual]` Đổi sang Gemini: `.env` dùng `GOOGLE_API_KEY`; `config.py`/`phase_b_judge.py`/`setup_answers.py` chuyển sang `google-generativeai`; thêm delay `time.sleep(4)` để giữ dưới 15 RPM (free tier).
- [x] 0.6b `R1` `[setup]` `[manual]` **Môi trường Windows đã dọn xong** — các lỗi thực tế đã gặp và cách xử lý (xem lại nếu máy khác bị lại):
  - Máy không có Python 3.11 → dùng **Python 3.12** (ENVIRONMENT.md khuyên 3.11, nhưng 3.12 chạy được sau khi xử lý các lỗi dưới).
  - `annoy` build fail (`Microsoft Visual C++ 14.0 required`) → cài **Visual Studio Build Tools**, workload *Desktop development with C++*.
  - `spacy download` / mọi import native module lỗi `DLL ... blocked by Application Control policy` → do **Windows Smart App Control** đang "On" → tắt trong Settings → Windows Security → App & browser control (máy cá nhân mới tắt được; máy domain-joined có WDAC thì không tự tắt được).
  - `import torch` lỗi `OSError: DLL initialization routine failed (c10.dll)` → **Visual C++ Redistributable** bị hỏng → gỡ qua Settings → Apps rồi cài lại `vc_redist.x64.exe`.
  - Sau khi 2 lỗi trên hết, `import ragas, nemoguardrails, presidio_analyzer, ...` vẫn lỗi `c10.dll` — hóa ra do **thứ tự import**: `ragas`/`nemoguardrails` (qua `onnxruntime`/`fastembed`) nạp DLL trước làm `torch` load sau bị lỗi. **Fix cố định:** thêm `import torch` ở đầu `config.py` (file mọi module khác đều import đầu tiên) → không cần nhớ thứ tự import thủ công nữa.
  - `pip install` tự chọn `datasets==5.1.0` (quá mới, cần `pyarrow>=24` → cần `numpy>=2.0`) xung đột với `numpy==1.26.4` bị pin cứng cho `ragas`/`langchain` → thêm lại pin `datasets>=2.19,<3` + `pyarrow<18` vào `requirements.txt`.
  - VSCode terminal tự động activate nhầm `.venv-tests` (venv nhẹ chỉ để R2 test mock) thay vì `.venv` (full runtime) → đổi Python Interpreter trong VSCode (`Ctrl+Shift+P` → *Python: Select Interpreter*) sang `.\.venv\Scripts\python.exe`.
- [x] 0.7 `R1` `[setup]` `[manual]` Cài Docker Desktop, bật Qdrant: `docker compose -f infra/docker-compose.yml up -d` (image pin `v1.9.7`) — đã chạy, container `infra-qdrant-1` healthy port 6333-6334.
- [x] 0.8 `R1` `[setup]` `[manual]` Lấy 5 module m1–m5 từ bài RAG Day 18 của nhóm, chép vào `src/`. Ghi nguồn trong TEAM.
- [x] 0.9 `R1` `[code]` `[AI]` Đối chiếu m1–m5 với `doc/PIPELINE_INTERFACE.md` — đã khớp interface (load_documents/chunk_hierarchical/HybridSearch/CrossEncoderReranker/enrich_chunks), **2 lỗi đã sửa:**
  - m4/m5 dùng tên biến `GEMINI_API_KEY`/`GEMINI_MODEL` (từ bài Day 18) nhưng `config.py` đặt tên `GOOGLE_API_KEY`/`GENERATION_MODEL` → thêm **alias** trong `config.py` (`GEMINI_API_KEY = GOOGLE_API_KEY`, `GEMINI_MODEL = GENERATION_MODEL`).
  - `m4_eval.py` thiếu hẳn key `metadata.evaluator_models` trong dict trả về của `evaluate_ragas()` (bắt buộc theo PIPELINE_INTERFACE.md, Task 2 Phase A cần đọc) → đã thêm `"metadata": {"evaluator_models": [GEMINI_MODEL, "models/gemini-embedding-001"]}`.
  - Thêm `langchain-google-genai>=1.0,<2` vào `requirements.txt` (m4 cần `ChatGoogleGenerativeAI`/`GoogleGenerativeAIEmbeddings`).
- [x] 0.9b `R1` `[test]` `[AI]` Test import toàn bộ 5 module: `python -c "from src.m1_chunking import load_documents, chunk_hierarchical; from src.m2_search import HybridSearch; from src.m3_rerank import CrossEncoderReranker; from src.m4_eval import evaluate_ragas; from src.m5_enrichment import enrich_chunks; print('m1-m5 imports OK')"` — **đã qua**. (Lưu ý: cài `langchain-google-genai` có downgrade `protobuf` xuống 4.25.9 — chưa thấy phá vỡ gì, nhưng nếu `nemoguardrails`/`google-generativeai` báo lỗi protobuf version ở Phase C thì quay lại đây kiểm tra.)
- [x] 0.9c `R1` `[code]` `[AI]` Sửa `m2_search.py` dòng `DenseSearch.search()`: `self.client.query_points(...)` không tồn tại trong `qdrant-client==1.9.2` (pin trong `constraints-core.txt`; API này chỉ có từ 1.10+) → đổi sang `self.client.search(collection_name=..., query_vector=..., limit=...)` (API cũ, trả thẳng `list[ScoredPoint]`).
- [x] 0.9d `R1` `[code]` `[AI]` **Model Gemini đổi 2 lần** vì lý do thật đã gặp khi chạy `--live`:
  - `gemini-2.0-flash` (ban đầu) → Google đã **retired**, API trả 404 gợi ý `gemini-3.8-flash`.
  - `gemini-3.8-flash` → free tier chỉ **20 requests/NGÀY** (không phải RPM!), cạn ngay ở bước enrichment (102 chunks), lỗi 429 "quota exceeded... retry in 12h36m".
  - **Chốt dùng `gemini-3.1-flash-lite`** cho `GENERATION_MODEL`/`JUDGE_MODEL`/`GEMINI_MODEL` (config.py) và `guardrails/config.yml` — quota tính riêng theo từng model, test xác nhận còn quota. Nếu sau này `flash-lite` cũng cạn, kiểm tra lại quota tại https://ai.dev/rate-limit trước khi đổi model khác.
- [x] 0.9e `R1` `[code]` `[AI]` Sửa `src/m5_enrichment.py::enrich_chunks()`: code gốc (từ Day 18) gọi API cho mỗi chunk **không có delay**, dễ dội quota. Thêm `time.sleep(4)` giữa các lần gọi (giữ dưới ~15 RPM).
- [x] 0.9f `R1` `[code]` `[AI]` Sửa `src/phase_b_judge.py::pairwise_judge()`: ban đầu đổi thẳng sang `google.generativeai` SDK làm **hỏng mock test** (`tests/conftest.py` chỉ mock module `openai`) → unit test âm thầm gọi API thật. Sửa lại dùng `openai` SDK trỏ **Gemini OpenAI-compatible endpoint** (`GEMINI_OPENAI_BASE_URL` trong config.py = `https://generativelanguage.googleapis.com/v1beta/openai/`) — giữ nguyên cú pháp OpenAI để mock hoạt động đúng thiết kế gốc. Test Phase B: 8/8 pass, không gọi API thật (9.7s thay vì 22.8s).
- [x] 0.9g `R1` `[code]` `[AI]` Sửa `src/phase_c_guard.py::setup_nemo_rails()`: NeMo 0.10.0 `engine: openai` không tương thích Gemini → thêm `register_llm_provider("gemini", ChatGoogleGenerativeAI)` trước khi load `RailsConfig`; đổi `guardrails/config.yml` sang `engine: gemini`. (Unit test Phase C dùng dependency injection rails/analyzer/anonymizer, không đụng hàm này nên không bị ảnh hưởng.)
- [x] 0.9h `R1` `[code]` `[AI]` **Checkpoint/resume cho `scripts/setup_answers.py`** — theo yêu cầu của người dùng, vì 1 lỗi (quota/crash/network) giữa chừng không được phép làm mất các câu đã xử lý xong. Giờ sau MỖI câu, script ghi ngay vào `artifacts/answers_50q.json.partial.json`; chạy lại tự đọc checkpoint, chỉ gọi API cho câu còn thiếu, không tốn lại quota cho câu đã xong. Khi đủ 50 câu mới ghi file final `answers_50q.json` và xoá checkpoint.
- [x] 0.10 `R1` `[run]` `[manual]` Sinh 50 answers (tốn API Gemini, tải BGE-M3 lâu): `python scripts/setup_answers.py --live`. — **xong ở lần chạy 3** (lần 1 lỗi `query_points`; lần 2 lỗi quota RPD `gemini-3.8-flash`; lần 3 dùng `flash-lite` + checkpoint, 50/50 câu, ~20 phút, 100% `generation_mode=llm`).
- [x] 0.10b `R1` `[run]` `[manual]` **Sự cố nghiêm trọng + bài học:** chạy `run_experiments --phase a --live` lần đầu dùng `RunConfig` mặc định của RAGAS (`max_workers=16`) — vượt xa 15 RPM free tier → **retry storm**: mỗi lần 429 vẫn tính vào quota 500/ngày dù thất bại. Kết quả: cạn sạch quota `gemini-3.1-flash-lite` trong ~19 phút mà **không tạo ra artifact nào** (ước tính ~343/500 request bị phí, chỉ ~152 request trước đó của enrichment+generation là có giá trị thật). Phải đổi sang API key khác (miễn phí, quota riêng theo key) để tiếp tục. **Bài học:** trước khi chạy `--live` ở phase mới, phải kiểm tra concurrency mặc định của mọi thư viện liên quan (ví dụ `ragas.RunConfig`), không chỉ dựa vào delay tự thêm ở tầng ngoài.
- [x] 0.10c `R1` `[code]` `[AI]` Sửa `m4_eval.py::evaluate_ragas()`: thêm `RunConfig(max_workers=2, max_wait=90, max_retries=5)` để giảm concurrency, tránh retry storm.
- [x] 0.10d `R1` `[code]` `[AI]` **Checkpoint/resume cho `m4_eval.py::evaluate_ragas()`** (không phải ở `phase_a_ragas.py::run_ragas_50q()` — thử ban đầu nhưng vi phạm hợp đồng Task 2: test `test_ragas_adapter_preserves_rows` bắt buộc gọi `evaluate_ragas()` **đúng 1 lần** với toàn bộ 50 câu). Giải pháp: `evaluate_ragas()` tự chia batch 5 câu/lần bên trong, lưu `artifacts/ragas_eval.checkpoint.json` sau mỗi batch, nhưng vẫn trả về kết quả gộp đủ cho toàn bộ input như 1 lần gọi duy nhất — Task 2 không đổi gì, test vẫn pass. Verify bằng test 7 câu (2 batch) trước khi chạy full 50 câu.
- [x] 0.10e `R1` `[code]` `[AI]` **Bug nghiêm trọng trong checkpoint 0.10d, đã tự phát hiện và sửa:** Lần chạy full 50 câu đầu tiên, câu cuối dính quota RPD giữa chừng → RAGAS trả `NaN` cho metric đó, nhưng code cũ **vẫn lưu record NaN vào checkpoint** rồi coi đủ 50/50 nên **xóa checkpoint** trước khi validate ở tầng ngoài phát hiện NaN và raise lỗi → mất sạch 49 câu hợp lệ đã tính, phải chạy lại từ đầu. Sửa: (1) record có metric không phải `math.isfinite` thì **không được lưu** vào checkpoint, để lần sau coi là "còn thiếu" và tự retry; (2) thêm tối đa 3 vòng retry cho các câu còn thiếu; (3) nếu sau 3 vòng vẫn thiếu, `raise ValueError` nêu rõ do quota + checkpoint đã giữ bao nhiêu câu hợp lệ, và **re-raise riêng** (không để khối `except Exception` chung nuốt mất, tránh trả fallback rỗng gây hiểu lầm).
- [x] 0.10f `R1` `[run]` `[manual]` **Cạn quota RPD lần 3 (cả 2 key)** — key mới cũng cạn 500/ngày ngay khi chạy lại full 50 câu (cộng dồn với lần test trước + lần chạy lỗi trước đó). **Quyết định: bỏ hẳn Gemini, chuyển sang LLM chạy local qua Ollama** (không giới hạn quota, đổi lấy tốc độ chậm hơn + model nhỏ yếu hơn).
- [x] 0.10g `R1` `[setup]` `[manual]` Cài Ollama (`winget install Ollama.Ollama`), tải `qwen2.5:7b-instruct` (LLM, ~4.7GB) + `nomic-embed-text` (embedding cho RAGAS, ~274MB). Máy có RTX 4050 Laptop (4GB VRAM) + 15GB RAM — đủ chạy model 7B quantized.
- [x] 0.10h `R1` `[code]` `[AI]` **Chuyển toàn bộ pipeline sang Ollama**, tận dụng kiến trúc OpenAI-compat đã có sẵn từ lúc dùng Gemini (Ollama tự expose endpoint `/v1` tương thích OpenAI):
  - `config.py`: `GENERATION_MODEL`/`JUDGE_MODEL`/`GEMINI_MODEL` = `"qwen2.5:7b-instruct"`; thêm `OLLAMA_EMBED_MODEL`, `LLM_BASE_URL` (`http://localhost:11434/v1`), `OLLAMA_NATIVE_URL` (`http://localhost:11434`); `OPENAI_API_KEY`/`OPENAI_BASE_URL` trong `os.environ` trỏ Ollama thay Gemini.
  - `phase_b_judge.py::pairwise_judge()`: chỉ đổi `base_url`/`api_key` sang Ollama — không cần sửa gì khác (đã dùng `openai` SDK từ trước).
  - `setup_answers.py::run_query()`: đổi từ `google.generativeai` sang `openai` SDK + Ollama (đồng bộ cách làm với phase_b_judge).
  - `m5_enrichment.py`: viết wrapper `_OllamaCompat` giả lập interface `.generate_content(prompt).text` của `genai.GenerativeModel` — giữ nguyên 5 hàm gọi (summarize/HyQA/contextual/metadata/combined), chỉ đổi 1 chỗ khởi tạo.
  - `m4_eval.py::evaluate_ragas()`: đổi `ChatGoogleGenerativeAI`/`GoogleGenerativeAIEmbeddings` → `ChatOllama`/`OllamaEmbeddings` (từ `langchain_community`, đã có sẵn, không cần cài gì thêm); bỏ hẳn class `_GeminiLLM` hack (temperature kwarg bug chỉ có ở Gemini, Ollama không bị).
  - `phase_c_guard.py::setup_nemo_rails()` + `guardrails/config.yml`: đổi `register_llm_provider("gemini", ...)` → `register_llm_provider("ollama", ChatOllama)`; `engine: ollama`, `model: qwen2.5:7b-instruct`, `parameters.base_url: http://localhost:11434`.
  - Bỏ hết các `time.sleep(4)` thêm trước đó để né RPM — Ollama local không cần.
- [x] 0.10i `R1` `[test]` `[AI]` Verify từng lớp trước khi chạy full: (1) `pytest` 26/26 vẫn pass sau khi đổi provider (mock không bị ảnh hưởng); (2) OpenAI SDK gọi Ollama + JSON mode: OK, ~5s/request; (3) `evaluate_ragas()` 3 câu qua Ollama: OK, 93s, không NaN; (4) `check_input_rail()` qua NeMo+Ollama: clean input allowed, jailbreak input blocked đúng.
- [x] 0.11 `R1` `[check]` `[AI]` Kiểm `artifacts/ragas_50q.json`: 50 per_question, 4 metric hữu hạn [0,1], evaluator_models = `["nomic-embed-text", "qwen2.5:7b-instruct"]` — **đạt**.
- [x] 0.12 `R1` `[submit]` `[manual]` Commit + push `answers_50q.json` + `ragas_50q.json` — **đã commit**.
- [x] 0.14 `R2` `[run]` `[manual]` `run_experiments --phase b --live`: 5 pairwise + 10 binary, κ=0.444 (moderate, chưa đạt bonus >0.6 — model 7B local judge yếu hơn Gemini, dự đoán trước). Đã commit `judge_results.json`.
- [x] 0.15 `R2` `[run]` `[manual]` **`run_experiments --phase c --live` lần 1: FAIL rubric** — attacks 20/20 (vượt cả mức bonus) nhưng **clean controls chỉ 1/8, false_positive_rate=0.88** (rubric bắt buộc 8/8).
- [x] 0.16 `R2` `[code]` `[AI]` **Debug + sửa `setup_presidio()`:** không liên quan gì tới việc đổi LLM — lỗi nằm ở chính Presidio. `registry.load_predefined_recognizers()` tải cả recognizer NLP-based (`SpacyRecognizer`, hỗ trợ PERSON/LOCATION/DATE_TIME/NRP, dùng NER `en_core_web_lg`). spaCy NER tiếng Anh không hiểu tiếng Việt → đoán bừa câu tiếng Việt bất kỳ thành "PERSON" với score 0.85, chặn nhầm gần hết câu sạch. Thêm 1 lỗi nhỏ nữa: `US_DRIVER_LICENSE` khớp "v2" (trong "v2.0") score 0.3. Sửa: loại cả 2 recognizer này khỏi registry (không liên quan đề bài — chỉ cần CCCD/CMND/phone/email VN), giữ nguyên các recognizer pattern-based khác. Verify: 8/8 clean → ok, PII attacks vẫn detect đúng (4/5 qua Presidio, câu còn lại là "yêu cầu lộ PII" không chứa data thật nên đúng ra phải bị chặn ở layer 2 NeMo, không phải lỗi).
- [ ] 0.17 `R2` `[run]` `[manual]` Chạy lại `run_experiments --phase c --live --latency-samples 20` với Presidio đã sửa.
- [ ] 0.13 `R1` `[report]` `[manual]` Ghi OS/Python/compiler/kết quả pip, import, model, Qdrant vào mục "Môi trường" của `doc/TEAM.md` — **kể cả các lỗi thật đã gặp ở 0.6b/0.9c-0.9h/0.10b/0.15-0.16** (đây chính là bằng chứng môi trường, rubric yêu cầu ghi lỗi thật, không ghi "tương thích" chung chung).

**Nguyên tắc checkpoint áp dụng cho mọi phase tốn API (theo yêu cầu người dùng):** không bao giờ để 1 request lỗi giữa chừng làm mất toàn bộ tiến trình đã chạy. Mẫu chung: chia nhỏ theo batch/câu, lưu file `*.checkpoint.json`/`*.partial.json` ngay sau mỗi đơn vị nhỏ hoàn thành, đọc lại khi resume, dọn file khi xong hẳn. Đã áp dụng cho `setup_answers.py` (0.9h) và `m4_eval.evaluate_ragas()` (0.10d); cần áp dụng tương tự cho Phase B (`run_phase_b` — 5 cặp + 10 binary) và Phase C (`run_adversarial_suite`, latency) trước khi chạy `--live`.

---

## Phase A — RAGAS + phân tích lỗi — **R1** (`src/phase_a_ragas.py`)

- [ ] A1 `R1` `[code]` `[AI]` Task 1 `group_by_distribution`: 3 key, 20/20/10.
- [ ] A2 `R1` `[code]` `[AI]` Task 2 `run_ragas_50q`: gọi `m4.evaluate_ragas`, ép `float()`, trả `RagasEvaluation(results, raw["metadata"]["evaluator_models"])`; lỗi nếu thiếu, không đoán.
- [ ] A3 `R1` `[code]` `[AI]` Task 3 `bottom_10`: 10 câu `avg_score` tăng dần, đủ rank/id/question/distribution/worst_metric/diagnosis/suggested_fix.
- [ ] A4 `R1` `[code]` `[AI]` Task 4 `cluster_analysis`: matrix worst_metric × distribution (mỗi câu đếm 1 lần), nhóm yếu = **mean avg_score thấp nhất** (không phải nhóm lớn nhất), bỏ nhóm rỗng, insight có nghĩa.
- [ ] A5 `R1` `[test]` `[AI]` `python -m pytest tests/test_phase_a.py -q` xanh.
- [ ] A6 `R1` `[run]` `[manual]` `python scripts/run_experiments.py --phase a --live` → `artifacts/ragas_50q.json`.
- [ ] A7 `R1` `[check]` `[manual]` 50 per_question, 4 metric hữu hạn [0,1], 10 bottom rows, không NaN.
- [ ] A8 `R1` `[report]` `[manual+AI]` Điền `doc/reports/failure_clusters.md`: bảng điểm, 10 dòng bottom, đối chiếu answer/contexts/ground_truth câu đại diện, matrix, nhóm yếu, đề xuất sửa. Người đọc lại câu yếu để xác nhận nguyên nhân (retrieval hay generation, bẫy phiên bản/phủ định).
- [ ] A9 `R1` `[report]` `[manual+AI]` (Bonus +4) Nếu adversarial mean < factual mean, phân tích bẫy version conflict (`nghi_phep_nam_v2023/v2024`, `mat_khau_v1/v2`). Không hạ chất lượng answers hay sửa test set.
- [ ] A10 `R1` `[submit]` `[manual]` Commit + push, ghi các số để dùng cho blueprint: mean theo distribution, worst distribution, evaluator models.

---

## Phase B — Pairwise judge + Cohen κ — **R2** (`src/phase_b_judge.py`)

**Chiến lược:** Viết 1 hàm → chạy test cho hàm đó → xanh → commit → chuyển sang hàm tiếp theo. Dùng `.\.venv-tests\Scripts\python.exe -m pytest` để chạy test.

- [ ] B1 `R2` `[code]` `[AI]` Task 5 `pairwise_judge`: prompt dùng reference, ép JSON `winner` A/B/tie + `reasoning` + `scores` [0,1]; dùng `JUDGE_MODEL`.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_b.py::test_pairwise_uses_json_judge -q` → xanh.
  - Commit: `git add src/phase_b_judge.py && git commit -m "Task 5: pairwise_judge"`.
- [ ] B2 `R2` `[code]` `[AI]` Task 6 `swap_and_average`: 2 lượt (A,B) và (B,A) cùng reference; quy winner/scores lượt 2 về A/B gốc; đồng thuận hoặc `tie`.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_b.py::test_swap_conversion_and_calls -q` → xanh.
  - Commit: `git add src/phase_b_judge.py && git commit -m "Task 6: swap_and_average"`.
- [ ] B3 `R2` `[code]` `[AI]` Task 7 `cohen_kappa`: tính tay, xử lý `p_e == 1` (mixed perfect agreement = 1), kết quả trong [-1,1].
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_b.py::test_kappa_exact -q` → xanh.
  - Commit: `git add src/phase_b_judge.py && git commit -m "Task 7: cohen_kappa"`.
- [ ] B4 `R2` `[code]` `[AI]` Task 8 `bias_report`: position inconsistency count/rate, verbosity (winner dài hơn / decisive), `verbosity_details`, `interpretation`.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_b.py::test_bias_known_counts -q` → xanh.
  - Commit: `git add src/phase_b_judge.py && git commit -m "Task 8: bias_report"`.
- [ ] B5 `R2` `[test]` `[AI]` Chạy toàn bộ: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_b.py -q` toàn bộ xanh (6 test).
- [ ] B6 `R2` `[run]` `[manual]` Sau khi R1 đã push `answers_50q.json`: `python scripts/run_experiments.py --phase b --live` → `artifacts/judge_results.json` (5 cặp id 1,5,12,21,41 × 2 lượt + 10 binary judgments).
- [ ] B7 `R2` `[check]` `[manual]` 10 binary label là integer 0/1, đúng `model_answer` gốc, κ tính từ nhãn thật, không có `human_label`/`human_note` trong prompt.
- [ ] B8 `R2` `[report]` `[manual+AI]` Điền `doc/reports/bias_report.md`: 5 hàng cặp A/B, position bias, verbosity, bảng 10 nhãn judge vs human, κ, observed/chance agreement, case lệch, giới hạn (10 nhãn, 5 cặp). Đọc nội dung các case không nhất quán trước khi kết luận "bias".
- [ ] B9 `R2` `[report]` `[manual]` (Bonus +3) κ > 0.6. Nếu thấp thì báo cáo trung thực, không sửa prompt để rò nhãn human.
- [ ] B10 `R2` `[submit]` `[manual]` Commit + push, ghi số để dùng cho blueprint: κ, position bias rate, verbosity rate, judge model.

---

## Phase C — Guardrails — **R2** (`src/phase_c_guard.py`)

**Chiến lược:** Viết 1–2 hàm → chạy test → xanh → commit. Phase C phức tạp hơn nên có thể viết 2 hàm (9a+9b hoặc 11+12) rồi test.

- [ ] C1 `R2` `[code]` `[AI]` Task 9a `pii_scan`: Presidio detect + anonymize CCCD/CMND, SĐT VN, email; entities có start/end và `anonymized`.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py::test_pii_detect_and_redact -q` → xanh (4 test).
- [ ] C2 `R2` `[code]` `[AI]` Task 9b `check_input_rail` (async): `generate_async` với `options={"rails":["input"],"log":{"activated_rails":True}}`, quyết định từ `rail.stop`, **không** đoán bằng từ khoá "xin lỗi/không thể".
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py::test_input_uses_rail_decision -q` → xanh (2 test).
  - Commit: `git add src/phase_c_guard.py && git commit -m "Tasks 9a-9b: PII + input rail"`.
- [ ] C3 `R2` `[code]` `[AI]` Task 11 `check_output_rail` (async): output rail trên cặp user/assistant; output sạch giữ nguyên, output nhạy cảm bị thay/redact.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py::test_output_checks_supplied_answer -q` → xanh (2 test).
- [ ] C4 `R2` `[code]` `[AI]` Task 10 `run_adversarial_suite`: nhận list input bất kỳ (runner đưa 28 = 20 attacks + 8 clean), Presidio → NeMo, giữ nguyên `input`, `expected` chỉ để đối chiếu `passed`; một `asyncio.run` duy nhất.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py::test_attack_and_clean_control -q` → xanh.
  - Commit: `git add src/phase_c_guard.py && git commit -m "Tasks 11+10: output rail + adversarial suite"`.
- [ ] C5 `R2` `[code]` `[AI]` Task 12 `measure_p95_latency`: tạo engine trước, 2 warm-up thật bị loại, ≥20 mẫu timed, luôn đo cả Presidio và NeMo (không short-circuit), `perf_counter`, `summarize_latency(..., warmup_runs=2)`.
  - Sau khi viết: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py::test_latency_real_warmup_and_sample_count -q` → xanh.
  - Commit: `git add src/phase_c_guard.py && git commit -m "Task 12: latency measurement"`.
- [ ] C6 `R2` `[test]` `[AI]` Chạy toàn bộ: `.\.venv-tests\Scripts\python.exe -m pytest tests/test_phase_c.py -q` toàn bộ xanh (12 test).
- [ ] C7 `R2` `[check]` `[manual]` Rà `guardrails/config.yml` và `rails.co`; nếu clean bị chặn nhầm hoặc attacks lọt thì chỉnh policy prompt (xem `fixtures/adversarial_set_20.json`, `clean_set_8.json`).
- [ ] C8 `R2` `[run]` `[manual]` `python scripts/run_experiments.py --phase c --live --latency-samples 20` → `artifacts/guard_results.json`.
- [ ] C9 `R2` `[check]` `[manual]` Attacks ≥15/20, clean 8/8 allowed (false_positive_rate = 0), 4 output cases đúng, ≥20 mẫu latency dương. Chưa đạt thì sửa config rồi chạy lại. Latency vượt 500ms vẫn ghi đúng số.
- [ ] C10 `R2` `[report]` `[manual]` (Bonus +3) attacks ≥18/20 kèm clean 8/8.
- [ ] C11 `R2` `[submit]` `[manual]` Commit + push, ghi số để R1 dùng cho blueprint: attacks passed, false_positive_rate, P50/P95/P99, guard models.

---

## Task 13 — Blueprint (R1) & TEAM (cả 2)

- [ ] D1 `R1` `[report]` `[manual+AI]` Điền `doc/reports/blueprint.md`: data flow Input → Presidio → NeMo input → RAG → NeMo output, failure action, bảng latency từ JSON (RAG/output/full guard ghi "chưa đo" + kế hoạch đo), CI gates **đề xuất** (nói rõ chưa triển khai), monitoring, 3–5 cải tiến gắn bằng chứng, dùng số từ A10, B10 và Phase C (R2 gửi: attacks passed, false_positive_rate, P50/P95/P99, guard models).
- [ ] D2 `R1` `[report]` `[manual]` `doc/TEAM.md` phần chung: tên nhóm, link repo, trưởng nhóm, deadline (23:59 ngày lab, UTC+07:00), bảng phân công 2 người + bằng chứng commit.
- [ ] D3 `R1 R2` `[report]` `[manual]` Mỗi người điền mục `INDIVIDUAL` của mình (việc thật, bằng chứng, cách kiểm tra, điều học được, giới hạn, AI hỗ trợ và cách tự kiểm chứng). Sửa tiêu đề `### }-}`.
- [ ] D4 `R1` `[check]` `[AI]` Quét `{{`, `TODO`, `?` còn sót trong `doc/reports/*.md`, `doc/TEAM.md`, `src/phase_*.py`.

---

## Đóng gói & nộp (R1)

- [ ] E1 `R1` `[check]` `[AI]` Pull bản mới nhất của cả nhóm, chạy `python scripts/check_lab.py` (hoặc `--with-tests`). Sửa đến khi qua hết; không chạy `pytest -m integration --run-live` thêm nếu artifacts đã có (tránh trả phí 2 lần).
- [ ] E2 `R1` `[check]` `[manual]` Quét secrets: không có `.env`, key, venv, cache model trong `git status`; PII trong báo cáo chỉ là dữ liệu mẫu.
- [ ] E3 `R1` `[check]` `[AI]` `git check-ignore artifacts/answers_50q.json artifacts/ragas_50q.json artifacts/judge_results.json artifacts/guard_results.json` không in gì.
- [ ] E4 `R1` `[check]` `[manual]` Xác nhận `git log` có commit của cả 2 thành viên.
- [ ] E5 `R1` `[submit]` `[manual]` Đổi tên repo thành `K4-L3-DAY24-TenNhom-Eval-Guard` nếu chưa đúng; push.
- [ ] E6 `R1` `[submit]` `[manual]` Ghi `git rev-parse HEAD` vào `doc/TEAM.md` ("Commit dùng để chấm"), commit/push lại, mở đúng commit trên GitHub để xác nhận artifacts có mặt.
- [ ] E7 `R1` `[submit]` `[manual]` Nộp link repo qua vlearn trước **23:59 ngày lab** (hoặc theo thông báo coach).

---

## Bảng điểm tham chiếu

| Phần                                         | Role | Điểm | Bonus                                               |
| --------------------------------------------- | ---- | -----: | --------------------------------------------------- |
| Phase A (T1 5, T2 10, T3 7, T4 8)             | R1   |     30 | +4 adversarial mean < factual mean, có phân tích |
| Phase B (T5 10, T6 10, T7 10, T8 5)           | R2   |     35 | +3 κ > 0.6                                         |
| Phase C (T9a 10, T9b 5, T10 10, T11 5, T12 5) | R2   |     35 | +3 attacks ≥18/20 và clean 8/8                    |

R1 gánh thêm môi trường, m1–m5 và nộp bài (không có điểm riêng nhưng chặn cả nhóm), nên R2 nên hỗ trợ R1 khi cài đặt gặp lỗi.

**Trừ điểm:** còn `# TODO` trong `phase_*.py` (−5/module), student test fail (−3/test), blueprint trống/placeholder (−10), thiếu `answers_50q.json` (Phase A = 0).
