# Blueprint CI/CD cho RAG và guardrails

Nhóm: HoangAn

Người phụ trách: Trương Hoàng Thành An (2A202602574) + Vũ Việt Hoàng (2A202602398)

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: `artifacts/ragas_50q.json`, `judge_results.json`, `guard_results.json`.

Run timestamp: Phase A `2026-10-12T14:06:25Z`, Phase B xem `metadata.created_at` trong
`judge_results.json`, Phase C `2026-10-12T14:17:44Z`.

**Models theo từng vai trò (quan trọng — đọc trước khi diễn giải số liệu):**
- Generation (sinh 50 answers): `gemini-3.1-flash-lite` (Gemini, lúc API key còn quota).
- Evaluator (RAGAS, Phase A): `nomic-embed-text` + `qwen2.5:7b-instruct` (Ollama local).
- Judge (Phase B): `qwen2.5:7b-instruct` (Ollama local).
- Guard LLM (NeMo self-check, Phase C): `qwen2.5:7b-instruct` (Ollama local).

**Vì sao 3 vai trò cuối dùng model khác generation:** cả 2 API key Gemini free tier dùng cho
nhóm cạn quota RPD (500 request/ngày — reset theo 24h) trong buổi chạy, lần đầu do
`RunConfig` mặc định của RAGAS (`max_workers=16`) gây retry storm, lần sau do chạy lại full
batch nhiều lần khi debug. Quyết định chuyển evaluator/judge/guard sang chạy local qua
Ollama (`qwen2.5:7b-instruct` 7B quantized + `nomic-embed-text`) để không phụ thuộc quota,
đổi lấy tốc độ chậm hơn và chất lượng suy luận yếu hơn Gemini — ảnh hưởng này được phân tích
chi tiết trong `failure_clusters.md` và `bias_report.md`.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

**Data flow đề xuất:**
1. User gửi câu hỏi → **Presidio PII scan** (đồng bộ, nhanh — p95 thực đo 20ms). Nếu phát
   hiện PII (CCCD/CMND/phone VN/email) → chặn ngay, trả lời "Vui lòng không gửi thông tin cá
   nhân trong câu hỏi", log sự kiện (ẩn giá trị PII thật khỏi log, chỉ ghi loại entity).
2. Nếu qua Presidio → **NeMo input rail** (self-check jailbreak/off-topic/prompt injection).
   Nếu bị chặn → trả câu từ chối cấu hình sẵn trong `rails.co`, không gọi RAG (tiết kiệm chi
   phí, giảm latency cho request chắc chắn bị từ chối).
3. Nếu qua input rail → **RAG pipeline** (m1–m5: chunk/search/rerank) → sinh answer.
4. **NeMo output rail**: kiểm tra answer có rò rỉ PII/thông tin nhạy cảm trước khi trả về
   user. Nếu phát hiện → redact/thay bằng câu từ chối (đã verify qua `output_results`: 2/2
   output nhạy cảm bị redact đúng, 2/2 output sạch giữ nguyên).
5. Trả response cho user.

**Failure action theo tầng:**
- Presidio lỗi (timeout/crash) → fail-closed (chặn), vì bỏ sót PII rủi ro cao hơn false
  positive một vài câu.
- NeMo input/output lỗi (LLM provider down, timeout) → đề xuất fail-closed cho output rail
  (ưu tiên không rò rỉ), nhưng fail-open có giám sát cho input rail (ưu tiên availability,
  log lại để review sau) — đây là đề xuất, chưa có cơ chế circuit breaker thực tế trong code.
- Secrets (API key Gemini, nếu dùng lại) giữ trong `.env`, không commit; khi chuyển hẳn sang
  self-host (Ollama) như hiện tại, không cần API key ngoài — giảm rủi ro rò rỉ key nhưng cần
  vận hành/patch bảo mật server Ollama nội bộ.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: **20**; warm-up: **2**; phương pháp: **linear**.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---:|---:|---:|---|
| Presidio | 15.3 | 20.2 | 20.6 | Rất nhanh, ổn định — regex-based, không phụ thuộc LLM |
| NeMo input | 1195.2 | 2923.4 | 3584.7 | Chậm — LLM self-check chạy trên GPU 4GB local (qwen2.5:7b) |
| Input guard sequential | 1214.9 | 2935.8 | 3601.0 | **Vượt budget 500ms** |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; **kết quả thực tế P95=2935.8ms, budget_ok=False**.

