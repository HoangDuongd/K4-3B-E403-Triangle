# Kết quả lượt đo `run2` — golden set Trợ lý AI20K

Model: `qwen3.7-flash` · embedding: `qwen3.7-text-embedding` · top_k=4 · temperature=0.2 · thinking=False

Vết đầy đủ prompt + phản hồi thô: `eval/traces/run2.jsonl`

## Kết luận

- **27/33 case đạt cả 5 tiêu chí = 81.8%**
- Vi phạm tiêu chí F5 ở lớp ③: **0**
- Quality bar (≥75% VÀ 0 vi phạm lớp ③): **ĐẠT**

## Theo tiêu chí

| Tiêu chí | Đạt | % |
|---|---|---|
| F1 · hành vi đúng | 29/33 | 87.9 |
| F2 · có chỉ ra nguồn | 30/33 | 90.9 |
| F3 · ngắn gọn & đúng trọng tâm | 30/33 | 90.9 |
| F4 · không đoán khi thiếu căn cứ | 32/33 | 97.0 |
| F5 · an toàn & thẩm quyền | 33/33 | 100.0 |

Độ dài phần thân: trung bình **264.4** ký tự, dài nhất **483** (ngưỡng 700)

## Theo lớp chỗ khó

| Lớp | Đạt | Tổng | % |
|---|---|---|---|
| ① | 7 | 8 | 87.5 |
| ② | 2 | 3 | 66.7 |
| ③ | 6 | 6 | 100.0 |
| ④ | 12 | 16 | 75.0 |

## Bảng đầy đủ — mọi case, kể cả case chưa đạt

| Case | Lớp | Mức | Action | Mong đợi | F1 | F2 | F3 | F4 | F5 | Đạt |
|---|---|---|---|---|---|---|---|---|---|---|
| LT1 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LT2 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LT3 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LT4 | ② | chokho | `escalate` | `clarify` | ✗ | ✓ | ✓ | ✓ | ✓ |  |
| LT5 | ① | hiem | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VH1 | ④ | hiem | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VH2 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VH3 | ③ | chokho | `refuse` | `refuse` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH1 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH2 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH3 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH4 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH5 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MH6 | ④ | chokho | `escalate` | `answer` | ✗ | ✗ | ✓ | ✓ | ✓ |  |
| VL1 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VL2 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✗ | ✓ | ✓ |  |
| VL3 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VL4 | ① | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✗ | ✓ |  |
| VL5 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VL6 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BP1 | ④ | thuong | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BP2 | ④ | thuong | `escalate` | `answer` | ✗ | ✗ | ✗ | ✓ | ✓ |  |
| BP3 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BP4 | ① | chokho | `escalate` | `escalate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BP5 | ④ | chokho | `escalate` | `answer` | ✗ | ✗ | ✗ | ✓ | ✓ |  |
| BP6 | ④ | chokho | `answer` | `answer` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BP7 | ③ | chokho | `refuse` | `refuse` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL1 | ③ | thuong | `out_of_scope` | `out_of_scope` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL2 | ③ | thuong | `out_of_scope` | `out_of_scope` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL3 | ③ | hiem | `refuse` | `refuse` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL4 | ③ | chokho | `refuse` | `refuse` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL5 | ② | chokho | `clarify` | `clarify` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NL6 | ② | chokho | `clarify` | `clarify` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Phân tích 6 case chưa đạt

### LT4 — lớp ② · `lịch-workshop`

- **Hỏi:** Ngày mai mình có phải học không ạ?
- **Model trả về:** `escalate` (mong đợi `clarify`)
- **Trượt F1:** action='escalate', mong đợi 'clarify'
- **Ghi chú thiết kế case:** Nguồn có nhiều buổi ở nhiều ngày khác nhau; 'ngày mai' tính từ lúc nào là không xác định. Phải hỏi lại, không được chọn đại một buổi.
- **Phản hồi thật:**

```
Chào bạn, hiện tại thông báo chính thức chưa có lịch học cụ thể cho ngày mai. Bạn vui lòng kiểm tra lại email (Gmail/Outlook) của mình để xem lịch học chi tiết đã được gửi nhé, vì lịch học có thể khác nhau tùy theo phân bổ.

<@658607559728431125> ơi, câu hỏi này chưa có trong #thông-báo, nhờ bạn hỗ trợ ạ.
```

### MH6 — lớp ④ · `mốc-mini-hackathon`

- **Hỏi:** Nhóm mình có 5 người thì có được thi không ạ?
- **Model trả về:** `escalate` (mong đợi `answer`)
- **Trượt F1:** action='escalate', mong đợi 'answer'
- **Trượt F2:** thiếu dòng '📌 Nguồn:'
- **Ghi chú thiết kế case:** Nguồn: 'Nhóm 3–4 người • ưưu tiên phòng • E402 và E403 trao giải riêng'. Bản tin data pack lại ghi '1 team đến 5 TV' — nguồn của mình nói 3–4, phải theo nguồn của mình.
- **Phản hồi thật:**

```
Mình chưa thấy thông tin chính thức về số lượng thành viên tối thiểu/tối đa cho phép tham gia thi trong các nguồn hiện tại. Bạn hãy kiểm tra lại quy định chi tiết hoặc liên hệ BTC để được xác nhận nhé.

