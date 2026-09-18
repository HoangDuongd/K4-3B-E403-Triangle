"""Khai thác số liệu nền từ k4_messages.csv (data pack Discord khoá 4).

Mục đích: có con số THẬT để đối chiếu với kết quả golden set của sản phẩm mình.
Không có baseline thì "đạt 75%" không nói lên điều gì — phải biết hiện trạng
đang là bao nhiêu.

Bám đúng pain một câu của nhóm:
  "học viên có thể nhận câu trả lời QUÁ DÀI, KHÔNG SÁT INTENT hoặc KHÔNG CHỈ RA
   ĐƯỢC NGUỒN CHÍNH THỨC; hậu quả là không biết tin được cái nào, PHẢI HỎI LẠI
   hoặc LIÊN HỆ TA THỦ CÔNG."

Nên bốn nhóm chỉ số dưới đây đo đúng bốn vế của pain đó.

Chạy:  python eval/mine_baseline.py <đường-dẫn-k4_messages.csv>
Mặc định tìm k4_messages.csv ở gốc repo, rồi tới repo đề bài cạnh nó.
"""

import csv
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(BASE_DIR, "eval", "results", "baseline.json")

DUONG_DAN_MAC_DINH = [
    os.path.join(BASE_DIR, "k4_messages.csv"),
    os.path.join(
        os.path.dirname(BASE_DIR),
        "K4-3B-Day05-06-AI-Product-Hackathon",
        "data",
        "discord-pack",
        "k4_messages.csv",
    ),
]

# --- nhận diện câu hỏi -------------------------------------------------------
DAU_HOI = re.compile(
    r"\?|(\b(khi nào|bao giờ|mấy giờ|ở đâu|như thế nào|ntn|thế nào|sao|"
    r"deadline|hạn|link|điểm danh|ticket|standup|xp|cho (em|mình|tớ|mk) hỏi|"
    r"cho hỏi|ai biết|cho em xin)\b)",
    re.I,
)

# --- 5 chủ đề dữ liệu hiện có của bot ----------------------------------------
# Thứ tự quan trọng: chủ đề đứng trước được ưu tiên khi một tin khớp nhiều nhóm.
CHU_DE = [
    (
        "hướng dẫn VLearn",
        r"vlearn|slide|lasso|tutor|codelab|\blab\b|đăng nhập|mật khẩu|26ai|"
        r"nộp bài|otp|tài khoản|phoenix",
    ),
    (
        "lịch workshop",
        r"workshop|\bws\d?\b|zoom|kick.?off|diễn giả|buổi học|thời lượng|lịch học",
    ),
    (
        "cơ chế build-phase",
        r"onboarding|ticket|standup|mentor duty|\bxp\b|đề tài|project bank|"
        r"team|đội|sprint|\bgate\b|repo|github|hồ sơ",
    ),
    (
        "các mốc mini-hackathon",
        r"\bcp[1-6]\b|mốc|điểm|giải|cụm|chung kết|đầu tư|rubric|\br[1-7]\b|"
        r"hackathon|pitch|slide pdf",
    ),
    (
        "văn hóa - nội quy - trang phục",
        r"trang phục|nội quy|văn hóa|kích thích|ứng xử|quy tắc|tôn trọng|"
        r"điểm danh|vắng|nghỉ",
    ),
]


def xep_chu_de(text: str) -> str:
    low = text.lower()
    for ten, pattern in CHU_DE:
        if re.search(pattern, low, re.I):
            return ten
    return "khác"