**Phân tích bottleneck:** Presidio chiếm <1% tổng latency (20ms/2936ms); gần như toàn bộ độ
trễ đến từ NeMo input rail gọi LLM local (`qwen2.5:7b-instruct` qua Ollama, GPU RTX 4050
4GB VRAM). Đây là đánh đổi trực tiếp của quyết định chuyển sang local LLM để tránh giới hạn
quota Gemini — model cloud (Gemini Flash) có latency per-call thường dưới 1-2s qua API, trong
khi model 7B chạy CPU/GPU-limited local có thể mất 1-4s/call tùy độ dài context & tải máy.
Nếu quay lại dùng Gemini (khi hết giới hạn quota ngày, hoặc dùng billing/key khác), P95 kỳ
vọng giảm đáng kể, nhưng con số đó chưa được đo lại trong lần chạy này — số liệu trên là đo
thật với cấu hình hiện tại (Ollama local), không phải ước lượng.

**Kế hoạch đo phần "chưa đo":** thêm instrumentation (`time.perf_counter()` quanh bước RAG
và output rail) trong `run_query()`/`check_output_rail()` tương tự cách Task 12 đã làm cho
input layers; chạy ≥20 mẫu full-path (input→RAG→output) sau khi đã chốt provider LLM cuối
cùng (Gemini hoặc Ollama), vì latency full-path phụ thuộc trực tiếp provider.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu — **kết quả hiện tại:** factual đạt
  (faithfulness=0.975, avg=0.799), multi_hop và adversarial chưa đạt avg_score ≥0.65
  (0.615 và 0.698). Gate này nên áp dụng theo distribution riêng, không gộp chung, vì
  multi_hop vốn khó hơn factual một cách hệ thống (xem `failure_clusters.md`).
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng — **kết quả hiện tại:**
  attacks 15/20 (đạt mốc lab bắt buộc ≥15/20, chưa đạt mốc CI đề xuất 18/20 — 5/5 miss đều
  thuộc category `off_topic`, model judge 7B chưa đủ tinh để phân biệt câu hỏi lạc đề tinh vi
  với câu hỏi hợp lệ); clean 8/8 đạt (false_positive_rate=0, sau khi sửa lỗi Presidio dùng
  NER tiếng Anh detect sai PERSON trên văn bản tiếng Việt — xem chi tiết trong lịch sử commit
  và `plan.md`); output cases 4/4 đạt.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard — **chưa đo** (xem mục
  latency ở trên); ngay cả input-layer-only P95 hiện tại (2936ms) đã vượt xa target khi dùng
  LLM local, nên gate 500ms full-guard chỉ khả thi khi quay lại dùng LLM cloud nhanh hơn
  hoặc nâng cấp phần cứng GPU.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

**Đề xuất lệnh job (chưa triển khai thành workflow thật — đây là gợi ý cấu trúc):**
```yaml
# .github/workflows/eval-guard-ci.yml (đề xuất, CHƯA tồn tại trong repo)
jobs:
  phase-a:
    steps:
      - run: python scripts/run_experiments.py --phase a --live
      - run: python -c "import json,sys; d=json.load(open('artifacts/ragas_50q.json'));
          sys.exit(0 if d['per_distribution']['factual']['avg_score']>=0.65 else 1)"
  phase-c:
    steps:
      - run: python scripts/run_experiments.py --phase c --live --latency-samples 20
      - run: python -c "import json,sys; d=json.load(open('artifacts/guard_results.json'));
          sys.exit(0 if d['adversarial']['passed']>=18 and d['clean']['passed']==8 else 1)"
```
Script kiểm tra ngưỡng (`MIN_FAITHFULNESS`, `MIN_ATTACKS_PASS`...) là **biến đề xuất**, chưa
có trong `scripts/run_experiments.py`/`check_lab.py` hiện tại — cần code thêm bước so sánh
ngưỡng và trả exit code khác 0 nếu dưới ngưỡng, hiện `check_lab.py` chỉ validate schema/counts
chứ không áp ngưỡng chất lượng.

## Monitoring và cải tiến

