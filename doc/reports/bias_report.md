# Đánh giá LLM Judge Phase B

Nhóm: HoangAn

Người phụ trách: Vũ Việt Hoàng — 2A202602398

Nguồn: `artifacts/judge_results.json`; run timestamp: xem `metadata.created_at` trong file.

Models generation/judge: `generation=["gemini-3.1-flash-lite"]`,
`judge=["qwen2.5:7b-instruct"]`. Judge chạy local qua Ollama vì cả 2 API key Gemini free
tier dùng cho nhóm đã cạn quota RPD (500 request/ngày) trong buổi chạy — xem giải thích
chi tiết trong `doc/reports/failure_clusters.md`. Đây là model nhỏ hơn và yếu hơn Gemini
đáng kể về suy luận, cần tính đến khi đọc các nhận xét dưới đây.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ `artifacts/answers_50q.json:answer`; B từ
`fixtures/human_labels_10q.json:model_answer`; reference từ
`fixtures/test_set_50q.json:ground_truth`. Ids: 1, 5, 12, 21, 41. Nguồn không đổi sau khi
xem kết quả judge.

| ID | len(A) | len(B) | Pass 1 | Pass 2 (quy về A/B gốc) | Final | Consistent |
|---|---:|---:|---|---|---|---|
| 1  | 48  | 57 | B | B | **B** | ✅ |
| 5  | 30  | 33 | A | A | **A** | ✅ |
| 12 | 85  | 50 | A | A | **A** | ✅ |
| 21 | 189 | 82 | B | A | **tie** | ❌ |
| 41 | 62  | 37 | A | A | **A** | ✅ |

Position bias count/rate: **1/5 (20%)** — cặp id=21.
Verbosity win rate: **0.75** (3/4 case quyết định, winner là candidate dài hơn); decisive
cases: **4** (loại case id=21 vì final="tie").

### Case không nhất quán — id=21

```
A (189 ký tự): "...9 năm thâm niên được hưởng 18 ngày phép... Thông tin về khoảng lương
               không được đề cập trong context."
B (82 ký tự):  "Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến
               35 triệu."
Pass 1 (A,B):  winner=B. Reasoning: "Answer B cung cấp đầy đủ thông tin về số ngày phép
               và khoảng lương theo chính sách."
Pass 2 (B,A):  winner (quy đổi)=A. Reasoning: "Trả lời B đầy đủ về ngày phép và chính xác
               về số ngày phép. Trả lời A thêm thông tin về lương nhưng không có trong
               context."
```

