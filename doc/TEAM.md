# Nhóm thực hiện K4 Track 3A

Tên nhóm: HoangAn

Repo chung: https://github.com/awnpvng/K4-L3-DAY24-TruongHoangThanhAn-Eval-Guard

Trưởng nhóm/người nộp: Trương Hoàng Thành An — 2A202602574

Ngày lab/deadline áp dụng: 2026-10-12, 23:59 — Asia/Ho_Chi_Minh (UTC+07:00), theo mặc định
README (chưa có thông báo điều chỉnh riêng từ coach).

Commit dùng để chấm: CHƯA CHỐT — chạy `git rev-parse HEAD` sau khi push commit cuối cùng,
thay dòng này bằng SHA đó rồi commit lại lần nữa trước khi gửi link nộp bài.

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên              | MSSV        | Vai trò / công việc thật | Bằng chứng         |
| --- | ------------------------- | ----------- | ---------------------------- | -------------------- |
| 1   | Trương Hoàng Thành An | 2A202602574 | Trưởng nhóm; môi trường (venv, Docker/Qdrant, 5 module m1–m5); Phase A (`src/phase_a_ragas.py` Tasks 1–4); tổng hợp blueprint; checker/nộp bài | Commit `846be57`, `db3b693`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`; `doc/reports/failure_clusters.md`, `doc/reports/blueprint.md` |
| 2   | Vũ Việt Hoàng          | 2A202602398 | Phase B (`src/phase_b_judge.py` Tasks 5–8: pairwise judge, swap-and-average, Cohen κ, bias report); Phase C (`src/phase_c_guard.py` Tasks 9a–12: PII scan, input/output rail, adversarial suite, latency) | Commit `720fe90`, `16a331d`; `artifacts/judge_results.json`, `artifacts/guard_results.json`; `doc/reports/bias_report.md` |

Người tích hợp/chạy batch/nộp link: Trương Hoàng Thành An — chạy cả 3 runner `--live`
(`scripts/run_experiments.py --phase a/b/c`), xử lý sự cố môi trường/quota, điền báo cáo
cuối cùng và nộp link repo.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 Home Single Language; Python 3.12 (không phải 3.11 như
`ENVIRONMENT.md` khuyến nghị — máy không có sẵn 3.11, build `annoy==1.17.3` vẫn thành công
trên 3.12 sau khi cài đủ Microsoft C++ Build Tools, workload *Desktop development with C++*).

Virtualenv/dependencies/imports: `py -3.12 -m venv .venv` rồi
`pip install -r requirements/requirements.txt -c requirements/constraints-core.txt`.
`pip check` không lỗi sau khi pin lại `datasets>=2.19,<3` + `pyarrow<18` (pip tự chọn
`datasets==5.1.0` nếu không pin, yêu cầu `pyarrow>=24` → `numpy>=2.0`, xung đột với
`numpy==1.26.4` cần cho `ragas`/`langchain`). `import ragas, nemoguardrails,
presidio_analyzer, spacy, google.generativeai` chỉ thành công sau khi xử lý 4 lỗi môi
trường Windows thực tế:
1. **Windows Smart App Control** chặn mọi DLL native (`.pyd`) không rõ nguồn gốc, báo lỗi
   "Application Control policy has blocked this file" — tắt trong Settings → Windows
   Security → App & browser control.
2. **Visual C++ Redistributable** bị hỏng, `import torch` lỗi
   `OSError: DLL initialization routine failed (c10.dll)` — gỡ qua Settings → Apps, cài lại
   `vc_redist.x64.exe`.
3. Ngay cả sau 2 bước trên, `torch` vẫn lỗi khi import **sau** `ragas`/`nemoguardrails` (thứ
   tự import, không phải thiếu thư viện) — `onnxruntime`/`fastembed` (dependency gián tiếp
   của `ragas`/`nemoguardrails`) nạp DLL trước làm `torch` load sau bị lỗi. Fix: thêm
   `import torch` ngay đầu `config.py` (file mọi module khác import đầu tiên).
4. VSCode terminal tự activate nhầm venv phụ (`.venv-tests`, dùng cho test mock nhẹ) thay vì
   venv đầy đủ (`.venv`) — đổi Python Interpreter trong VSCode sang `.\.venv\Scripts\python.exe`.

Models/Qdrant/50 answers đã chuẩn bị: Qdrant chạy qua
`docker compose -f infra/docker-compose.yml up -d` (image pin `v1.9.7`, port 6333-6334
healthy). BGE-M3 (embedding) + BGE-reranker-v2-m3 tải qua `sentence-transformers` lúc chạy
`setup_answers.py --live`. 50 answers sinh bằng Gemini (`gemini-3.1-flash-lite`), 100%
`generation_mode="llm"`, 0 extractive_fallback — xác nhận trong `artifacts/answers_50q.json`.

**Sự cố quota nghiêm trọng và quyết định đổi kiến trúc (ghi lại đầy đủ vì ảnh hưởng toàn bộ
Phase A/B/C — chi tiết trong `plan.md`):** cả 2 API key Gemini free tier dùng cho nhóm cạn
quota RPD (500 request/ngày cho `gemini-3.1-flash-lite`, trước đó còn cạn 20/ngày với
`gemini-3.8-flash` đã bị Google retired khỏi `gemini-2.0-flash` ban đầu) hai lần liên tiếp
trong buổi chạy — nguyên nhân gồm RAGAS `RunConfig` mặc định `max_workers=16` gây retry
storm (mỗi request 429 vẫn tính vào quota dù thất bại), và việc phải chạy lại full batch
nhiều lần khi debug checkpoint. Quyết định: cài **Ollama** (local LLM server, không giới
hạn quota), chuyển toàn bộ evaluator (RAGAS)/judge (Phase B)/guard LLM (NeMo, Phase C) sang
`qwen2.5:7b-instruct` + `nomic-embed-text` chạy trên GPU RTX 4050 Laptop (4GB VRAM). Đổi lấy
tốc độ chậm hơn nhiều (latency P95 input-layer đo được 2936ms, vượt budget 500ms) và chất
lượng suy luận yếu hơn Gemini (κ Phase B = 0.444, không đạt bonus >0.6; 5/20 attack miss ở
category off_topic). Sinh 50 answers (`generation`) vẫn dùng Gemini vì bước đó hoàn thành
trước khi quota cạn — nên `metadata.models.generation` khác hẳn `evaluator`/`judge`/`guard`
trong các artifact, đây là thông tin thật, không phải lỗi.

## INDIVIDUAL

### TruongHoangThanhAn-2A202602574

- Phần được giao và phần thực tế đã làm: Trưởng nhóm, phụ trách CP0 (môi trường, 5 module
  m1–m5 từ bài RAG trước, Qdrant) và Phase A. Thực tế đã làm thêm: debug và sửa toàn bộ lỗi
  môi trường Windows (Smart App Control, VC++ Redistributable, thứ tự import DLL), sửa
  `m2_search.py` (API `qdrant-client` đổi giữa version), sửa `m4_eval.py` (thiếu
  `metadata.evaluator_models` theo `PIPELINE_INTERFACE.md`, thêm checkpoint/resume theo batch
  cho RAGAS), chuyển toàn bộ pipeline (`config.py`, `m5_enrichment.py`, `setup_answers.py`)
  từ Gemini sang Ollama khi quota cạn, viết `failure_clusters.md` và `blueprint.md`.
- Bằng chứng: Commit `846be57`, `db3b693`; `artifacts/answers_50q.json`,
  `artifacts/ragas_50q.json`; `doc/reports/failure_clusters.md`, `doc/reports/blueprint.md`.
- Cách kiểm tra: `pytest tests/test_phase_a.py -q` (6/6 pass, mock); live
  `python scripts/run_experiments.py --phase a --live` (50/50 câu, không NaN).
- Điều đã học: cách checkpoint/resume cho tác vụ gọi LLM dài (chia batch, lưu sau mỗi đơn vị
  nhỏ, không bao giờ lưu record không hợp lệ/NaN vào checkpoint trước khi validate); tầm quan
  trọng của việc kiểm tra concurrency mặc định của thư viện (RAGAS `RunConfig.max_workers=16`)
  trước khi chạy `--live` tốn phí; cách debug lỗi môi trường Windows theo lớp (compiler →
  runtime redistributable → thứ tự import → security policy hệ điều hành).
- Giới hạn/cách xử lý: không có Python 3.11 sẵn trên máy, chấp nhận dùng 3.12 sau khi xác
  nhận build/test pass; không còn quota Gemini miễn phí trong buổi, chuyển hẳn sang Ollama
  local — ảnh hưởng chất lượng evaluator được ghi rõ trong `failure_clusters.md`.
- Nguồn/AI hỗ trợ nếu có: dùng Claude Code (Claude Sonnet 5) hỗ trợ viết code theo đúng
  `PIPELINE_INTERFACE.md`, debug lỗi môi trường, và chạy trực tiếp các lệnh PowerShell/pytest
  qua tool được cấp quyền trên máy của nhóm trưởng. Mọi kết quả trong `artifacts/` đều từ lệnh
  `--live` thật, không phải số do AI tự điền; đã tự kiểm chứng bằng cách đọc lại answer/context/
  reasoning thật trong JSON trước khi viết báo cáo (xem các ví dụ đối chiếu cụ thể trong
  `failure_clusters.md`/`bias_report.md`).

### VuVietHoang-2A202602398

_Ghi chú: 4 mục dưới đây được soạn nháp từ commit/code/kết quả thật của Phase B/C (không
phải lời tự thuật của Vũ Việt Hoàng). Vũ Việt Hoàng cần đọc lại và sửa theo đúng trải nghiệm
bản thân, đặc biệt mục "Điều đã học" và "Nguồn/AI hỗ trợ", trước khi nộp bài._

- Phần được giao và phần thực tế đã làm: Phase B (Tasks 5–8: `pairwise_judge`,
  `swap_and_average`, `cohen_kappa`, `bias_report`) và Phase C (Tasks 9a–12: `pii_scan`,
  `check_input_rail`, `check_output_rail`, `run_adversarial_suite`, `measure_p95_latency`).
- Bằng chứng: Commit `720fe90`, `16a331d`; `artifacts/judge_results.json`,
  `artifacts/guard_results.json`; `doc/reports/bias_report.md`.
- Cách kiểm tra: `pytest tests/test_phase_b.py tests/test_phase_c.py -q` (8/8 + 12/12 pass,
  mock, không gọi API thật); live `run_experiments --phase b/c --live` (5 pairwise + 10
  binary; 20 attacks + 8 clean + 4 output + 20 latency samples).
- Điều đã học: (nháp — cần Vũ Việt Hoàng xác nhận/viết lại theo trải nghiệm thật) kỹ thuật
  swap-and-average giúp phát hiện position bias bằng cách đảo thứ tự A/B rồi quy đổi lại, so
  với chỉ chạy 1 lượt; cách Cohen's κ phân biệt "đồng thuận thật" với "đồng thuận do ngẫu
  nhiên"; Presidio có 2 loại recognizer (pattern-based regex và NLP-based dùng NER), loại
  sau có thể detect sai nặng nếu ngôn ngữ text không khớp ngôn ngữ model NER.
- Giới hạn/cách xử lý: Phase B κ=0.444 chưa đạt bonus — do judge chạy model 7B local
  (`qwen2.5:7b-instruct`) thay Gemini (quota cạn), 2/3 case bất đồng với human là lỗi suy
  luận thật của judge (xem `bias_report.md`). Phase C: lần chạy đầu clean controls chỉ 1/8
  (false_positive_rate 88%) — gốc rễ là Presidio dùng NER tiếng Anh detect sai PERSON trên
  văn bản tiếng Việt, không liên quan LLM; đã sửa bằng cách loại recognizer NLP-based khỏi
  registry, chạy lại đạt 8/8.
- Nguồn/AI hỗ trợ nếu có: (nháp — cần xác nhận) Claude Code (Claude Sonnet 5) được dùng để
  viết code Tasks 5–12 theo đúng `PIPELINE_INTERFACE.md`/hợp đồng test, và chạy trực tiếp các
  lệnh `--live`/pytest trên máy nhóm trưởng. Tự kiểm chứng bằng cách chạy test mock offline
  (8/8 Phase B, 12/12 Phase C pass) trước khi chạy live, và đọc lại reasoning/entities thật
  trong JSON kết quả trước khi viết `bias_report.md`.

## Cập nhật sau khi nộp

Chưa có cập nhật sau deadline. Nếu sửa sau khi nộp, ghi rõ commit SHA, thời điểm sửa, lý do,
và xác nhận đã được coach cho phép áp dụng bản cập nhật trước khi tính vào điểm.
