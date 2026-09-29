# LLMOps Audit Trail & Retention Policy

Hệ thống ghi nhận Audit Trail độc lập theo tiêu chuẩn an ninh và tuân thủ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP của Chính phủ Việt Nam và GDPR Điều 6).

## 1. Mục đích và phạm vi

- **Mục đích:** Ghi lại mọi hành động nhạy cảm về an toàn thông tin, bảo vệ dữ liệu cá nhân, thay đổi cấu hình runtime (incident injection), và kiểm soát truy cập LLM.
- **Phân biệt với Application Log:** 
  - Application Log (`data/logs.jsonl`): phục vụ observability, debug kỹ thuật và tính toán SLO metric.
  - Audit Log (`data/audit.jsonl`): phục vụ compliance, pháp lý và an ninh; có chữ ký băm mật mã (cryptographic hash chain) chống sửa đổi hoặc chèn xóa log.

## 2. Cấu trúc Schema và tính toàn vẹn (Tamper-Evidence)

Audit log tuân thủ schema JSON tại [`config/audit_schema.json`](../config/audit_schema.json):

- `audit_id`: Mã định danh duy nhất của bản ghi audit (`aud-<uuid>`).
- `ts`: Thời điểm ghi nhận chuẩn ISO 8601 UTC.
- `correlation_id`: Khóa ngoại nối sang Application Log và Langfuse Traces.
- `event_type`: Loại sự kiện kiểm toán (`pii_detected_and_redacted`, `incident_state_changed`, `security_policy_enforced`,...).
- `severity`: Mức độ quan trọng (`INFO`, `WARNING`, `CRITICAL`).
- `actor`: Thông tin chủ thể thực hiện hành động (`user_id_hash`, `role`, `client_ip`).
- `action`: Hành động thực hiện (`REDACT`, `ENABLE`, `DISABLE`, `EXECUTE`).
- `resource`: Đối tượng tài nguyên bị tác động (`user_prompt`, `incident_injector`,...).
- `compliance_tags`: Nhãn quy định pháp lý (`Decree13-VN-Art9-PII-Protection`, `PCI-DSS-Req3`, `SOC2-CC7.2`).
- `prev_hash`: Giá trị hash SHA-256 của bản ghi liền trước (tạo thành chuỗi Merkle/blockchain log).
- `record_hash`: Giá trị hash SHA-256 của toàn bộ nội dung bản ghi hiện tại.

## 3. Chính sách lưu trữ (Retention Policy)

| Tầng lưu trữ (Tier) | Thời gian duy trì | Vị trí lưu trữ | Mã hóa & Quyền truy cập |
|---|---|---|---|
| **Hot Storage** (Truy vấn nhanh) | 90 ngày | Hệ thống tệp cục bộ (`data/audit.jsonl`) hoặc CloudWatch Logs / Elasticsearch | Mã hóa AES-256, chỉ đọc (Append-Only), cấp quyền riêng cho Security Team |
| **Warm Archive** | 1 năm | Object Storage (AWS S3 Glacier Instant Retrieval / GCS Nearline) | Object Lock (WORM - Write Once Read Many), mã hóa KMS key riêng |
| **Cold Compliance Archive** | 5 năm | AWS S3 Glacier Deep Archive / Coldline | Tuân thủ lưu trữ dữ liệu tài chính/pháp lý, kiểm tra tính toàn vẹn định kỳ 6 tháng |
| **Hủy dữ liệu (Destruction)** | Sau 5 năm | Tiêu hủy an toàn (Secure Crypto-shredding) | Tự động xóa bằng S3 Lifecycle Rules, xuất biên bản tiêu hủy dữ liệu |

## 4. Minh họa truy vấn và kiểm tra toàn vẹn

Sử dụng công cụ `scripts/query_audit.py`:

```bash
# 1. Kiểm tra tính toàn vẹn mật mã của toàn bộ chuỗi audit log
python scripts/query_audit.py --verify

# 2. Lọc các sự kiện phát hiện PII và xử lý che dữ liệu
python scripts/query_audit.py --event pii_detected_and_redacted

# 3. Lọc các sự kiện cảnh báo mức độ WARNING
python scripts/query_audit.py --severity WARNING --limit 10
```