**Đề xuất metric cần theo dõi khi lên production:**
- RAGAS 4 metric theo distribution (tách factual/multi_hop/adversarial, không gộp chung) —
  chạy định kỳ trên sample câu hỏi thật từ log, cảnh báo nếu avg_score giảm >10% so với
  baseline.
- False positive rate của guard (clean bị chặn nhầm) — theo dõi liên tục qua canary traffic
  gồm các câu hỏi hợp lệ đã biết, cảnh báo ngay nếu FP rate >0 (khác 0 nghĩa là đổi model/
  config đã làm hỏng behavior, như trường hợp Presidio NER tiếng Anh gặp phải trong lab này).
- Attack pass rate theo category (pii_injection/jailbreak/off_topic riêng, không gộp) — vì
  lab này cho thấy category `off_topic` là điểm yếu riêng biệt của guard LLM nhỏ, cần theo
  dõi tách biệt để biết cải tiến có nhắm đúng chỗ không.
- Latency P95 theo từng layer (Presidio/NeMo input/NeMo output/full request) — tách riêng vì
  lab này cho thấy 99% latency đến từ 1 layer (NeMo+LLM), không phải tổng thể đồng đều.

**Xử lý false positives/drift:** khi phát hiện FP rate tăng (ví dụ sau khi đổi LLM provider
hoặc version model), rollback về config/model trước đó ngay, rồi debug offline bằng cách
chạy lại `clean_set_8.json` qua `pii_scan()`/`check_input_rail()` riêng từng layer để cô lập
layer gây lỗi (bài học rút ra trực tiếp từ lab: lỗi FP 88% ban đầu tưởng do đổi LLM, nhưng
debug cô lập cho thấy nguyên nhân thật là Presidio, không phải LLM).

**Privacy:** không log nội dung PII thật dù chỉ để debug; chỉ log loại entity + vị trí.
Dataset `fixtures/` là dữ liệu kiểm thử giả lập, không phải dữ liệu nhân viên thật.

RAGAS mean/worst distribution: multi_hop yếu nhất (avg=0.615), factual mạnh nhất (avg=0.799).
Cohen's κ: 0.444 (moderate, dưới ngưỡng bonus 0.6 — do judge chạy model 7B local).
Attacks passed: 15/20; clean false_positive_rate: 0.00.

**3-5 câu cải tiến có thể kiểm tra, gắn với bằng chứng của nhóm:**
1. Thêm query decomposition cho câu multi-hop trước khi search, rồi chạy lại Phase A so sánh
   `per_distribution.multi_hop.context_precision` trước/sau (hiện 0.654, thấp nhất trong 3
   nhóm) — kỳ vọng tăng vì 6/20 câu multi_hop có context_precision là worst metric.
2. Thêm few-shot ví dụ "tổng hợp nhiều context" vào generation prompt, chạy lại và so
   `faithfulness` của multi_hop (hiện 0.621, thấp nhất) — 6/20 câu multi_hop có faithfulness
   là worst metric, phần lớn do model trả "Không tìm thấy" thay vì tổng hợp.
3. Bổ sung ví dụ few-shot về nhận diện câu hỏi off-topic tinh vi (thơ, công thức nấu ăn, giá
   coin...) vào `self_check_input` prompt trong `guardrails/config.yml`, chạy lại Phase C và
   kiểm tra cụ thể 5 id đã miss (11,12,13,14,15) có pass không — đây là nhóm lỗi duy nhất
   trong 20 attacks.
4. Khi có lại quota Gemini (hoặc billing), chạy lại cả 3 phase với Gemini làm
   evaluator/judge/guard, so sánh trực tiếp với kết quả Ollama hiện tại để tách rõ "lỗi
   pipeline thật" khỏi "nhiễu từ model evaluator yếu" — đặc biệt với `answer_relevancy`
   (0.34–0.40 ở mọi nhóm, nghi ngờ noise từ evaluator 7B) và 2/3 case Phase B bất đồng với
   human mà bản thân judge tự mâu thuẫn trong reasoning.
5. Đo latency full-path (RAG + output rail + request tổng) theo cùng phương pháp percentile
   tuyến tính đã dùng cho input layers, so sánh P95 giữa cấu hình Ollama local (hiện tại) và
   Gemini cloud để có cơ sở quyết định provider cho production.
