# Ghi chú lượt đo — đọc tay từng output

> Bước 1 của guide §2.6: *"Chạy tay 10–20 input qua prototype, đọc từng output, ghi thô"*.
> File này là phần **máy không chấm được**, do người đọc và ghi lại.
> Số liệu máy nằm ở `run1.md` / `run2.md`; file này ghi những gì chỉ mắt người thấy.

Nguồn đọc: `eval/results/run1.json`, `eval/results/run2.json` (33 output mỗi lượt) và
`eval/traces/run1.jsonl`, `eval/traces/run2.jsonl` (prompt + phản hồi thô của từng lượt gọi model).

Các trích dẫn dưới đây là **nguyên văn**, chép từ file kết quả chứ không gõ lại.

---

## Phát hiện 1 · Sai thứ trong tuần — thước đo máy KHÔNG bắt được

**Case LT1** · `"Workshop 02 diễn ra khi nào và theo hình thức nào ạ?"`

Cả hai lượt, model đều trả:

> "Workshop 02 diễn ra vào lúc 20:00 tối ngày 13/09 (thứ Năm). Buổi học được tổ chức theo
> hình thức Online qua Zoom. Bạn nhớ vào sớm từ 19:50 để ổn định kỹ thuật nhé!"

Nhưng `13/09/2026` là **Chủ Nhật** — và chính corpus ghi rõ *"22h00 hôm nay, **Chủ Nhật**,
ngày 13/09/2026"*.

**Nguyên nhân gốc:** thông báo WS02 viết *"định kì tối **thứ 5 và chủ nhật hàng tuần** sẽ là
các Buổi WS, vào tối 13/9 ( hôm nay )"*. Model lấy "thứ 5" từ câu nói về **lịch định kì**
rồi gán vào **một buổi cụ thể**. Hai phạm vi khác nhau bị gộp làm một.

**Vì sao máy không bắt:** F2/F4 chỉ kiểm con số và mốc ngày có trace được về nguồn không.
"Thứ Năm" và "13/09" đều có trong nguồn — sai ở chỗ **ghép chúng lại với nhau**, mà kiểm
phép ghép thì cần suy luận lịch, không phải so chuỗi.

**Hậu quả:** học viên tin sai ngày và có thể bỏ lỡ buổi học. Đây đúng là lớp ④ — sai là
mất điểm/mất niềm tin ngay.

---

## Phát hiện 2 · Cùng họ lỗi với VL4 — gộp hai phạm vi

**Case VL4** · `"Nộp bài lab muộn có bị trừ điểm không ạ?"` — nguyên văn:

> "Mình có thể xác nhận là bài nộp muộn sẽ bị trừ điểm theo quy chế nhé bạn. Cụ thể, đối với
> các mốc CP1–CP5, nếu nộp đúng hạn bạn được 5 điểm, nhưng nếu nộp muộn thì mốc đó sẽ tính
> 0 điểm."

Nguồn nói **hai chuyện khác nhau** ở hai chỗ: (a) bài **lab** nộp muộn thì bị trừ điểm
*theo quy chế, không nêu mức*; (b) **mốc checkpoint** CP1–CP5 nộp muộn thì mất 5 điểm mốc đó.
Model lấy (b) trả lời cho (a).

Cùng cơ chế với phát hiện 1: **fact đúng, phạm vi sai**.

→ Gom hai cái này thành một nhóm lỗi có tên: **E6 · Gộp hai phạm vi khác nhau**, đã bổ sung
vào `eval/rubric.md`.

---

## Phát hiện 3 · 9,1% lượt model trả về `reply` rỗng

Trên `traces/`: **3/33 lượt ở mỗi lượt đo** model trả `{"action": "escalate", "reply": "", "sources": []}`
— JSON hợp lệ, hành vi đúng, nhưng phần chữ để gửi học viên **rỗng**.

Cả 3 lượt đều là `escalate`, và **`FALLBACK_REPLY` trong `codebase/prompts.py` đã cứu**:
học viên vẫn nhận được *"Mình chưa tìm thấy thông tin này trong thông báo chính thức."*
nên trải nghiệm không vỡ.

