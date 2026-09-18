"""Sinh eval/corpus/announcements.json từ cache .rag_cache.json.

VÌ SAO PHẢI CHE THÔNG TIN
-------------------------
Repo nộp bài bắt buộc để công khai. Kênh #thông-báo là kênh vận hành nội bộ
của khoá: trong đó có link Zoom kèm passcode, link mời Phoenix (có token), và
email. Đưa nguyên văn lên GitHub công khai là rò rỉ thông tin vận hành — không
phải vì dữ liệu người học (kênh này không có dữ liệu cá nhân), mà vì an toàn
của chính khoá.

Bản trong eval/ vì vậy đã che các chuỗi đó, nhưng GIỮ NGUYÊN mọi thông tin mà
bài kiểm thử cần: mốc thời gian, con số, quy định, cú pháp, tên mục. Nhờ vậy
người chấm chạy lại được toàn bộ golden set mà không cần quyền vào Discord.

Chạy:  python eval/build_corpus.py        (từ gốc repo, cần .rag_cache.json)
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

CACHE_PATH = os.path.join(BASE_DIR, ".rag_cache.json")
OUT_PATH = os.path.join(BASE_DIR, "eval", "corpus", "announcements.json")

# Quy tắc che — thứ tự quan trọng: che URL trước rồi mới tới mã nhúng trong URL
QUY_TAC = [
    # Link Zoom kèm pwd, và link rút gọn zoom.us
    (r"https?://[\w.-]*zoom\.us/\S+", "[link:zoom]"),
    (r"(?i)Meeting ID:\s*[\d ]+", "Meeting ID: [REDACTED]"),
    (r"(?i)Passcode:\s*\S+", "Passcode: [REDACTED]"),
    # Link mời Phoenix — có token trong đường dẫn
    (
        r"https?://phoenix\.note\.transformerlabs\.ai/\S+",
        "https://phoenix.note.transformerlabs.ai/[REDACTED:invite]",
    ),
    # Google Sheets / Docs nội bộ
    (r"https?://docs\.google\.com/\S+", "[link:google-doc]"),
    (r"https?://drive\.google\.com/\S+", "[link:google-drive]"),
    # Email
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "[REDACTED:email]"),
    # Tên người thật (giảng viên, lab coach, nhân sự chương trình).
    # Chính thông báo văn hoá của chương trình cũng nhắc: không đăng công khai
    # thông tin cá nhân của người khác khi chưa được đồng ý — nên bản công khai
    # trong repo cũng theo đúng chuẩn đó.
    (r"Lab Coach\s*-\s*Hoàng Blue'?s?", "[REDACTED:người]"),
    (r"Hoàng Blue", "[REDACTED:người]"),
    (r"ThS\s+Lê Anh Tiến", "[REDACTED:người]"),
    (r"Jimmy Lee", "[REDACTED:người]"),
    (r"\ba Đăng\b", "[người]"),
]


def che(text: str) -> str:
    for pattern, thay in QUY_TAC:
        text = re.sub(pattern, thay, text)
    return text


def main() -> None:
    if not os.path.exists(CACHE_PATH):
        raise SystemExit(
            f"Không thấy {CACHE_PATH}.\n"
            "Cache này do bot sinh ra khi chạy lần đầu trên Discord. "
            "Chạy `python -m codebase.bot` một lần, hoặc chép cache từ máy đã chạy."
        )

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)

    # Cache lưu theo ĐOẠN; gộp lại theo tin nhắn để snapshot giữ đúng đơn vị
    # "một tin nhắn thông báo" — giống thứ bot nhận được từ Discord.
    theo_tin: dict[int, dict] = {}
    for chunk in cache["chunks"]:
        mid = chunk["message_id"]
        if mid not in theo_tin:
            theo_tin[mid] = {
                "message_id": mid,
                "created_at": chunk["created_at"],
                # jump_url để rỗng: bản trong eval không trỏ về server thật.
                # compose_reply thấy rỗng thì trích nguồn bằng nhãn mục.
                "jump_url": "",
                "content": [],
            }
        theo_tin[mid]["content"].append(chunk["content"])

    messages = []
    for mid, m in sorted(theo_tin.items(), key=lambda kv: kv[1]["created_at"]):
        m["content"] = che("\n\n".join(m["content"]))
        messages.append(m)

    snapshot = {
        "meta": {
            "nguon": "kênh #thông-báo — Discord AI20K Build Phase Cohort 4",
            "so_tin_nhan": len(messages),
            "da_che": [
                "link Zoom + Meeting ID + Passcode",
                "link mời Phoenix (có token)",
                "link Google Docs/Sheets nội bộ",
                "địa chỉ email",
                "tên người thật (giảng viên, lab coach, nhân sự chương trình)",
            ],
            "ly_do": (
                "Repo nộp bài bắt buộc công khai; bản này giữ nguyên mốc thời gian, "
                "con số và quy định mà bài kiểm thử cần, chỉ che thông tin vận hành."
            ),
            "luu_y": (
                "Bot chạy thật index trực tiếp từ kênh Discord, không dùng file này. "
                "File này chỉ để chấm golden set tái lập được."
            ),
        },
        "messages": messages,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"Đã ghi {OUT_PATH}")
    print(f"  {len(messages)} tin nhắn")

    # Soát lại xem còn sót chuỗi nhạy cảm nào không. Cố tình dùng mẫu CHẶT để
    # không báo động giả với @Learner/@everyone hay template 26ai.<tên>@vinuni.edu.vn
    # (template đăng nhập, không phải địa chỉ của người thật).
    can_soat = [
        (r"zoom\.us/j/", "link Zoom"),
        (r"Passcode:\s*\d", "passcode"),
        (r"Meeting ID:\s*\d", "meeting id"),
        (r"transformerlabs\.ai/invite/", "link mời Phoenix"),
        (r"docs\.google\.com/\w+/d/", "link Google nội bộ"),
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "email thật"),
    ]
    sot = []
    for m in messages:
        for pattern, ten in can_soat:
            if re.search(pattern, m["content"]):
                sot.append(f"{ten} (msg {m['message_id']})")
    print(f"  chuỗi nhạy cảm còn sót: {sot or 'không có'}")


if __name__ == "__main__":
    main()