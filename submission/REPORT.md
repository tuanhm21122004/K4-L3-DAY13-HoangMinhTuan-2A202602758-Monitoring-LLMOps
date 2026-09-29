# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Báo cáo kết quả hoàn thành bài lab Day 13: Monitoring & LLMOps. Toàn bộ evidence dẫn bằng đường dẫn tương đối `evidence/<file>.png`.

## 1. Thông tin học viên

- **Họ và tên:** Hoàng Minh Tuấn
- **MSSV:** 2A202602758
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/tuanhm21122004/K4-L3-DAY13-HoangMinhTuan-2A202602758-Monitoring-LLMOps
- **Commit SHA cuối:** 13b606680ae4a3072eda90334959b632fe4ecba0
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602758`

## 2. Evidence index

| Evidence | Mô tả | Đường dẫn |
|---|---|---|
| Pytest cuối | 25/25 unit tests pass hoàn chỉnh (PII, Middleware, Dashboard, Metrics, Tracing, Challenge) | `evidence/01-pytest.png` |
| Log validator | `scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 | `evidence/02-log-validator.png` |
| Dashboard validator | `scripts/validate_dashboard.py` xác thực hợp lệ 6/6 panel contract | `evidence/03-dashboard-validator.png` |
| Structured log | JSON log chuẩn với đầy đủ `correlation_id`, `service`, `event`, `latency_ms`, `cost_usd`, metadata | `evidence/04-structured-log.png` |
| PII redaction | Kiểm chứng scrubbing Email, Phone VN, CCCD, Credit Card, Passport trước khi ghi log | `evidence/05-pii-redaction.png` |
| Trace list | Danh sách >= 10 traces thực tế (22 traces) trong project `day13-k4-l3a-2A202602758` | `evidence/06-trace-list.png` |
| Trace waterfall | Chi tiết trace waterfall phân cấp quan hệ cha con: `lab-agent-run` -> `retrieval` + `generation` | `evidence/07-trace-waterfall.png` |
| Trace metadata | Drawer chi tiết observation metadata (`correlation_id`, prompt version, model, token, cost) | `evidence/08-trace-metadata.png` |
| Prompt versions | Quản lý prompt `day13-chat` với Version 1 (`production`, `baseline`) và Version 2 (`candidate`) | `evidence/09-prompt-versions.png` |
| Prompt rollback | Lịch sử audit log minh chứng quy trình promote v2 và rollback tức thời về v1 an toàn | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | 6 panel dashboard trực quan hóa toàn bộ metrics hệ thống, SLO thresholds và chi phí | `evidence/11-dashboard-overview.png` |
| Incident metric | Đồ thị metrics ghi nhận tail latency spike vượt ngưỡng SLO 500ms khi xảy ra sự cố | `evidence/12-incident-metric.png` |
| Incident log | Dòng log bất thường trong `data/logs.jsonl` với `correlation_id: req-d37483df` (latency 2652ms) | `evidence/13-incident-log.png` |
| Incident trace | Langfuse Trace `b1954a03bb534800ae2d89c4c4bbf6d5` định vị chính xác span `retrieval` (2501ms) | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 0/100 (Thiếu metadata, rò rỉ PII, thiếu enrichment) | **100/100** | Đạt toàn bộ 12/12 tiêu chí đánh giá tự động |
| `validate_dashboard.py` | Thiếu panel contract, thiếu threshold | **Hợp lệ: 6/6 panels** | Đáp ứng đầy đủ contract về query, units và SLO thresholds |
| `pytest` | 12 passed, 13 failed/unimplemented | **25/25 passed (100%)** | Đã bao phủ toàn diện unit test cho PII, Middleware, Prompts, Tracing |
| Số traces hợp lệ | 0 traces | **22 traces (60+ observations)** | Đã đẩy toàn bộ workload vào project cá nhân `day13-k4-l3a-2A202602758` |
| Số PII leak | 5 leaks (Email, Phone VN, CCCD, Card, Passport) | **0 leaks (100% redacted)** | Scrubbing triệt để ở cả tầng Log và Langfuse Observation |
| Latency P95 / TTFT P95 | Latency: 156ms / TTFT: 50ms | **156ms / 50ms (Normal)**<br>2652ms (Incident) | Hệ thống vận hành ổn định trong điều kiện chuẩn; phát hiện tức thì khi incident kích hoạt |
| Retrieval success rate | 100% | **100%** | Tool retrieval luôn trả về tài liệu hợp lệ trong SLA quy định |

