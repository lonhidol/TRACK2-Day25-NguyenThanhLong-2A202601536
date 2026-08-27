# NimbusAI — Báo Cáo Kỹ Thuật FinOps & Chiến Lược Tối Ưu Hóa Chi Phí GPU

**Tác giả:** Kỹ sư FinOps (FinOps Engineer)  
**Khóa học:** AICB · Phase 2 · Track 2 (Cơ sở hạ tầng AI) · Day 25  
**Sản phẩm đầu ra:** Báo cáo Tối ưu hóa Chi phí GPU (Đầu vào cho Milestone 2)  

---

## 1. Tổng quan Điều hành: Chi phí Cơ sở (Baseline) vs. Sau Tối ưu (Optimized)

Bằng cách chuyển đổi tư duy đo lường từ các chỉ số thuê bao phần cứng truyền thống (`$/GPU-giờ`) sang kinh tế học đơn vị của ứng dụng AI (**`$/1M-token`**), NimbusAI đã kiểm toán toàn diện hạ tầng tính toán và phát hiện các điểm rò rỉ ngân sách nghiêm trọng.

* **Tổng chi phí ban đầu (Baseline spend):** **$27,133 / tháng** (tương đương **$6.488 / 1M-token** cho dịch vụ phục vụ suy luận LLM).
* **Tổng chi phí sau tối ưu (Optimized spend):** **$14,626 / tháng** (tương đương **$1.126 / 1M-token** cho dịch vụ phục vụ suy luận LLM).
* **Mức tiết kiệm ròng hàng tháng:** **$12,507 / tháng** (**Giảm 46.1% tổng chi phí toàn hệ thống**).
* **Mức cải thiện kinh tế học đơn vị (Unit Economics):** **Giảm 82.6% chi phí trên mỗi 1 triệu token suy luận**.

---

## 2. Phân Tích Chuyên Sâu 4 Đòn Bẩy Tiết Kiệm (FinOps Levers)

| Đòn bẩy tối ưu | Tiết kiệm hàng tháng | Tỷ trọng đóng góp | Cơ chế kỹ thuật cốt lõi |
|---|---|---|---|
| **1. Chiến lược Mua sắm (Purchasing)** | **$10,040** | **80.3%** | Chuyển job training sang Spot Instance + Cam kết Reserved 3 năm cho dịch vụ 24/7 |
| **2. Tối ưu hóa Suy luận (Inference)** | **$1,212** | **9.7%** | Model Cascading + Prompt Caching (giảm 90%) + Batch API (giảm 50%) |
| **3. Right-sizing GPU-Util Lies** | **$655** | **5.2%** | Hạ cấp GPU dư thừa công suất (`gpu-h100-4`) xuống dòng phù hợp (A100/A10G) |
| **4. Tắt GPU chạy không tải (Kill Idle)** | **$600** | **4.8%** | Tự động ngắt các GPU không có tác vụ (`gpu-h100-5` bỏ trống 8h/ngày) |
| **Tổng cộng** | **$12,507** | **100.0%** | **Cắt giảm 46.1% tổng hóa đơn GPU hàng tháng** |

### Tại sao Chiến lược Mua sắm đóng góp phần lớn mức tiết kiệm (80.3%)?
Hầu hết các tác vụ huấn luyện (`job-train-llm`, `job-train-embed`) sử dụng cụm GPU đắt tiền (H100/A100) và có tính chất gián đoạn được (`interruptible=True`). Bằng cách áp dụng **Spot Instance kết hợp Checkpointing định kỳ**, chi phí giảm hơn $40\%$ sau khi đã trừ đi overhead lưu checkpoint (3%) và thời gian chạy lại do gián đoạn (5%). Đồng thời, các dịch vụ suy luận trực tuyến (`job-infer-chat`, `job-infer-rag`) có chu kỳ hoạt động cao ($\ge 55\%$), đạt chuẩn điểm hòa vốn để mua Reserved Instance nhận trọn chiết khấu 45%.

