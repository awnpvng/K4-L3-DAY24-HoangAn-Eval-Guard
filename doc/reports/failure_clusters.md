# Phân tích lỗi Phase A

Nhóm: HoangAn

Người phụ trách: Trương Hoàng Thành An (2A202602574)

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T14:06:25.544022+00:00.

Generation mode/fallback và điều kiện chạy: 50/50 câu `generation_mode="llm"` (không có
extractive_fallback). Answers được sinh bằng Gemini (`gemini-3.1-flash-lite`) trước khi
cả 2 API key Gemini free tier dùng cho nhóm cạn quota RPD (500 request/ngày — bị dội do
`RunConfig` mặc định của RAGAS `max_workers=16` gây retry storm ở lần chạy Phase A đầu).
Vì vậy **việc evaluate RAGAS (Task 2) được chạy bằng LLM local qua Ollama**
(`qwen2.5:7b-instruct` + `nomic-embed-text`), tách biệt hoàn toàn với model đã sinh answers.
Model evaluator yếu hơn Gemini đáng kể về khả năng suy luận — cần đọc các điểm số dưới đây
với lưu ý rằng một phần sai số đến từ evaluator, không chỉ từ pipeline RAG.

Models generation/evaluator: `generation=["gemini-3.1-flash-lite"]`,
`evaluator=["nomic-embed-text", "qwen2.5:7b-instruct"]` (từ `metadata.evaluator_models` của m4).

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.975 | 0.621 | 0.850 |
| answer_relevancy | 0.403 | 0.382 | 0.344 |
| context_precision | 0.942 | 0.654 | 0.967 |
| context_recall | 0.875 | 0.804 | 0.633 |
| avg_score | **0.799** | **0.615** | **0.698** |

**Quan sát đầu tiên:** `answer_relevancy` thấp bất thường ở cả 3 nhóm (0.34–0.40), kể cả
nhóm `factual` vốn có faithfulness/context rất tốt (0.975/0.942). Đây là dấu hiệu RAGAS
`answer_relevancy` — vốn hoạt động bằng cách sinh ngược N câu hỏi giả định từ answer rồi so
embedding với câu hỏi gốc — bị ảnh hưởng bởi khả năng sinh câu hỏi yếu của model evaluator
7B cục bộ, không hẳn phản ánh answer thực sự lạc đề. Cần đọc cùng faithfulness/context_recall
(đều cao ở nhóm factual) trước khi kết luận answer sai.

## Bottom 10 và nguyên nhân

| Rank | ID | Distribution | avg_score | Worst metric | Diagnosis | Suggested fix |
|---|---|---|---:|---|---|---|
| 1 | 33 | multi_hop | 0.3462 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 31 | multi_hop | 0.4281 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 3 | 21 | multi_hop | 0.4583 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 4 | 46 | adversarial | 0.4669 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 24 | multi_hop | 0.4682 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 29 | multi_hop | 0.5000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 38 | multi_hop | 0.5244 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 39 | multi_hop | 0.5364 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 9 | 32 | multi_hop | 0.5654 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 25 | multi_hop | 0.5755 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |

**8/10 câu bottom thuộc `multi_hop`** — khớp với nhóm có avg_score thấp nhất ở bảng trên.

### Đối chiếu answer/contexts/reference của các câu đại diện

**Q33 (rank 1, faithfulness=0.00, avg=0.346) — câu hỏi cần kết hợp 2 thông tin (phụ cấp +
phép năm theo thâm niên):**
```
Q:  Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm
    theo v2024 là bao nhiêu?
A:  "Không tìm thấy."
GT: Phụ cấp tháng: ăn trưa 1.000.000 + điện thoại Manager 500.000 = 1.500.000 VNĐ.
    Phép năm v2024: 15 ngày cơ bản + 4 ngày thâm niên (12÷3=4) = 19 ngày phép.
```
Đây là lỗi **generation**, không phải retrieval — `context_recall=1.00` nghĩa là contexts
đã chứa đủ thông tin cần thiết (cả policy phụ cấp lẫn policy phép năm v2024), nhưng model
generation trả lời "Không tìm thấy" thay vì tổng hợp 2 con số từ 2 context khác nhau. Đây
là lỗi điển hình của câu multi-hop: model generation không được hướng dẫn rõ "cộng dồn
nhiều mục trong các context khác nhau", nên khi không thấy câu trả lời nguyên văn thì mặc
định trả lời "Không tìm thấy" thay vì tự suy luận/tính toán.