**Quan trọng: ba case bị rỗng KHÁC NHAU giữa hai lượt.**

| | Case có `reply` rỗng |
|---|---|
| run1 | MH4, VL2, BP5 |
| run2 | BP2, BP7, NL4 |

Không case nào rỗng ở cả hai lượt → đây là **lỗi hệ thống, không gắn với case nào**. Tỉ lệ
giống hệt ở hai lượt (đều 3/33) cũng cho thấy nó ổn định chứ không phải ngẫu nhiên.

**Đây là ứng viên số 1 để sửa trước demo** — sửa rẻ (kiểm tra `reply` rỗng rồi gọi lại một
lần, hoặc siết chỉ dẫn) và sửa được một lỗi ảnh hưởng 9% lượt.

---

## Phát hiện 4 · Truy xuất hụt là nguyên nhân lớn nhất của "phải hỏi lại"

Ba case model escalate trong khi nguồn **có** câu trả lời — kiểm trace thấy chunk đúng
**không được lấy ra** ở top-4. Kiểm riêng ở run2:

| Case | Câu hỏi | Chunk chứa câu trả lời | Chunk thực sự lấy về |
|---|---|---|---|
| **VL2** | Quên mật khẩu VLearn | *"Quên mật khẩu (3/4)"* — bấm Quên mật khẩu để nhận OTP | 3 đoạn `(mở đầu)` + `5 BƯỚC HỌC TẬP` |
| **BP5** | Hạn onboarding và lập đội | *"[REMIND] THÔNG BÁO HOÀN THIỆN CÁC BƯỚC ONBOARDING"* — dòng `🗓️ Thời hạn hoàn thành đến 21:00 14/9/2026` | **cùng mục** nhưng **đoạn khác**, không có dòng thời hạn |
| **MH6** | Nhóm 5 người có được thi | *"Cuộc thi tư duy sản phẩm AI"* — Nhóm 3–4 người | 4 mục khác, không có mục này |

Kiểm chứng BP5: dòng `21:00 14/9/2026` **không có** trong khối nguồn đã gửi cho model
(`'21:00 14/9' in nguon == False`), dù nó nằm ngay trong tin nhắn đã được truy xuất — chỉ là
**đoạn khác** của cùng tin nhắn đó.

Đây **chính là pain của nhóm tái hiện trên sản phẩm mình**: nguồn có mà không tới được tay
học viên → học viên phải hỏi lại hoặc nhờ TA. Đúng vế *"phải hỏi lại hoặc liên hệ TA thủ công"*.

Chú ý: 3 đoạn `(mở đầu)` chiếm chỗ trong top-4 ở VL2 — nhãn `(mở đầu)` là phần văn bản trước
tiêu đề đầu tiên, thường dài và chung chung, dễ hút điểm tương đồng.

---

## Phát hiện 5 · Nói "chưa có" trong khi nguồn CÓ

Bằng chứng lấy từ **run1** (ở run2, chính case này lại rơi vào nhóm `reply` rỗng của phát hiện 3).

**Case BP2** · `"Repo nhóm mình phải đặt tên như thế nào và có cần fork repo của BTC không ạ?"`
— run1 trả nguyên văn:

> "Chào bạn, hiện tại thông báo chính thức chưa có hướng dẫn cụ thể về cú pháp đặt tên repo
> nhóm cũng như quy định chi tiết về việc fork repo."

Nhưng chunk *"2. BA ĐIỀU ĐỂ LÀM SAI"* **đã được lấy về** và trong đó có nguyên văn:

> **02 • REPO MỚI, KHÔNG FORK:** Repo phải công khai; fork có thể mang data pack lên mạng.
> **Cú pháp tên repo:** `K4-<lớp>-<phòng>-<tên nhóm>`

Đây là lỗi **ngược** với bịa: không phải thêm thông tin không có, mà **phủ nhận thông tin
đang có**. Với học viên thì hậu quả y hệt — họ không nhận được câu trả lời và phải đi hỏi TA.