## 4. Logging và PII

### Cách tạo/nhận và truyền correlation ID
1. **Tiếp nhận & Khởi tạo:** Tại tầng FastAPI Middleware (`app/middleware.py`), request đến được kiểm tra header `X-Correlation-ID` hoặc `X-Request-ID`. Nếu không có hoặc sai format, middleware tự sinh một correlation ID duy nhất theo chuẩn `req-<8-hex-chars>` (ví dụ: `req-57ed9999`).
2. **Contextvars & Structlog Binding:** Correlation ID được gán vào `structlog.contextvars.bind_contextvars(correlation_id=cid)` và lưu trong `request.state.correlation_id`. Nhờ đó, bất kỳ log line nào được sinh ra ở bất cứ function/module nào trong suốt vòng đời xử lý request đều tự động mang theo `correlation_id` mà không cần truyền tay thủ công qua tham số.
3. **HTTP Response Propagation:** Middleware trả về `X-Request-ID: cid` và `X-Response-Time-Ms` trên response header để client và các downstream services dễ dàng đối chiếu.

### Các metadata được ghi vào structured log
Toàn bộ log được chuẩn hóa theo JSON Lines (`data/logs.jsonl`) bao gồm:
- **Core fields:** `ts` (ISO-8601 UTC timestamp), `level` (`info`, `warning`, `error`), `service="api"`, `environment` (`dev` hoặc `production`).
- **Context enrichment:** `correlation_id`, `user_id_hash` (SHA-256 hashed từ `user_id`, bảo vệ định danh người dùng), `session_id`, `feature` (`qa`, `summary`, v.v.), `model` (`claude-sonnet-4-5`).
- **Performance & Observability:** `latency_ms` (tổng thời gian xử lý endpoint), `ttft_ms` (thời gian đến token đầu tiên), `tokens_in` (prompt tokens), `tokens_out` (completion tokens), `cost_usd` (ước tính chi phí LLM call), `quality_score` (điểm chất lượng heuristic).
- **Tool breakdown:** `tool_name="retrieval"`, `tool_latency_ms`, `tool_success=True/False`.

### Cách bảo đảm PII được scrub trước khi ghi
1. **Regex Pattern Engine (`app/pii.py`):** Triển khai tập biểu thức chính quy mạnh mẽ nhận diện 5 loại PII nhạy cảm:
   - `email`: `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+` -> thay bằng `[REDACTED_EMAIL]`.
   - `phone_vn`: `(?:\+84|84|0)(?:3|5|7|8|9)\d{8}` (hỗ trợ cả dấu cách, gạch nối, chấm) -> thay bằng `[REDACTED_PHONE]`.
   - `cccd`: Số định danh cá nhân / CCCD 12 chữ số -> thay bằng `[REDACTED_CCCD]`.
   - `credit_card`: Số thẻ tín dụng 13-19 chữ số (Visa, Mastercard, Amex) có phân tách -> thay bằng `[REDACTED_CREDIT_CARD]`.
   - `passport`: Hộ chiếu Việt Nam (chữ cái B theo sau là 7 chữ số) -> thay bằng `[REDACTED_PASSPORT]`.
2. **Deep Recursive Structlog Processor (`app/logging_config.py`):** Hàm `scrub_event(logger, method_name, event_dict)` duyệt đệ quy qua toàn bộ các dictionary lồng nhau, danh sách, chuỗi text trong `event_dict`. Quá trình này được đặt **trước** `JSONRenderer` và file writer, đảm bảo không một byte dữ liệu PII thô nào có thể chạm tới disk hay log collector.
3. **Langfuse Observation Sanitization:** Tương tự, input và output truyền vào Langfuse span/generation đều đi qua hàm `summarize_text()` và scrub engine để đảm bảo tuân thủ nghiêm ngặt chuẩn bảo mật dữ liệu.

### Cách kiểm chứng kết quả
- **Unit test suite:** 5 bài test chuyên biệt trong `tests/test_pii.py` kiểm tra từng loại PII với các dạng format phức tạp (có dấu cách, dấu chấm, mã quốc gia `+84`).
- **Validator tự động:** `python scripts/validate_logs.py` quét toàn bộ `data/logs.jsonl`, đạt điểm tuyệt đối 100/100, xác nhận 0 PII leak.
- **Scanner bảo mật chuyên dụng:** `python scripts/scan_secrets_pii.py` quét toàn bộ 70 files trong repository, xác nhận không rò rỉ secret hoặc PII thô.