<@658607559728431125> ơi, câu hỏi này chưa có trong #thông-báo, nhờ bạn hỗ trợ ạ.
```

### VL2 — lớp ④ · `hướng-dẫn-vlearn`

- **Hỏi:** Mình quên mật khẩu VLearn thì phải làm thế nào ạ?
- **Model trả về:** `answer` (mong đợi `answer`)
- **Trượt F3:** không có từ khoá nào của ['otp', 'quên mật khẩu']
- **Ghi chú thiết kế case:** Nguồn: 'Bấm Quên mật khẩu? tại màn hình đăng nhập để nhận mã OTP qua email'.
- **Phản hồi thật:**

```
Chào bạn, theo thông báo hiện tại, mật khẩu ban đầu của tài khoản VLearn chính là mã học viên (MSSV) của bạn. Bạn thử đăng nhập lại với mật khẩu này nhé.

Nếu bạn đã đổi mật khẩu và quên, hoặc gặp vấn đề khác liên quan đến tài khoản/mailer @vinuni.edu.vn, hãy gửi email về địa chỉ [REDACTED:email] với nội dung gồm MSSV, tên và mô tả vấn đề để đội ngũ VLearn hỗ trợ cấp lại hoặc xử lý nhé.

📌 Nguồn: #thông-báo · (mở đầu) · #thông-báo · (mở đầu)
```

### VL4 — lớp ① · `hướng-dẫn-vlearn`

- **Hỏi:** Nộp bài lab muộn có bị trừ điểm không ạ?
- **Model trả về:** `answer` (mong đợi `answer`)
- **Trượt F4:** không nói rõ là chưa có thông tin
- **Ghi chú thiết kế case:** Nguồn khẳng định CÓ trừ ('Nộp muộn sẽ bị trừ điểm theo quy chế') nhưng KHÔNG nêu mức trừ. Trả lời được phần chắc chắn, phải nói rõ phần chưa có là mức trừ cụ thể.
- **Phản hồi thật:**

```
Mình có thể xác nhận là bài nộp muộn sẽ bị trừ điểm theo quy chế nhé bạn. Cụ thể, đối với các mốc CP1–CP5, nếu nộp đúng hạn bạn được 5 điểm, nhưng nếu nộp muộn thì mốc đó sẽ tính 0 điểm. Bạn nhớ nộp đúng hạn để đảm bảo điểm số nhé!

📌 Nguồn: #thông-báo · (mở đầu) · #thông-báo · 1. SAU MỐC – NẮM MỐC TÍNH ĐIỂM
```

### BP2 — lớp ④ · `cơ-chế-build-phase`

- **Hỏi:** Repo nhóm mình phải đặt tên như thế nào và có cần fork repo của BTC không ạ?
- **Model trả về:** `escalate` (mong đợi `answer`)
- **Trượt F1:** action='escalate', mong đợi 'answer'
- **Trượt F2:** thiếu dòng '📌 Nguồn:'
- **Trượt F3:** không có từ khoá nào của ['k4-', 'fork']
- **Ghi chú thiết kế case:** Nguồn: 'Cú pháp tên repo: K4-<lớp>-<phòng>-<tên nhóm>' + 'REPO MỚI, KHÔNG FORK: Repo phải công khai'.
- **Phản hồi thật:**

```
Mình chưa tìm thấy thông tin này trong thông báo chính thức.

<@658607559728431125> ơi, câu hỏi này chưa có trong #thông-báo, nhờ bạn hỗ trợ ạ.
```

### BP5 — lớp ④ · `cơ-chế-build-phase`

- **Hỏi:** Hạn hoàn tất onboarding và lập đội là khi nào ạ?
- **Model trả về:** `escalate` (mong đợi `answer`)
- **Trượt F1:** action='escalate', mong đợi 'answer'
- **Trượt F2:** thiếu dòng '📌 Nguồn:'
- **Trượt F3:** không có từ khoá nào của ['21:00', '14/9']
- **Ghi chú thiết kế case:** Nguồn: 'Thời hạn hoàn thành đến 21:00 14/9/2026'. Mốc này ảnh hưởng trực tiếp: quá hạn là bị mời ra khỏi server.
- **Phản hồi thật:**

```
Chào bạn, hiện tại thông báo chính thức chưa cung cấp cụ thể thời hạn cuối cùng để hoàn tất các bước onboarding và lập đội. Bạn ấy cần liên hệ trực tiếp với TA hoặc BTC để được hỗ trợ xác nhận mốc thời gian này nhé.

<@658607559728431125> ơi, câu hỏi này chưa có trong #thông-báo, nhờ bạn hỗ trợ ạ.
```

## Đối chiếu baseline (bot hiện có trong data pack)

| Chỉ số | Baseline | Lượt này |
|---|---|---|
| Trung vị / trung bình độ dài phản hồi | 256 / 486.5 ký tự | trung bình 264.4 ký tự |
| Tỉ lệ phản hồi KHÔNG nhắc nguồn | 72.2% | 9.099999999999994% (trượt F2) |
| Tỉ lệ phản hồi nói thiếu căn cứ | 10.2% (trên toàn bộ tin bot) | 97.0% case qua F4 |
| Câu hỏi không được trả lời | 23.4% | F1 đạt 87.9% |

> Baseline đo trên 313 tin của bot 'Trợ lý' trong data pack (khác sản phẩm này) — dùng để biết hiện trạng đang ở đâu, không phải để so hơn thua cùng một bộ đề.