Điều đáng chú ý: **reasoning của Pass 2 vẫn mô tả B tốt hơn A** ("B đầy đủ... A thêm thông
tin không có trong context" — câu này thực chất là lý do để chọn B, không phải A), nhưng
`winner` cuối cùng model trả lại là candidate tương ứng với A. Đây không phải vị trí bias
cổ điển (ưu tiên câu xuất hiện trước/sau cố định) mà là **judge tự mâu thuẫn giữa reasoning
và quyết định** — một hạn chế điển hình của model nhỏ 7B: nó sinh lý luận đúng hướng nhưng
không map được lý luận đó sang nhãn `winner` chính xác. Swap-and-average đã làm đúng việc
của nó: phát hiện mâu thuẫn và trả về `tie` thay vì chọn liều một bên.

### Verbosity bias

| Case | Final winner | len(winner) vs len(loser) |
|---|---|---|
| id=1 | B (57) | dài hơn A (48) |
| id=5 | A (30) | ngắn hơn B (33) |
| id=12 | A (85) | dài hơn B (50) |
| id=41 | A (62) | dài hơn B (37) |

3/4 case quyết định, judge chọn candidate dài hơn → verbosity_bias=0.75. **Đây là dấu hiệu
thống kê, không phải kết luận nguyên nhân** — cần đọc nội dung: ở id=12 và id=41, answer dài
hơn (A, từ pipeline RAG) thực sự chứa nhiều chi tiết chính sách cụ thể hơn answer ngắn (B),
nên việc judge chọn candidate dài hơn ở 2 case này phù hợp với chất lượng nội dung thực tế,
không hẳn là bias độ dài thuần túy. Case id=1 (B dài hơn thắng) cần xem thêm nội dung cụ thể
để kết luận chắc chắn, nhưng với n=4 case quyết định, mẫu quá nhỏ để khẳng định verbosity
bias là vấn đề hệ thống — chỉ nên xem là tín hiệu cần theo dõi khi có nhiều cặp judge hơn.

## Calibration đúng model_answer

Helper đánh giá đúng `question`/`model_answer` lấy nguyên văn từ
`fixtures/human_labels_10q.json`; không dùng answer mới của pipeline. Prompt chỉ nhận
question, answer, reference — không gửi `human_label`/`human_note` vào judge (đúng yêu cầu
`doc/ASSIGNMENT.md`).

| question_id | model_answer (rút gọn) | judge label | judge reasoning (rút gọn) | human label | agree |
|---|---|---:|---|---:|---|
| 1  | (đúng nghỉ phép theo v2024) | 1 | — | 1 | ✅ |
| 5  | (đáp án sai chính sách) | 0 | — | 0 | ✅ |
| 12 | "Thưởng Tết tối thiểu 1 tháng lương" | 0 | Thiếu điều kiện ≥6 tháng làm việc | **1** | ❌ |
| 21 | (đúng 18 ngày phép + lương) | 1 | — | 1 | ✅ |
| 23 | (đúng) | 1 | — | 1 | ✅ |
| 29 | (sai) | 0 | — | 0 | ✅ |
| 33 | "Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng" | 0 | "Thiếu ý về số ngày phép năm (nên là 19 ngày)" | **1** | ❌ |
| 41 | (sai) | 0 | — | 0 | ✅ |
| 46 | "Nhân viên thử việc không được nghỉ phép năm, phải xin nghỉ không lương nếu cần" | 0 | "Câu trả lời sai bởi nó phủ định... không được nghỉ phép năm, trong khi thực tế là họ không được nghỉ phép năm" | **1** | ❌ |
| 50 | (sai) | 0 | — | 0 | ✅ |

7/10 đồng thuận. **Cohen's κ = 0.444** (thang Landis-Koch: moderate agreement, 0.4–0.6).

### Phân tích 3 case bất đồng — đây là lỗi thật của judge, không phải mơ hồ trong đề bài

- **id=33**: model_answer là *"Phép: **19 ngày**. Phụ cấp: 1.500.000 VNĐ/tháng"* — câu trả
  lời **đã có đúng con số 19 ngày**. Nhưng judge reasoning lại viết "thiếu ý về số ngày phép
  năm (nên là 19 ngày)" — **tự mâu thuẫn với chính nội dung answer đang đọc**. Đây là lỗi
  đọc/suy luận của model 7B, không phải mơ hồ trong tiêu chí chấm.
- **id=46**: model_answer nói "KHÔNG được nghỉ phép năm" — đúng với reference (cũng là
  "KHÔNG"). Judge reasoning viết: *"Câu trả lời sai bởi nó phủ định... không được nghỉ phép
  năm, trong khi thực tế là họ không được nghỉ phép năm"* — câu reasoning này **tự phủ định
  chính nó** (nói "X sai vì nó nói Y, trong khi thực tế đúng là Y"). Một lỗi suy luận logic rõ
  ràng của judge model.
- **id=12**: model_answer bỏ sót điều kiện "≥6 tháng làm việc" khi nói về thưởng Tết. Đây là
  case duy nhất trong 3 case bất đồng mà lý do judge đưa ra **hợp lý và nhất quán** (thiếu
  điều kiện quan trọng = có thể coi là sai theo tiêu chí đề bài "thiếu ý thiết yếu"). Khác
  biệt với human ở đây có thể là mức độ nghiêm khắc: human coi ý chính (mức thưởng) là đủ,
  judge coi điều kiện áp dụng cũng là ý thiết yếu.

Observed agreement p_o = 7/10 = 0.70. Chance agreement p_e (từ tỷ lệ nhãn 1 của judge=3/10,
0 của judge=7/10; nhãn 1 của human=6/10, 0=4/10): p_e = (0.3×0.6)+(0.7×0.4) = 0.18+0.28=0.46.
κ = (0.70−0.46)/(1−0.46) = 0.444, khớp giá trị `cohen_kappa` trong artifact.

## Giới hạn và cách dùng judge

- **n nhỏ**: chỉ 5 cặp pairwise và 10 nhãn binary — mọi con số (κ, verbosity_bias, position
  bias rate) đều có biên sai số lớn với mẫu này, không nên khái quát hóa.
- **κ=0.444 chưa đạt ngưỡng bonus (>0.6)** — hợp lý vì judge chạy trên model 7B cục bộ
  (`qwen2.5:7b-instruct`) thay vì Gemini do sự cố quota; 2/3 case bất đồng (id=33, id=46) là
  lỗi đọc/suy luận rõ ràng của chính judge (reasoning tự mâu thuẫn với nội dung đang đánh
  giá), không phải do đề bài mơ hồ. Khuyến nghị chạy lại Phase B với Gemini/GPT khi có quota
  để so sánh κ, tách rõ "judge yếu" khỏi "câu hỏi khó chấm".
- **Không coi judge là đáp án tuyệt đối**: ở cả 3 case bất đồng, việc đối chiếu trực tiếp
  answer với reference cho thấy nhãn human hợp lý hơn judge trong 2/3 case. Pipeline production
  thực tế nên dùng judge làm tín hiệu sơ bộ, không thay thế hoàn toàn human review cho các
  quyết định quan trọng (ví dụ: chặn/block nội dung).