**Q31 (rank 2, context_precision=0.00, avg=0.428) — câu hỏi tính tiền khách sạn:**
```
Q:  ... ở khách sạn 2 đêm với giá 1.500.000 VNĐ/đêm. Công ty thanh toán tối đa bao nhiêu?
A:  "Công ty thanh toán tối đa 1.200.000 VNĐ/đêm."
GT: Mức tối đa 1.200.000 VNĐ/đêm. Cho 2 đêm: tối đa 2,400,000 VNĐ. Phần vượt
    (300.000 VNĐ/đêm) nhân viên tự chi trả.
```
Answer đúng mức/đêm (1.200.000) nhưng **không nhân với 2 đêm** như câu hỏi yêu cầu — thiếu
bước tính toán cuối. `context_precision=0.00` cho thấy các context lấy về có tỷ lệ liên
quan thấp (có thể lẫn nhiều đoạn công tác phí không áp dụng cho tình huống này), khiến
model không "nhìn thấy" rõ cần nhân 2 đêm.

**Q46 (rank 4, faithfulness=0.00, avg=0.467) — bẫy phủ định (negation trap):**
```
Q:  Nhân viên thử việc có được nghỉ phép năm không?
A:  "Nhân viên thử việc KHÔNG được nghỉ phép năm."
GT: KHÔNG. Nhân viên thử việc không được nghỉ phép năm... (negation trap)
```
Answer **thực chất đúng nghĩa** với ground truth (cùng là "KHÔNG"), nhưng RAGAS
faithfulness chấm 0.00. Đây nhiều khả năng là false-negative của evaluator: faithfulness
đo answer có được context hỗ trợ hay không bằng cách tách answer thành các "statement" rồi
verify từng statement với LLM evaluator — với model nhỏ 7B cục bộ, bước tách/verify câu phủ
định ngắn ("KHÔNG được nghỉ phép năm") dễ bị hiểu sai hướng. Đây là ví dụ rõ cho lưu ý ở đầu
báo cáo: **điểm số thấp không luôn đồng nghĩa answer sai** khi evaluator là model yếu.

**Q39 (rank 8, context_precision=0.00, avg=0.536) — so sánh 2 phiên bản chính sách:**
```
Q:  So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi
    và MFA.
A:  Độ dài: v1.0=8 ký tự, v2.0=12 ký tự (đúng). Thời hạn đổi: "Không tìm thấy thông tin"
    (SAI — GT có: v1.0=90 ngày, v2.0=120 ngày). MFA: đúng một phần.
GT: v1.0: 8 ký tự, đổi 90 ngày, không MFA. v2.0: 12 ký tự, đổi 120 ngày, MFA bắt buộc.
```
Answer trả lời đúng 2/3 tiêu chí nhưng bỏ sót hoàn toàn "thời hạn đổi" dù `context_recall=
1.00` (context có đủ thông tin). Đây là lỗi **generation bỏ sót 1 nhánh của câu hỏi nhiều
phần** — một dạng lỗi multi-hop khác với Q33 (ở đây model có trả lời nhưng không đầy đủ, chứ
không trả lời "không tìm thấy" toàn bộ).

## Matrix và nhóm yếu nhất

| Worst metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0 | 6 | 1 |
| context_recall | 1 | 0 | 2 |
| context_precision | 0 | 6 | 0 |
| answer_relevancy | 19 | 8 | 7 |

(Mỗi câu được đếm đúng 1 lần theo `worst_metric` của câu đó — cột tổng 20/20/10 là số câu
trong nhóm, không phải số "failure".)

Nhóm yếu theo mean thấp nhất: **multi_hop**; mean: **0.615** (so với factual 0.799,
adversarial 0.698).