## 5. Tracing và prompt versioning

### Xác nhận traces thuộc project cá nhân
- Toàn bộ traces và prompts được quản lý trên Langfuse Cloud (Japan Region `https://jp.cloud.langfuse.com`) dưới project ID `cmumf6eoz0002ad0cs4moso0p`, tên project: `day13-k4-l3a-2A202602758`.
- API keys được cấu hình qua biến môi trường an toàn trong `.env`, xác thực hợp lệ qua `langfuse.auth_check() == True`.

### Cấu trúc root/retrieval/generation observations
Một request hoàn chỉnh được phân cấp theo quan hệ cha con rõ ràng:
1. **Root Span:** `@observe(name="lab-agent-run", as_type="agent")` đóng vai trò root observation, ghi nhận toàn bộ transaction của agent, gán tags `["lab", feature, model]`, `session_id`, `user_id_hash` và `correlation_id`.
2. **Child Span 1 (Retrieval):** `@observe(name="retrieval", as_type="retriever")` đo đạc thời gian vector search / semantic retrieval (`Corpus`), ghi nhận số tài liệu trả về (`doc_count`) và độ trễ truy xuất.
3. **Child Span 2 (Generation):** `@observe(name="generation", as_type="generation")` mô phỏng cuộc gọi LLM sinh text, nhận prompt object quản lý, cập nhật `usage_details` (input, output, total tokens), `cost_details` (USD) và `model="claude-sonnet-4-5"` qua `update_current_generation()`.

### Cách nối trace với log
- Mỗi khi FastAPI middleware sinh ra `correlation_id`, giá trị này được đưa đồng thời vào:
  - Trường `correlation_id` trong `logs.jsonl` qua structlog contextvars.
  - Trường `metadata={"correlation_id": correlation_id}` của Langfuse root span và generation observation.
- Người trực vận hành khi đọc một alert chỉ cần lấy `correlation_id` từ log line bất thường và search trên Langfuse search bar để mở ngay lập tức trace waterfall tương ứng.

### Thông số Prompt Management
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 với labels `['baseline', 'production']`. Template:
  ```text
  Feature={{feature}}
  Docs={{docs}}
  Question={{message}}
  ```
- **Version/label candidate:** Version 2 với labels `['candidate']`. Template:
  ```text
  Feature={{feature}}
  Docs={{docs}}
  Question={{message}}
  Provide a concise and direct answer based strictly on the context.
  ```
- **Trace ID tương ứng từng version:**
  - Trace chạy trên Baseline v1: `1760db419dda46f6559ae44135bea312` (`correlation_id: req-98982998`)
  - Trace chạy trên Candidate v2: `a6bfb751a79f27e1fc7327d0824ac1f9` (`correlation_id: req-57ed9999`)
  - Trace chạy trong Incident: `b1954a03bb534800ae2d89c4c4bbf6d5` (`correlation_id: req-d37483df`)

### Cách promote và rollback `production`
- **Promote:** Khi Version 2 hoàn thành thử nghiệm và đạt tiêu chí đánh giá chất lượng (Eval score), điều hướng production sang v2 bằng cách gán nhãn `production` cho v2:
  ```python
  langfuse.create_prompt(name="day13-chat", prompt=p2.prompt, labels=["production", "candidate"])
  ```
- **Rollback:** Nếu phát hiện hồi quy chất lượng hoặc latency tăng cao, rollback tức thì mà không cần sửa code ứng dụng hay restart uvicorn server, chỉ cần tái kích hoạt nhãn `production` cho Version 1:
  ```python
  langfuse.create_prompt(name="day13-chat", prompt=p1.prompt, labels=["production", "baseline"])
  ```
  Ứng dụng thông qua `resolve_prompt(..., label="production")` sẽ tự động tải lại v1 từ bộ nhớ đệm mà không có downtime.

## 6. Dashboard, SLO và alerts

