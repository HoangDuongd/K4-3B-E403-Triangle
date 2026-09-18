# `eval/` — Bộ kiểm thử và kết quả đo

Thư mục này trả lời câu hỏi: **sản phẩm đang đúng đến đâu, và con số đó có tin được không.**

Quality bar đã chốt cùng `spec.md` tại CP4 và **giữ nguyên sau đó**:
> **Đạt khi ≥75% case qua cả 5 tiêu chí F1–F5, VÀ không case nào ở lớp ③ vi phạm tiêu chí F5.**

---

## Chạy lại từ đầu

```bash
# 1. Kiểm golden set có đủ điều kiện không (đếm lại từ file, không tin lời khai)
python eval/check_golden_set.py

# 2. Số liệu nền từ data pack — cần k4_messages.csv (đã gitignore, không nằm trong repo)
python eval/mine_baseline.py

# 3. Chạy trọn bộ golden set qua đúng đường code sản phẩm
python eval/run_eval.py --run run3
```

Bước 2 cần `k4_messages.csv`. Script tự tìm ở gốc repo, rồi tới
`../K4-3B-Day05-06-AI-Product-Hackathon/data/discord-pack/`; không thấy thì truyền đường dẫn:

```bash
python eval/mine_baseline.py "đường/dẫn/tới/k4_messages.csv"
```

Bước 3 cần `.env` có `AUTH_TOKEN` hợp lệ, và **gọi model thật** — mất khoảng 90 giây cho 33 case.

---

## Bản đồ file

| File | Là gì |
|---|---|
| `golden_set.json` | 33 case, phân loại theo 4 lớp chỗ khó + 5 chủ đề + User Input Grid |
| `check_golden_set.py` | Kiểm cấu trúc, đếm lại coverage, bắt lỗi gõ mất dấu trong đề bài |
| `rubric.md` | 5 chiều chất lượng F1–F5, 6 nhóm lỗi có tên, đối chiếu baseline |
| `run_eval.py` | Harness: gọi `codebase/decision.py` + `compose_reply`, chấm, ghi kết quả |
| `mine_baseline.py` | Khai thác số liệu nền từ `k4_messages.csv` |
| `build_corpus.py` | Sinh `corpus/announcements.json` từ cache, **có che thông tin vận hành** |
| `corpus/announcements.json` | 25 thông báo `#thông-báo` đã che — để chấm eval tái lập được |
| `results/baseline.json` | Số liệu nền (bot hiện có trong data pack) |
| `results/runN.json` | Dữ liệu thô từng case: input, output, từng tiêu chí, lý do trượt |
| `results/runN.md` | Bảng kết quả + % + phân tích case trượt + đối chiếu baseline |
| `results/run2-notes.md` | **Đọc tay**: 7 phát hiện mà thước đo máy không bắt được |
| `results/grading_sheet.md` | 5 output để 2 thành viên chấm độc lập |
| `traces/runN.jsonl` | Prompt đầu vào + phản hồi thô của từng lượt gọi model |

---

## Đọc kết quả cho đúng

**`runN.md` là bản máy sinh.** Nó có bảng đủ mọi case (kể cả case chưa đạt), % theo từng
tiêu chí, % theo lớp, và phân tích lý do trượt của từng case.

**`run2-notes.md` là bản người đọc.** Máy không bắt được hai loại lỗi:
lỗi gộp phạm vi (E6) và lỗi giọng — xem `rubric.md`. Đọc file này **cùng với** `runN.md`,
đừng chỉ đọc con số.

**Con số có dao động.** Cùng một case, cùng câu hỏi, nhiệt độ 0.2, mà giữa hai lượt vẫn đổi
hành vi (LT4: `clarify` → `escalate`). Một case đổi = ±3% trên 33 case. Muốn kết luận thì
chạy vài lượt rồi xem xu hướng, đừng kết luận từ một lượt — nhất là khi khoảng cách tới bar
chỉ vài case.

---

## Luật khi sửa

Sửa **prompt hoặc code quyết định** thì phải chạy lại **trọn bộ**, không chạy vài case rồi
suy ra. Sửa chỗ này vỡ chỗ kia là chuyện thường.

Sửa **thước đo** (cách chấm) hoặc **case** thì phải ghi rõ lý do và chạy lại trọn bộ. Lượt
`run2` đã làm đúng như vậy: sửa 3 lỗi thước đo + 1 lỗi thiết kế case, lý do ghi trong
`golden_set.json` (case MH5) và trong `run2.md`.

**Không được đổi quality bar sau khi đã thấy kết quả.** Không đạt bar mà phân tích được
nguyên nhân vẫn tính đủ điểm; chỉnh sửa hoặc che số liệu thì không được tính.

---

## Bảo mật dữ liệu

`corpus/announcements.json` là bản **đã che**: link Zoom + Meeting ID + Passcode, link mời
Phoenix, link Google Docs/Sheets nội bộ, địa chỉ email, và tên người thật đều đã được thay
bằng nhãn. Mốc thời gian, con số và quy định — tức mọi thứ bài kiểm thử cần — giữ nguyên.

Sinh lại bản này từ cache bằng `python eval/build_corpus.py`; script tự soát lại xem còn sót
chuỗi nhạy cảm nào không.

Bot chạy thật **không dùng** file này — nó index trực tiếp từ kênh Discord. File này chỉ để
người chấm chạy lại được golden set mà không cần quyền vào server.

`k4_messages.csv` **không bao giờ được commit** (đã có trong `.gitignore`). Mọi case lấy từ
chatlog đều ghi mã `msg_id` thay vì dán nguyên văn, và mỗi trích dẫn không quá 2 câu theo
quy định của data pack.