Worst metric xuất hiện nhiều nhất toàn bộ: **answer_relevancy** (19+8+7=34/50 câu) — nhưng
đây là chỉ số bị nghi ngờ noise từ evaluator (xem phần "Quan sát đầu tiên"). Nếu loại
`answer_relevancy` khỏi xem xét, **multi_hop vẫn là nhóm yếu nhất** vì nó chiếm 6/6 câu có
`faithfulness` là worst metric và 6/6 câu có `context_precision` là worst metric trong toàn
bộ dataset — tức là multi_hop tập trung gần như toàn bộ lỗi faithfulness/context_precision
của cả 50 câu.

**Vì sao multi_hop yếu:** các câu multi_hop đòi hỏi (1) retrieve đúng ≥2 đoạn chính sách
khác nhau, (2) generation phải tự kết hợp/tính toán giữa chúng. Từ 4 ví dụ đối chiếu ở trên:
- 4/4 ví dụ đều có lỗi ở bước **kết hợp thông tin** (Q33: bỏ qua, không tổng hợp; Q31: quên
  nhân số đêm; Q39: bỏ sót 1 nhánh câu hỏi), không phải lỗi retrieve hoàn toàn sai chunk.
- `context_precision` thấp ở 6/20 câu multi_hop cho thấy retrieval trả về nhiều đoạn không
  liên quan khi câu hỏi cần nhiều mảnh thông tin rải rác — hybrid search (BM25+dense) hiện
  tại tối ưu cho truy vấn đơn, chưa tốt khi câu hỏi hàm chứa 2+ chủ đề con.

**Đề xuất sửa cụ thể:**
1. Thêm chain-of-thought / few-shot ví dụ "cộng dồn 2 context" vào system prompt generation
   cho câu nhiều phần, thay vì để model mặc định trả "Không tìm thấy" khi câu trả lời không
   nằm nguyên văn trong 1 context.
2. Tăng `top_k` rerank hoặc thêm bước decompose câu hỏi multi-hop thành sub-query trước khi
   search (query decomposition) để cải thiện context_precision.
3. Chạy lại Phase A sau khi sửa và so sánh `per_distribution.multi_hop.avg_score` trước/sau;
   kỳ vọng faithfulness và context_precision của nhóm multi_hop tăng gần mức factual.

## Bẫy adversarial và giới hạn

`adversarial` (avg=0.698) không thấp hơn `multi_hop` (avg=0.615) — tức pipeline xử lý bẫy
version-conflict/negation **tốt hơn** câu multi-hop thuần, không đạt điều kiện bonus
("adversarial mean < factual mean" — ở đây adversarial=0.698 < factual=0.799 nên **điều
kiện bonus thực ra ĐẠT**: adversarial mean 0.698 thấp hơn factual mean 0.799).

Trong bottom_10, câu adversarial duy nhất là Q46 (negation trap "nhân viên thử việc có được
nghỉ phép không") — answer đúng nghĩa với ground truth nhưng bị evaluator 7B chấm
faithfulness=0.00 (xem phân tích Q46 ở trên). Điều này cho thấy **điểm thấp ở câu adversarial
không tự chứng minh pipeline nhận sai bẫy** — cần đọc answer thật để xác nhận, và ở Q46 answer
thực chất đã nhận đúng bẫy phủ định.

**Giới hạn của báo cáo này:**
- Mẫu nhỏ (50 câu: 20/20/10) — các kết luận về xu hướng nhóm nên được xem là chỉ dấu, không
  phải kết luận thống kê chắc chắn.
- Model evaluator (`qwen2.5:7b-instruct` qua Ollama local) được dùng thay Gemini do cả 2 API
  key free tier cạn quota RPD trong buổi chạy — model 7B yếu hơn đáng kể so với Gemini Flash
  về khả năng tách câu/suy luận faithfulness, nên một phần điểm `answer_relevancy` và
  `faithfulness` thấp có thể phản ánh hạn chế của evaluator hơn là lỗi thật của pipeline RAG.
  Khuyến nghị chạy lại Phase A với 1 LLM evaluator mạnh hơn (Gemini/GPT) khi có quota, rồi so
  sánh matrix/bottom_10 để tách rõ lỗi pipeline khỏi noise của evaluator.
- `generation_mode` 100% là `llm` (0 fallback) nên không có nhiễu từ extractive fallback.