### Dashboard và 6 panel
Dashboard được cấu hình chi tiết tại `config/dashboard.yaml` và trực quan hóa tại `evidence/11-dashboard-overview.png`:
1. **Panel 1 — Latency & TTFT Distribution:** Thống kê P50, P95, P99 Latency và TTFT P95. Có đường ngưỡng SLO 500ms.
2. **Panel 2 — Request Volume & Error Rate:** Biểu đồ lưu lượng request thành công/thất bại và tỷ lệ lỗi hệ thống (ngưỡng cảnh báo > 5%).
3. **Panel 3 — Token Usage Breakdown:** Phân rã tổng token tiêu thụ thành Prompt Tokens và Completion Tokens.
4. **Panel 4 — Estimated Cost per Request:** Chi phí tích lũy và chi phí trung bình trên mỗi request theo thời gian thực ($/req).
5. **Panel 5 — Retrieval Health & Latency:** Tỷ lệ truy xuất thành công của vector database (SLO >= 98%) và thời gian trễ của retrieval span.
6. **Panel 6 — Output Quality Score:** Điểm số đánh giá chất lượng phản hồi heuristic của LLM (thang điểm 0.0 - 1.0, mục tiêu >= 0.8).

### SLO và lý do chọn
- **Latency SLO:** P95 Latency <= 500ms cho các tác vụ hỏi đáp thông thường. Lý do: Giữ trải nghiệm người dùng tương tác trực tiếp qua giao diện chat mượt mà, tránh tình trạng giao diện bị đơ.
- **Availability SLO:** Error Rate < 1.0% (Độ sẵn sàng 99.0%). Lý do: Đảm bảo dịch vụ AI trợ lý luôn phản hồi ổn định trong giờ cao điểm.
- **Retrieval SLO:** Retrieval Success Rate >= 98.0% và Retrieval Latency <= 300ms. Lý do: RAG phụ thuộc hoàn toàn vào vector database; nếu retrieval chậm hoặc lỗi, toàn bộ pipeline sẽ suy giảm chất lượng nghiêm trọng.

### Cách tính error budget
- Với mục tiêu độ sẵn sàng 99.0% trong chu kỳ 30 ngày:
  $$\text{Error Budget} = 100\% - 99.0\% = 1.0\%$$
- Tính theo thời gian:
  $$30 \text{ ngày} \times 24 \text{ giờ/ngày} \times 60 \text{ phút/giờ} \times 0.01 = 432 \text{ phút downtime tối đa cho phép trong 30 ngày.}$$
- Đội ngũ vận hành theo dõi tốc độ đốt ngân sách lỗi (Burn Rate). Nếu Burn Rate > 14.4x (đốt hết 100% budget trong 2 ngày), hệ thống lập tức kích hoạt cảnh báo P1 khẩn cấp để chặn toàn bộ đợt deploy tính năng mới.

### Ba alerts và runbook tương ứng
1. **`HighLatencyP95` (P95 Latency > 1000ms trong 5 phút):**
   - *Triệu chứng:* Request phản hồi chậm, người dùng than phiền giao diện treo.
   - *Check steps:* Kiểm tra Panel 1 & 5 trên Dashboard; lọc `logs.jsonl` tìm các request có `latency_ms > 1000`; mở trace trên Langfuse để xem span con nào (retrieval hay generation) chiếm nhiều thời gian nhất.
   - *Mitigation:* Nếu do retrieval, kiểm tra vector DB connection pool và chỉ mục HNSW/IVF; kích hoạt caching layer.
2. **`HighErrorRate` (Tỷ lệ lỗi HTTP 5xx > 5% trong 3 phút):**
   - *Triệu chứng:* Request fail hàng loạt, client nhận HTTP 500.
   - *Check steps:* Kiểm tra Panel 2; lọc logs tìm `event="request_failed"`; phân loại mã lỗi (`error_type`).
   - *Mitigation:* Kích hoạt circuit breaker; chuyển tiếp traffic sang fallback model; restart worker pods nếu rò rỉ bộ nhớ.
3. **`RetrievalDegradation` (Retrieval success < 95% hoặc retrieval latency > 1000ms):**
   - *Triệu chứng:* Câu trả lời của LLM mất context, chất lượng điểm quality tụt dốc.
   - *Check steps:* Kiểm tra Panel 5; lọc logs tìm `tool_name="retrieval"` và `tool_success=False`.
   - *Mitigation:* Tăng timeout của client retrieval lên mức tạm thời; kích hoạt fallback documents nội bộ (`CORPUS fallback`).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 09:21:50 – 09:22:20 UTC
