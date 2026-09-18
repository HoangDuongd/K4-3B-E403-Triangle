"""Cấu hình dùng chung — đọc từ .env, không hardcode token vào code.

Mọi giá trị ở đây đều có mặc định hợp lý để harness eval chạy được mà không
cần dựng biến môi trường riêng. Riêng token thì bắt buộc phải có trong .env.
"""

import os
import ssl

from dotenv import load_dotenv

# Gốc repo — dùng để tìm .env và cache, không phụ thuộc thư mục đang đứng
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chỉ định thẳng đường dẫn .env để không phụ thuộc cwd lúc chạy
load_dotenv(os.path.join(BASE_DIR, ".env"))

DISCORD_TOKEN = (os.getenv("DISCORD_TOKEN") or "").strip()
AI_BASE_URL = (os.getenv("BASE_URL") or "https://api.ai-box.vn").rstrip("/")
AI_TOKEN = (os.getenv("AUTH_TOKEN") or "").strip()
AI_MODEL = (os.getenv("MODEL") or "qwen3.7-flash").strip()
AI_MAX_TOKENS = int(os.getenv("MAX_TOKENS") or 4000)

# Tắt phần suy nghĩ nội bộ của model. Đo thực tế: 29.1s -> 0.6s (nhanh ~48 lần),
# đổi lại model suy xét ít hơn nên câu hỏi khó có thể kém chính xác hơn.
AI_THINKING = (os.getenv("THINKING") or "false").strip().lower() in ("1", "true", "yes", "on")

# Nhiệt độ thấp để việc PHÂN LOẠI ổn định. Đo thực tế: ở temperature mặc định,
# cùng một câu hỏi lúc trả "clarify" lúc trả "escalate", và chỉ số nguồn trích
# dẫn cũng lúc đúng lúc sai.
AI_TEMPERATURE = float(os.getenv("TEMPERATURE") or 0.2)

EMBED_MODEL = (os.getenv("EMBED_MODEL") or "qwen3.7-text-embedding").strip()
TA_USER_ID = int(os.getenv("TA_USER_ID") or 0)
TOP_K = int(os.getenv("TOP_K") or 4)

# Cache vector đặt ở gốc repo (file đã bị .gitignore) để vị trí không đổi
# khi code chuyển vào codebase/
CACHE_PATH = os.path.join(BASE_DIR, ".rag_cache.json")

ANNOUNCE_CHANNEL = "thông-báo"
DISCUSS_CHANNEL = "thảo-luận"

# Số tin gần nhất gửi kèm làm ngữ cảnh. Cố tình để ngắn: ngữ cảnh dài dễ khiến
# model trả lời dựa vào lượt trước thay vì dựa vào nguồn.
HISTORY_SIZE = 4

# Ghi vết các lượt gọi model của bot đang chạy (thư mục đã bị .gitignore).
# Harness eval tự truyền đường dẫn riêng nên không dùng hằng số này.
BOT_TRACE_PATH = os.path.join(BASE_DIR, "logs", "bot_calls.jsonl")

# Python trên Windows không dựng được chuỗi chứng chỉ của api.ai-box.vn từ kho cert
# hệ thống, nên dùng bundle CA sẵn có của certifi.
try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # certifi không có thì dùng kho cert hệ thống
    SSL_CONTEXT = ssl.create_default_context()