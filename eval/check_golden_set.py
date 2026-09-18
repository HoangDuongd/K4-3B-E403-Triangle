"""Kiểm tra golden_set.json có đúng yêu cầu của đề bài không.

Chạy trước mỗi lượt đo. Script này là bằng chứng coverage cho R4: nó đếm lại
từ chính file golden set chứ không tin vào lời khai trong phần "coverage".

    python eval/check_golden_set.py

Kiểm 4 nhóm:
  1. Cấu trúc   — mỗi case đủ trường bắt buộc, action hợp lệ
  2. Định lượng — đủ 20 case, 8–10 thường, 2–4 hiếm, ≥2 mỗi lớp, ≥10 từ chatlog
  3. Nhất quán — danh sách trong "coverage" phải khớp case thật
  4. Chính tả   — bắt lỗi gõ mất dấu tiếng Việt trong đề bài
"""

import json
import os
import re
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE_DIR, "eval", "golden_set.json")

ACTIONS = {"answer", "clarify", "escalate", "refuse", "out_of_scope", "introduce"}
LOP = {"①", "②", "③", "④"}
MUC_DO = {"thuong", "hiem", "chokho"}
TRUONG_BAT_BUOC = ["id", "muc_do", "lop", "chu_de", "nguon", "grid", "input", "expect"]

# Cụm từ tiếng Việt hay bị gõ mất dấu — nếu thấy trong đề bài thì gần như chắc chắn lỗi
MANGLED = [
    "câu hi", "đang hi", "(?<!ư)u tiên", "tra cu", "hi đáp", "khong", "nguoi ",
    "TUYT", "ĐI KHÔNG", "ĐU TƯ", "SAU MC", "Chng", "ct ", "thm quyn",
]


def main() -> None:
    with open(GOLDEN, encoding="utf-8") as f:
        gs = json.load(f)

    cases = gs["cases"]
    loi: list[str] = []
    canh_bao: list[str] = []

    # ---- 1. cấu trúc -----------------------------------------------------
    ids = [c["id"] for c in cases]
    trung = [i for i, n in Counter(ids).items() if n > 1]
    if trung:
        loi.append(f"id trùng: {trung}")

    for c in cases:
        for t in TRUONG_BAT_BUOC:
            if t not in c:
                loi.append(f"{c.get('id', '?')}: thiếu trường {t}")
        if c.get("muc_do") not in MUC_DO:
            loi.append(f"{c['id']}: muc_do lạ {c.get('muc_do')!r}")
        if c.get("lop") not in LOP:
            loi.append(f"{c['id']}: lớp lạ {c.get('lop')!r}")
        exp = c.get("expect", {})
        if exp.get("action") not in ACTIONS:
            loi.append(f"{c['id']}: action lạ {exp.get('action')!r}")
        if not c.get("input", "").strip():
            loi.append(f"{c['id']}: input rỗng")
        # Case mong đợi answer thì phải có cách kiểm "đúng trọng tâm" bằng máy
        if exp.get("action") == "answer" and not exp.get("must_include_any"):
            loi.append(f"{c['id']}: action=answer nhưng thiếu must_include_any")
        # Case mong đợi escalate phải yêu cầu báo thiếu căn cứ
        if exp.get("action") == "escalate" and not exp.get("must_flag_missing"):
            loi.append(f"{c['id']}: action=escalate nhưng thiếu must_flag_missing")

    # ---- 2. định lượng ---------------------------------------------------
    dem_muc_do = Counter(c["muc_do"] for c in cases)
    dem_lop = Counter(c["lop"] for c in cases)
    dem_chu_de = Counter(c["chu_de"] for c in cases)
    tu_chatlog = [c["id"] for c in cases if c["nguon"]["loai"] == "chatlog"]

    def kiem(ten, dieu_kien, thuc_te, yeu_cau):
        if not dieu_kien:
            loi.append(f"{ten}: có {thuc_te}, yêu cầu {yeu_cau}")

    kiem("tổng số case", len(cases) >= 20, len(cases), "≥20")
    kiem("case thường", 8 <= dem_muc_do["thuong"] <= 10, dem_muc_do["thuong"], "8–10")
    kiem("case hiếm", 2 <= dem_muc_do["hiem"] <= 4, dem_muc_do["hiem"], "2–4")
    kiem("case chỗ khó", dem_muc_do["chokho"] >= 8, dem_muc_do["chokho"], "≥8")
    for lop in sorted(LOP):
        kiem(f"lớp {lop}", dem_lop[lop] >= 2, dem_lop[lop], "≥2")
    kiem("case từ chatlog thật", len(tu_chatlog) >= 10, len(tu_chatlog), "≥10")

    # ---- 3. nhất quán với phần coverage ----------------------------------
    cov = gs["coverage"]
    kiem("coverage.tong_case", cov["tong_case"] == len(cases), cov["tong_case"], str(len(cases)))
    for lop, khoa in [("①", "① nguồn sự thật"), ("②", "② mơ hồ / thiếu thông tin"),
                      ("③", "③ ngoài phạm vi / thẩm quyền"), ("④", "④ đặc thù domain")]:
        that = sorted(c["id"] for c in cases if c["lop"] == lop)
        khai = sorted(cov["theo_lop_chokho"][khoa]["case"])
        if that != khai:
            loi.append(f"coverage lớp {lop} lệch: khai {khai} / thật {that}")
    for ten, ds in cov["theo_chu_de"].items():
        that = sorted(c["id"] for c in cases if c["chu_de"] == ten)
        if that != sorted(ds):
            loi.append(f"coverage chủ đề {ten!r} lệch: khai {sorted(ds)} / thật {that}")

    # ---- 4. chính tả -----------------------------------------------------
    for c in cases:
        for truong in ("input",):
            for m in MANGLED:
                if re.search(m, c[truong]):
                    canh_bao.append(f"{c['id']}.{truong}: nghi gõ mất dấu {m!r}")
        for khoa in ("ghi_chu", "must_not_contain"):
            for m in MANGLED:
                if re.search(m, json.dumps(c["expect"].get(khoa, ""), ensure_ascii=False)):
                    canh_bao.append(f"{c['id']}.expect.{khoa}: nghi gõ mất dấu {m!r}")

    # ---- in kết quả ------------------------------------------------------
    print(f"Golden set: {len(cases)} case")
    print(f"  theo mức độ : {dict(dem_muc_do)}")
    print(f"  theo lớp    : {dict(sorted(dem_lop.items()))}")
    print(f"  theo chủ đề : {dict(dem_chu_de)}")
    print(f"  từ chatlog  : {len(tu_chatlog)} case -> {tu_chatlog}")
    print(f"  quality bar : {gs['meta']['quality_bar']}")
    print()

    for c in canh_bao:
        print(f"  [CẢNH BÁO] {c}")
    for c in loi:
        print(f"  [LI] {c}")

    if loi:
        print(f"\n=> KHÔNG ĐẠT: {len(loi)} lỗi")
        sys.exit(1)
    print("=> ĐẠT: golden set đủ điều kiện để chạy lượt đo.")


if __name__ == "__main__":
    main()