---

## 3. Bản Chất Của "GPU-Util Lie" & Phân Tích Nguyên Nhân Gốc Rễ

### 3.1. "GPU-Util Lie" là gì?
Chỉ số `GPU-Util %` hiển thị từ lệnh `nvidia-smi` thực chất chỉ đo **tỷ lệ thời gian mà xung nhịp GPU/kernel đang hoạt động**, hoàn toàn **không** phản ánh hiệu quả tính toán của các nhân Tensor Cores bên trong.
* Trong tập dữ liệu kiểm toán, **`gpu-h100-4` báo cáo 98.2% GPU Utilization**, nhưng **Model FLOPs Utilization (MFU) chỉ đạt 19.4% (0.194)** và Model Bandwidth Utilization (MBU) đạt 20.7%.
* Tương tự, **`gpu-a10g-1` báo cáo 96.9% GPU Utilization** nhưng MFU chỉ đạt **26.8%**.

### 3.2. Nguyên nhân kỹ thuật gốc rễ:
1. **Hiện tượng nghẽn băng thông nhớ (Memory-Bound Decode):** Trong giai đoạn sinh từ (autoregressive token decode) của LLM, cường độ số học rất thấp ($\sim 1-2 \text{ FLOP/byte}$ so với điểm đỉnh Roofline của H100 là $295 \text{ FLOP/byte}$). GPU tiêu tốn thời gian chờ chuyển dữ liệu từ HBM sang thanh ghi thay vì thực hiện phép nhân ma trận.
2. **Kích thước Batch không tối ưu (Batch size = 1):** Phục vụ từng request đơn lẻ khiến phần cứng không thể kích hoạt năng lực tính toán song song cực đại của Tensor Cores.
3. **Nghẽn đường truyền I/O & PCIe:** Độ trễ trong quá trình Tokenization hoặc truyền dữ liệu Host-to-Device khiến luồng điều khiển GPU bận rộn nhưng chip tính toán rơi vào trạng thái chờ (stall).

### 3.3. Tác động tài chính:
Việc trả đủ $2.50/giờ cho một GPU H100 nhưng chỉ nhận lại $\sim 20\%$ giá trị tính toán tương đương với việc **ném bỏ $1.80 – $2.00 mỗi giờ cho mỗi GPU**. Việc phát hiện và hạ cấp (Right-sizing) ngay lập tức thu hồi **$655/tháng** chỉ trên một phiên bản phần cứng.

---

## 4. Các Phần Mở Rộng ("Your Turn") Đã Triển Khai & Kết Quả Đo Lường

### Extension 1: Nâng cấp Chính sách Gợi ý Mua sắm (`recommend_tier`)
* **Logic triển khai:** Tích hợp đánh giá đa yếu tố gồm: Hệ số chu kỳ sử dụng (Duty cycle), Khả năng chịu ngắt quãng (Interruptibility), Dòng GPU (H100 có tỷ lệ ngắt quãng thấp hơn A10G), và Thời gian cam kết dự án.
* **Kết quả:** Phân loại chính xác 100% các workload ngắn hạn/linh hoạt sang Spot và workload 24/7 dài hạn sang Reserved 3 năm, tối đa hóa tỷ lệ tiết kiệm lên 39.1% cho toàn bộ nhóm Purchasing.

### Extension 3: Kinh tế học Bộ nhớ đệm (`cache_is_worth_it`)
* **Công thức hòa vốn:**
  $$\text{Số lượt đọc hòa vốn} = \frac{\text{Chi phí ghi/lưu Cache}}{\text{Đơn giá Input} \times (1 - \text{Mức chiết khấu đọc})}$$