def chuan_hoa(text: str) -> str:
    """Chuẩn hoá để đếm câu hỏi lặp: bỏ tag, dấu câu, khoảng trắng, viết thường."""
    t = re.sub(r"\[@[A-Z]+\]|<@!?\d+>|@\w+", " ", text)
    t = re.sub(r"[^\w\s]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def tim_duong_dan() -> str:
    for p in DUONG_DAN_MAC_DINH:
        if os.path.exists(p):
            return p
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return sys.argv[1]
    raise SystemExit(
        "Không tìm thấy k4_messages.csv.\n"
        "Truyền đường dẫn: python eval/mine_baseline.py <đường-dẫn>"
    )


def main() -> None:
    path = tim_duong_dan()
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    nay = lambda r: r["is_bot"] == "True"
    nguoi = [r for r in rows if not nay(r)]
    bot = [r for r in rows if nay(r)]

    # ---- B. phân loại tin của người -------------------------------------
    cau_hoi = [r for r in nguoi if DAU_HOI.search(r["content"])]
    hoi_bot = [r for r in cau_hoi if r["mentions_bot"] == "True"]

    # ---- C. ai trả lời ai (theo chuỗi reply_to) --------------------------
    tra_loi_boi = defaultdict(list)
    for r in rows:
        if r["reply_to"]:
            tra_loi_boi[r["reply_to"]].append(r)

    def dem_duoc_tra_loi(ds):
        co_nguoi = co_bot = khong = 0
        for r in ds:
            replies = tra_loi_boi.get(r["msg_id"], [])
            if not replies:
                khong += 1
            elif any(not nay(x) for x in replies):
                co_nguoi += 1
            elif any(nay(x) for x in replies):
                co_bot += 1
        return co_nguoi, co_bot, khong

    ch_nguoi, ch_bot, ch_khong = dem_duoc_tra_loi(cau_hoi)
    bh_nguoi, bh_bot, bh_khong = dem_duoc_tra_loi(hoi_bot)

    # ---- D1. độ dài câu trả lời của bot ---------------------------------
    do_dai_bot = sorted(int(r["n_chars"]) for r in bot if r["n_chars"].isdigit())
    do_dai_nguoi = sorted(
        int(r["n_chars"]) for r in nguoi if r["n_chars"].isdigit()
    )

    def pct(ds, nguong):
        if not ds:
            return 0.0
        return 100.0 * sum(1 for x in ds if x > nguong) / len(ds)

    # ---- D2. có chỉ ra nguồn không --------------------------------------
    mau_nguon = re.compile(
        r"nguồn|tham chiếu|theo thông báo|xem thêm|https?://|docs\.google|"
        r"trích dẫn|link",
        re.I,
    )
    bot_co_nguon = [r for r in bot if mau_nguon.search(r["content"])]

    # ---- D3. câu trả lời rập khuôn (không sát intent) --------------------
    dem_bot = Counter(chuan_hoa(r["content"]) for r in bot)
    rập_khuôn = {k: v for k, v in dem_bot.items() if v >= 3 and k}

    # ---- E. câu hỏi lặp --------------------------------------------------
    dem_ch = Counter(chuan_hoa(r["content"]) for r in cau_hoi)
    lap = {k: v for k, v in dem_ch.items() if v >= 2 and len(k) > 15}

    # ---- F. phân bố 5 chủ đề --------------------------------------------
    chu_de_ch = Counter(xep_chu_de(r["content"]) for r in cau_hoi)

    # ---- G. lỗi thật của bot hiện có (bản tin) --------------------------
    # Chuỗi "nguồn tham chiếu" bị chèn vào giữa từ — lỗi đã biết ở k4_daily_reports
    loi_chen = [
        r for r in bot if re.search(r"\w(nguồn tham chiếu|Nguồn tham chiếu)\w", r["content"])
    ]

    # ---- I. bot hiện tại có dám nói "chưa có căn cứ" không ----------------
    # Đây là vế "không biết tin được cái nào" của pain: nếu bot không bao giờ
    # nói thiếu căn cứ thì học viên không có tín hiệu nào để biết lúc nào nên
    # kiểm lại thông tin.
    mau_thieu_can_cu = re.compile(
        r"chưa có thông tin|không có thông tin|chưa cập nhật|chưa đủ căn cứ|"
        r"mình không nắm|mình không rõ|liên hệ TA|nhờ TA|tạo ticket",
        re.I,
    )
    bot_thieu_can_cu = [r for r in bot if mau_thieu_can_cu.search(r["content"])]

    # ---- J. độ phủ chủ đề "văn hóa - nội quy - trang phục" ----------------
    # Bot CÓ dữ liệu về chủ đề này trong #thông-báo, nhưng học viên có hỏi
    # không? Chênh lệch này quyết định có nên đưa chủ đề vào golden set hay không.
    tu_khoa_van_hoa = ["trang phục", "nội quy", "văn hóa", "kích thích", "ứng xử", "quy tắc"]
    do_phu_van_hoa = {
        kw: {
            "tin_nguoi": sum(1 for r in nguoi if kw in r["content"].lower()),
            "tin_bot": sum(1 for r in bot if kw in r["content"].lower()),
        }
        for kw in tu_khoa_van_hoa
    }

    kq = {
        "nguon_du_lieu": {
            "file": os.path.basename(path),
            "tong_tin": len(rows),
            "tin_nguoi": len(nguoi),
            "tin_bot": len(bot),
            "so_kenh": len({r["channel"] for r in rows}),
            "so_tac_gia": len({r["author"] for r in rows}),
            "tu_ngay": min(r["created_at_vn"][:10] for r in rows),
            "den_ngay": max(r["created_at_vn"][:10] for r in rows),
        },
        "A_khoi_luong_hoi_dap": {
            "tin_nguoi": len(nguoi),
            "tin_nguoi_la_cau_hoi": len(cau_hoi),
            "ty_le_cau_hoi_pct": round(100.0 * len(cau_hoi) / len(nguoi), 1),
            "cau_hoi_tag_bot": len(hoi_bot),
            "ty_le_tag_bot_pct": round(100.0 * len(hoi_bot) / len(cau_hoi), 1),
        },
        "B_ty_le_duoc_tra_loi": {
            "moi_cau_hoi": {
                "tra_loi_boi_nguoi": ch_nguoi,
                "tra_loi_boi_bot": ch_bot,
                "khong_ai_tra_loi": ch_khong,
                "ty_le_khong_ai_tra_loi_pct": round(100.0 * ch_khong / len(cau_hoi), 1),
            },
            "cau_hoi_tag_bot": {
                "tra_loi_boi_nguoi": bh_nguoi,
                "tra_loi_boi_bot": bh_bot,
                "khong_ai_tra_loi": bh_khong,
                "ty_le_phai_nho_nguoi_tra_loi_pct": round(100.0 * bh_nguoi / len(hoi_bot), 1)
                if hoi_bot
                else 0.0,
                "ty_le_khong_ai_tra_loi_pct": round(100.0 * bh_khong / len(hoi_bot), 1)
                if hoi_bot
                else 0.0,
            },
        },
        "C_do_dai_cau_tra_loi": {
            "bot_trung_binh": round(statistics.mean(do_dai_bot), 1) if do_dai_bot else 0,
            "bot_trung_vi": round(statistics.median(do_dai_bot), 1) if do_dai_bot else 0,
            "bot_dai_nhat": max(do_dai_bot) if do_dai_bot else 0,
            "bot_tren_500_ky_tu_pct": round(pct(do_dai_bot, 500), 1),
            "bot_tren_1000_ky_tu_pct": round(pct(do_dai_bot, 1000), 1),
            "nguoi_trung_vi": round(statistics.median(do_dai_nguoi), 1) if do_dai_nguoi else 0,
        },
        "D_co_chi_ra_nguon": {
            "bot_co_nguon": len(bot_co_nguon),
            "bot_khong_nguon": len(bot) - len(bot_co_nguon),
            "ty_le_khong_nguon_pct": round(100.0 * (len(bot) - len(bot_co_nguon)) / len(bot), 1)
            if bot
            else 0.0,
        },
        "E_cau_tra_loi_rap_khuon": {
            "so_mau_lap_lai": len(rập_khuôn),
            "so_tin_bi_lap": sum(rập_khuôn.values()),
            "ty_le_pct": round(100.0 * sum(rập_khuôn.values()) / len(bot), 1) if bot else 0.0,
        },
        "F_cau_hoi_lap": {
            "so_nhom_cau_hoi_lap": len(lap),
            "so_tin_lap": sum(lap.values()),
            "ty_le_pct": round(100.0 * sum(lap.values()) / len(cau_hoi), 1) if cau_hoi else 0.0,
        },
        "G_phan_bo_chu_de": dict(chu_de_ch.most_common()),
        "H_loi_chen_chuoi_nguon": {
            "so_tin_bot_dinh_loi": len(loi_chen),
        },
        "I_bao_thieu_can_cu": {
            "so_tin_bot": len(bot_thieu_can_cu),
            "ty_le_pct": round(100.0 * len(bot_thieu_can_cu) / len(bot), 1) if bot else 0.0,
            "ghi_chu": "bot có nói 'chưa có thông tin' / 'tạo ticket' không",
        },
        "J_do_phu_chu_de_van_hoa": do_phu_van_hoa,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(kq, f, ensure_ascii=False, indent=2)

    print(f"Nguồn: {kq['nguon_du_lieu']['file']} — {len(rows)} tin\n")
    for nhom, gia_tri in kq.items():
        if nhom == "nguon_du_lieu":
            continue
        print(f"[{nhom}]")
        if nhom == "G_phan_bo_chu_de":
            for k, v in gia_tri.items():
                print(f"    {k}: {v}")
        else:
            for k, v in gia_tri.items():
                if isinstance(v, dict):
                    print(f"    {k}:")
                    for k2, v2 in v.items():
                        print(f"        {k2}: {v2}")
                else:
                    print(f"    {k}: {v}")
        print()
    print(f"-> {OUT_JSON}")


if __name__ == "__main__":
    main()