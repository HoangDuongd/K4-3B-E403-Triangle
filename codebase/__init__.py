"""Module quyết định trung tâm của Trợ lý AI20K.

Package này tách phần "AI thật sự quyết định" ra khỏi Discord để:
  - bot chạy production và harness chạy golden set dùng CHUNG một đường code;
  - mọi lượt gọi model đều đi qua một chỗ, nên ghi vết được đầy đủ.

Bản đồ file:
  config.py     — đọc .env, hằng số dùng chung
  prompts.py    — chỉ dẫn hệ thống + câu dự phòng
  tracing.py    — ghi vết prompt đầu vào / phản hồi thô ra JSONL
  retrieval.py  — chia đoạn thông báo + embedding + tìm kiếm (không biết Discord)
  decision.py   — MODULE QUYẾT ĐỊNH TRUNG TÂM: dựng nguồn, gọi model, phân xử action
  bot.py        — adapter Discord (lớp mỏng, chỉ chuyển sự kiện vào decision.py)
  demo_cli.py   — chạy một câu hỏi trong terminal, để quay video 30 giây
"""