* **Kết quả đo lường:** Với mức giảm giá đọc 90% (Anthropic/OpenAI prompt cache), bất kỳ tiền tố prompt nào được tái sử dụng từ **1.39 lần trở lên** đều chắc chắn mang lại lợi nhuận ròng. Khi kết hợp Cache Hit cùng Batch API, chi phí chỉ còn **0.05 (giảm 95%)** so với chi phí thông thường.

### Extension 4: Quản lý Ngân sách Token Suy Luận Phức Tạp (`is_reasoning`)
* **Phân tích thực nghiệm:** Các truy vấn reasoning (`is_reasoning=1`) tiêu thụ lượng điện năng gấp **$\sim 80\times$** so với truy vấn thông thường ($19.2 \text{ Wh}$ so với $0.24 \text{ Wh}$ cho mỗi truy vấn) do tạo ra chuỗi suy nghĩ (Chain-of-Thought) dài hàng nghìn token.
* **Giải pháp đề xuất:** Thiết lập bộ định tuyến thông minh (Smart Router) chỉ cấp quyền kích hoạt reasoning đối với các bài toán logic/lập trình phức tạp, kèm theo giới hạn trần (hard token cap) cho CoT.

### Extension 5: Lập Lịch Tối Ưu Hóa Phát Thải Carbon (Carbon-Aware Scheduling)
* **Đo lường phát thải lưới điện theo vùng:**
  * `us-east-1` (Bắc Virginia): $380 \text{ gCO}_2/\text{kWh}$ (Giá điện: $0.12/\text{kWh}$).
  * `europe-north1` (Na Uy - Thủy điện): $30 \text{ gCO}_2/\text{kWh}$ (Giá điện: $0.09/\text{kWh}$).
  * `us-east-wa` (Washington - Thủy điện): $90 \text{ gCO}_2/\text{kWh}$ (Giá điện: $0.055/\text{kWh}$).
* **Kết quả:** Di chuyển các job huấn luyện linh hoạt từ `us-east-1` sang `europe-north1` giúp **giảm 92.1% lượng phát thải carbon** ($0.091 \rightarrow 0.007 \text{ gCO}_2e/\text{query}$) đồng thời giảm thêm **25% chi phí năng lượng điện**.

---

## 5. Khuyến Nghị 3 Hành Động Hàng Đầu Cho Ban Lãnh Đạo NimbusAI

1. **Hành động 1 (Tuần 1 — Khắc phục Lãng phí Tức thì):**
   * Triển khai kịch bản tự động ngắt (Auto-shutdown) đối với bất kỳ GPU nào rơi vào trạng thái Idle (`Util < 10%`) quá 15 phút ➔ **Thu hồi ngay $600/tháng**.
   * Chuyển đổi ngay workload của `gpu-h100-4` sang phiên bản A100 ➔ **Tiết kiệm ngay $655/tháng**.

2. **Hành động 2 (Tháng 1 — Cơ cấu lại Danh mục Mua sắm):**
   * Thiết lập cơ chế Checkpointing tự động cho các pipeline huấn luyện (`job-train-llm`, `job-train-embed`, `job-finetune`) để chuyển toàn bộ sang hạ tầng Spot ➔ **Tiết kiệm $10,040/tháng**.
   * Ký hợp đồng Reserved Instance 3 năm cho các cụm máy chủ phục vụ Chat/RAG hoạt động liên tục 24/7.

3. **Hành động 3 (Quý 1 — Kích hoạt Chargeback & Cổng Quản Trị Inference Gateway):**
   * Với **Tag Coverage đã đạt 92%** (vượt ngưỡng an toàn 80%), chính thức chuyển từ chế độ Showback sang **Chargeback** tự động theo chuẩn **FOCUS 1.x** để quy trách nhiệm ngân sách về từng team (`assistant`, `search`, `eval`, `rag`).
   * Triển khai LiteLLM Gateway kích hoạt mặc định tính năng Prompt Caching và Model Cascading, duy trì mốc đơn giá tối ưu **$1.126 / 1M-token**.
