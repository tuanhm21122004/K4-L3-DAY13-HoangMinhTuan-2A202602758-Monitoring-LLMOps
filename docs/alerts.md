# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1: high-latency-p95

- **Tên:** `high_latency_p95`
- **Severity:** Warning
- **Duration:** 3m (duy trì liên tục trong 3 phút)
- **Kênh thông báo:** Slack `#alerts-llmops`
- **SLI/SLO liên quan:** SLO `fast_successful_requests` (Latency P95 <= 3000ms trong cửa sổ rolling)
- **Điều kiện và thời gian duy trì:** `latency_p95 > 3000ms` kéo dài > 3 phút trên luồng requests tới `/chat`
- **Ảnh hưởng tới người dùng:** Người dùng trải nghiệm phản hồi chậm, timeout giao diện người dùng, tăng tỷ lệ bỏ dở request
- **Ba bước kiểm tra đầu tiên:**
  1. Kiểm tra panel Latency và TTFT trên Dashboard (`data/logs.jsonl`) để xác định latency tăng đột biến từ thời điểm nào.
  2. Lọc log gần nhất trong `data/logs.jsonl` có `latency_ms > 3000` để lấy `correlation_id` của các request bị chậm.
  3. Mở Langfuse trace bằng `correlation_id` đó để kiểm tra span tree (retrieval vs generation) xem span nào chiếm phần lớn thời gian (ví dụ: retrieval bị nghẽn do vector database hay LLM generation chậm).
- **Mitigation tạm thời:**
  - Nếu span `retrieval` bị chậm (như vector store degraded/rag_slow): tạm thời bật cache kết quả retrieval hoặc bypass domain retrieval sang fallback response.
  - Nếu LLM generation bị chậm: chuyển sang model có latency thấp hơn hoặc kiểm tra rate limit / upstream connectivity.
- **Owner:** `oncall-llmops`

## Alert 2: high-error-rate

- **Tên:** `high_error_rate`
- **Severity:** Critical
- **Duration:** 2m (duy trì liên tục trong 2 phút)
- **Kênh thông báo:** Slack `#alerts-llmops-critical` / PagerDuty
- **SLI/SLO liên quan:** Guardrail Error Rate (`error_rate_pct_max: 2%`), ảnh hưởng trực tiếp đến Error Budget của primary SLO
- **Điều kiện và thời gian duy trì:** `error_rate_pct > 2.0%` (số request failed / tổng request received * 100 > 2%) kéo dài > 2 phút
- **Ảnh hưởng tới người dùng:** Người dùng nhận mã lỗi HTTP 500 (`Internal Server Error`), tính năng chat/hỏi đáp hoàn toàn không trả lời được
- **Ba bước kiểm tra đầu tiên:**
  1. Kiểm tra panel Errors trên Dashboard và đếm `error_type` (ví dụ: `RuntimeError`, `TimeoutError`, `HTTPException`).
  2. Mở file log `data/logs.jsonl`, tìm các log event `request_failed`, trích xuất `error_type`, `detail` và `correlation_id`.
  3. Tra cứu trace tương ứng trên Langfuse để xem chính xác step nào ném exception (ví dụ span `retrieval` bị timeout do vector store hay upstream API 503).
- **Mitigation tạm thời:**
  - Bật circuit breaker đối với tool/vector store nếu lỗi đến từ retrieval dependency (`tool_fail`), trả lời với graceful degradation.
  - Khởi động lại worker pods nếu phát hiện process leak/deadlock.
- **Owner:** `oncall-llmops`

## Alert 3: retrieval-degradation

- **Tên:** `retrieval_degradation`
- **Severity:** Critical
- **Duration:** 5m (duy trì liên tục trong 5 phút)
- **Kênh thông báo:** Slack `#alerts-llmops`
- **SLI/SLO liên quan:** Guardrail Retrieval Success (`retrieval_success_rate_pct_min: 90%`) và Quality Score (`quality_score_avg_min: 0.75`)
- **Điều kiện và thời gian duy trì:** `retrieval_success_rate_pct < 90.0%` hoặc `quality_score_avg < 0.75` trong 5 phút liên tục
- **Ảnh hưởng tới người dùng:** Câu trả lời của hệ thống suy giảm chất lượng nghiêm trọng, mô hình bị ảo giác (hallucination) do thiếu context hoặc trả lời câu mặc định không đúng ý người dùng
- **Ba bước kiểm tra đầu tiên:**
  1. Mở panel Errors & Quality trên Dashboard để xem tỷ lệ retrieval thành công và điểm chất lượng trung bình.
  2. Lọc log có `tool_success == false` hoặc `quality_score < 0.6` trong `data/logs.jsonl` để lấy `correlation_id`.
  3. Đối chiếu trace trên Langfuse để xác định document corpus có bị rỗng, query embedding bị lỗi, hay prompt template gần nhất (label candidate) làm giảm chất lượng.
- **Mitigation tạm thời:**
  - Nếu do prompt mới được triển khai: thực hiện rollback prompt label `production` về phiên bản ổn định trước đó trên Langfuse ngay lập tức.
  - Nếu do vector store / retrieval service index hỏng: fallback sang semantic cache hoặc keyword search.
- **Owner:** `oncall-llmops`