Đáng chú ý: thông tin nằm trong mục có tiêu đề *"BA ĐIỀU ĐỂ LÀM SAI"*, không có từ nào giống
"repo" ở tiêu đề — có thể vì vậy model coi nhẹ đoạn này.

---

## Phát hiện 6 · Bất ổn định giữa hai lượt — đọc số phải kèm cảnh báo này

**Case LT4** · `"Ngày mai mình có phải học không ạ?"` — đổi kết quả giữa hai lượt, dù
nhiệt độ chỉ 0.2 và không có gì thay đổi ở câu hỏi:

| | Hành vi | Phản hồi (nguyên văn, cắt ngắn) |
|---|---|---|
| run1 | `clarify` ✓ | *"Bạn vui lòng cho mình biết ngày mai cụ thể là ngày bao nhiêu (tháng/năm)…"* |
| run2 | `escalate` | *"Chào bạn, hiện tại thông báo chính thức chưa có lịch học cụ thể cho ngày mai…"* |

Cả hai phản hồi đều **không bịa**, nhưng `clarify` đúng hơn: câu hỏi mơ hồ thì phải hỏi lại,
không phải từ chối.

**Hệ quả cho việc đọc con số:** một case đổi trạng thái = ±3% trên tổng 33 case. Khoảng cách
giữa 81,8% và bar 75% là **2 case** — nằm trong biên độ dao động giữa các lượt. Vì vậy phải
chạy nhiều lượt rồi lấy xu hướng, không kết luận từ một lượt.

---

## Phát hiện 7 · Sai giọng ở một lượt escalate

**Case BP5** ở run2 — nguyên văn:

> "Chào bạn, hiện tại thông báo chính thức chưa cung cấp cụ thể thời hạn cuối cùng để hoàn tất
> các bước onboarding và lập đội. **Bạn ấy** cần liên hệ trực tiếp với TA hoặc BTC…"

Bot đang nói **với** học viên nhưng lại gọi học viên là *"bạn ấy"* như đang nói về người thứ ba.
Chỉ dẫn hệ thống yêu cầu xưng "mình" và gọi học viên là "bạn" — lượt này lệch giọng.

Mức độ nhẹ (không sai thông tin), nhưng đúng vào vế "không sát" của pain và vào nguyên tắc
HAX **G5 · hợp chuẩn mực xã hội**. Máy không chấm được vì không có tiêu chí nào cho giọng.

---

## Việc nên làm trước demo (xếp theo mức đau)

1. **Truy xuất hụt** (phát hiện 4) — ảnh hưởng nhiều case nhất và đúng vào pain. Hướng: tăng `TOP_K`,
   hoặc xử lý riêng các đoạn `(mở đầu)`, hoặc gộp đoạn theo mục trước khi embed.
2. **`reply` rỗng** (phát hiện 3) — 9% lượt, sửa rẻ, ảnh hưởng hệ thống.
3. **Gộp hai phạm vi** (phát hiện 1+2) — hậu quả nặng nhất về niềm tin nhưng khó sửa bằng prompt;
   cần thêm câu trong chỉ dẫn kiểu *"mỗi khẳng định phải thuộc đúng đối tượng được hỏi"*.
4. **Phủ nhận thông tin đang có** (phát hiện 5) — thêm chỉ dẫn *"trước khi nói chưa có, phải soát
   lại toàn bộ các đoạn nguồn, kể cả đoạn có tiêu đề không liên quan"*.

## Giới hạn đã biết của thước đo

- Thước đo máy **không bắt được** lỗi gộp phạm vi (E6) và lỗi giọng (phát hiện 7) — đây là lý do
  bắt buộc phải có bước đọc tay, và là lý do phiếu `grading_sheet.md` cho 2 người chấm độc lập
  vẫn cần thiết.
- Golden set chạy **từng case độc lập, `history` rỗng** — chưa đo phần NGỮ CẢNH GẦN ĐÂY của prompt.
- Chưa có case nào cho luồng TA ra lệnh (`TA_COMMAND_PROMPT`).