- **Triệu chứng từ metrics:** Dashboard Panel 1 hiển thị P95 Latency tăng vọt đột biến từ 156ms lên 2666ms (vượt xa ngưỡng `latency_threshold_ms: 2000` của BTC challenge và vi phạm nghiêm trọng SLO P95 <= 500ms). Cột Latency chuyển sang màu đỏ cảnh báo.
- **Log line và correlation ID liên quan:**
  - Correlation ID chính thức từ load test challenge: `req-63ecfb81` (cùng các request trong batch: `req-ff7e408f`, `req-c52844e3`, `req-141bc84d`, `req-dd283af3`)
  - User ID: `k4-l3a-u01` (hashed), Session ID: `k4-l3a-challenge-s01`, Feature: `monitoring`, Query: `"Explain why metrics traces and logs work together."`
  - Dòng log trích xuất từ `data/logs.jsonl`:
    ```json
    {
      "ts": "2026-09-29T09:22:02.492145Z",
      "level": "info",
      "service": "api",
      "environment": "production",
      "correlation_id": "req-63ecfb81",
      "user_id_hash": "4570299f37e2...",
      "session_id": "k4-l3a-challenge-s01",
      "feature": "monitoring",
      "event": "response_sent",
      "latency_ms": 2652,
      "ttft_ms": 50,
      "tool_name": "retrieval",
      "tool_success": true,
      "quality_score": 0.9
    }
    ```
- **Trace ID và span gây ảnh hưởng:**
  - Langfuse Trace ID: `700b1dab1ed9c4d9fb7d3f71110feab6` (và các trace cùng đợt: `608be10ddaeb13602ecd249503d73cd9`, `ae73769a132bf42b92ddc34d5f8e863f`, `a94e3532aef28800a757c4c0d638c0b8`, `d204c6a0bd982ac13224b2cbfd061ec5`)
  - Span ID: `df04e0031f0c5913` (Tên span: `retrieval`, Type: `RETRIEVER`)
  - Thời gian thực thi span `retrieval`: **2.501s (2501ms)**, chiếm tới 93.8% tổng thời gian thực thi của cả transaction (2666ms), trong khi LLM generation chỉ mất 165ms.
- **Root cause:** Module truy xuất dữ liệu vector store bị nghẽn (do cờ mô phỏng sự cố `STATE["rag_slow"] = True` làm trễ 2.5s mô phỏng việc vector index bị lock hoặc quét full scan bảng vector không đánh index khi xử lý feature `monitoring`).
- **Fix action:**
  1. Tắt cờ sự cố khẩn cấp: Gửi `POST /incidents/rag_slow/disable`.
  2. Bổ sung client timeout 500ms cho hàm `retrieve()` để ngắt sớm các truy vấn treo.
  3. Cấu hình fallback document tức thì khi timeout xảy ra để bảo vệ latency cho người dùng.
- **Preventive measure:**
  - Thiết lập alert riêng trên span level: Cảnh báo khi P95 retrieval latency > 300ms liên tục trong 2 phút.
  - Triển khai Semantic Cache (Redis) ở phía trước vector database để phục vụ các câu hỏi trùng lặp với độ trễ < 5ms.

## 8. Giải thích và tự đánh giá

### Một quyết định kỹ thuật quan trọng và lý do
- **Quyết định:** Sử dụng đệ quy Structlog Processor (`scrub_event`) ở cấp độ engine logging thay vì scrub thủ công từng biến trong endpoint hay trong serializer.
- **Lý do:** Cách tiếp cận này loại bỏ hoàn toàn rủi ro "bỏ quên" PII do lập trình viên sơ suất khi bổ sung trường dữ liệu mới vào `payload`. Bất kể object lồng nhau bao nhiêu cấp (nested dicts, lists, error exception tracebacks), mọi giá trị string đều bị kiểm tra qua regex và thay thế bằng `[REDACTED_*]` trước khi ghi ra stream, đảm bảo tuân thủ triệt để nguyên tắc bảo mật phòng thủ theo chiều sâu (Defense-in-Depth).

### Một lỗi/blocker đã gặp và cách xử lý
- **Lỗi gặp phải:** Langfuse Cloud phiên bản v4 trên hạ tầng mới đã deprecate endpoint `GET /api/public/traces` và trả về mã lỗi HTTP 410 Gone đối với các organization tạo mới.
- **Cách xử lý:** Tra cứu Langfuse SDK specification và skill guide, chuyển hướng toàn bộ việc truy vấn và đối soát trace sang endpoint hiện đại `GET /api/public/v2/observations?fromStartTime=...` (qua `langfuse.api.observations.get_many(from_start_time=..., to_start_time=...)`) với timezone-aware UTC datetime. Đồng thời sử dụng đúng phương thức `update_current_generation()` với `usage_details` và `cost_details` để ghi nhận token và chi phí chính xác.

### Luồng Metrics → Logs → Traces hoạt động cùng nhau
1. **Metrics (Phát hiện - "Cái gì đang xảy ra?"):** Dashboard và Prometheus quan sát các chỉ số cấp cao (P95 Latency tăng vọt lên 2.6s, SLO bị vi phạm). Metrics cho biết hệ thống đang suy thoái nhưng chưa giải thích được do request nào.
2. **Logs (Thu hẹp phạm vi - "Ai và Request nào bị ảnh hưởng?"):** Bộ lọc log truy quét các dòng `response_sent` có `latency_ms > 2000`, chỉ ra chính xác `correlation_id: req-d37483df`, thời điểm xảy ra, user bị ảnh hưởng và tham số truy vấn.
3. **Traces (Định vị nguyên nhân gốc rễ - "Tại sao và Ở đâu?"):** Dùng `correlation_id` mở Trace `b1954a03bb534800ae2d89c4c4bbf6d5` trên Langfuse. Cây waterfall bóc tách chi tiết từng mili-giây cho thấy LLM sinh text hoàn toàn bình thường (150ms), nhưng span `retrieval` bị nghẽn tới 2501ms. Ba trụ cột kết hợp tạo nên một vòng lặp điều tra sự cố chuẩn mực trong LLMOps.

### Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM
- Khác với phần mềm truyền thống nơi code thay đổi chậm và có tính tiền định, hệ thống LLM phụ thuộc sâu sắc vào prompt và dữ liệu đầu vào.
- Prompt versioning tách biệt vòng đời cập nhật prompt khỏi vòng đời release mã nguồn. Nhờ dynamic label (`production`, `candidate`), kỹ sư AI có thể A/B testing prompt mới ngoài đời thực và rollback về bản an toàn trong vòng dưới 1 giây nếu phát hiện tỷ lệ ảo giác hay chi phí token tăng bất thường, từ đó bảo vệ ngân sách lỗi (SLO) và ngân sách tài chính của doanh nghiệp.

### Các hạng mục Bonus đã hoàn thành (+10 điểm)
1. **Bonus 1 — Tamper-evident Audit Logging with SHA-256 Hash Chaining:**
   - Triển khai `app/audit.py` tuân thủ schema `config/audit_schema.json` và chính sách kiểm toán bảo mật `docs/audit_policy.md`.
   - Mỗi hành động nhạy cảm (bật/tắt incident, phát hiện rò rỉ PII) đều được ghi vào `data/audit.jsonl` với chữ ký hàm băm nối chuỗi mật mã học `previous_hash` -> `record_hash` (Blockchain-like Hash Chaining).
   - Tool xác thực `scripts/query_audit.py` kiểm tra toàn vẹn chuỗi, phát hiện ngay nếu có ai chỉnh sửa log kiểm toán trái phép.
2. **Bonus 2 — Automated CI/CD & Secret/PII Leak Scanning:**
   - Xây dựng GitHub Actions workflow `.github/workflows/ci.yml` tự động chạy pytest, log validator, dashboard validator khi có pull request.
   - Viết công cụ bảo mật chuyên dụng `scripts/scan_secrets_pii.py` tự động quét regex để ngăn chặn việc commit nhầm `.env`, Langfuse API key (`sk-lf-...`) hoặc PII thô vào Git.
3. **Bonus 3 — LLM Cost Optimization & Token Economics:**
   - Xây dựng bài phân tích tối ưu hóa chi phí `scripts/cost_optimization_analysis.py`.
   - Chứng minh mô hình kết hợp Semantic Caching + Prompt Compression giúp giảm **51.49% chi phí LLM** hàng tháng (từ $450 xuống còn $218.30 trên 100,000 requests), đồng thời cải thiện đáng kể P95 TTFT.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối (`evidence/<file>.png`).
- [x] Incident evidence nối đúng metric → log → trace (Correlation ID: `req-d37483df`, Trace ID: `b1954a03bb534800ae2d89c4c4bbf6d5`).
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân `day13-k4-l3a-2A202602758` và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
